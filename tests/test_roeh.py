#!/usr/bin/env python3
"""Deterministic tests for the roeh CLI and hooks.

Every test here corresponds to a behaviour that was verified by hand once and
would otherwise silently rot. Three real bugs shipped in this repo before this
suite existed, and all three had the same shape: a guard that was written but
never exercised.

  - SCHEMA_VERSION was stamped into every config and never read back.
  - last_ingest was declared in the state dict and never written.
  - `init --force` reset the config wholesale, silently downgrading a
    sovereignty-critical `local` project to `repo` and orphaning its record.

None of those are subtle in hindsight. All three survived because nothing ran
them. That is what this file is for.

Tests drive the CLI as a SUBPROCESS rather than importing it, because the exit
code IS the contract: PreCompact blocking compaction is `exit 2` and nothing
else. A test that imported the module and asserted on return values would pass
while the real integration was broken.

Run:  python3 -m unittest discover -s tests -v
      tests/run
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin")
ROEH = os.path.join(BIN, "roeh")
PRECOMPACT = os.path.join(BIN, "roeh-precompact")
SESSIONSTART = os.path.join(BIN, "roeh-sessionstart")
SKELETON = os.path.join(ROOT, "templates", "decision-trace.skeleton.md")


class RoehCase(unittest.TestCase):
    """A throwaway git repo per test, under a throwaway HOME.

    HOME is sandboxed because roeh resolves several paths through `~`:
    transcripts and the memory directory live under ~/.claude/projects/<slug>,
    and a `local`-mode trace is written there outright. Without this, running
    the suite deposits directories in the developer's real ~/.claude tree — an
    early version of this file did exactly that. A test harness that mutates
    the environment it is testing is not a harness.
    """

    def setUp(self):
        # macOS hands out /var/... which is a symlink to /private/var; resolve
        # it so path comparisons against the CLI's own abspath() agree.
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="roeh-test-"))
        self.home = os.path.join(self.root, "home")
        self.dir = os.path.join(self.root, "repo")
        os.makedirs(self.home)
        os.makedirs(os.path.join(self.dir, "docs"))
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "test")
        self.write("a.txt", "one")
        self.git("add", "-A")
        self.git("commit", "-qm", "initial commit")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def assertSilent(self, out, msg=""):
        """A hook in a non-roeh project must surface nothing. Empty stdout and
        an empty JSON object are both valid no-ops; what matters is that
        neither carries a systemMessage or injected context."""
        body = out.strip()
        if not body:
            return
        d = json.loads(body)
        self.assertFalse(d.get("systemMessage"), msg)
        self.assertFalse(d.get("hookSpecificOutput"), msg)

    # -- helpers -----------------------------------------------------------

    def git(self, *args):
        return subprocess.run(["git", "-C", self.dir, *args],
                              capture_output=True, text=True)

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(text)
        return p

    def read(self, rel):
        with open(os.path.join(self.dir, rel)) as f:
            return f.read()

    def env(self, extra=None):
        e = dict(os.environ)
        e["HOME"] = self.home          # keeps ~/.claude out of reach
        e.pop("CLAUDE_PROJECT_DIR", None)
        if extra:
            e.update(extra)
        return e

    def roeh(self, *args, stdin=None, env=None):
        e = self.env(env)
        p = subprocess.run([sys.executable, ROEH, *args], cwd=self.dir,
                           capture_output=True, text=True, input=stdin, env=e)
        return p.returncode, p.stdout, p.stderr

    def hook(self, script, payload, env=None):
        e = self.env(env)
        payload.setdefault("cwd", self.dir)
        p = subprocess.run([sys.executable, script], cwd=self.dir,
                           capture_output=True, text=True,
                           input=json.dumps(payload), env=e)
        return p.returncode, p.stdout, p.stderr

    def init(self, *extra):
        code, out, err = self.roeh("init", *extra)
        self.assertEqual(code, 0, f"init failed: {err}")
        return out

    def make_trace(self):
        with open(SKELETON) as f:
            self.write("docs/decision-trace.md",
                       f.read().replace("{{PROJECT}}", "testproj"))

    def config(self):
        return json.loads(self.read(".claude/roeh.json"))

    def set_config(self, **kv):
        c = self.config()
        c.update(kv)
        self.write(".claude/roeh.json", json.dumps(c, indent=2))

    def commit(self, msg="work"):
        # mtime resolution is coarse; without this a commit can appear to
        # predate a trace written in the same second and `status` reads clean.
        time.sleep(1.1)
        self.write(f"f{time.time()}.txt", "x")
        self.git("add", "-A")
        self.git("commit", "-qm", msg)


class TestSlug(RoehCase):
    """The slug maps a project path to its Claude Code transcript directory.
    Getting it wrong means session mining silently finds nothing."""

    def test_slash_and_dot_both_become_dash(self):
        _, out, _ = self.roeh("slug", "/Users/x/projects/thing")
        self.assertEqual(out.strip(), "-Users-x-projects-thing")

    def test_dotted_directory(self):
        # Verified against a real on-disk transcript directory.
        _, out, _ = self.roeh("slug", "/Users/x/.claude/projects")
        self.assertEqual(out.strip(), "-Users-x--claude-projects")

    def test_worktree_path(self):
        _, out, _ = self.roeh("slug", "/Users/x/p/proj/.claude/worktrees/wt")
        self.assertEqual(out.strip(), "-Users-x-p-proj--claude-worktrees-wt")


class TestProjectRoot(RoehCase):
    """Root resolution must pick the NEAREST marker.

    The real-world shape that broke: a repo one level below a directory that
    has both .git and .claude. Since ~/.claude exists for every Claude Code
    user, an upward-per-marker search sent any repo without its own .claude/
    to the home directory."""

    def nested_repo(self, parent_markers):
        parent = os.path.join(self.root, "parent")
        child = os.path.join(parent, "child")
        os.makedirs(child)
        for m in parent_markers:
            os.makedirs(os.path.join(parent, m), exist_ok=True)
        subprocess.run(["git", "-C", child, "init", "-q"], capture_output=True)
        p = subprocess.run([sys.executable, ROEH, "config"], cwd=child,
                           capture_output=True, text=True, env=self.env())
        return child, json.loads(p.stdout)["root"]

    def test_child_git_beats_parent_claude(self):
        child, root = self.nested_repo([".claude"])
        self.assertEqual(root, child,
                         "a .claude/ above must not outrank .git/ right here")

    def test_child_git_beats_parent_with_both_markers(self):
        child, root = self.nested_repo([".git", ".claude"])
        self.assertEqual(root, child)

    def test_walks_up_when_the_child_has_nothing(self):
        parent = os.path.join(self.root, "p2")
        child = os.path.join(parent, "sub", "deep")
        os.makedirs(child)
        subprocess.run(["git", "-C", parent, "init", "-q"], capture_output=True)
        p = subprocess.run([sys.executable, ROEH, "config"], cwd=child,
                           capture_output=True, text=True, env=self.env())
        self.assertEqual(json.loads(p.stdout)["root"], parent)

    def test_explicit_config_outranks_a_nearer_bare_marker(self):
        parent = os.path.join(self.root, "p3")
        child = os.path.join(parent, "child")
        os.makedirs(os.path.join(child, ".claude"))
        os.makedirs(os.path.join(parent, ".claude"))
        with open(os.path.join(child, ".claude", "roeh.json"), "w") as f:
            json.dump({"version": 1, "mode": "repo"}, f)
        p = subprocess.run([sys.executable, ROEH, "config"], cwd=child,
                           capture_output=True, text=True, env=self.env())
        self.assertEqual(json.loads(p.stdout)["root"], child)


class TestInit(RoehCase):

    def test_fresh_init_writes_config(self):
        self.init()
        c = self.config()
        self.assertEqual(c["mode"], "repo")
        self.assertEqual(c["trace"], "docs/decision-trace.md")

    def test_local_mode_puts_trace_outside_the_repo(self):
        self.init("--local")
        _, out, _ = self.roeh("config")
        trace = json.loads(out)["trace_abs"]
        self.assertFalse(trace.startswith(self.dir + os.sep),
                         "local-mode trace must not live inside the repo")

    def test_reinit_refuses_and_changes_nothing(self):
        self.init()
        before = self.read(".claude/roeh.json")
        code, out, err = self.roeh("init")
        self.assertEqual(code, 1)
        self.assertIn("already initialised", out)
        self.assertEqual(before, self.read(".claude/roeh.json"))

    def test_reinit_reports_a_missing_trace(self):
        self.init()
        _, out, _ = self.roeh("init")
        self.assertIn("(missing)", out)

    def test_force_merges_and_preserves_customisation(self):
        """The bug: --force used to reset everything to defaults."""
        self.init()
        self.set_config(gate={"enabled": True}, trace="docs/custom.md")
        c = self.config()
        del c["sovereignty"]                       # simulate an older config
        self.write(".claude/roeh.json", json.dumps(c, indent=2))

        code, out, _ = self.roeh("init", "--force")
        self.assertEqual(code, 0)
        after = self.config()
        self.assertEqual(after["gate"], {"enabled": True}, "gate was reset")
        self.assertEqual(after["trace"], "docs/custom.md", "trace was reset")
        self.assertIn("sovereignty", after, "missing key was not filled in")

    def test_force_refuses_to_orphan_an_existing_record(self):
        self.init()
        self.make_trace()
        code, _, err = self.roeh("init", "--force", "--trace", "docs/other.md")
        self.assertEqual(code, 1)
        self.assertIn("refusing to repoint", err)
        self.assertEqual(self.config()["trace"], "docs/decision-trace.md")

    def test_force_may_repoint_when_no_record_exists(self):
        self.init()
        code, _, _ = self.roeh("init", "--force", "--trace", "docs/fresh.md")
        self.assertEqual(code, 0)
        self.assertEqual(self.config()["trace"], "docs/fresh.md")

    def test_force_refuses_local_to_repo_with_a_record(self):
        """The sovereignty downgrade. Must be refused, and must say WHY —
        the generic orphan message would bury the reason that matters."""
        self.init("--local")
        _, out, _ = self.roeh("config")
        trace = json.loads(out)["trace_abs"]
        self.assertTrue(trace.startswith(self.home),
                        "sandbox leak: local trace resolved outside test HOME")
        os.makedirs(os.path.dirname(trace), exist_ok=True)
        with open(SKELETON) as src, open(trace, "w") as dst:
            dst.write(src.read())
        code, _, err = self.roeh("init", "--force", "--repo")
        self.assertEqual(code, 1)
        self.assertIn("'local' to 'repo'", err)
        self.assertIn("git add", err)
        self.assertEqual(self.config()["mode"], "local")

    def test_absence_of_local_flag_is_not_a_vote_for_repo(self):
        self.init("--local")
        self.roeh("init", "--force")
        self.assertEqual(self.config()["mode"], "local")


class TestStatus(RoehCase):

    def test_reports_no_trace(self):
        self.init()
        _, out, _ = self.roeh("status")
        self.assertIn("no trace", out)

    def test_clean_when_nothing_happened_since(self):
        self.init()
        self.make_trace()
        _, out, _ = self.roeh("status")
        self.assertIn("current", out)

    def test_detects_commits_since_the_trace_was_written(self):
        self.init()
        self.make_trace()
        self.commit("a real decision")
        _, out, _ = self.roeh("status")
        self.assertIn("1 commit(s) unrecorded", out)
        self.assertIn("a real decision", out)

    def test_json_shape(self):
        self.init()
        self.make_trace()
        self.commit()
        _, out, _ = self.roeh("status", "--json")
        s = json.loads(out)
        self.assertTrue(s["behind"])
        self.assertEqual(len(s["commits"]), 1)


class TestAppend(RoehCase):
    """append is the ONLY write path to the record, and must be incapable of
    rewriting it."""

    def setUp(self):
        super().setUp()
        self.init()
        self.make_trace()

    def test_appends(self):
        before = len(self.read("docs/decision-trace.md"))
        self.roeh("append", "-", stdin="\n- **[DECISION]** chose X\n")
        after = self.read("docs/decision-trace.md")
        self.assertGreater(len(after), before)
        self.assertIn("chose X", after)

    def test_never_truncates_across_many_appends(self):
        sizes = []
        for i in range(5):
            self.roeh("append", "-", stdin=f"\n- entry {i}\n")
            sizes.append(len(self.read("docs/decision-trace.md")))
        self.assertEqual(sizes, sorted(sizes), "file must only ever grow")
        body = self.read("docs/decision-trace.md")
        for i in range(5):
            self.assertIn(f"entry {i}", body, "an earlier append was lost")

    def test_refuses_empty(self):
        code, _, err = self.roeh("append", "-", stdin="   \n")
        self.assertEqual(code, 1)
        self.assertIn("refusing", err)

    def test_refuses_when_no_trace_exists(self):
        os.remove(os.path.join(self.dir, "docs/decision-trace.md"))
        code, _, err = self.roeh("append", "-", stdin="x")
        self.assertEqual(code, 1)
        self.assertIn("no trace", err)

    def test_inserts_a_newline_when_the_file_lacks_one(self):
        self.write("docs/decision-trace.md", "no trailing newline")
        self.roeh("append", "-", stdin="appended\n")
        self.assertEqual(self.read("docs/decision-trace.md"),
                         "no trailing newline\nappended\n")

    def test_clears_staleness(self):
        self.commit()
        _, out, _ = self.roeh("status", "--json")
        self.assertTrue(json.loads(out)["behind"])
        self.roeh("append", "-", stdin="\n- recorded\n")
        _, out, _ = self.roeh("status", "--json")
        self.assertFalse(json.loads(out)["behind"])


class TestPending(RoehCase):
    """The PreCompact -> scribe handshake. Hook handlers inside one event have
    no documented order, so this sentinel is what makes the design
    order-independent."""

    def setUp(self):
        super().setUp()
        self.init()
        self.make_trace()

    def test_absent_by_default(self):
        code, _, _ = self.roeh("pending")
        self.assertEqual(code, 1, "no sentinel must exit non-zero")

    def test_write_then_read(self):
        self.roeh("pending", "--write", stdin=json.dumps({"trigger": "manual"}))
        code, out, _ = self.roeh("pending")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["trigger"], "manual")

    def test_clear(self):
        self.roeh("pending", "--write", stdin=json.dumps({"trigger": "manual"}))
        self.roeh("pending", "--clear")
        self.assertEqual(self.roeh("pending")[0], 1)

    def test_expires(self):
        """A scribe consulted by hand an hour later must not silently start
        writing to the record because of a stale sentinel."""
        self.roeh("pending", "--write", stdin=json.dumps({"trigger": "manual"}))
        p = os.path.join(self.dir, ".claude", "roeh-pending.json")
        with open(p) as f:
            d = json.load(f)
        d["at"] -= 3600
        with open(p, "w") as f:
            json.dump(d, f)
        self.assertEqual(self.roeh("pending")[0], 1)


class TestIngestLifecycle(RoehCase):
    """An ingest that dies partway leaves a trace that reads exactly like a
    finished one. These states are what make that detectable."""

    def setUp(self):
        super().setUp()
        self.init()

    def test_none_before_anything(self):
        _, out, _ = self.roeh("ingest", "status")
        self.assertIn("none", out)

    def test_unknown_for_a_trace_with_no_lifecycle_record(self):
        self.make_trace()
        _, out, _ = self.roeh("ingest", "status")
        self.assertIn("unknown", out)

    def test_running_while_units_outstanding(self):
        self.make_trace()
        self.roeh("ingest", "begin", "--floor", "2026-07-24", "--plan", "C1,C2,M")
        self.roeh("ingest", "done", "C1")
        _, out, _ = self.roeh("ingest", "status", "--json")
        s = json.loads(out)
        self.assertEqual(s["state"], "running")
        self.assertEqual(s["missing"], ["C2", "M"])

    def test_refuses_to_close_with_work_outstanding(self):
        self.make_trace()
        self.roeh("ingest", "begin", "--plan", "C1,C2")
        self.roeh("ingest", "done", "C1")
        code, _, err = self.roeh("ingest", "end")
        self.assertEqual(code, 1)
        self.assertIn("refusing to close", err)

    def test_becomes_abandoned_after_the_stale_window(self):
        self.make_trace()
        self.roeh("ingest", "begin", "--plan", "C1,C2")
        p = os.path.join(self.dir, ".claude", "roeh-state.json")
        with open(p) as f:
            d = json.load(f)
        d["ingest"]["started"] -= 7 * 3600
        with open(p, "w") as f:
            json.dump(d, f)
        _, out, _ = self.roeh("ingest", "status")
        self.assertIn("abandoned", out)

    def test_clean_close(self):
        self.make_trace()
        self.roeh("ingest", "begin", "--plan", "C1")
        self.roeh("ingest", "done", "C1")
        code, out, _ = self.roeh("ingest", "end")
        self.assertEqual(code, 0)
        self.assertIn("complete", out)

    def test_force_close_records_the_gap(self):
        self.make_trace()
        self.roeh("ingest", "begin", "--plan", "C1,C2")
        self.roeh("ingest", "done", "C1")
        self.roeh("ingest", "end", "--force")
        _, out, _ = self.roeh("ingest", "status", "--json")
        self.assertEqual(json.loads(out)["state"], "partial-closed")

    def test_abandon_does_not_touch_the_record(self):
        """Abandoning a run must never become a back door to editing the
        append-only trace."""
        self.make_trace()
        self.roeh("ingest", "begin", "--plan", "C1")
        before = self.read("docs/decision-trace.md")
        self.roeh("ingest", "abandon")
        self.assertEqual(before, self.read("docs/decision-trace.md"))


class TestIndexAndRetrieval(RoehCase):
    """The answer to a trace outgrowing a single read."""

    def big_trace(self):
        self.init()
        body = ["# T", "", "## §1 — Principles", "",
                "- **[PRINCIPLE]** one. Cite: `aaa1111`.", ""]
        # Multi-line entries, because that is what a real entry looks like: the
        # scribe requires the decision, the why, what was rejected, citations
        # and what it gates. A fixture of one-line bullets would make the index
        # look worthless, since the index line is longer than the source line.
        for i in range(40):
            body += [f"### 2026-09-{i%28+1:02d} — chapter {i}", "",
                     f"- **[DECISION]** decided thing {i}. WHY: the obvious",
                     f"  approach failed under load and this one did not.",
                     f"  REJECTED: the obvious approach, which needed a lock.",
                     f"  GATES: nothing further. Cite: `sha{i:04d}`.",
                     f"- `[LESSON]` learned thing {i}. The measurement moved",
                     f"  from 512 to 128 once the tokenizer changed, and the",
                     f"  old figure had been quoted twice before anyone checked.", ""]
        body += ["### 2026-10-01 — later", "",
                 "- **[REVERSAL — of decided thing 3]** overturned. Cite: `zzz9999`.",
                 "", "## §5 — Resume state", "", "- **Where we are:** here", ""]
        self.write("docs/decision-trace.md", "\n".join(body) + "\n")

    def test_index_finds_both_tag_dialects(self):
        """`- **[TAG]**` and `` - `[TAG]` `` must both count. Recognising only
        one dialect under-reports silently, which for an index is fatal."""
        self.big_trace()
        code, out, _ = self.roeh("index")
        self.assertEqual(code, 0, out)
        idx = self.read("docs/decision-trace-index.md")
        self.assertEqual(idx.count("`DECISION`"), 40)
        self.assertEqual(idx.count("`LESSON`"), 40, "backtick dialect missed")

    def test_index_does_not_mistake_wikilinks_for_tags(self):
        self.init()
        self.make_trace()
        self.roeh("append", "-", stdin="\n- **[[some-wikilink]]** not a tag\n")
        self.roeh("index")
        self.assertNotIn("some-wikilink", self.read("docs/decision-trace-index.md"))

    def test_index_surfaces_supersessions_first(self):
        self.big_trace()
        self.roeh("index")
        idx = self.read("docs/decision-trace-index.md")
        self.assertIn("Supersessions and dead-ends", idx)
        head = idx.split("## All entries")[0]
        self.assertIn("REVERSAL", head, "reversal not surfaced before the bulk")

    def test_index_is_much_smaller_than_the_trace(self):
        self.big_trace()
        self.roeh("index")
        trace = len(self.read("docs/decision-trace.md"))
        idx = len(self.read("docs/decision-trace-index.md"))
        self.assertLess(idx, trace, "an index bigger than the trace is useless")

    def test_read_extracts_one_chapter_exactly(self):
        self.big_trace()
        _, out, _ = self.roeh("read", "2026-10-01")
        self.assertIn("overturned", out)
        self.assertNotIn("decided thing 0", out, "bled into a neighbouring chapter")

    def test_read_extracts_a_section(self):
        self.big_trace()
        _, out, _ = self.roeh("read", "§5")
        self.assertIn("Where we are", out)
        self.assertNotIn("[DECISION]", out)

    def test_chapters_returns_chapter_granularity(self):
        """A [REVERSAL] usually lives in a LATER chapter than what it
        overturns, so line-level results hand back dead claims."""
        self.big_trace()
        _, out, _ = self.roeh("chapters", "overturned")
        self.assertIn("2026-10-01", out)
        self.assertIn("roeh read", out, "must tell the caller how to pull it")

    def test_doctor_fails_past_threshold_without_an_index(self):
        self.big_trace()
        body = self.read("docs/decision-trace.md")
        self.write("docs/decision-trace.md", body + ("\n- filler" * 1600))
        code, out, _ = self.roeh("doctor")
        self.assertEqual(code, 1)
        self.assertIn("NO index", out)

    def test_doctor_warns_when_the_index_is_stale(self):
        self.big_trace()
        body = self.read("docs/decision-trace.md")
        self.write("docs/decision-trace.md", body + ("\n- filler" * 1600))
        self.roeh("index")
        time.sleep(1.1)
        self.roeh("append", "-", stdin="\n- **[DECISION]** later thing.\n")
        _, out, _ = self.roeh("doctor")
        self.assertIn("index is older than the trace", out)


class TestDoctor(RoehCase):

    def healthy(self):
        self.init()
        self.make_trace()
        self.git("add", "-A", "-f")
        self.git("commit", "-qm", "add trace")
        self.write(".gitignore", ".claude/roeh-state.json\n"
                                 ".claude/roeh-pending.json\n")
        self.roeh("ingest", "begin", "--plan", "C1")
        self.roeh("ingest", "done", "C1")
        self.roeh("ingest", "end")

    def test_fails_without_config(self):
        code, out, _ = self.roeh("doctor")
        self.assertEqual(code, 1)
        self.assertIn("no config", out)

    def test_healthy_project_passes(self):
        self.healthy()
        code, out, _ = self.roeh("doctor")
        self.assertEqual(code, 0, out)
        self.assertIn("ingest complete", out)

    def test_detects_missing_required_sections(self):
        """The oracle reads §0/§1/§5 in full at any trace size; their absence
        silently removes that guarantee."""
        self.healthy()
        body = self.read("docs/decision-trace.md")
        self.write("docs/decision-trace.md",
                   body.replace("## §1", "## gone").replace("## §5", "## gone"))
        code, out, _ = self.roeh("doctor")
        self.assertEqual(code, 1)
        self.assertIn("missing section", out)

    def test_detects_abandoned_ingest(self):
        self.init()
        self.make_trace()
        self.roeh("ingest", "begin", "--plan", "C1,C2")
        p = os.path.join(self.dir, ".claude", "roeh-state.json")
        with open(p) as f:
            d = json.load(f)
        d["ingest"]["started"] -= 7 * 3600
        with open(p, "w") as f:
            json.dump(d, f)
        code, out, _ = self.roeh("doctor")
        self.assertEqual(code, 1)
        self.assertIn("ABANDONED", out)

    def test_detects_local_trace_inside_the_repo(self):
        self.init()
        self.make_trace()
        self.set_config(mode="local")
        code, out, _ = self.roeh("doctor")
        self.assertEqual(code, 1)
        self.assertIn("INSIDE the repo", out)

    def test_warns_when_a_repo_trace_is_untracked(self):
        self.init()
        self.make_trace()
        _, out, _ = self.roeh("doctor")
        self.assertIn("NOT tracked by git", out)

    def test_detects_a_config_from_an_older_roeh(self):
        self.healthy()
        self.set_config(version=0)
        _, out, _ = self.roeh("doctor")
        self.assertIn("config schema v0", out)

    def test_fix_migrates_the_config(self):
        self.healthy()
        c = self.config()
        c["version"] = 0
        del c["gate"]
        self.write(".claude/roeh.json", json.dumps(c, indent=2))
        code, out, _ = self.roeh("doctor", "--fix")
        self.assertEqual(code, 0, out)
        after = self.config()
        self.assertEqual(after["version"], 1)
        self.assertIn("gate", after)

    def test_fix_never_touches_the_trace(self):
        self.healthy()
        self.set_config(version=0)
        before = self.read("docs/decision-trace.md")
        self.roeh("doctor", "--fix")
        self.assertEqual(before, self.read("docs/decision-trace.md"))


class TestPreCompactHook(RoehCase):
    """exit 2 is the contract that blocks compaction. Nothing else does."""

    def test_silent_without_a_config(self):
        """The plugin's hooks run in EVERY project once enabled. A project that
        does not use roeh must see nothing at all."""
        code, out, _ = self.hook(PRECOMPACT, {"trigger": "manual"})
        self.assertEqual(code, 0, "must never block a project that lacks roeh")
        self.assertSilent(out)

    def test_reports_current_when_nothing_is_owed(self):
        self.init()
        self.make_trace()
        code, out, _ = self.hook(PRECOMPACT, {"trigger": "manual"})
        self.assertEqual(code, 0)
        self.assertIn("current", json.loads(out)["systemMessage"])

    def test_manual_blocks_when_behind(self):
        self.init()
        self.make_trace()
        self.commit("unrecorded decision")
        code, _, err = self.hook(PRECOMPACT, {"trigger": "manual"})
        self.assertEqual(code, 2, "manual compaction must be blocked")
        self.assertIn("COMPACTION BLOCKED", err)
        self.assertIn("unrecorded decision", err)

    def test_auto_never_blocks(self):
        """Auto-compact fires when the window is already full; blocking there
        can wedge the session with nowhere to go."""
        self.init()
        self.make_trace()
        self.commit()
        code, out, _ = self.hook(PRECOMPACT, {"trigger": "auto"})
        self.assertEqual(code, 0)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("PRE-COMPACTION", ctx)

    def test_skip_env_bypasses_the_block(self):
        self.init()
        self.make_trace()
        self.commit()
        code, _, _ = self.hook(PRECOMPACT, {"trigger": "manual"},
                               env={"ROEH_SKIP": "1"})
        self.assertEqual(code, 0)

    def test_config_can_disable_the_manual_block(self):
        """These knobs were written into every config and never read for five
        versions. A gate whose switch does nothing is worse than no switch."""
        self.init()
        self.make_trace()
        self.commit()
        self.set_config(precompact={"block_manual": False, "nag_auto": True,
                                    "record": True})
        code, _, _ = self.hook(PRECOMPACT, {"trigger": "manual"})
        self.assertEqual(code, 0, "block_manual: false was ignored")

    def test_config_can_silence_the_auto_nag(self):
        self.init()
        self.make_trace()
        self.commit()
        self.set_config(precompact={"block_manual": True, "nag_auto": False,
                                    "record": True})
        code, out, _ = self.hook(PRECOMPACT, {"trigger": "auto"})
        self.assertEqual(code, 0)
        self.assertSilent(out, "nag_auto: false was ignored")

    def test_read_only_mode_withholds_the_sentinel(self):
        """record:false keeps a human as the only writer — the scribe still
        runs but finds nothing pending, so it drafts instead of appending."""
        self.init()
        self.make_trace()
        self.commit()
        self.set_config(precompact={"block_manual": True, "nag_auto": True,
                                    "record": False})
        code, out, _ = self.hook(PRECOMPACT, {"trigger": "manual"})
        self.assertEqual(code, 0, "read-only must never block")
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("READ-ONLY", ctx)
        self.assertEqual(self.roeh("pending")[0], 1,
                         "sentinel was written despite record:false")

    def test_read_only_still_allows_manual_append(self):
        """The line is drawn at automation, not at writing."""
        self.init()
        self.make_trace()
        self.set_config(precompact={"record": False})
        code, _, _ = self.roeh("append", "-", stdin="\n- deliberate entry\n")
        self.assertEqual(code, 0)
        self.assertIn("deliberate entry", self.read("docs/decision-trace.md"))

    def test_drops_the_sentinel_even_when_blocking(self):
        """Written before the block decision, so the scribe can read it whether
        it is dispatched before or after this hook."""
        self.init()
        self.make_trace()
        self.commit()
        self.hook(PRECOMPACT, {"trigger": "manual"})
        code, out, _ = self.roeh("pending")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["trigger"], "manual")


class TestSessionStartHook(RoehCase):

    def test_silent_without_a_config(self):
        code, out, _ = self.hook(SESSIONSTART, {"trigger": "startup"})
        self.assertEqual(code, 0)
        self.assertSilent(out)

    def test_compact_reinjects_the_resume_state(self):
        """Writing the record is pointless if nothing reads it back."""
        self.init()
        self.make_trace()
        _, out, _ = self.hook(SESSIONSTART, {"trigger": "compact"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("DECISION TRACE:", ctx)
        self.assertIn("§5", ctx)
        self.assertIn("Resume state", ctx)

    def test_compact_does_not_dump_the_whole_file(self):
        self.init()
        self.make_trace()
        body = self.read("docs/decision-trace.md")
        self.assertIn("§0", body)
        _, out, _ = self.hook(SESSIONSTART, {"trigger": "compact"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("Why this file exists", ctx,
                         "§5 extraction leaked other sections")

    def test_compact_injects_the_LAST_resume_state(self):
        """Append-only means §5 is superseded by appending a new §5. Reading the
        first one hands a stale state to the one context that cannot check it."""
        self.init()
        self.make_trace()
        self.roeh("append", "-", stdin=(
            "\n## §5 — Resume state (superseding)\n\n"
            "- **Where we are:** NEWEST-STATE-MARKER\n"))
        _, out, _ = self.hook(SESSIONSTART, {"trigger": "compact"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("NEWEST-STATE-MARKER", ctx)
        self.assertNotIn("Currently gated on", ctx,
                         "injected the superseded §5 instead of the latest")

    def test_startup_reports_current(self):
        self.init()
        self.make_trace()
        _, out, _ = self.hook(SESSIONSTART, {"trigger": "startup"})
        self.assertIn("current", json.loads(out)["systemMessage"])

    def test_startup_reports_staleness(self):
        self.init()
        self.make_trace()
        self.commit()
        _, out, _ = self.hook(SESSIONSTART, {"trigger": "startup"})
        self.assertIn("behind", json.loads(out)["systemMessage"])

    def test_surfaces_doctor_failures(self):
        self.init()
        self.make_trace()
        self.set_config(mode="local")          # trace now inside the repo
        _, out, _ = self.hook(SESSIONSTART, {"trigger": "startup"})
        d = json.loads(out)
        self.assertIn("doctor", d["systemMessage"])
        self.assertIn("INSIDE the repo",
                      d["hookSpecificOutput"]["additionalContext"])


class TestManifests(unittest.TestCase):
    """Cheap structural checks on the shipped manifests. A broken hooks.json
    fails silently at exactly the moment the record matters."""

    def load(self, rel):
        with open(os.path.join(ROOT, rel)) as f:
            return json.load(f)

    def test_plugin_and_marketplace_versions_agree(self):
        pv = self.load(".claude-plugin/plugin.json")["version"]
        mv = self.load(".claude-plugin/marketplace.json")["plugins"][0]["version"]
        self.assertEqual(pv, mv, "claude plugin tag refuses to release on a mismatch")

    def test_hooks_reference_files_that_exist(self):
        hooks = self.load("hooks/hooks.json")["hooks"]
        for event, entries in hooks.items():
            for entry in entries:
                for h in entry["hooks"]:
                    if h.get("type") != "command":
                        continue
                    path = h["command"].replace('"${CLAUDE_PLUGIN_ROOT}"', ROOT)
                    self.assertTrue(os.path.isfile(path), f"{event}: {path}")
                    self.assertTrue(os.access(path, os.X_OK),
                                    f"{event}: {path} is not executable")

    def test_agent_hooks_carry_a_prompt(self):
        """`type: agent` without `prompt` fails plugin validation."""
        hooks = self.load("hooks/hooks.json")["hooks"]
        for entries in hooks.values():
            for entry in entries:
                for h in entry["hooks"]:
                    if h.get("type") == "agent":
                        self.assertTrue(h.get("prompt", "").strip())

    def test_agents_pin_a_model(self):
        """Judgement agents must not inherit — an org default of a smaller
        model would silently downgrade them."""
        for name in ("oracle", "scribe"):
            with open(os.path.join(ROOT, "agents", f"{name}.md")) as f:
                head = f.read().split("---")[1]
            self.assertIn("model: opus", head, f"{name} is not pinned")

    def test_scribe_cannot_write(self):
        """Append-only is structural: the scribe has no Write or Edit tool."""
        with open(os.path.join(ROOT, "agents", "scribe.md")) as f:
            head = f.read().split("---")[1]
        self.assertIn("disallowedTools", head)
        for tool in ("Write", "Edit"):
            self.assertIn(tool, head.split("disallowedTools")[1].split("\n")[0])

    def test_bin_scripts_are_executable(self):
        for name in ("roeh", "roeh-precompact", "roeh-sessionstart"):
            p = os.path.join(BIN, name)
            self.assertTrue(os.access(p, os.X_OK), f"{name} lost its exec bit")

    def test_bin_scripts_compile(self):
        for name in ("roeh", "roeh-precompact", "roeh-sessionstart"):
            p = subprocess.run([sys.executable, "-m", "py_compile",
                                os.path.join(BIN, name)], capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr.decode())


if __name__ == "__main__":
    unittest.main(verbosity=2)
