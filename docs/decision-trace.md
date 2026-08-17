# DECISION TRACE — roeh

> **APPEND-ONLY.** Nothing in this file is ever edited or deleted. A superseded decision
> gets a new `[REVERSAL]` beside it; a wrong number gets a new `[CORRECTION]`. The
> history of what we believed and when is part of the record, not noise in it.
>
> Written by the `scribe`. Read by the `oracle`. Consult the oracle *before* re-deriving
> any architecture, eval, model choice or design decision.

---

## §0 — Why this file exists

A model that lives in a context window does not forget randomly. It forgets the
expensive, hard-won thing and keeps the cheap recent thing — so the failure mode is not
ignorance, it is **confident re-derivation** of something already settled.

roeh keeps this record about itself for the same reason it keeps one for any project,
and with a specific edge: this repo's history is unusually rationale-dense because every
commit message was written to carry the *why*. That density is the asset. The commits
say what changed; this file says what was decided, what was rejected, and what already
failed.

**How to extend it:** never rewrite. Append a dated entry under §3 with a tag, the why,
what was rejected, citations, and what it gates. Update §5 when the resume state moves.

---

## §1 — Standing principles

- **[PRINCIPLE] append-only is structural, not honour-system.** The scribe has no
  `Write` or `Edit` tool, and `roeh append` opens in append mode and never seeks, so
  rewriting an entry is *not expressible*. WHY: the original design forbade the scribe
  from writing at all, reasoning that an agent with write access to an append-only file
  is one bad edit from destroying the record it protects — an objection about
  Write/Edit, which can truncate. Removing the capability answers it better than
  forbidding its use. Origin: `b8de529`.

- **[PRINCIPLE] two records is worse than none.** Never orphan, duplicate or silently
  repoint a trace. WHY: with two accounts of the same events, neither is authoritative
  and nothing says which is live — whereas one thin record is at least trustworthy about
  its own thinness. Origin: `d58d4e6`, `c31b311`.

- **[PRINCIPLE] under-claim beats confabulate.** "The record does not cover this" is a
  correct and valuable answer. WHY: manufacturing rationale files the model's own
  reflection as history, where the next session reads it back as fact. Origin: `b8de529`.

- **[PRINCIPLE] assistant prose is never a source.** Learnings come from the owner's
  turns, the code, PR artifacts and measurements. WHY: the hall of mirrors — a record
  fed its own emissions compounds them. Origin: `b8de529`.

- **[PRINCIPLE] judgement is pinned; extraction is cheap.** WHY: the two are different
  jobs and fail differently. Origin: `c948bea`.

- **[PRINCIPLE] a guard that is never exercised is not a guard.** WHY: four bugs shipped
  here with exactly that shape before anything ran them. Origin: `d8098d3` and the
  `[GOTCHA]` entries below.

- **[PRINCIPLE] prefer loud failure to soft failure.** A gate whose result must be
  inferred, a check that silently degrades, a warning shown on every start until it is
  tuned out — all are worse than the absence of the thing. Origin: `c948bea`, `20914b6`.

- **[PRINCIPLE] never infer personal identity from a filesystem path.** WHY: a directory
  name is not a legal name, and a published artifact is the wrong place to guess.
  Origin: `e1b08ea`, `a52dd6f`.

---

## §2 — Rehydration & the staleness ledger

No sibling memory files exist for this project — it has never been worked on from within
its own directory (see the `[OPEN]` entry in §3), so there is nothing to rehydrate. The
commit bodies are the primary source and are mined directly.

### Contradictions & staleness ledger

| Claim | Conflicts with | Status |
|---|---|---|
| "the scribe never writes to the trace" (inherited design) | `[REVERSAL]` `b8de529` | superseded — it writes via `roeh append` only |
| `init --force` overwrites the config | `[REVERSAL]` `d58d4e6` | superseded — it merges |
| test suite has 62 cases (`d8098d3`) | `[CORRECTION]` `ddad17b` | superseded — 66 |

---

## §3 — Chronological decision trace

### 2026-08-16 — roeh built, from a working single-project system

*The whole repo is one day. Entries are ordered as the work happened.*

- **[DECISION] Split the Oracle into invariant method plus a generated profile.**
  `agents/oracle.md` holds only the method — read the record in full, the degradation
  ladder, the supersession check, the consequence pass, the `VERDICT` vocabulary — while
  vocabulary, principles digest and the live dead-ends table live in a generated
  `.claude/roeh-profile.md`. WHY: a new project then needs no edits to the agent.
  REJECTED: shipping the source project's specifics inside the agent, which is what the
  original did and what made it unportable. GATES: everything — no path is hardcoded
  anywhere; every component resolves through `roeh config`. Cite: `b8de529`.

- **[REVERSAL — of the original system's rule] The scribe may write, through an
  append-only CLI.** The inherited design forbade it outright. WHY the reversal: the
  objection was about `Write`/`Edit`, which can truncate; `roeh append` cannot. REJECTED:
  keeping draft-only, which left the record dependent on a human remembering to paste.
  Cite: `b8de529`.

- **[DECISION] Hook policy differs by trigger.** Manual `/compact`: dispatch the scribe,
  block with `exit 2` if still behind, `ROEH_SKIP=1` bypasses. Auto-compact: never block.
  WHY: auto fires when the window is already full, and refusing it there can wedge the
  session with nowhere to go. On manual you typed the command, so there is room to record
  first. Cite: `b8de529`.

- **[DECISION] Make the hook handshake order-independent.** Handlers within one event
  have no documented execution order, so the command hook drops a sentinel
  (`roeh pending`) that the scribe reads. WHY: if the scribe runs first, its append makes
  the record current so the blocking check passes; if the command hook runs first, its
  refusal names the scribe. Both orders are correct. Cite: `b8de529`.

- **[DECISION] `SessionStart` on compact/clear/fork re-injects the pointer and §5.**
  WHY: writing the record is pointless if nothing reads it back. Cite: `b8de529`.

- **[DECISION] Author metadata uses the GitHub handle, not a personal name.** WHY: the
  name had been inferred from a local directory path, which does not belong in a
  published artifact. REJECTED: guessing. Cite: `e1b08ea`, reaffirmed `a52dd6f`.

- **[DECISION] Pin judgement to `opus`; run extraction on `sonnet`.** Nothing declared a
  model, so everything inherited the session's — wrong in both directions, silently.
  Oracle and scribe are pinned by *alias* so they track the current Opus; the scribe is
  the stronger case because it writes unattended to a file that cannot be cleaned up.
  Chapter, memory and artifact passes drop to Sonnet: bounded extraction where the source
  text does the reasoning. Session mining and the refresh drift check are left
  **inheriting** — the two passes needing real judgement. REJECTED: pinning everything up
  (a first ingest expensive enough that people skip it) and pinning everything down (a
  gate that fails softly). MEASURED: with the session pinned to Sonnet, the oracle
  subagent reports running as Opus 5. Cite: `c948bea`.

- **[DECISION] No `roeh update` command.** The harness already has `claude plugin
  update`, `marketplace update`, `tag` and `/reload-plugins`. REJECTED: reimplementing
  them. WHY it still mattered to ask: the question surfaced two real gaps — no
  marketplace manifest existed, and nothing migrated a *project's* artifacts when the
  plugin moved. Cite: `20914b6`.

- **[GOTCHA] `SCHEMA_VERSION` was stamped into every config and never read back.**
  `load_config` merged the file over the defaults and never compared them. Dead code
  wearing the appearance of a version check. Fixed by `roeh doctor`. Cite: `20914b6`.

- **[GOTCHA] `last_ingest` was declared in the state dict and never written.** The same
  dead-field bug as `SCHEMA_VERSION`, found the same way — by asking what a command
  actually did rather than reading its name. Cite: `c31b311`.

- **[DECISION] Track the ingest lifecycle; make a re-run ask instead of assume.** A
  fan-out that dies at chapter 4 of 7 leaves a trace that reads exactly like a finished
  one, so the Oracle answers "not recorded" for decisions that *are* recorded and sounds
  exactly as confident as when it is right. A run now declares its plan, marks units off
  as chapters are **appended** (not when agents return), and refuses to close with work
  outstanding. Six hours of silence turns `running` into `abandoned`. REJECTED: silently
  deduping on a second ingest — an append-only file cannot replace old chapters, only
  append beside them. GATES: `/roeh:ingest` must branch on state and ask, recommending
  `/roeh:refresh` by name. Cite: `c31b311`.

- **[REVERSAL — of `init --force` behaviour] `--force` merges; it no longer resets.**
  It had overwritten the config wholesale, so a `local`-mode trace — local precisely
  because its rationale must not enter git — silently became `repo` mode pointing at an
  empty path, and `roeh status` then invited building a second history. Two refusals
  added that cannot be forced: repointing while a record exists, and flipping
  local→repo. The sovereignty check runs **first**, because that flip also repoints and
  the generic message would bury the reason that matters. Cite: `d58d4e6`.

- **[DECISION] MIT license.** WHY: a public repo with no license is all-rights-reserved,
  so nobody could legally use, fork or vendor a plugin whose entire purpose is
  distribution. Version bumped so it propagates as a release. Cite: `a52dd6f`.

- **[DECISION] Test the CLI as a subprocess, and sandbox `HOME`.** The exit code *is* the
  contract — `PreCompact` blocking is `exit 2` and nothing else — so a test that imported
  the module would pass while the real integration was broken. `HOME` is sandboxed
  because the first version of the suite deposited directories in the real `~/.claude`
  tree. REJECTED: pytest — `bin/roeh` has no third-party dependencies by design, since it
  runs inside hooks where a missing import fails silently at the worst moment.
  Cite: `d8098d3`.

- **[LESSON] The suite found a real bug on its first run.** `status` counted a commit made
  in the *same second* as the trace write as unrecorded, so a project read as "behind" the
  instant after it was recorded — spuriously blocking a manual `/compact`. Manual checks
  had missed it for weeks-equivalent because they happened to include a `sleep 1`.
  Cite: `b4fd479`.

- **[DECISION] CI on Linux and macOS both.** WHY: the two things most likely to differ
  across platforms are exactly what roeh depends on — path resolution through `~` and
  slug computation from an absolute path. Also asserts the exec bits survived checkout,
  since hooks invoke these scripts by path. Cite: `47fe0d8`.

- **[DECISION] Prompt contracts are a separate, opt-in tier.** Four cases assert
  *mechanical* properties of the Oracle against a fixture trace — never answer quality,
  which drifts with the model. Kept out of `tests/run` because every case calls a model:
  the cheap suite has to stay cheap or it stops being run. `claude plugin eval` is the
  right eventual home but is in early access. Cite: `b70483e`.

- **[GOTCHA] `find_project_root` resolved to the wrong project entirely.** It exhausted
  each marker upward before trying the next, so a `.claude/` several levels up beat a
  `.git/` in the current directory. Since `~/.claude` exists for every Claude Code user,
  **any repo without its own `.claude/` resolved its root to the home directory** —
  config written to `~/.claude/roeh.json`, trace aimed at `~/docs/decision-trace.md`.
  Found by running roeh on roeh, which sits one level below a directory holding both
  markers. The suite missed it because every fixture builds a repo in a tmpdir with clean
  ancestors — the bug needs a polluted ancestor, the normal case on a real machine and
  the impossible case in a sandbox. Cite: `ddad17b`.

- **[LESSON] Dogfooding found what both the tests and the manual checks could not.** The
  root-resolution bug required a *realistic environment*, not a correct one. Fixture
  sandboxes are clean by construction, which is exactly why they cannot catch a class of
  bug that only appears in dirty ones. Cite: `ddad17b`.

- **[OPEN] roeh's own conversational history is invisible to its own session mining.**
  Transcripts are filed by the *working directory*, so this project's decisions live under
  the slug of wherever the work happened, not under `-Users-dovrichman-projects-roeh`.
  `roeh sessions` for this project finds nothing relevant. Not a bug — a property of the
  transcript layout — but it means the commit bodies are the only source here, and any
  project worked on from outside its own directory has the same gap.

---

## §4 — Artifact & script index

- **`bin/roeh`** — the CLI everything resolves through: `init`, `config`, `status`,
  `append`, `sessions`, `mark`, `pending`, `doctor`, `ingest`, `slug`. Deliberately
  dependency-free; it runs inside hooks. Gotchas: `append` is the only write path and
  cannot seek; `find_project_root` must return the *nearest* marker (`ddad17b`).
- **`bin/roeh-precompact`** — the gate. `exit 2` blocks; anything else does not. Drops
  the sentinel *before* deciding to block, so ordering does not matter.
- **`bin/roeh-sessionstart`** — re-injects §5 after compaction; surfaces `doctor`
  failures only, never warnings.
- **`agents/oracle.md`** — invariant method only. Pinned `model: opus`.
- **`agents/scribe.md`** — writes via `roeh append`; `disallowedTools: [Write, Edit]` is
  the structural half of the append-only guarantee. Pinned `model: opus`.
- **`skills/{init,ingest,refresh}`** — user-invoked (`disable-model-invocation: true`)
  so an expensive fan-out is never auto-triggered.
- **`templates/`** — trace skeleton (§0–§5) and profile template. `doctor` checks the
  trace still has §0/§1/§3/§5 and a staleness ledger.
- **`tests/test_roeh.py`** — 66 cases, subprocess-driven, `HOME` sandboxed.
- **`tests/eval-prompts`** + **`tests/fixtures/trace.md`** — prompt contracts. Costs
  money; opt-in.
- **`.github/workflows/test.yml`** — Linux + macOS.

---

## §5 — Resume state

- **Where we are:** v0.3.4, published at `github.com/mbrichman/roeh`, MIT, marketplace
  manifest live. Both test tiers green; CI green on both platforms. roeh is now
  initialised on itself and this is its first trace.
- **Currently gated on:** nothing.
- **Next:** nothing committed. Candidates only — `doctor` does not detect agents shadowed
  by a project-level `.claude/agents/` copy; `claude plugin eval` migration once it
  leaves early access.
- **Do not re-derive:**
  - The scribe's write capability — settled at `b8de529`, structural not honour-system.
  - The model split — settled and measured at `c948bea`.
  - A `roeh update` command — the harness owns this (`20914b6`).
  - Whether `init --force` should reset — no (`d58d4e6`).
  - Whether prompt evals belong in `tests/run` — no (`b70483e`).

- **[DECISION] Comment-sourced rationale is read at its commit, never at HEAD, and cited
  `file:line@sha`.** WHY: the honest objection to mining comments is that they go stale —
  humans change code and leave the comment above it untouched. Reading at the commit that
  introduced the change is the mitigation: at that moment the author wrote code and
  comment together, so they are maximally in sync, and the citation becomes a durable
  claim about what was *believed then* rather than a fragile one about what the code does
  *now*. REJECTED: mining comments at HEAD (fastest to implement, silently accumulates
  drift), and dropping comments as a source (they remain the highest-yield rationale in
  most repos). GATES: `/roeh:refresh` must check comment-sourced entries first.
  Cite: `skills/ingest/SKILL.md` §"Every subagent prompt MUST carry these".

- **[LESSON] A comment that has drifted from its code is usually an unrecorded decision.**
  The property that makes comments unreliable as a *live* source makes them a tripwire as
  a *historical* one: if the record says "X because Y" citing a comment, and HEAD no
  longer does X, something changed and nobody wrote it down. `/roeh:refresh` now sorts
  comment drift into three outcomes — unchanged (live), code-changed-comment-didn't
  (`[REVERSAL]` for the unrecorded change plus `[GOTCHA]` for the stale comment), and
  comment-rewritten (`[CORRECTION]` if it contradicts). Cite: `skills/refresh/SKILL.md`
  Phase 2 step 2.

- **[CORRECTION — to the README's claim that comments are "maintained under review"]**
  They are not, reliably; reviewers skim them. The claim was removed rather than softened,
  and replaced with the mechanism that actually holds: read-at-commit plus a drift check.
  A README limitations section now states what is NOT fixed — a comment wrong when
  written, or aspirational, is recorded faithfully as what someone believed.
