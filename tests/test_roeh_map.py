"""Unit tests for the v3 read-path core (step 1): tokenizer, parser, graph, liveness.

Unlike tests/test_roeh.py (which drives the CLI as a subprocess because the exit code is the
contract), step 1 is pure functions, so these import and assert directly — the fastest way to
turn the spec's invariants into executable checks (impl-read-path.md §7).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
import roeh_map as rm  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "trace-v3.md")


def load():
    with open(FIXTURE, encoding="utf-8") as f:
        return f.read()


class Tokenizer(unittest.TestCase):
    def test_keeps_joined_identifiers_whole(self):
        toks = rm.tokenize("See hooks/precompact.py and find_project_root now")
        self.assertIn("hooks/precompact.py", toks)
        self.assertIn("find_project_root", toks)

    def test_lowercases_and_splits_and_drops_short(self):
        toks = rm.tokenize("The QUOKKA_flag is Set")
        self.assertIn("quokka_flag", toks)   # joined identifier, whole + lowered
        self.assertIn("the", toks)
        self.assertIn("set", toks)
        self.assertNotIn("is", toks)          # len < 3 dropped

    def test_deterministic(self):
        s = "hooks/precompact.py append-only guard"
        self.assertEqual(rm.tokenize(s), rm.tokenize(s))


class Parser(unittest.TestCase):
    def setUp(self):
        self.entries = rm.parse_entries(load())
        self.by = {e.id: e for e in self.entries}

    def test_counts_all_tagged_entries_not_untagged_bullets(self):
        # p01 + e01..e20 = 21; the plain "- first §5 block" bullets are untagged and excluded.
        self.assertEqual(len(self.entries), 21)
        self.assertEqual({e.id for e in self.entries}, {"p01"} | {"e%02d" % n for n in range(1, 21)})

    def test_both_dialects_recognized(self):
        self.assertEqual(self.by["e01"].dialect, "bold")
        self.assertEqual(self.by["e03"].dialect, "tick")
        ticks = {e.id for e in self.entries if e.dialect == "tick"}
        self.assertEqual(ticks, {"e03", "e05", "e09", "e13", "e16"})

    def test_metadata_comment_parsed(self):
        e = self.by["e01"]
        self.assertEqual(e.tag, "DECISION")
        self.assertEqual(e.cls, "decision")
        self.assertIs(e.atomic, True)
        self.assertEqual(e.date, "2026-08-10")
        self.assertEqual(e.topic_hint, ["hooks"])

    def test_atomic_false_parsed(self):
        self.assertIs(self.by["e12"].atomic, False)

    def test_visible_relations_and_cites(self):
        self.assertEqual(self.by["e03"].supersedes, ["e02"])
        self.assertEqual(self.by["e07"].supersedes, ["e06"])
        self.assertEqual(self.by["e07"].augments, ["e05"])
        self.assertEqual(self.by["e09"].conflicts, ["e08"])
        self.assertEqual(self.by["e01"].cites, ["hooks/precompact.py", "b8de529"])

    def test_lead_extracted(self):
        self.assertTrue(self.by["e01"].lead.startswith("PreCompact blocks"))


class Liveness(unittest.TestCase):
    def setUp(self):
        entries = rm.parse_entries(load())
        self.status, self.reasons = rm.compute_liveness(entries)

    def _ids(self, want):
        return {i for i, s in self.status.items() if s == want}

    def test_live_set(self):
        self.assertEqual(
            self._ids("live"),
            {"p01", "e01", "e04", "e05", "e07", "e08", "e09", "e13", "e18"},
        )

    def test_dead_set(self):
        self.assertEqual(
            self._ids("dead"),
            {"e02", "e03", "e06", "e10", "e14", "e19", "e20"},
        )

    def test_uncertain_set(self):
        self.assertEqual(
            self._ids("uncertain"),
            {"e11", "e12", "e15", "e16", "e17"},
        )

    def test_prose_only_reason(self):
        self.assertIn("prose-only", self.reasons["e11"])

    def test_non_atomic_superseded_reason(self):
        self.assertIn("non-atomic", self.reasons["e12"])

    def test_competing_successors_reason(self):
        self.assertIn("competing", self.reasons["e15"])
        self.assertIn("competing", self.reasons["e16"])

    def test_dangling_edge_reason(self):
        self.assertIn("dangling", self.reasons["e17"])

    def test_augments_and_conflicts_never_kill(self):
        # e05 is augmented (not superseded) → live; e08 has an inbound conflict → still live.
        self.assertEqual(self.status["e05"], "live")
        self.assertEqual(self.status["e08"], "live")


class ReviewFixes(unittest.TestCase):
    """One test per /code-review finding, each on a minimal input (not the fixture)."""

    def _live(self, txt):
        entries = rm.parse_entries(txt)
        return entries, {e.id: e for e in entries}, rm.compute_liveness(entries)

    def test_1_missing_id_does_not_collapse_and_is_loud(self):
        txt = (
            "- **[DECISION] A thing.** WHY: x.\n"
            "  <!-- roeh class=decision atomic=true date=2026-01-01 -->\n"
            "- **[DECISION] Another thing.** WHY: y.\n"
            "  <!-- roeh class=decision atomic=true date=2026-01-02 -->\n"
        )
        entries, _, (status, reasons) = self._live(txt)
        self.assertEqual(len(entries), 2)
        self.assertEqual(len({e.id for e in entries}), 2)      # no collapse to status[""]
        for e in entries:
            self.assertEqual(status[e.id], "uncertain")
            self.assertIn("missing id", reasons[e.id])

    def test_2_competing_successor_partial_conflict(self):
        txt = (
            "- **[DECISION] Target.**\n  <!-- roeh id=t1 atomic=true date=2026-01-01 -->\n"
            "- **[CORRECTION] sA.**\n  Supersedes: t1\n  <!-- roeh id=sA atomic=true date=2026-01-02 -->\n"
            "- **[CORRECTION] sB.**\n  Supersedes: t1\n  Conflicts: sA\n  <!-- roeh id=sB atomic=true date=2026-01-03 -->\n"
            "- **[CORRECTION] sC.**\n  Supersedes: t1\n  <!-- roeh id=sC atomic=true date=2026-01-04 -->\n"
        )
        _, _, (status, reasons) = self._live(txt)
        self.assertEqual(status["sC"], "uncertain")            # the lone unresolved successor
        self.assertIn("competing", reasons["sC"])
        self.assertNotIn("competing", reasons.get("sA", ""))   # sA/sB mutually conflict → resolved
        self.assertNotIn("competing", reasons.get("sB", ""))

    def test_3_multiple_uncertain_reasons_accumulate(self):
        txt = (
            "- **[CORRECTION] two ghosts.**\n  Supersedes: ghost1\n  Augments: ghost2\n"
            "  <!-- roeh id=g1 atomic=true date=2026-01-01 -->\n"
        )
        _, _, (_, reasons) = self._live(txt)
        self.assertIn("ghost1", reasons["g1"])
        self.assertIn("ghost2", reasons["g1"])                 # neither dropped

    def test_4_bold_lead_is_clean(self):
        lead = rm._lead("- **[DECISION] PreCompact blocks manual compaction, never auto.** WHY: auto fires.")
        self.assertEqual(lead, "PreCompact blocks manual compaction, never auto")

    def test_5_multiline_cites_accumulate(self):
        txt = (
            "- **[DECISION] multi cite.**\n  Cites: retrieval/a.py\n  Cites: b8de529\n"
            "  <!-- roeh id=mc atomic=true date=2026-01-01 -->\n"
        )
        _, by, _ = self._live(txt)
        self.assertEqual(by["mc"].cites, ["retrieval/a.py", "b8de529"])

    def test_6_fence_in_body_does_not_sever_metadata(self):
        txt = (
            "- **[DECISION] has a code block.**\n"
            "  ```\n  # run this\n  ```\n"
            "  <!-- roeh id=fb atomic=true date=2026-01-01 -->\n"
        )
        entries, by, _ = self._live(txt)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].id, "fb")                  # not "" — meta survived the `#`

    def test_7_duplicate_supersedes_id_not_competing(self):
        txt = (
            "- **[DECISION] t.**\n  <!-- roeh id=t atomic=true date=2026-01-01 -->\n"
            "- **[CORRECTION] dup.**\n  Supersedes: t, t\n  <!-- roeh id=d atomic=true date=2026-01-02 -->\n"
        )
        _, by, (status, reasons) = self._live(txt)
        self.assertEqual(by["d"].supersedes, ["t"])            # deduped
        self.assertNotIn("competing", reasons.get("d", ""))
        self.assertEqual(status["d"], "live")


class Step2Map(unittest.TestCase):
    def test_determinism(self):
        a = rm.build_map(load(), as_of="2026-08-24")
        b = rm.build_map(load(), as_of="2026-08-24")
        self.assertEqual(a.rendered, b.rendered)

    def test_coverage_every_entry_represented(self):
        m = rm.build_map(load())
        for e in rm.parse_entries(load()):
            covered = (e.id in m.live_ids or e.id in m.ledger_ids
                       or bool(m.id_regions[e.id] & m.header_regions))
            self.assertTrue(covered, "uncovered entry: %s" % e.id)

    def test_last_wins_preamble(self):
        m = rm.build_map(load())
        self.assertIn("fifth", m.rendered)             # §5 digest = LAST block
        self.assertNotIn("first §5 block", m.rendered)  # never the first

    def test_deprecated_region_retired(self):
        m = rm.build_map(load())
        self.assertEqual(m.states["deprecated"], "retired")

    def test_settled_via_injection_and_stability_breaks_it(self):
        txt = ("- **[DECISION] ancient but standing.**\n  Cites: old/x.py\n"
               "  <!-- roeh id=o1 class=decision atomic=true date=2020-01-01 topic-hint=old -->\n")
        settled = rm.build_map(txt, as_of="2026-08-24", D=180, modified_paths=frozenset())
        self.assertEqual(settled.states["old"], "settled")
        churned = rm.build_map(txt, as_of="2026-08-24", D=180, modified_paths={"old/x.py"})
        self.assertEqual(churned.states["old"], "hot")   # cited path recently modified → not stable

    def test_budget_collapse_and_fit(self):
        roomy = rm.build_map(load(), budget_tokens=5000)
        self.assertTrue(roomy.fits)
        self.assertEqual(roomy.collapsed, set())          # nothing collapsed when it fits
        tight = rm.build_map(load(), budget_tokens=80)
        self.assertGreaterEqual(len(tight.collapsed), 1)  # forced to collapse hot regions

    def test_bounded_fanout_groups_regions(self):
        parts = []
        for k in range(20):
            parts.append(
                "- **[DEAD-END] dead %d.**\n"
                "  <!-- roeh id=d%02d class=dead-end atomic=true date=2026-08-01 topic-hint=t%02d -->\n"
                % (k, k, k))
        m = rm.build_map("".join(parts), budget_tokens=100000)  # roomy: isolate fan-out from collapse
        self.assertGreaterEqual(len(m.header_regions), 20)
        region_section = m.rendered.split("## regions", 1)[1]
        hdr_lines = [l for l in region_section.splitlines() if l.startswith("- ")]
        self.assertLessEqual(len(hdr_lines), rm.MAX_FANOUT)          # grouped, not 20 lines
        self.assertTrue(any(l.startswith("- group ") for l in hdr_lines))


class Step2ReviewFixes(unittest.TestCase):
    def test_1_fenced_example_not_parsed_as_edge(self):
        txt = (
            "- **[DECISION] target t1.**\n  <!-- roeh id=t1 class=decision atomic=true date=2026-07-01 topic-hint=real -->\n"
            "- **[DECISION] has a fenced example.**\n"
            "  ```\n  Supersedes: t1\n  <!-- roeh id=FAKE -->\n  ```\n"
            "  Cites: real/a.py\n  <!-- roeh id=r1 class=decision atomic=true date=2026-08-01 topic-hint=real -->\n"
        )
        entries = rm.parse_entries(txt)
        by = {e.id: e for e in entries}
        self.assertIn("r1", by)                       # real id survives
        self.assertNotIn("FAKE", by)                  # fenced id ignored
        self.assertEqual(by["r1"].supersedes, [])     # fenced Supersedes ignored
        status, _ = rm.compute_liveness(entries)
        self.assertEqual(status["t1"], "live")        # not wrongly superseded

    def test_2_uncertain_surfaced_in_settled_region(self):
        txt = (
            "- **[DECISION] old standing thing.**\n  Cites: oldz/a.py\n"
            "  <!-- roeh id=z1 class=decision atomic=true date=2020-01-01 topic-hint=oldz -->\n"
            "- **[REVERSAL] we changed our minds long ago.**\n  Cites: oldz/a.py\n"
            "  <!-- roeh id=z2 class=reversal atomic=true date=2020-02-01 topic-hint=oldz -->\n"
        )
        m = rm.build_map(txt, as_of="2026-08-24", D=180, modified_paths=frozenset())
        self.assertEqual(m.states["oldz"], "settled")
        self.assertIn("z2", m.ledger_ids)             # uncertain not dropped by the settled header
        self.assertIn("UNCERTAIN z2", m.rendered)

    def test_3_fanout_bounded_at_large_scale(self):
        parts = [
            "- **[DEAD-END] d%d.**\n  <!-- roeh id=x%03d class=dead-end atomic=true date=2026-08-01 topic-hint=t%03d -->\n"
            % (k, k, k) for k in range(145)]
        m = rm.build_map("".join(parts), budget_tokens=10_000_000)
        self.assertGreaterEqual(len(m.header_regions), 145)
        region_section = m.rendered.split("## regions", 1)[1]
        hdr = [l for l in region_section.splitlines() if l.startswith("- ")]
        self.assertLessEqual(len(hdr), rm.MAX_FANOUT)   # >MAX_FANOUT^0 groups would break the invariant

    def test_4_unclassified_always_hot(self):
        txt = (
            "- **[DECISION] no topic no cite one.**\n  <!-- roeh id=u1 class=decision atomic=true date=2026-08-01 -->\n"
            "- **[WITHDRAWN] no topic no cite two.**\n  Supersedes: u1\n"
            "  <!-- roeh id=u2 class=withdrawn atomic=true date=2026-08-02 -->\n"
        )
        m = rm.build_map(txt)
        self.assertEqual(m.states["unclassified"], "hot")   # not retired despite all-dead
        self.assertIn("u1", m.ledger_ids)                   # stays visible, not a header count

    def test_5_as_of_default_is_today_not_frozen(self):
        import inspect
        self.assertIsNone(inspect.signature(rm.build_map).parameters["as_of"].default)
        txt = ("- **[DECISION] ancient.**\n  Cites: old/x.py\n"
               "  <!-- roeh id=o1 class=decision atomic=true date=2020-01-01 topic-hint=old -->\n")
        self.assertEqual(rm.build_map(txt).states["old"], "settled")   # 2020 vs a real 'today'


class Step3Bloom(unittest.TestCase):
    def _blooms(self):
        entries = rm.parse_entries(load())
        by = {e.id: e for e in entries}
        id_regions, region_ids = rm.assign_regions(entries)
        return entries, by, id_regions, rm.build_blooms(by, region_ids)

    def test_no_false_negative_over_whole_fixture(self):
        # THE guarantee: for every token in every entry, the entry's regions are in scope.
        entries, _, id_regions, blooms = self._blooms()
        for e in entries:
            for tok in rm.tokenize(e.text):
                hits = rm.scope_literal(tok, blooms)
                for r in id_regions[e.id]:
                    self.assertIn(r, hits, "false negative: token %r missing region %r" % (tok, r))

    def test_scope_literal_targeted(self):
        _, _, _, blooms = self._blooms()
        self.assertIn("retrieval", rm.scope_literal("quokka_flag", blooms))  # e18 lives in retrieval

    def test_tokenizer_symmetry_is_the_basis(self):
        # scope and build_blooms must share the tokenizer; assert they do (same callable).
        b = rm.bloom_of_tokens(rm.tokenize("hooks/precompact.py"))
        self.assertTrue(rm.bloom_contains(b, "hooks/precompact.py"))

    def test_build_map_exposes_blooms(self):
        m = rm.build_map(load())
        self.assertIn("retrieval", m.blooms)
        self.assertIn("retrieval", rm.scope_literal("quokka_flag", m.blooms))

    def test_saturation_subdivides_below_threshold(self):
        txt = "".join(
            "- **[DECISION] unique token zzz%03d here.**\n"
            "  <!-- roeh id=s%03d class=decision atomic=true date=2026-08-%02d topic-hint=big -->\n"
            % (k, k, (k % 28) + 1) for k in range(40))
        entries = rm.parse_entries(txt)
        by = {e.id: e for e in entries}
        rids = [e.id for e in entries]
        m, k, F = 256, 7, 0.10
        whole = rm._fpr(rm._density(rm.bloom_of_tokens(rm._region_token_set(rids, by), m, k), m), k)
        self.assertGreater(whole, F)                                    # region is saturated
        segs = rm.subdivide_for_saturation(rids, by, m, k, F)
        self.assertEqual(sorted(sum(segs, [])), sorted(rids))          # a partition, nothing lost
        self.assertGreater(len(segs), 1)                               # it actually split
        for seg in segs:
            if len(seg) > 1:
                fpr = rm._fpr(rm._density(rm.bloom_of_tokens(rm._region_token_set(seg, by), m, k), m), k)
                self.assertLessEqual(fpr, F)                           # each multi-entry segment is calm


class Step3ReviewFixes(unittest.TestCase):
    def test_1_conflict_surfaced_symmetrically(self):
        m = rm.build_map(load())
        self.assertIn("CONFLICT e08 ⚠ e09", m.rendered)   # a ledger line, visible from either side
        self.assertIn("e08", m.ledger_ids)
        self.assertIn("e09", m.ledger_ids)

    def test_2_fenced_section_not_picked_as_last_wins(self):
        txt = (
            "## §5 — Resume state\n- real one.\n\n"
            "## §5 — Resume state\n- real two newest.\n\n"
            "## §0 — why\nintro\n\n```\n## §5 — Resume state\n- FAKE fenced\n```\n"
        )
        blk = rm._last_section_block(txt, "5")
        self.assertIn("real two", blk)
        self.assertNotIn("FAKE", blk)

    def test_3_meta_value_with_spaces(self):
        txt = ("- **[DECISION] two regions.**\n"
               "  <!-- roeh id=z1 class=decision atomic=true topic-hint=alpha, beta date=2026-01-01 -->\n")
        e = rm.parse_entries(txt)[0]
        self.assertEqual(e.topic_hint, ["alpha", "beta"])
        self.assertEqual(e.date, "2026-01-01")

    def test_4_saturation_wired_into_build_blooms(self):
        txt = "".join(
            "- **[DECISION] unique zzz%03d here.**\n"
            "  <!-- roeh id=s%03d class=decision atomic=true date=2026-08-%02d topic-hint=big -->\n"
            % (k, k, (k % 28) + 1) for k in range(40))
        entries = rm.parse_entries(txt)
        by = {e.id: e for e in entries}
        _, region_ids = rm.assign_regions(entries)
        blooms = rm.build_blooms(by, region_ids, m=256, k=7, F=0.10)
        self.assertTrue(any(key.startswith("big/") for key in blooms))   # segmented
        self.assertNotIn("big", blooms)                                  # saturated aggregate not stored
        for bl in blooms.values():
            self.assertLessEqual(bl["fpr"], 0.10)                        # every stored filter is calm
        self.assertIn("big", rm.scope_literal("zzz013", blooms))         # region-granular, no false neg

    def test_5_duplicate_id_no_collapse(self):
        txt = ("- **[DECISION] one.**\n  <!-- roeh id=dup class=decision atomic=true date=2026-08-01 -->\n"
               "- **[DECISION] two.**\n  <!-- roeh id=dup class=decision atomic=true date=2026-08-02 -->\n")
        entries = rm.parse_entries(txt)
        self.assertEqual(len(entries), 2)
        self.assertEqual(len({e.id for e in entries}), 2)     # disambiguated, no collapse
        status, reasons = rm.compute_liveness(entries)
        self.assertEqual(sum(1 for s in status.values() if s == "uncertain"), 2)
        for e in entries:
            self.assertIn("duplicate", reasons[e.id])

    def test_6_multi_edge_rendered(self):
        m = rm.build_map(load())
        line = next(l for l in m.rendered.splitlines() if l.startswith("- e07 "))
        self.assertIn("↑e06", line)
        self.assertIn("+e05", line)                            # both edges shown, not just the first

    def test_7_toplevel_case_insensitive_extension(self):
        self.assertEqual(rm._toplevel("plan.PY"), "plan")
        self.assertEqual(rm._toplevel("hooks/x.PY"), "hooks")
        self.assertIsNone(rm._toplevel("b8de529"))            # bare SHA → no path-topic


class Step4Read(unittest.TestCase):
    def test_entry_read_closure_surfaces_live_augments(self):
        r = rm.read(load(), "e05")
        self.assertEqual(r.kind, "entry")
        self.assertIn("e07", r.augments)      # live augmenter surfaced before citing e05
        self.assertNotIn("e06", r.augments)   # dead augmenter excluded

    def test_entry_conflict_is_symmetric(self):
        self.assertIn("e09", rm.read(load(), "e08").conflicts)   # inbound conflict surfaced
        self.assertIn("e08", rm.read(load(), "e09").conflicts)   # outbound conflict surfaced

    def test_unreadable_for_missing_selector(self):
        self.assertEqual(rm.read(load(), "does-not-exist").kind, "unreadable")

    def test_unresolved_path_marker_is_not_unreadable(self):
        r = rm.read(load(), "e01", resolve_cite=lambda c: c != "b8de529")
        self.assertEqual(r.kind, "entry")                        # intact entry still returned
        self.assertTrue(any("b8de529" in mk for mk in r.markers))

    def test_section_read_is_last_wins(self):
        r = rm.read(load(), "§5")
        self.assertEqual(r.kind, "section")
        self.assertIn("fifth", r.rendered)

    def test_region_read_returns_control_plane(self):
        r = rm.read(load(), "retrieval")
        self.assertEqual(r.kind, "region")
        self.assertIn("e05", r.rendered)                          # a live retrieval entry

    def test_region_segments_and_drill_recurses(self):
        r = rm.read(load(), "retrieval", budget_tokens=40)
        self.assertEqual(r.kind, "region")
        self.assertIn("retrieval/0", r.rendered)                  # segmented under a tiny budget
        seg = rm.read(load(), "retrieval/0", budget_tokens=40)
        self.assertEqual(seg.kind, "region")
        self.assertTrue(seg.rendered.strip())                     # the segment resolves to a CP
        self.assertEqual(rm.read(load(), "retrieval/999", budget_tokens=40).kind, "unreadable")


class Step4ReviewFixes(unittest.TestCase):
    def test_1_read_section_preserves_fenced_content(self):
        txt = ("## §3 — trace\nintro\n```\ncode_example()\n```\ntail\n\n"
               "## §5 — Resume state\n- x.\n")
        r = rm.read(txt, "§3")
        self.assertEqual(r.kind, "section")
        self.assertIn("code_example()", r.rendered)   # fenced content NOT stripped from returned bytes

    def test_2_group_drill_resolves(self):
        txt = "".join(
            "- **[DEAD-END] d%d.**\n  <!-- roeh id=x%03d class=dead-end atomic=true date=2026-08-01 topic-hint=t%03d -->\n"
            % (k, k, k) for k in range(30))
        m = rm.build_map(txt, budget_tokens=10_000_000)
        self.assertIn("read group:0", m.rendered)
        r = rm.read(txt, "group:0", budget_tokens=10_000_000)
        self.assertEqual(r.kind, "region")
        self.assertIn("## regions", r.rendered)
        self.assertEqual(rm.read(txt, "group:999", budget_tokens=10_000_000).kind, "unreadable")

    def test_3_ledger_collapses_to_fit_budget(self):
        txt = "".join(
            "- **[REVERSAL] prose only reversal number %d here.**\n"
            "  <!-- roeh id=r%03d class=reversal atomic=true date=2026-08-01 topic-hint=big -->\n"
            % (k, k) for k in range(60))                # all prose-only → all UNCERTAIN → all in ledger
        m = rm.build_map(txt, budget_tokens=120)
        self.assertTrue(m.fits)                          # exit-3 avoided: the ledger collapsed
        self.assertIn("read @ledger", m.rendered)
        full = rm.read(txt, "@ledger", budget_tokens=120)
        self.assertEqual(full.kind, "region")
        self.assertIn("UNCERTAIN r000", full.rendered)

    def test_5_augment_lost_across_supersession_flagged(self):
        base = ("- **[DECISION] base A.**\n  <!-- roeh id=A class=decision atomic=true date=2026-08-01 -->\n"
                "- **[DECISION] B augments A.**\n  Augments: A\n  <!-- roeh id=B class=decision atomic=true date=2026-08-02 -->\n")
        lost = base + ("- **[CORRECTION] C supersedes B, no restatement.**\n  Supersedes: B\n"
                       "  <!-- roeh id=C class=correction atomic=true date=2026-08-03 -->\n")
        status, reasons = rm.compute_liveness(rm.parse_entries(lost))
        self.assertEqual(status["A"], "uncertain")
        self.assertIn("augment lost", reasons["A"])
        kept = base + ("- **[CORRECTION] C supersedes B and restates.**\n  Supersedes: B\n  Augments: A\n"
                       "  <!-- roeh id=C class=correction atomic=true date=2026-08-03 -->\n")
        status2, _ = rm.compute_liveness(rm.parse_entries(kept))
        self.assertEqual(status2["A"], "live")            # restatement clears the gap

    def test_6_atomic_stamp_trusted_but_non_atomic_still_flagged(self):
        # The old >=2-clause-marker heuristic flagged every well-formed five-part entry
        # (WHY:+REJECTED:+GATES: = 3 markers) as UNCERTAIN when superseded — REMOVED
        # (impl-write-path.md §3.3): a valid producer `atomic` stamp is trusted, not second-guessed by
        # a bad proxy. The SOUND check stays: a superseded NON-atomic entry is still surfaced.
        five = ("- **[DECISION] use content ids. WHY: keys. REJECTED: a counter. GATES: the chain.**\n"
                "  <!-- roeh id=M atomic=true date=2026-08-01 -->\n"
                "- **[CORRECTION] fix.**\n  Supersedes: M\n  <!-- roeh id=N atomic=true date=2026-08-02 -->\n")
        s, r = rm.compute_liveness(rm.parse_entries(five))
        self.assertEqual(s["M"], "dead")                   # trusted atomic stamp: superseded, not flagged
        self.assertNotIn("claim", r.get("M", ""))
        s2, r2 = rm.compute_liveness(rm.parse_entries(five.replace("id=M atomic=true", "id=M atomic=false")))
        self.assertEqual(s2["M"], "uncertain")             # sound check kept
        self.assertIn("non-atomic", r2["M"])

    def test_7_segment_indices_stable_across_budgets(self):
        a = rm.read(load(), "retrieval/0", budget_tokens=40)
        b = rm.read(load(), "retrieval/0", budget_tokens=5000)
        self.assertEqual(a.rendered, b.rendered)           # same segment regardless of display budget

    def test_9_tag_with_digits_recognized(self):
        entries = rm.parse_entries("- **[V2] versioned tag.**\n  <!-- roeh id=v1 class=v2 atomic=true date=2026-08-01 -->\n")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].tag, "V2")


class Step5Verify(unittest.TestCase):
    def test_projection_id_stamped_in_map(self):
        m = rm.build_map(load(), as_of="2026-08-24")
        self.assertTrue(m.projection_id)
        self.assertIn("projection-id: " + m.projection_id, m.rendered)
        self.assertNotIn("(step-5)", m.rendered)

    def test_freshness_fresh_then_stale_on_dirty_append(self):
        t = load()
        m = rm.build_map(t, budget_tokens=1500, D=180, as_of="2026-08-24")
        self.assertEqual(rm.verify(m, t, 1500, 180, "2026-08-24")[0], 0)                 # fresh
        # an UNCOMMITTED EOF append moves the log-terminal hash (not git HEAD) → stale
        self.assertEqual(rm.verify(m, t + "\n- **[NOTE] later.**\n", 1500, 180, "2026-08-24")[0], 6)

    def test_freshness_stale_on_param_change(self):
        t = load()
        m = rm.build_map(t, budget_tokens=1500, D=180, as_of="2026-08-24")
        self.assertEqual(rm.verify(m, t, 1500, 999, "2026-08-24")[0], 6)                 # D changed
        self.assertEqual(rm.verify(m, t, 1500, 180, "2027-01-01")[0], 6)                 # as_of changed

    def test_chain_intact_then_tamper(self):
        entries = rm.parse_entries(load())
        exp = rm._expected_chains(entries)
        for e in entries:
            e.chain = exp[e.id]
        self.assertEqual(rm.verify_chain(entries)[0], 0)                                 # intact
        entries[3].chain = "tampered"
        self.assertEqual(rm.verify_chain(entries)[0], 7)                                 # break detected

    def test_chain_skips_absent_chains(self):
        entries = rm.parse_entries("- **[DECISION] x.**\n  <!-- roeh id=z1 class=decision atomic=true date=2026-08-01 -->\n")
        self.assertEqual(entries[0].chain, "")
        self.assertEqual(rm.verify_chain(entries)[0], 0)     # no chain stamped → not falsely flagged


class Step5ReviewFixes(unittest.TestCase):
    def test_1_unbalanced_fence_does_not_swallow(self):
        txt = ("- **[DECISION] first.**\n  ```\n  some code line (fence left open)\n"
               "- **[DECISION] second.**\n  <!-- roeh id=e2 class=decision atomic=true date=2026-08-02 -->\n")
        entries = rm.parse_entries(txt)
        self.assertEqual(len(entries), 2)                # unbalanced fence must not drop the 2nd entry
        self.assertIn("e2", {e.id for e in entries})

    def test_2_section_read_is_exact_not_dotted(self):
        txt = "## §1 — principles\n- p one.\n\n## §1.2 — addendum\n- addendum content.\n"
        blk = rm._last_section_block(txt, "1")
        self.assertIn("p one", blk)
        self.assertNotIn("addendum", blk)                # §1 must not match §1.2

    def test_3_dangling_augment_target_no_phantom(self):
        txt = ("- **[DECISION] A base.**\n  <!-- roeh id=A class=decision atomic=true date=2026-08-01 -->\n"
               "- **[DECISION] B augments a ghost.**\n  Augments: ghost\n  <!-- roeh id=B class=decision atomic=true date=2026-08-02 -->\n"
               "- **[CORRECTION] C supersedes B.**\n  Supersedes: B\n  <!-- roeh id=C class=correction atomic=true date=2026-08-03 -->\n")
        status, _ = rm.compute_liveness(rm.parse_entries(txt))
        self.assertNotIn("ghost", status)                # no phantom id injected

    def test_4_region_named_ledger_not_shadowed(self):
        txt = "- **[DECISION] x.**\n  <!-- roeh id=z1 class=decision atomic=true date=2026-08-01 topic-hint=ledger -->\n"
        r = rm.read(txt, "ledger")
        self.assertEqual(r.kind, "region")               # the real region, not the reserved drill
        self.assertIn("z1", r.rendered)

    def test_5_legacy_trace_diagnosis_note(self):
        legacy = "".join("- **[DECISION] n%d.**\n" % k for k in range(5))   # no v3 metadata
        self.assertIn("PRE-V3", rm.build_map(legacy).rendered)
        self.assertNotIn("PRE-V3", rm.build_map(load()).rendered)           # a real v3 trace has ids


class Step6ReviewFixes(unittest.TestCase):
    def test_1_two_unclosed_fences_drop_no_entry(self):
        # metadata BEFORE each unclosed fence → ids survive; the point is neither entry vanishes.
        txt = ("- **[DECISION] first.**\n  <!-- roeh id=e1 class=decision atomic=true date=2026-08-01 -->\n  ```\n  unclosed\n"
               "- **[DECISION] second.**\n  <!-- roeh id=e2 class=decision atomic=true date=2026-08-02 -->\n  ```\n  unclosed\n")
        ids = {e.id for e in rm.parse_entries(txt)}
        self.assertEqual(ids, {"e1", "e2"})      # even fence-count no longer mis-pairs and swallows

    def test_2_fenced_why_examples_dont_inflate_atomic_heuristic(self):
        txt = ("- **[DECISION] atomic decision.**\n  ```\n  WHY: example one\n  WHY: example two\n  ```\n"
               "  <!-- roeh id=A class=decision atomic=true date=2026-08-01 -->\n"
               "- **[CORRECTION] fix.**\n  Supersedes: A\n  <!-- roeh id=B class=correction atomic=true date=2026-08-02 -->\n")
        status, _ = rm.compute_liveness(rm.parse_entries(txt))
        self.assertEqual(status["A"], "dead")    # NOT uncertain — the WHY: are a fenced example

    def test_3_conflict_to_later_entry_not_flagged(self):
        txt = ("- **[DECISION] a.**\n  Conflicts: b\n  <!-- roeh id=a class=decision atomic=true date=2026-08-01 -->\n"
               "- **[DECISION] b.**\n  <!-- roeh id=b class=decision atomic=true date=2026-08-02 -->\n")
        status, reasons = rm.compute_liveness(rm.parse_entries(txt))
        self.assertNotIn("not strictly earlier", reasons.get("a", ""))  # conflicts are symmetric

    def test_4_augment_lost_skips_already_dead_target(self):
        txt = ("- **[DECISION] A.**\n  <!-- roeh id=A class=decision atomic=true date=2026-08-01 -->\n"
               "- **[DECISION] K supersedes A.**\n  Supersedes: A\n  <!-- roeh id=K class=decision atomic=true date=2026-08-02 -->\n"
               "- **[DECISION] B augments A.**\n  Augments: A\n  <!-- roeh id=B class=decision atomic=true date=2026-08-03 -->\n"
               "- **[CORRECTION] C supersedes B.**\n  Supersedes: B\n  <!-- roeh id=C class=correction atomic=true date=2026-08-04 -->\n")
        status, reasons = rm.compute_liveness(rm.parse_entries(txt))
        self.assertEqual(status["A"], "dead")    # already superseded → not re-surfaced as uncertain
        self.assertNotIn("augment lost", reasons.get("A", ""))

    def test_5_legacy_note_collapses_the_missing_id_flood(self):
        legacy = "".join("- **[DECISION] n%d here.**\n" % k for k in range(20))   # no v3 metadata
        m = rm.build_map(legacy)
        self.assertIn("PRE-V3", m.rendered)
        self.assertIn("read @ledger", m.rendered)                # ledger collapsed to a manifest
        self.assertLess(m.rendered.count("missing id"), 20)      # not 20 per-entry lines in the map

    def test_6_group_drill_is_recursively_bounded(self):
        txt = "".join(
            "- **[DEAD-END] d%d.**\n  <!-- roeh id=x%03d class=dead-end atomic=true date=2026-08-01 topic-hint=t%03d -->\n"
            % (k, k, k) for k in range(200))
        r = rm.read(txt, "group:0", budget_tokens=10_000_000)
        self.assertEqual(r.kind, "region")
        lines = [l for l in r.rendered.splitlines() if l.startswith("- ")]
        self.assertLessEqual(len(lines), rm.MAX_FANOUT)          # bounded at this level too
        self.assertTrue(any("group:0/" in l for l in lines))     # sub-grouped, not a flat 17-line dump


if __name__ == "__main__":
    unittest.main()
