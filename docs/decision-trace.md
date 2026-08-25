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

### 2026-08-17 — first refresh

*Two commits of delta plus the first drift check. Single-pass; a two-commit delta does not
warrant a fan-out.*

- **[DECISION] The README's competitive claims are researched, not asserted.** The owner's
  framing was that "virtually all other products exclude git diffs and code comments." A
  search found that false as stated — [Lore](https://arxiv.org/abs/2603.15566) restructures
  commit messages via native git trailers, [Deciduous](https://deciduous.dev/) builds
  decision graphs from existing git history, and compaction-gating is not unique either.
  REJECTED: publishing the sweeping claim, which would have been wrong and unfair in a
  public README. The defensible claim is narrower and more interesting: reading the **diff
  body and the inline comments inside it**, for which no other tool was found. Lore is
  credited rather than contrasted — its abstract states the shared problem better than we
  did ("Each commit captures a code diff but discards the reasoning behind it") — and the
  two point in opposite time directions, prospective encoding versus retrospective
  excavation, so they compose. A "what is NOT unique" subsection was added deliberately.
  GATES: any future comparative claim gets verified before it ships. Cite: `b152c93`.

- **[CORRECTION — to the three comment-staleness entries above]** They were appended
  before the work was committed, so they cite skill-file sections rather than a SHA. The
  commit is `391d34c`. Recording the entry before the commit exists is a real ordering
  hazard of writing the record by hand; the scribe dispatched by the gate does not have
  it, because it runs after the work.

- **[CORRECTION — to §5 "Where we are"]** It records v0.3.4. Actual is **v0.3.5** as of
  `391d34c`. Caught by the drift check, not by anything that fires automatically — a
  version string inside prose is invisible to `roeh doctor`, which checks the config
  schema and the trace's structure but never the trace's *claims*.

- **[GOTCHA] Test invocations create session transcripts indistinguishable from real work.**
  Driving the Oracle with `claude --plugin-dir . -p "..."` from inside the repo leaves a
  `.jsonl` that `roeh sessions` reports as UNMINED, exactly like a genuine working session.
  Mining it would fold the tool's own test harness into the record. Marked mined after
  inspection. No automatic way to tell the two apart currently exists; the mitigation is
  that a human reads the first turn before mining, which is a weak mitigation.

- **[LESSON] The first drift check found the record's citations sound and its prose stale.**
  All twelve SHA citations resolve. The staleness ledger's own claims still hold. What had
  rotted was an unstructured sentence in §5. **Structured citations survive; prose claims
  drift** — which argues for keeping status assertions out of prose and in fields that
  something can check.

- **[OPEN] This trace predates the `file:line@sha` convention** introduced at `391d34c`, so
  it carries zero comment-sourced citations and the new comment-drift check had nothing to
  verify. The convention applies to entries written from here on; the existing chapter will
  not be retrofitted, because rewriting entries is exactly what this file forbids.

---

## §5 — Resume state (superseding the §5 above, 2026-08-17)

*The §5 above is retained as written. This block supersedes it.*

- **Where we are:** v0.3.5, published at `github.com/mbrichman/roeh`, MIT, marketplace
  live. 66 tests green, CI green on Linux and macOS, four prompt contracts passing.
  First refresh complete.
- **Currently gated on:** nothing.
- **Next:** nothing committed. Candidates only — `doctor` cannot detect agents shadowed by
  a project-level `.claude/agents/` copy, nor distinguish a test transcript from a real
  one; `claude plugin eval` migration once it leaves early access.
- **Do not re-derive:** everything in the previous §5, plus —
  - Mining comments at HEAD rather than at their commit (`391d34c`).
  - Sweeping competitive claims in the README; verify first (`b152c93`).

- **[GOTCHA] `SessionStart` was injecting the SUPERSEDED §5.** `section()` took the first
  regex match, but in an append-only file a section is superseded by appending a new copy
  of it — so the first `§5` is the *oldest* resume state. The hook was handing a stale
  state to the one context that has nothing else to check it against, which is precisely
  the failure it exists to prevent. Now takes the **last** match. Found within minutes of
  appending this refresh's own §5, i.e. by the tool being used as designed. REJECTED:
  editing the old §5 in place, which would have hidden the bug rather than exposing it.
  Cite: `bin/roeh-sessionstart` `section()`; regression test
  `test_compact_injects_the_LAST_resume_state`.

### 2026-08-09 — origin (recorded 2026-08-17, out of chronological order)

*Appended late. The trace is append-only, so an entry that belongs earlier goes at the
end with its own date rather than being inserted — the file records when we learned
things, not only when they happened.*

- **[DECISION — owner] The decision trace was commissioned in these words, at
  2026-08-09 11:51pm local**, while the six archaeology agents were already running
  (dispatched 05:40–05:42 UTC on 2026-08-10):

  > *"I have the AI tonight launching agents to do archaeology to go through the commit
  > history and to build an immutable append-only log of decision traces that we've made
  > along the way. So I'm going to fucking tattoo the stuff on itself. So we have a record
  > of the decisions we made and why and we can go back and look at the assets and like
  > not have to be in this stupid recursion that I feel I'm stuck in."*

  Every load-bearing property of this tool is already in that sentence, before any of it
  had a name:

  - **"immutable append-only log"** — stated as the requirement, not derived later. This
    is `[PRINCIPLE] append-only is structural`, and everything downstream follows from
    it: supersession instead of editing, `roeh append` unable to seek, the scribe with no
    `Write` tool.
  - **"tattoo the stuff on itself"** — the record lives *with* the thing it describes, not
    in a separate system. Why the trace is a file in the repo rather than a service.
  - **"the decisions we made **and why**"** — the why was the point from the first
    sentence. It is why comments and diffs are mined at all, rather than commit subjects.
  - **"go back and look at the assets"** — §4, the artifact index.
  - **"this stupid recursion that I feel I'm stuck in"** — §0. The recursion is the
    problem statement, named by the person experiencing it, not a framing invented
    afterwards to justify a tool.

  REJECTED, implicitly and importantly: a mutable memory that gets updated in place. The
  requirement was *immutable* and *append-only* in the first utterance — a constraint
  chosen before anyone had been bitten by the alternative, which is rarer than it sounds.

  GATES: nothing operational. It is here because it is the primary source. Every
  reconstruction of "why does roeh work this way" in §1 and §3 is downstream of this, and
  where any of them disagrees with this quote, **this quote wins.**

- **[LESSON] The origin statement survived only because the owner kept it and pasted it
  back.** It was not in a commit, a doc, or a session transcript this tool can reach — it
  was said aloud, elsewhere, at midnight. The record that exists to stop things being lost
  came within one act of memory of losing its own founding sentence. That is not an
  argument against the tool; it is the sharpest available illustration of the gap it
  cannot close on its own.

- **[CORRECTION — to the `[LESSON]` immediately above]** That entry claimed the origin
  sentence "survived only because the owner kept it and pasted it back," and read the
  moral as a gap the tool cannot close. **Both halves are wrong.** The owner's correction:

  > *"The quote was mined back from the memory system I built."*

  It was not rescued by human memory. It was **retrieved from the upstream project** —
  the owner's personal memory system, the one whose decision trace this tool generalises,
  deliberately not named in this public record. The sentence that commissioned that
  decision trace was recovered by the system it exists to protect.

  The corrected lesson is the opposite of the recorded one, and stronger: nothing was
  nearly lost. The apparatus worked. A midnight remark that reached no commit, no doc and
  no session transcript was captured, held, and handed back eight days later — which is
  precisely the capability the whole stack exists to provide, demonstrated on its own
  founding statement.

- **[PRINCIPLE — owner] The recursion, stated exactly.** Earlier entries describe it as
  "confident re-derivation," which is the symptom. The owner's formulation is the
  structure:

  > *"The recursion is that I need a memory system for the tool I'm using to build the
  > memory system."*

  Four layers, each remembering the one below:

  1. **The upstream project** — memory for the owner's own material.
  2. **Its decision trace** — memory for the work of building it, commissioned
     2026-08-09 because building it kept losing its own decisions.
  3. **roeh** — that decision trace generalised into a portable tool, so any project can
     have layer 2.
  4. **roeh's own trace** — this file, because building roeh has the same problem.

  The origin entry above closed the loop: layer 1 supplied the primary source for layer 4.
  This is not a curiosity. It is the strongest evidence in the record that the design is
  sound, because the only real test of a memory system is whether it can hand back the
  thing you most needed and had no other copy of.

  GATES: nothing operational — but where §0 and §1 paraphrase "the recursion," this is the
  authoritative statement and they defer to it.

  **Append-only protects the record's integrity; it is not a reason to publish something
  that should not be public.** When the two conflict, redact and say that you did — which
  is what this entry is. GATES: check for names before appending to a trace in a public
  repo. `local` mode exists precisely so this trade-off never arises.

### 2026-08-17 — retrieval layer & read-only mode (recorded 2026-08-24, out of chronological order)

*Appended by the second refresh. These commits landed on 08-17 after the first refresh's `391d34c` baseline; append-only means they go at the end with their own date, not inserted into the "first refresh" chapter above.*

- **[DECISION] `precompact.record: false` (read-only mode) withholds the sentinel rather than disabling the scribe.** WHY: the scribe's `hooks.json` entry is plugin-level and not disableable per project, so instead of stopping the dispatch the design starves it of work — the scribe still fires, finds nothing pending, stays in DRAFT mode, and returns entries instead of writing them; the owner stays the only writer. `roeh append` deliberately keeps working: *"The line is drawn at automation, not at writing."* REJECTED: disabling the scribe outright. Surfaced by the real question of whether to point roeh at an existing project whose ~3,000-line trace was built by hand over a week — where an unattended scribe with write access is exactly what someone is right to be wary of; now a supported configuration rather than a reason not to install. Cite: `9c587a7`.

- **[GOTCHA] `precompact.block_manual` / `nag_auto` were written into every config from v1 and never read** — the fifth dead field of this shape (after `SCHEMA_VERSION`, `last_ingest`), and *"the worst of them, because a gate whose switch does nothing is worse than a gate with no switch: the owner believes they turned it off."* Both are now honoured. Cite: `9c587a7`.

- **[DECISION] Give the oracle index/read/chapters primitives instead of an honour-system degradation instruction.** WHY: past ~1,500 lines the oracle's charter told it to "degrade to chapter reads" — an honour-system ladder with no tooling behind it, the exact "gate that fails softly" this project warns against everywhere else, and `doctor` warned at the threshold while offering no remedy. The naive grep fallback is silently worse: *"Grepping cannot find what you do not know to look for,"* so the answer is a confident one sourced from whichever chapters happened to match, indistinguishable from a complete one. REJECTED: leaving the honour-system ladder in place and warning louder. GATES: `doctor` now FAILS past the threshold with no index and warns when the index is stale; the oracle reads `<trace>-index.md` in full at any size, then pulls only the chapters it needs. Cite: `09b0987`.

- **[DECISION] `roeh chapters` / `roeh read` return CHAPTERS, never lines.** WHY: a `[REVERSAL]` almost always lives in a *later* chapter than the entry it overturns, so a line-level result hands back a dead claim without its correction — supersession is chapter-distance, not proximity. `roeh read` pulls the LAST matching section, since append-only means sections are superseded by appending. Cite: `09b0987`.

- **[DECISION] The threshold for "no longer one comfortable read" is ~400KB / ~1,500 lines** — the same figure the prior charter used, now backed by tooling rather than instruction. On the validation trace the index was ~480 lines against 3,058 (15%); `roeh index` says so when the ratio is poor, because an index that is not much smaller than the trace buys nothing. Cite: `09b0987`.

- **[GOTCHA] The section regex matched two-or-three hashes, so `### 2026-08-16` was reported as section "§2026"** — producing overlapping, duplicated spans in `chapters` and the index. Found by validating against a real 3,058-line trace, not a fixture. Fixed to exactly two hashes. Cite: `09b0987`.

- **[GOTCHA] The entry parser recognised only this tool's own `- **[DECISION]**` dialect and silently under-reported by ~90% — 41 of 397 entries — on a trace written as `` - `[DECISION]` ``.** An index that silently under-reports is the worst possible failure for an index, *because it looks complete.* Both dialects are now recognised, `[[wikilinks]]` excluded, and thematic chapters indexed alongside dated ones. Cite: `09b0987`.

### 2026-08-18 — Python floor & first-contact messaging (recorded 2026-08-24, out of chronological order)

*Appended by the second refresh, at the end per append-only.*

- **[DECISION] The Python floor is 3.8, enforced loudly at runtime, with the file kept parseable on old interpreters.** WHY: `cmd_config` used the dict-union `|` (3.9+), which survived review because it sat on a continuation line a `} | {` grep missed, and survived CI because CI ran a single modern version. That failure is worse than it sounds — a `SyntaxError` fires at PARSE time, so a version check inside the file could never report it, and *"inside a hook that surfaces as silence — the gate simply does not fire, and nobody notices until a decision has already been lost."* Fix: `dict.update` replaces the union so the file parses on the oldest version claimed; a `MIN_PYTHON` guard fails loudly and names the interpreter for the runtime case (an old interpreter that parses the file but is unsupported). GATES: CI matrix now runs 3.8 + 3.13 on both platforms, and every script is parsed with `ast(feature_version=(3,8))` rather than assumed. Cite: `12aa744`.

- **[DECISION] `roeh status` on an unconfigured project points to `/roeh:init`, not `/roeh:ingest`.** WHY: the old message sent a new user to step two — past the step that decides where the trace lives — and showed the default path as fact rather than a guess. Now distinguishes "never set up" from "set up but not yet ingested" and shows the default path as a parenthetical. Surfaced by the owner saying they were still unclear how to add roeh to a new project — the tool's own first-contact message was part of why. Cite: `199109d`.

- **[DECISION] README: install is machine-once, enable is per-project — two numbered steps, not one code block.** WHY: `roeh`'s `bin/` is on PATH only inside an active Claude Code Bash session (plugin-injected while enabled), never the login shell — *"which was never written down, and is the likeliest reason the instructions read as incomplete."* Now called out in a blockquote at the top of the project step and above the CLI reference. Also recorded: `claude plugin update` needs the `@marketplace` suffix or it fails with "Plugin not found"; and the CLI reference, which had omitted `index`/`read`/`chapters` entirely (added in 0.4.0), now groups commands by purpose with a check that every registered subcommand appears. Cite: `f6689e7`.

### 2026-08-24 — second refresh

*Delta of five commits (`391d34c..HEAD`) plus two sessions. Session `f7d6fc34` mined, no net-new (a gate-mode oracle test, already covered). The live session `1ef25bff` deliberately not mined — in-progress design exploration, no owner decisions reached.*

- **[CORRECTION — to §4 artifact index] `bin/roeh`'s command set now includes `index`, `read` and `chapters`.** §4's CLI line lists only `init, config, status, append, sessions, mark, pending, doctor, ingest, slug` — the CLI as it was *before* the retrieval layer existed. The three retrieval primitives, added in 0.4.0, are missing from the recorded index. Cite: `09b0987`, `f6689e7`; verified against the dispatch table at `bin/roeh:1075` (HEAD).

- **[CORRECTION — to §4 "66 cases" and the §2 ledger's test-count row] The deterministic suite is now 81 test methods** (`def test_` in `tests/test_roeh.py` at HEAD), not the recorded 66. Verified sequence since the last count: 66 (`ddad17b`, `391d34c`) → 71 (`9c587a7`) → 80 (`09b0987`) → 81 (`199109d`), then held through `12aa744` and `f6689e7`. NOTE: `9c587a7` added +5 methods by count though its commit body claims "Four tests" — recorded as counted, not as claimed. Cite: counted at HEAD across the cited SHAs.

- **[GOTCHA — this file was edited, against its own rule] Commit `9c587a7` deleted an 11-line `[GOTCHA]` from this trace, with no mention of the deletion in its commit body** (which is entirely about read-only mode and the dead-field fix). The deleted entry had documented a *prior* redaction — the upstream project's name scrubbed from this public repo by amend + force-push, chosen over a revert because a revert leaves the name readable in history forever. The deletion left a dangling paragraph at HEAD (*"Append-only protects the record's integrity … which is what this entry is"*, L450–453) whose "this entry" now points at nothing. WHY the meta-entry was removed is stated in neither the commit body nor any inline comment; under *under-claim beats confabulate*, this is flagged, not explained. It is NOT edited away here — that would repeat the very offence being recorded. Cite: `9c587a7` (diff to `docs/decision-trace.md`).

- **[LESSON] The append-only guarantee is structural only on the *automated* path; the file itself remains hand-editable — and has been edited at least twice.** The scribe has no `Write`/`Edit` and `roeh append` cannot seek, so no agent on that path can rewrite the record. But a human — or the main-loop assistant — committing a direct edit is bound by neither, and the record's own git history shows two such edits: the force-push name-redaction, then the `9c587a7` deletion. Git makes such an edit *visible* in the diff; nothing currently *rejects* it. Enforcing append-only against direct commits is unenforced and now an open design question (see §5). Cite: `9c587a7`; the redaction it deleted.

## §5 — Resume state (superseding the §5 above, 2026-08-24)

*The §5 above (2026-08-17) is retained as written. This block supersedes it.*

- **Where we are:** v0.4.3. The retrieval layer (`index`/`read`/`chapters` + `<trace>-index.md`), read-only mode (`precompact.record`), and the Python 3.8 floor have all shipped. 81 deterministic tests green; CI on 3.8 + 3.13, Linux + macOS. This second refresh reconciled the record through `f6689e7`.
- **Currently gated on:** nothing operational.
- **Currently active (owner-stated, NOT a decision):** a rethink of the storage & retrieval model, prompted by the *upstream* layer-1 trace reaching ~900KB and becoming unmanageable. The owner's initial instinct — splitting the file by section (§1/§3/§5) — was noted as insufficient, because §3 is the unbounded section and section-splitting addresses the wrong axis. A prior-art survey was conducted (mem0, Deciduous, projectmem, repomemory, Lore, claude-mem; plus LSM compaction, event-sourcing snapshots, MemGPT, git packfiles/commit-graph). **No decision has been reached.** The specific candidate architectures so far are assistant-derived and unendorsed; recording them is deferred to a design doc, not this trace, until the owner decides.
- **Open questions:** (1) how to bound retrieval cost as the append-only log grows without bound; (2) enforcing append-only against *direct* (non-scribe) edits — see the [LESSON] in the 2026-08-24 chapter; (3) whether any lossy summarisation tier is acceptable given *under-claim beats confabulate*.
- **Do not re-derive:** everything in the previous §5, plus —
  - The retrieval-primitives design — settled `09b0987`.
  - Read-only mode (`precompact.record: false`) — settled `9c587a7`.
  - The Python 3.8 floor — settled `12aa744`.
  - `roeh status` pointing new users to `/roeh:init` — settled `199109d`.

*Appended after this chapter's §5 per append-only (`roeh append` writes only at EOF). This `[LESSON]` extends the 2026-08-24 second-refresh chapter — it records an adversarial review of the retrieval-at-scale RFC (`docs/design/retrieval-at-scale.md`). The superseding §5 below carries the current resume state.*

- **[LESSON] Liveness is not mechanical: the overturn-vs-refine distinction is semantic, so it must be typed at WRITE time, and every gap in that typing must fail LOUD.** [auto-recorded] The RFC's §4 proposed an entry is dead *iff* a later entry `supersedes:` its id (plus terminal `[DEAD-END]`/`[CLOSED]`) — *"a pure graph walk over `supersedes:` edges + terminal tags — no judgment, no model"* (`docs/design/retrieval-at-scale.md` §4). An adversarial (five-lens) review of the RFC found this unsound. A `[CORRECTION]` that **overturns** an entry (target → dead) and one that merely **refines** it (fixes a number or citation; target stays live) are *semantically* different, and the RFC's own §2.2 stamps a single, single-meaning `supersedes:` edge on **every** `[REVERSAL]`/`[CORRECTION]` — so §4 would read every refinement as killing its target. The distinction cannot be both mechanical and correct at read time; the judgment has to be made at WRITE time and typed onto the edge (e.g. `supersedes:` = dead vs `refines:` = target stays live). Read-time liveness is then only ever as trustworthy as that typing — so every gap in it (prose-only supersession with no machine edge; a dangling pointer; partial or double supersession; a dialect the parser misses) must fail **loud** — surface both entries as *liveness-uncertain* — never silently resolve to live-or-dead. This trace demonstrates the failure on itself, two ways. (1) Its supersession is **prose-only**: 15 `[REVERSAL]`/`[CORRECTION]` tags, **zero** `supersedes:`/`id` machine edges — a graph-walk liveness finds no edges and wrongly marks every superseded entry live. (2) The `[CORRECTION — to §4 artifact index]` in this chapter targets the §4 `bin/roeh` bullet, which in the *same bullet* still carries the live, load-bearing fact *"append is the only write path and cannot seek"* — under whole-entry mechanical supersession, marking that bullet dead deletes a live fact. A silent liveness error is roeh's worst failure: it hides a live entry AND can return a dead claim wearing its citations. REJECTED: an untyped, single-meaning supersession edge that always means "dead" (the RFC's original §4, and §2.2's single `supersedes:` on every correction). GATES: the retrieval-at-scale RFC and any future liveness/supersession mechanism — neither may proceed until overturn-vs-refine is typed and uncertain liveness fails loud. Cite: `docs/design/retrieval-at-scale.md` §4 (and §2.2); the `[CORRECTION — to §4 artifact index]` and the §4 `bin/roeh` bullet (*"append is the only write path and cannot seek"*) in this trace.

## §5 — Resume state (superseding the §5 above, 2026-08-24)

*The §5 above (2026-08-24, second refresh) is retained as written. This block supersedes it, adding the RFC's adversarial-review status.*

- **Where we are:** v0.4.3, as in the §5 above — retrieval layer, read-only mode, and the Python 3.8 floor all shipped; 81 deterministic tests green; CI on 3.8 + 3.13, Linux + macOS. New since: the storage/retrieval rethink (§5 above, "Currently active") now has a written RFC — `docs/design/retrieval-at-scale.md` (untracked; **PROPOSAL**, assistant-derived, nothing implemented).
- **RFC status:** the RFC has been **adversarially reviewed** (a five-lens red-team pass). The central finding is the `[LESSON]` above: liveness cannot be a pure mechanical graph walk (RFC §4), because overturn-vs-refine is semantic. The RFC is **now being revised**, direction: (a) type the supersession edge — overturn vs refine; (b) a freshness/integrity gate on the Oracle's read path; (c) loud-fail on uncertain liveness (surface both entries), never silent resolve; (d) lexically-rich cold-topic headers so retrieval does not hinge on `scope(Q)` derivation.
- **Still a PROPOSAL, not a decision.** The specific fixes live in the RFC; **none is recorded here as a `[DECISION]`, and none is implemented.** The owner has not ruled.
- **Currently gated on:** nothing operational. GATED by the `[LESSON]` above: any future liveness/supersession mechanism must type the edge and fail loud on uncertainty before it is built.
- **Open questions:** unchanged from the §5 above — (1) bound retrieval cost as the log grows; (2) enforce append-only against *direct* (non-scribe) edits; (3) whether any lossy summarisation tier is acceptable given *under-claim beats confabulate*. Now sharpened by (4) how to type and backfill overturn-vs-refine onto a prose-only trace with zero machine edges.
- **Do not re-derive:** everything in the previous §5, plus —
  - A mechanical, untyped, single-meaning supersession edge (always "dead") — rejected by the `[LESSON]` above; the overturn-vs-refine distinction is semantic and must be typed at write time.

*Appended after this chapter's §5 per append-only (`roeh append` writes only at EOF). This `[DECISION — owner]` extends the 2026-08-24 second-refresh chapter — a firm owner ruling on migration stance, stated directly this session and authorized for recording. The superseding §5 below carries the current resume state.*

- **[DECISION — owner] roeh always starts clean; it never converts a legacy trace in place.** [auto-recorded] On any project — one arriving with an older roeh trace, another tool's trace, or a large hand-built artifact — roeh (re)ingests the record from **primary evidence under the current model**, and never migrates an existing trace file into a new schema. A pre-existing trace is treated as a **test fixture and a pointer to gaps**: it validates the design and reveals what a clean ingest missed, but is **never a source to copy from and never mangled into the new format.** Holes a clean ingest leaves are filled by re-deriving from primary evidence (owner turns, commits, code); a hole whose only support is the old trace's assistant-authored prose is recorded as `[OPEN]`, not imported — importing it would be the hall of mirrors, filing the record's own reflection back as fact. WHY: converting a legacy artifact inherits its pathologies — measured on a real large trace (~10,000 lines): doubled dated chapters, mixed tag dialects, ~100% prose-only supersession (zero machine edges), a heterogeneous ad-hoc tag taxonomy — and risks re-importing agent-synthesized rationale as fact, the exact confabulation this record exists to prevent. A clean ingest instead writes typed supersession edges natively at write time, which is the reliable path: an independent two-pass classification recovered the overturn-vs-augment relation at ~97.5% agreement, whereas reconstructing those edges from the stale prose was only ~58% confidently auto-typable, left a ~12% hand-typed tail, and depended on an untested target-resolution step. REJECTED: (1) in-place conversion / a legacy-manifest "backfill" as a *product/migration* path — the RFC's earlier migration path A; (2) treating the old trace as a source to copy from during gap-fill. GATES: the retrieval-at-scale RFC (`docs/design/retrieval-at-scale.md`) — its legacy-backfill path is removed, and any `backfill`/manifest tooling (§2.4, §10, §13) is demoted to fixture/analysis use, never a migration feature — and any future roeh upgrade/migration behaviour. This reframes §5 open-question (4) (*"how to type and backfill overturn-vs-refine onto a prose-only trace with zero machine edges"*): the answer is not to backfill the old trace but to re-ingest clean and emit typed edges natively. Cite: owner decision, this session, 2026-08-24; backfill feasibility measurement (figures in aggregate; upstream artifact deliberately unnamed).

## §5 — Resume state (superseding the §5 above, 2026-08-24)

*The §5 above (2026-08-24, RFC adversarial-review) is retained as written. This block supersedes it, recording the migration-stance decision.*

- **Where we are:** v0.4.3 — retrieval layer, read-only mode, and the Python 3.8 floor all shipped; 81 deterministic tests green; CI on 3.8 + 3.13, Linux + macOS. The storage/retrieval rethink has a written RFC (`docs/design/retrieval-at-scale.md`), still a **PROPOSAL**.
- **Migration stance: DECIDED — clean-start-always.** roeh (re)ingests from primary evidence under the current model; it never converts a legacy trace in place (the `[DECISION — owner]` above). The RFC's legacy-backfill/migration path is removed; `backfill`/manifest tooling survives only as fixture/analysis, never a migration feature.
- **The upstream large artifact is a TEST FIXTURE, not a migration target** — used to validate the design and expose what a clean ingest misses; never copied from.
- **Next build (critical path):** the v3 **write** side first — the schema (`id`, `chain`, typed `supersedes`/`augments` edges) and the ingest/scribe emitting it — then a clean ingest, then the read-side map. Read-side `roeh map`/Bloom/recursion come **after** there is typed data to map.
- **Still a PROPOSAL, not a decision:** the retrieval *mechanism* (map / typed-edges / Bloom / recursion) remains RFC-only, nothing implemented. Only the migration stance is now a decision.
- **Currently gated on:** nothing operational. GATED by the `[LESSON]` in this chapter (overturn-vs-refine must be typed at write time; uncertain liveness fails loud) and by this decision: any liveness/supersession mechanism must type the edge and fail loud on uncertainty; any migration must clean-start, never convert.
- **Open questions:** carried from the §5 above — (1) bound retrieval cost as the log grows; (2) enforce append-only against *direct* (non-scribe) edits; (3) whether any lossy summarisation tier is acceptable given *under-claim beats confabulate*. Open-question (4) (backfilling overturn-vs-refine onto a prose-only trace) is **resolved by the decision above**: clean re-ingest with native typed edges, not backfill.
- **Do not re-derive:** everything in the previous §5, plus —
  - Converting or migrating a legacy trace in place, or copying from an old trace during gap-fill — rejected by the `[DECISION — owner]` above; roeh always starts clean and re-derives from primary evidence.

### 2026-08-25 — the v3 read path, built consumer-first

*The read/consumer side of RFC v3 (`docs/design/retrieval-at-scale.md`) implemented against its
impl spec (`docs/design/impl-read-path.md`). Everything here — `bin/roeh_map.py`, `tests/test_roeh_map.py`,
`tests/fixtures/trace-v3.md`, both design docs — is **untracked/uncommitted working-tree**, so
citations are `file:line` in the working tree, not SHAs. Entries `[auto-recorded]` by the scribe on
the owner's instruction; see UNSOURCED notes reported back to the session for the verbatim-owner-phrasing caveats.*

- **[DECISION] The v3 read path is built CONSUMER-FIRST — the read/consumer side before the write side — as a standalone, stdlib-only module (`bin/roeh_map.py`).** [auto-recorded] WHY: the read path's guarantees define what each entry must carry, so the write-path schema is *derived* from the read spec, not guessed — `docs/design/impl-read-path.md` states it directly (L8: "Consumer-first: §5 (persisted vs. derived fields) is the output that defines the write-path spec"), and its §5 field split (L179–190) and §7 build order (L230–238, "Only after this is green do the **write-path spec** … follow") are the artifact of building the reader first. Catching the ordering here avoided mis-building the authority boundary — e.g. persisting model-assigned semantic *topics* into the immutable log; impl §5 keeps `topic[]` membership DERIVED at map time, never persisted (L181: "semantic classification must not re-enter the immutable log"). The ordering was the owner's call this session. What exists now, verifiable and green in `bin/roeh_map.py`: `tokenize` (the single canonical tokenizer, L41); typed-edge liveness over supersedes/augments/conflicts (`compute_liveness`, L206); a bounded recursive control-plane map — regions (`assign_regions` L317), retirement (`_region_state` L348), a token-budget collapse loop (`build_map` L562–577), bounded fan-out (`_group_regions` L431, `group:` drill L791) and a ledger-manifest fallback (L506, `@ledger` L812); a per-region Bloom literal-existence index (`build_blooms` L635); a recursive `read` (L772) with read-closure (`_read_closure` L712/L829), symmetric conflict surfacing (L820/L837) and fail-closed UNREADABLE vs still-returned UNRESOLVED-PATH (L788/L830); and a projection-id freshness gate (`projection_id` L873, `verify` → exit 6 on stale L885). **159 deterministic tests green** (`python3 -m unittest discover -s tests`: 81 in `tests/test_roeh.py` + 78 in `tests/test_roeh_map.py`), stdlib-only (`re`/`hashlib`/`dataclasses`/`datetime`/`typing`) and 3.8-parseable (`ast(feature_version=(3,8))` OK) — the `d8098d3`/`12aa744` fences hold. REJECTED: write-path-first — **this REVERSES the "Next build (critical path): the v3 *write* side first … Read-side `roeh map`/Bloom/recursion come after there is typed data to map" plan recorded in the 2026-08-24 migration-stance §5** (the block this chapter's §5 supersedes). GATES: the write-path spec and the clean ingest that follow it. **Still a PROPOSAL, not adopted:** the module is standalone, NOT wired into `bin/roeh` (no `build_map`/`cmd_map`/`cmd_scope` in the dispatch table at `bin/roeh:1075`; the `cmd_read` there is the old `09b0987` retrieval primitive), and v3 is not adopted until the write path and a real ingest exist. Cite: `bin/roeh_map.py`; `docs/design/impl-read-path.md` §0/§5/§7 — all working-tree, uncommitted.

- **[DECISION] Entry on-disk format is HYBRID: supersession relations and cites stay VISIBLE in prose; the machine fields (`id`, `chain`, `class`, `atomic`, `date`, `topic-hint`) go in a trailing `<!-- roeh … -->` comment.** [auto-recorded] WHY: a human reading the raw trace still sees *what overturns what* (the `Supersedes:`/`Augments:`/`Conflicts:` lines) and *where it is cited* (`Cites:`) — roeh's visible-provenance ethos — while the hash/id plumbing does not clutter the prose. Chosen by the owner over all-hidden (every field in the comment, raw trace unreadable) and all-visible (ids/chains inline, prose noise). The parser reads relations/cites from the prose and id/class/atomic/date from the trailing comment. Cite: `tests/fixtures/trace-v3.md` header L3–5 and entries L11–95; parsed by `bin/roeh_map.py` `parse_entries` (L134) + `_parse_meta` (L99). Working-tree, uncommitted.

- **[LESSON] Fence handling in the trace parser regressed three times, each fix a fresh heuristic; the durable fix was structural, not another heuristic.** [auto-recorded] The parser must not let a code fence inside an entry body sever the entry or get mined as a real edge — but three distinct fence shapes each broke a preceding heuristic: (1) a fenced `#` heading severing an entry's trailing metadata comment (`tests/test_roeh_map.py::test_6_fence_in_body_does_not_sever_metadata`; code `round-2 #6`, `parse_entries` L142); (2) an unbalanced/unclosed fence swallowing everything after it (`test_1_unbalanced_fence_does_not_swallow`); (3) two *separate* unclosed fences whose total count is even — defeating any "fences balance ⇒ even count" heuristic (`test_1_two_unclosed_fences_drop_no_entry`; both `round-6 #1`). The principled rule that ended it: **a code fence can never hide a real entry-head — entry heads are FENCE-IMMUNE (structural precedence) — and only CLOSED fence pairs suppress non-structural lines** (`_fenced_lines` L118–131, `parse_entries` L140–149). General lesson: for a parser whose worst failure is *silent under-reporting*, prefer a structural invariant over a "usually balanced" heuristic — the same class as the `09b0987` 90%-under-report bug. Cite: `bin/roeh_map.py` `_fenced_lines`/`parse_entries`; regression tests in `tests/test_roeh_map.py`. (Review rounds touching fences that ARE named in the code: `round-2`, `round-6`.) Working-tree, uncommitted.

- **[LESSON] Dogfooding the read path on roeh's OWN pre-v3 trace confirmed completeness and loud-on-legacy behaviour — and earned a refinement.** [auto-recorded] Run over `docs/decision-trace.md`, `parse_entries` found **58 entries — exactly the 58 a raw grep of tag-bullets finds** (no silent under-count), handled the real dirty markdown without crashing, and — because 58/58 (100%) carry no v3 `id` — `build_map` emits ONE loud note *"⚠ 58/58 entries lack v3 metadata (no id) — this looks like a PRE-V3 trace; run a clean ingest and do not trust the map as-is"* in place of a per-entry flood. That single-note collapse is the refinement dogfooding earned (`build_map` L543–549, threshold `missing ≥ 0.8·N`, `round-6 #5`). This is the `ddad17b` gate paying off — fixtures have clean ancestors by construction, so only a real dirty trace exercises legacy handling; dogfooding finds what tests can't. Cite: `bin/roeh_map.py` `build_map` legacy note L543–549; dogfooded against `docs/decision-trace.md` (58 == 58 and the note verified this session). Working-tree, uncommitted.

- **[GOTCHA] "A guard that is never exercised is not a guard" bit the NEW code too: the Bloom saturation-subdivision was implemented but never CALLED.** [auto-recorded] `subdivide_for_saturation` (L675) existed, but `build_blooms` never invoked it — so a dense region could have saturated to an all-ones filter (match-everything) and silently become a drill-everything machine, undetected. Caught by review (finding `#4`); `build_blooms` now measures per-region FPR and, above `SATURATION_FPR = 0.10` (L594), stores segment filters via `subdivide_for_saturation` instead of the saturated aggregate (L635–660, docstring L639–640: *"This is what actually EXERCISES the saturation guard (review #4): a guard never called is not a guard"*), covered by `tests/test_roeh_map.py::test_saturation_subdivides_below_threshold`. Reinforces the standing principle (§1) inside fresh code — the same shape as the dead-field/unexercised-guard bugs already recorded (`SCHEMA_VERSION`, `last_ingest`, `precompact.block_manual`). Cite: `bin/roeh_map.py` `build_blooms`/`subdivide_for_saturation`; `tests/test_roeh_map.py`. Working-tree, uncommitted.

## §5 — Resume state (superseding the §5 above, 2026-08-25)

*The §5 above (2026-08-24, migration-stance) is retained as written. This block supersedes it, recording the read-path implementation.*

- **Where we are:** v0.4.3 shipped surface unchanged (retrieval layer, read-only mode, Python 3.8 floor). NEW this session: the v3 **read-path core** is built and **review-complete** — `bin/roeh_map.py`, a standalone, stdlib-only, 3.8-parseable module (tokenizer, typed-edge liveness, a bounded recursive control-plane map, a per-region Bloom literal index, a recursive `read` with read-closure / conflict-symmetry / fail-closed, and a projection-id freshness gate). Six review rounds folded (`round-6` is the highest named in the code; findings `#1`–`#9`), dogfooded on roeh's own pre-v3 trace, **~159 deterministic tests green** (81 `test_roeh.py` + 78 new `test_roeh_map.py`). Design docs: `docs/design/retrieval-at-scale.md` (RFC v3) and `docs/design/impl-read-path.md` (impl spec). **All of it — code, tests, fixture, design docs — is untracked/uncommitted working-tree and NOT yet CLI-wired into `bin/roeh`.**
- **STALE now (superseded by this chapter):** the 2026-08-24 §5 line *"Next build (critical path): the v3 **write** side first … Read-side `roeh map`/Bloom/recursion come after there is typed data to map"* — the order was **REVERSED to consumer-first** (read before write), because the read guarantees define the write schema; see this chapter's `[DECISION]`. Also stale: that §5's *"Still a PROPOSAL … nothing implemented"* — the read-side core now IS implemented (standalone); the RFC/architecture adoption is what remains a PROPOSAL.
- **Next (critical path):** the **write-path spec** — the §5 persisted-field contract the read spec derived (`docs/design/impl-read-path.md` §5: `id`/`chain`/typed `supersedes`/`augments`/`conflicts_with`/`atomic:true`/`cites[]`; topic membership DERIVED, never persisted) → **build** the write side → a **clean ingest** that finally produces a real v3 trace. Read-side CLI wiring, the `09b0987` supersession, and the oracle-charter/profile update come with adoption, not before (`impl-read-path.md` §0/§7).
- **Still a PROPOSAL:** the v3 architecture (RFC + impl spec) is not adopted; the owner has not ruled on adoption. Only the read-path *code* exists, standalone.
- **Currently gated on:** nothing operational. GATED (carried forward): any liveness/supersession mechanism must type the overturn-vs-refine edge and fail LOUD on uncertain liveness (the 2026-08-24 `[LESSON]`); any migration must clean-start, never convert (the 2026-08-24 `[DECISION — owner]`).
- **Open questions:** carried from the §5 above — (1) bound retrieval cost as the log grows; (2) enforce append-only against *direct* (non-scribe) edits; (3) whether any lossy summarisation tier is acceptable given *under-claim beats confabulate*.
- **Do not re-derive:** everything in the previous §5, plus —
  - Building the write side before the read side — REVERSED this session to consumer-first (read first), because the read guarantees define the write schema (this chapter's `[DECISION]`).
  - Leaving the Bloom saturation guard uncalled — it must be exercised (this chapter's `[GOTCHA]`).

- **[DECISION — owner] The read-side control-plane concept is named "map" (`roeh map`, `bin/roeh_map.py`), not "project."** [auto-recorded 2026-08-25] After the architecture was re-explained, the owner rejected "project" as the term and chose "map": *"I don't like the term 'project'. What about roeh map."* The name then carried into the module and command surface throughout the 2026-08-25 read-path work; the chapter above uses `roeh map` as a given without recording the rename. REJECTED: "project" as the concept's name — overloaded, since roeh is itself a *per-project* tool. WHY it matters: prevents a future session re-litigating the term. Cite: owner turn, this session (transcript `1ef25bff`), 2026-08-24; the name is now load-bearing across `bin/roeh_map.py` and its tests.

### 2026-08-25 — the scribe/refresh architecture: one author, two passes

*A distinct theme from the same day's "v3 read path" chapter above; per append-only it lands
at EOF after that chapter's §5, not inserted beside it. These are owner-ratified architecture
decisions, `[auto-recorded]` by the scribe on the owner's ON-DEMAND instruction ("scribe the
decisions first") — NOT the PreCompact gate. The division-of-labor rationale had lived only in
`agents/scribe.md` and `skills/refresh/SKILL.md`, never in this trace; an oracle CONSULT this
session established the gap. These three entries close it. Owner turns cited verbatim from
transcript `1ef25bff` (grepped, not the assistant's prose).*

- **[DECISION — owner] Scribe and refresh are not two kinds of thing: ONE author, TWO passes, selected by TRIGGERS.** [auto-recorded 2026-08-25] There is a single author — the scribe — and two passes over the record: CAPTURE (forward, work→record: *"what did this decide?"*) and RECONCILE (backward, record→world: *"is what we wrote still true?"*). `ingest`/`refresh`/`gate`/`on-demand` are not separate authors but TRIGGERS that select which passes run and how wide, exactly as the owner ruled — `ingest` → capture, everything once (bootstrap); `refresh` → capture + reconcile, delta + full-record drift, also profile/§5; `gate` (PreCompact) → capture only, this session; `on-demand` → either/both, as asked. The scribe is the SOLE writer — `Write`/`Edit`-free, `roeh append` only — so `refresh` must author THROUGH the scribe and never append directly. WHY: the old scribe-vs-refresh boundary was tool-shaped, putting the seam at "which command runs" instead of at "which pass runs"; the record had already named the real seam as two passes needing judgement (`c948bea`, §3 L125–134: *"Session mining and the refresh drift check … the two passes needing real judgement"*) — this entry formalizes that latent split into the model, and AUGMENTS that prior entry rather than duplicating it. The owner's own turns this session: *"there's a tension that exists here between scribe and refresh that I think we need to resolve"*; *"the discussion in the session itself is important. Where does that get captured? On ingest and refresh it should. But what about scribe? Are these really one thing when we're pretending they are two?"*; *"I agree that the first is the way"*; ratified with *"Let's do it the way you first proposed and we can adjust if needed with experience:"* followed by the trigger table above. REJECTED: keeping scribe and refresh as two independent tools — the tool-shaped seam, which located the boundary at the command rather than the pass and left the sole-writer guarantee unstated. GATES: a pending charter/hook refactor (`agents/scribe.md`, `skills/refresh`, `skills/ingest`, the hook scripts) must conform — the scribe becomes the sole author and every trigger routes its writes through it. Cite: owner turns, transcript `1ef25bff`; oracle CONSULT this session (which located the rationale only in `agents/scribe.md` and `skills/refresh/SKILL.md`, verified against the trace); `c948bea` §3 L125–134; `skills/refresh/SKILL.md` Phase 3.

- **[DECISION — owner] The gate runs CAPTURE only; RECONCILE is deliberate, never automatic at compaction.** [auto-recorded 2026-08-25] The PreCompact gate runs the capture pass alone. Drift — whether already-recorded entries still hold — runs deliberately, via `refresh` or on-demand, and is never fired automatically at compaction. WHY: reconcile's judgement half is expensive, per-claim reasoning on the session model (`skills/refresh/SKILL.md` L14–18: *"the drift check in Phase 2 does NOT [run on sonnet] … judgement against evidence, not retrieval"*); auto-compact fires when the window is already full and must not be wedged (the standing principle, §1, `b8de529`); the gate stays cheap and simple. DEFERRED — a live alternative deliberately NOT taken, recorded as a deferral so it reads as a choice, not an omission: running LOCAL reconcile (this session's OWN supersessions) at compaction was raised by the owner — *"Why not reconcile on compaction"* — on the reasoning that the session being compacted is the one most likely to have created drift and compaction is the freshest-context moment to judge it. It was explicitly deferred pending experience, per *"Let's do it the way you first proposed and we can adjust if needed with experience"*. A future session should neither re-litigate it from scratch nor silently flip the gate to run reconcile. CONSEQUENCE to flag: reconcile therefore fires only on explicit invocation, so silent rot between refreshes is possible. The intended mitigation, to be designed in the refactor, is a detect-vs-judge split INSIDE the reconcile pass — cheap mechanical detection of broken citations and moved cited code runs automatically and produces a worklist, plus an "overdue" signal for the semantic remainder that still needs the model. REJECTED: running the full reconcile pass at the gate — the expensive judgement half at the worst moment for both cost and context window. GATES: the same charter/hook refactor — the PreCompact path stays capture-only, and the reconcile detect/judge split + overdue signal are net-new design. Cite: owner turns, transcript `1ef25bff` (*"Why not reconcile on compaction"*; *"Let's do it the way you first proposed …"* + the trigger table, scope column *"gate (PreCompact) → capture only → this session — reconcile deliberately excluded"*); `skills/refresh/SKILL.md` L14–18.

- **[GOTCHA] `refresh` has been appending DIRECTLY to the trace, against the sole-author rule just ratified (Entry A above).** [auto-recorded 2026-08-25] The trace's own chapter preambles — *"Appended by the second refresh"* (`docs/decision-trace.md` L457 and L475; and the second-refresh chapter it authored, L483) — show `refresh` writing to the record directly. That contradicts refresh's OWN designed flow: `skills/refresh/SKILL.md` Phase 3 (L83–93) says *"Dispatch the **scribe** with the findings … The scribe appends via `roeh append`, which cannot rewrite."* Under the sole-author model now ratified (Entry A), refresh MUST author through the scribe; the direct-append path is the wrong turn and left unstated the guarantee that only one Write/Edit-free author touches the file. FIX PENDING in the charter refactor. Also to resolve there — a doc-internal tension in `agents/scribe.md`, flagged by the oracle CONSULT this session and verified directly: L145–147 charges the scribe with naming supersession INSIDE the entry (*"When your entry invalidates something already recorded, say so inside the entry — name the entry it contradicts"*), while the output guidance at L185 routes supersession-naming into a separate closing *"CONTRADICTS"* report block. The two describe different homes for the same act; the refactor should state once where supersession-naming lives (the entry body is load-bearing; the report block is ephemeral). Cite: `docs/decision-trace.md` L457/L475/L483; `skills/refresh/SKILL.md` Phase 3 (L83–93); `agents/scribe.md` L145–147 vs L185; oracle CONSULT this session.

## §5 — Resume state (superseding the §5 above, 2026-08-25)

*The §5 above (2026-08-25, v3 read-path) is retained as written. This block supersedes it, recording the scribe/refresh architecture ratification and two fixed-but-uncommitted hook bugs. It carries the v3 read-path state forward unchanged — that workstream is untouched by today's architecture decisions.*

- **Where we are:** v0.4.3 shipped surface unchanged (retrieval layer, read-only mode, Python 3.8 floor). Two uncommitted workstreams live in the working tree: (1) the **v3 read-path core** (`bin/roeh_map.py`, `tests/test_roeh_map.py`, `tests/fixtures/trace-v3.md`, `docs/design/*`), review-complete, ~159 deterministic tests green, standalone and NOT CLI-wired — carried forward from the §5 above; (2) the scribe/refresh work described next.
- **NEW this session — scribe/refresh architecture RATIFIED (owner):** ONE author (the scribe), TWO passes — CAPTURE (work→record) and RECONCILE (record→world) — selected by TRIGGERS (`ingest`/`refresh`/`gate`/`on-demand`), not separate tools. The scribe is the SOLE writer; `refresh` must author through it. The **gate runs capture-only**; RECONCILE is deliberate (refresh/on-demand), never automatic at compaction — **local-reconcile-at-compaction was considered and DEFERRED pending experience** (owner: *"we can adjust if needed with experience"*). See this chapter's `[DECISION — owner]` Entry A and Entry B. GOTCHA flagged: `refresh` has been appending directly, against the sole-author rule (Entry C).
- **Two hook bugs FIXED in the working tree but UNCOMMITTED** (`M bin/roeh-precompact`, `M bin/roeh-sessionstart`), to be **committed-then-scribed WITH their SHA next** — no code entry is recorded for them yet, because they cite uncommitted code:
  - **Bug 1 — `roeh-precompact` emitted an invalid `hookSpecificOutput.additionalContext`, which Claude Code rejects** (*"Hook JSON output validation failed"*), so the nag it tried to deliver was silently dropped on every compaction. Removed — the supported channel is `SessionStart` (trigger=compact), which already re-injects §5 and the "behind → /roeh:refresh" prompt. Working-tree cite: `bin/roeh-precompact:89–95`.
  - **Bug 2 — the active session is now EXCLUDED from the behind-check**, so the manual `/compact` gate is no longer unsatisfiable. The firing session's own transcript is still being written, so it always reads "unmined" against itself; counting it *"made this gate unsatisfiable, wedging the very /compact that fired the hook."* Working-tree cite: `bin/roeh-precompact:47–53`.
- **Next (critical path), two tracks:** (a) **the charter/hook refactor** — bring `agents/scribe.md`, `skills/refresh`, `skills/ingest` and the hooks into the ratified model (sole-author; refresh authors through the scribe; gate capture-only) AND design the reconcile **detect/judge split + overdue signal**; also resolve the `agents/scribe.md` L145–147-vs-L185 supersession-naming tension; (b) **the v3 track, unchanged from the §5 above** — the write-path spec → build the write side → a clean ingest. **CLARIFICATION of the §5 above:** its *"Next (critical path): the write-path spec"* is now one of two parallel tracks, not the sole next; and committing the two hook fixes (then scribing with SHA) precedes both.
- **Still a PROPOSAL:** the v3 architecture (RFC + impl spec) is not adopted; the owner has not ruled on adoption. Only the read-path *code* exists, standalone.
- **Currently gated on:** nothing operational. GATED (carried forward): any liveness/supersession mechanism must type the overturn-vs-refine edge and fail LOUD on uncertain liveness (2026-08-24 `[LESSON]`); any migration must clean-start, never convert (2026-08-24 `[DECISION — owner]`). GATED (new): the charter/hook refactor must conform to the one-author/two-passes/triggers model, and the PreCompact path stays capture-only (this chapter's Entries A/B).
- **Open questions:** carried from the §5 above — (1) bound retrieval cost as the log grows; (2) enforce append-only against *direct* (non-scribe) edits; (3) whether any lossy summarisation tier is acceptable given *under-claim beats confabulate*.
- **Do not re-derive:** everything in the previous §5, plus —
  - Treating scribe and refresh as two independent tools — REJECTED this session; one author, two passes, triggers select the passes (Entry A).
  - Running the full reconcile pass at the PreCompact gate — REJECTED; the gate is capture-only, reconcile is deliberate (Entry B). Note: LOCAL reconcile at compaction is DEFERRED, not rejected — do not re-litigate it from scratch, and do not silently enable it.

*Appended after this chapter's §5 per append-only (`roeh append` writes only at EOF). These two entries are the FIRST WORKED EXAMPLES of the one-author/two-passes model ratified in this chapter's Entry A/B — one RECONCILE finding, one CAPTURE+supersession — for the hook fixes now committed as `cf89c7c` (subject "Fix two PreCompact hook bugs found dogfooding the gate") on branch `precompact-gate-fixes`, **not yet merged to main** (main HEAD is `f6689e7`). They REPLACE the fixed-but-uncommitted pending-state lines in the §5 above (L599–601); the superseding §5 below carries the current resume state. `[auto-recorded]` by the scribe on the owner's ON-DEMAND instruction (*"fix the two hook bugs first"*, transcript `1ef25bff`), NOT the PreCompact gate.*

- **[GOTCHA] `bin/roeh-precompact` had silently emitted `hookSpecificOutput.additionalContext` — a shape `PreCompact` does NOT support — so Claude Code rejected it at runtime (*"Hook JSON output validation failed"*) and the pre-compaction nag was dropped on every compaction.** [auto-recorded 2026-08-25] This is the RECONCILE pass's first worked example: not a new decision but CODE that had drifted from two things the record already got right, caught by nothing automatic — only by dogfooding an actual compaction this session. The record was CORRECT; the code had silently violated it. The two recorded contracts it broke: the `[DECISION]` that `SessionStart(trigger=compact)` is the channel that re-injects §5 (§3 L118, `b8de529`), and the recorded contract that `PreCompact` blocking is *"exit 2 and nothing else"* (§3 L173, `d8098d3`) — i.e. `PreCompact` controls flow, it does not inject context. FIX (`cf89c7c`): removed the invalid field; the NOTE now states the contract in the code — *"PreCompact does NOT support `hookSpecificOutput.additionalContext` … an earlier version of this file emitted it, so the nag it was trying to deliver was silently dropped on every compaction … delivered by the SessionStart hook (trigger=compact), which re-injects §5 RESUME STATE and the 'behind → /roeh:refresh' prompt … the one supported channel"* (`bin/roeh-precompact:89–100@cf89c7c`). The docs contract was confirmed via a claude-code-guide research pass against the official hooks docs (per the commit message: only `PreToolUse`/`UserPromptSubmit`/`PostToolUse`/`PostToolBatch`/`Stop` carry `additionalContext`; `PreCompact` uses `exit 2` or `decision:block` and nothing else). META-POINT — the same shape as the standing dead-field/unexercised-guard lessons: the tests had ASSERTED the invalid `additionalContext` shape and passed anyway, because a unit test parses JSON while the real harness rejects it — *"a guard never exercised against the true contract"* (cf. `SCHEMA_VERSION` `20914b6`, `last_ingest` `c31b311`, `precompact.block_manual` `9c587a7`; principle §1, `d8098d3`). The fix rewrote them to the real contract and added a guard that `PreCompact` never emits `hookSpecificOutput` across every non-blocking path (`tests/test_roeh.py::test_never_emits_the_precompact_specific_output`); 166 deterministic tests green. REJECTED: delivering the pre-compaction nag through `PreCompact` `additionalContext` — unsupported (commit `cf89c7c` REJECTED clause). GATES: nothing operational — it reconciles committed code back to the recorded contract, and feeds the pending charter/hook refactor (this chapter's Entry A/B), where the `PreCompact` path stays capture-only and injects nothing. Cite: `cf89c7c` (message + diff); `bin/roeh-precompact:89–100@cf89c7c` (the NOTE) and `:50–56@cf89c7c` (the two emit paths reduced to `systemMessage`); the runtime rejection *"Hook JSON output validation failed"* as quoted in the commit and the code comment; `[DECISION]` §3 L118 and the exit-2 contract §3 L173; owner turn *"fix the two hook bugs first"* (transcript `1ef25bff`). NOTE: on branch `precompact-gate-fixes`, not yet merged to main.

- **[DECISION] `roeh status` now EXCLUDES the currently-active session from the unmined/behind check (`status(active_session=…)`), so the manual `/compact` gate is no longer UNSATISFIABLE.** [auto-recorded 2026-08-25] The CAPTURE pass's first worked example: a new call recorded forward from the work, with its supersession named. WHY: an in-progress transcript grows every turn, so `roeh mark`ing it never sticks and `behind` stayed true — the manual `/compact` gate could never be satisfied, and it **wedged the very compaction that fired the hook** (commit `cf89c7c`: *"Its transcript grows every turn, so `roeh mark` never sticks and `behind` stayed true, making the manual /compact gate UNSATISFIABLE: it wedged the very compaction that fired the hook."*). The rationale is not at risk from excluding it: the `.jsonl` persists across compaction and is mined by the NEXT session, where it is no longer active (`bin/roeh:255–262@cf89c7c` comment). HOW: `status(cfg, active_session=None)` (`bin/roeh:224@cf89c7c`); exclusion in the unmined comprehension via `s["id"] != active_session` (`bin/roeh:264–268@cf89c7c`); `opt_value` reads `--session VALUE` (`bin/roeh:411@cf89c7c`); `cmd_status` plumbs the `--session` flag or `CLAUDE_SESSION_ID` for standalone runs (`bin/roeh:420–426@cf89c7c`); both hooks pass it from the event's `session_id` (`bin/roeh-precompact:50–53@cf89c7c`, `bin/roeh-sessionstart:81–84@cf89c7c`). This REFINES the hook-policy `[DECISION]` (§3 L106–110, `b8de529`) — it adds "exclude the active session from 'still behind'" to the manual-compact-blocks rule — and PARTIALLY CLOSES the `[GOTCHA]` at §3 L317–322 (test/self transcripts show as UNMINED indistinguishably from real work): closed now for the ACTIVE-session case (the hook drops the firing session from the count), still OPEN for the test-harness-transcript case (a `claude -p` run from inside the repo still leaves an unmined `.jsonl` indistinguishable from real work). Scope verified — exclusion is the active session ONLY: `tests/test_roeh.py::test_excludes_only_the_active_session`, `::test_a_different_unmined_session_still_blocks`, `::test_active_session_alone_does_not_block`. REJECTED: counting the active session and instructing the user to `roeh mark` it — unsatisfiable, it grows again next turn (commit `cf89c7c` REJECTED clause). GATES: nothing operational — it UNBLOCKS the gate (a manual `/compact` on a live session now clears). Cite: `cf89c7c`; `bin/roeh` `status()`/`opt_value`/`cmd_status` (`:224`/`:411`/`:420–426@cf89c7c`) and the `session_id` plumbing in `bin/roeh-precompact:50–53@cf89c7c` and `bin/roeh-sessionstart:81–84@cf89c7c`; `[DECISION]` §3 L106–110; `[GOTCHA]` §3 L317–322; owner turns *"flip the block"*, *"getting blocked by roeh"*, *"fix the two hook bugs first"* (transcript `1ef25bff`). NOTE: on branch `precompact-gate-fixes`, not yet merged to main.

## §5 — Resume state (superseding the §5 above, 2026-08-25)

*The §5 above (2026-08-25, scribe/refresh architecture) is retained as written. This block supersedes it, recording that the two PreCompact hook bugs are now COMMITTED (`cf89c7c`, branch `precompact-gate-fixes`, not yet merged to main) and SCRIBED (the `[GOTCHA]` and `[DECISION]` two entries above). It carries the v3 read-path and scribe/refresh-architecture state forward unchanged.*

- **Where we are:** v0.4.3 shipped surface unchanged (retrieval layer, read-only mode, Python 3.8 floor). Two uncommitted workstreams remain in the working tree: (1) the **v3 read-path core** (`bin/roeh_map.py`, `tests/test_roeh_map.py`, `tests/fixtures/trace-v3.md`, `docs/design/*`), review-complete, standalone and NOT CLI-wired — carried forward unchanged; (2) the **scribe/refresh architecture RATIFIED** (owner) this session — ONE author (the scribe), TWO passes (CAPTURE / RECONCILE), selected by TRIGGERS (`ingest`/`refresh`/`gate`/`on-demand`); the gate runs capture-only; local-reconcile-at-compaction DEFERRED (see the 2026-08-25 chapter, Entries A/B/C). NEW and now off the working tree: the **two PreCompact hook bugs are COMMITTED as `cf89c7c`** ("Fix two PreCompact hook bugs found dogfooding the gate") on branch **`precompact-gate-fixes`** — a direct child of main HEAD `f6689e7`, **NOT yet merged to main** — and **SCRIBED** (the two entries above). `cf89c7c` brings `tests/test_roeh.py` to **88** `def test_` methods; the commit's "166 deterministic tests green" is the full working-tree `unittest discover` = 88 (`test_roeh.py`) + 78 (uncommitted `test_roeh_map.py`).
- **SUPERSEDES the §5 above's pending-hook-state (L599–601):** the lines *"Two hook bugs FIXED in the working tree but UNCOMMITTED … to be committed-then-scribed WITH their SHA next … no code entry is recorded for them yet"* are now stale — both are committed (`cf89c7c`) and each has a real §3-style entry. Bug 1 (removed the unsupported `hookSpecificOutput.additionalContext`; SessionStart(compact) is the channel) is the `[GOTCHA]` above; Bug 2 (active-session exclusion so the manual `/compact` gate is satisfiable) is the `[DECISION]` above. These were the FIRST WORKED EXAMPLES of the one-author/two-passes model — one reconcile, one capture+supersession.
- **Next (critical path), two tracks — the two hook fixes that previously preceded both are now DONE:**
  - **(a) the charter/hook refactor — the immediate next step.** Bring `agents/scribe.md`, `skills/refresh`, `skills/ingest` and the hook scripts into the ratified one-author / two-passes / triggers model (the scribe is the sole author; `refresh` authors THROUGH the scribe; the PreCompact path stays capture-only and injects nothing), AND design the reconcile **detect/judge split + overdue signal**; also resolve the `agents/scribe.md` L145–147-vs-L185 supersession-naming tension (Entry C).
  - **(b) the v3 track, unchanged** — the **write-path spec** the read spec derived (`docs/design/impl-read-path.md` §5) → build the write side → a clean ingest producing a real v3 trace.
- **Loose end (not gated):** `precompact-gate-fixes` is unmerged; merging it to main is an open thread, separate from the refactor.
- **Still a PROPOSAL:** the v3 architecture (RFC + impl spec) is not adopted; the owner has not ruled on adoption. Only the read-path *code* exists, standalone.
- **Currently gated on:** nothing operational. GATED (carried forward): any liveness/supersession mechanism must type the overturn-vs-refine edge and fail LOUD on uncertain liveness (2026-08-24 `[LESSON]`); any migration must clean-start, never convert (2026-08-24 `[DECISION — owner]`); the charter/hook refactor must conform to the one-author/two-passes/triggers model and keep the PreCompact path capture-only (2026-08-25 Entries A/B).
- **Open questions:** carried from the §5 above — (1) bound retrieval cost as the log grows; (2) enforce append-only against *direct* (non-scribe) edits; (3) whether any lossy summarisation tier is acceptable given *under-claim beats confabulate*.
- **Do not re-derive:** everything in the previous §5, plus —
  - Delivering the pre-compaction reminder through `PreCompact` `hookSpecificOutput.additionalContext` — REJECTED; the shape is unsupported and rejected at runtime, `SessionStart(compact)` is the channel (the `[GOTCHA]` above, `cf89c7c`).
  - Counting the currently-active session as "behind" — REJECTED; it makes the manual `/compact` gate unsatisfiable, so `status` excludes it (the `[DECISION]` above, `cf89c7c`).

*Continuation of the 2026-08-25 "scribe/refresh architecture" chapter (Entries A/B/C at §3 L587/L589/L591). Appended at EOF per append-only (`roeh append` writes only at end-of-file), not inserted beside that chapter. These two entries capture **Part A** — the charter/hook conformance refactor now committed as `db57c2e` on branch `precompact-gate-fixes` (not merged) — and record a boundary the owner set on the scribe's assistant-prose rule. `[auto-recorded 2026-08-25]` by the scribe on the owner's ON-DEMAND capture instruction, NOT the PreCompact gate. Owner turns quoted verbatim from transcript `1ef25bff` (grepped from the live session, not assistant prose). The superseding §5 below carries current resume state.*

- **[DECISION] Part A landed — the charters and hooks are now CONFORMED to the one-author / two-passes / triggers model (`db57c2e`), which CLOSES the "FIX PENDING" on Entry C (§3 L591).** [auto-recorded 2026-08-25] The model ratified this morning (Entries A/B, §3 L587/L589) was, until this commit, aspirational: the code still let `refresh` append directly and `agents/scribe.md` argued with itself. `db57c2e` ("charters: conform scribe/refresh/ingest/hooks to one-author, two-passes", branch `precompact-gate-fixes`) writes the model into the operating instructions. Concretely, per the diff: (1) **`agents/scribe.md`** gained a **"What you are"** section stating the scribe is the SOLE author, every trigger (`gate`/`refresh`/`ingest`/`on-demand`) routes its writes THROUGH it, and `roeh append` is the one write path — and it names the two passes **CAPTURE**/**RECONCILE** as explicitly *orthogonal* to the DRAFT/RECORD mode (*"pass is which question you answer, mode … is whether you append or hand back blocks"*); on-demand RECORD dispatch is now first-class (RECORD when *"either `roeh pending` exits 0 … **or** an on-demand dispatch explicitly instructs you to append/record"*), not only the gate sentinel; and the Entry-C supersession-naming contradiction is RESOLVED — the entry body is the load-bearing home of a supersession, the report's `CONTRADICTS` line only its echo (stated at both the append-only-discipline line and the CONTRADICTS output guidance, closing Entry C's "L145–147 vs L185" item). (2) **`skills/refresh/SKILL.md`**: refresh never writes the trace itself — **every** trace write, INCLUDING the §5 update (Phase 5), now routes through the scribe (Phase 3); only the profile is written directly (Phase 4); phases relabelled **CAPTURE** (Phase 1) / **RECONCILE** (Phase 2). This is the concrete FIX for Entry C's "refresh appends directly" GOTCHA. (3) **`skills/ingest/SKILL.md`**: framed as the capture pass at *bootstrap* scope — the genesis exception, *"the one trigger that writes the record wholesale rather than through the scribe … after ingest, the scribe is the sole author."* (4) **`hooks/hooks.json` + `bin/roeh-precompact`**: the gate's scribe dispatch is now **CAPTURE-only** (prompt: *"This is the CAPTURE pass ONLY … do NOT run the reconcile/drift check over the existing record here"*), per Entry B; and a stale docstring that still described the removed injected-reminder was fixed to point at `SessionStart(trigger=compact)`. Commit reports **166 tests green; `claude plugin validate` passes**. REJECTED / deferred: **Part B** — the reconcile **detect/judge split + overdue signal** — is deliberately NOT in this refactor; it is net-new design, deferred (commit message: *"Part B … is deferred, net-new design"*). This entry does not GATE anything new; it CLOSES Entry C's "FIX PENDING". Cite: `db57c2e` (message + diff); `agents/scribe.md` ("What you are" §; the modes §; the supersession lines) @ `db57c2e`; `skills/refresh/SKILL.md` (Phases 1/2/3/5) @ `db57c2e`; `skills/ingest/SKILL.md` (bootstrap-capture note) @ `db57c2e`; `hooks/hooks.json` (scribe prompt) + `bin/roeh-precompact` (docstring) @ `db57c2e`; Entries A/B/C this chapter (§3 L587/L589/L591); owner turn *"Do A first"* (transcript `1ef25bff`). NOTE: on branch `precompact-gate-fixes`, not yet merged to main (main HEAD `f6689e7`).

- **[DECISION — owner] The scribe's strict "assistant/system prose is NEVER a source" rule is KEPT AS-IS; a refinement to admit provenance-labelled rejected-alternative *reasoning* was considered and DEFERRED — not rejected.** [auto-recorded 2026-08-25] The hard rule (`agents/scribe.md` "NOT a source: assistant prose", @ `db57c2e`; and the foundational `[PRINCIPLE]` §1 L48, origin `b8de529`) stands unchanged. WHY, in the owner's own words: *"I just checked the original scribe file, and it works the way you originally defined it with a system turns as not a source. And I have found in practice, it seems to be working pretty well. So my inclination right now is to mark this as a decision not taken and make a note that this might be something we wanna revisit in the future."* The bright line's value is that it needs no per-entry judgement. DEFERRED — a live alternative deliberately not taken, recorded as a deferral (with its revisit trigger) so a future session neither re-litigates it cold nor silently adopts it: admitting rejected-alternative **reasoning** (as opposed to **facts**) from assistant analysis WHEN provenance-labelled — on the owner's argument that the road-not-taken often lives in assistant turns more than in the code: *"my concern is that assistant turns do contain valuable supporting information and excluding them may be leaving useful information on the floor. While the commit's contain the path taken, I wonder if the path's not taken live more in the assistant turns that in the code."* A narrower **"ratification clause"** (assistant articulation admissible only through the owner's ratifying turn) was also on the table and — per the dispatch — briefly added to `agents/scribe.md` this session, then reverted; the committed state confirms the end result: `agents/scribe.md` @ `db57c2e` carries the original strict rule with NO ratification/articulation clause (verified: no such text at HEAD). REVISIT TRIGGER: revisit if a real session catches itself re-deriving a rejected alternative that was genuinely reasoned through but never recorded because the reasoning lived only in assistant turns — that is the empirical signal the bright line is costing the road-not-taken. Absent that signal, "working in practice" wins. REJECTED (for now): the fact/argument split + provenance-label, and the ratification clause. GATES: nothing — it records a boundary so it is not re-derived. Cite: owner turns this session, transcript `1ef25bff` (the concern and the ruling, both quoted verbatim above); `agents/scribe.md` "NOT a source: assistant prose" @ `db57c2e` and `[PRINCIPLE]` §1 L48 (`b8de529`).

## §5 — Resume state (superseding the §5 above, 2026-08-25)

*The §5 above (2026-08-25, hook fixes committed) is retained as written. This block supersedes it, recording that **Part A — the charter/hook conformance refactor — is now COMMITTED** (`db57c2e`, branch `precompact-gate-fixes`, still not merged to main) and that the two entries just above are scribed. It carries the v3 read-path state forward unchanged.*

- **Where we are:** v0.4.3 shipped surface unchanged (retrieval layer, read-only mode, Python 3.8 floor). Branch `precompact-gate-fixes` now holds **three commits** off main HEAD `f6689e7`, still UNMERGED: `cf89c7c` (two PreCompact hook bugs), `2f75bb3` (record: scribe/refresh architecture + the two hook-fix entries), and **`db57c2e`** (Part A — charters/hooks conformed to the one-author / two-passes / triggers model; commit reports 166 tests green, `claude plugin validate` passes). One uncommitted workstream remains in the working tree: the **v3 read-path core** (`bin/roeh_map.py`, `tests/test_roeh_map.py`, `tests/fixtures/trace-v3.md`, `docs/design/*`), review-complete, standalone, NOT CLI-wired — carried forward unchanged.
- **CLOSED this session:** Entry C's "FIX PENDING" (§3 L591) — `refresh` appending directly to the trace, and the `agents/scribe.md` L145-147-vs-L185 supersession-naming tension — are both RESOLVED in `db57c2e` (Entry 1 above). Separately, the scribe's strict assistant-prose rule is **KEPT**: a refinement (admit provenance-labelled rejected-alternative *reasoning*; a "ratification clause") was considered and **DEFERRED**, not adopted, by owner decision (Entry 2 above; owner: *"a decision not taken … revisit in the future"*).
- **SUPERSEDES the §5 above's next-step line (L623):** *"the charter/hook refactor — the immediate next step"* is now **DONE** for its conformance half (Part A committed as `db57c2e`). The immediate next step is therefore **Part B** — the reconcile **detect/judge split + overdue signal** (cheap mechanical detection of broken citations / moved cited code runs automatically and yields a worklist, plus an "overdue" signal for the semantic remainder that still needs the model; see Entry B, §3 L589) — still **DEFERRED / UNSTARTED**, net-new design.
- **Next (critical path), two tracks:**
  - **(a) Part B — the reconcile detect/judge split + overdue signal** (net-new design, unstarted).
  - **(b) the v3 track, unchanged** — the write-path spec the read spec derived (`docs/design/impl-read-path.md` §5) → build the write side → a clean ingest producing a real v3 trace.
- **Loose end (not gated):** `precompact-gate-fixes` (now three commits: `cf89c7c`, `2f75bb3`, `db57c2e`) is unmerged; merging to main is an open thread, separate from Part B.
- **Still a PROPOSAL:** the v3 architecture (RFC + impl spec) is not adopted; the owner has not ruled on adoption. Only the read-path *code* exists, standalone.
- **Currently gated on:** nothing operational. GATED (carried forward): any liveness/supersession mechanism must type the overturn-vs-refine edge and fail LOUD on uncertain liveness (2026-08-24 `[LESSON]`); any migration must clean-start, never convert (2026-08-24 `[DECISION — owner]`); the PreCompact path stays capture-only (2026-08-25 Entry B — now enforced in `hooks/hooks.json` + `bin/roeh-precompact` @ `db57c2e`).
- **Open questions:** carried forward — (1) bound retrieval cost as the log grows; (2) enforce append-only against *direct* (non-scribe) edits — note the charter now states this norm (refresh routes THROUGH the scribe, `db57c2e`), but it is doc-enforced, not mechanically enforced; (3) whether any lossy summarisation tier is acceptable given *under-claim beats confabulate*.
- **Do not re-derive:** everything in the previous §5, plus —
  - Re-opening scribe/refresh conformance — Part A is committed (`db57c2e`); the model is now in the operating instructions, not just the trace (Entry 1).
  - Loosening the assistant-prose rule without the empirical signal — the strict rule is KEPT by owner decision; the refinement is DEFERRED with a named revisit trigger, do not silently adopt it (Entry 2).

### 2026-08-25 — the v3 write-path spec, and validating by clean re-derivation

*Continuation of the 2026-08-25 v3 track (the "v3 read path, built consumer-first" chapter, §3 L543/L551). Appended at EOF per append-only (`roeh append` writes only at end-of-file), not inserted beside that chapter. These two entries capture the v3 **write-path spec** (the producer contract) and the **validation method**, now committed as `0a85a60` ("v3 (proposal): design docs + read-path core, and the write-path spec") — HEAD of branch `precompact-gate-fixes`, a fourth commit off main HEAD `f6689e7`, NOT merged to main. `[auto-recorded 2026-08-25]` by the scribe on the owner's ON-DEMAND capture instruction (*"commit and scribe"*), NOT the PreCompact gate. Owner turns quoted verbatim from transcript `1ef25bff` (grepped from the live session, not assistant prose). The read-path core + design docs, recorded as "working-tree, uncommitted" at §3 L551/L557 and in the §5 above (L643), are now COMMITTED at `0a85a60` — a STATUS CHANGE carried in the superseding §5 below, not a new entry. The superseding §5 below carries current resume state.*

- **[DECISION — owner] v3 is validated by clean RE-DERIVATION on a real project — roeh itself first, then upstream — NOT by feeding the existing dirty trace to the read path.** [auto-recorded 2026-08-25] The correctness/dogfood check for v3 is to re-ingest CLEAN from primary evidence on a real project and inspect the result, in the order **roeh first, then the upstream project**; the dirty trace is the comparison BASELINE, never a read-path input. WHY, owner verbatim (transcript `1ef25bff`): *"we dogfood not on the dirty trace, but we re-derive clean on another project. It could be the source upstream project, this project, or a different one. If we choose the upstream project we can compare the dirty trace to the newly derived one."* Order fixed by the owner: *"roeh first them upstream"*. This is the operational form of the clean-start `[DECISION — owner]` (§3 L527), which already cast the dirty trace as a *"test fixture and a pointer to gaps … reveals what a clean ingest missed"* — so on upstream (the layer holding the ~10k dirty trace) the clean re-derivation doubles as a **dirty-vs-clean comparison**: what a clean ingest recovers, and the holes it leaves to backfill from primary evidence. In production the reader never sees a dirty v3 trace, because clean-start guarantees a re-ingest first. The committed write-path spec encodes exactly this order — `docs/design/impl-write-path.md` §7 step 4 (*"clean-ingest roeh itself → a real v3 trace; map it; diff coverage vs the current trace"*) then step 5 (*"Then upstream (scale + dirty-vs-clean comparison), scratchpad-only, aggregate stats"*), @ `0a85a60`. REJECTED / reordered: making the **read path's dogfood on the ~10k dirty trace the PRIMARY correctness gate**. The read spec's `docs/design/impl-read-path.md` §6/§7 step 6 gate (*"Dogfood on the real dirty trace (correctness gate) — before declaring the read path done"*, @ `0a85a60`) is reframed: the read path's dirty-trace pass already ran on roeh's own 58-entry trace (§3 L557, 58==58, no under-count), and the go-forward gate is clean re-derivation, with a scale check on the dirty ~10k retained only as a scratchpad, aggregate-stats step inside the upstream phase (spec §7 step 5), not the primary gate. CONSTRAINT: the upstream artifact stays sensitive — scratchpad-only, aggregate figures only, its name never entering the repo. GATES: the v3 build sequence — build the write side, THEN clean-ingest roeh (diff coverage vs the current trace), THEN upstream. Cite: owner turns, transcript `1ef25bff` (both quoted verbatim); clean-start `[DECISION — owner]` §3 L527; `docs/design/impl-write-path.md` §7 steps 4–5 and `docs/design/impl-read-path.md` §6/§7 step 6 @ `0a85a60`.

- **[DECISION] The write-path producer contract is SPECIFIED and committed (`docs/design/impl-write-path.md` v2 @ `0a85a60`), deriving the writer from the reader — the reader defines the schema, the WRITER enforces a stronger validity contract at creation.** [auto-recorded 2026-08-25] Consumer-first (the `[DECISION]` §3 L551) means the reader's parser/liveness/verify *is* the write contract; the spec formalizes it BEFORE the write side is built, so the authority boundary is not mis-built. Framing (spec §0/§1 @ `0a85a60`): the reader asks *"can I interpret this?"*, the writer asks *"will I allow this into the authority?"* — a **mechanical-vs-epistemic split**: mechanical facts (syntax, `id`-uniqueness, edge targets exist + strictly-earlier, `chain`) are *refused* on failure and never emitted; epistemic assertions (overturns-vs-refines, conflicts, atomic) are recorded as producer assertions and surfaced by the reader, *neither fabricated nor silently trusted* — roeh's "don't convert model judgment into authority" line, drawn at the write boundary. The concrete calls in the committed spec (delegated by the owner — *"you decide"*, transcript `1ef25bff`; v2 folds an external review per the spec header): (1) **`id` = 64-bit** = `sha256(NFC(date)·\0·TAG·\0·NFC(collapse_ws(lead)))[:16]`, canonical, **immutable once written**, with a defined collision/duplicate-refusal path (§3.1) — REJECTING a 32-bit (`[:8]` hex) id, which *"birthday-collides at ~65k entries; too small for a permanent foreign key"*. (2) The write is a **serialized, fsync'd, record-atomic transaction** — PREPARE (no mutation) / COMMIT under `flock` with tail-recheck, *"exactly one complete record or zero bytes"* surviving a crash (§4) — closing the chain race two unlocked writers would open (each chaining off the same `prev`, the second's `chain` lying); today's `cmd_append` (`bin/roeh:456`) has neither lock nor fsync (no `flock`/`fsync` anywhere in `bin/roeh`). (3) **`class` is DROPPED** — redundant with the tag; the reader's terminal test is `tag∈TERMINAL` OR `cls∈{dead-end,withdrawn}`, the same set (`compute_liveness` L254), so the writer never emits `class` and the reader drops the `cls` clause — the derivable-stored-field trap of the recorded dead-field lessons. This **supersedes the machine-field list recorded in the hybrid-format `[DECISION]` §3 L553** (which listed `id, chain, class, atomic, date, topic-hint`): `class` is removed from that set. (4) The reader's **atomic ≥2-clause heuristic is REMOVED** (`compute_liveness` L273–275) — it flagged every well-formed five-part entry (WHY:+REJECTED:+GATES: = 3 markers) as `UNCERTAIN`, turning the signal to noise and second-guessing a valid producer assertion with a bad proxy; the SOUND check — a *superseded* `atomic≠true` entry (L270) — is kept, plus a regression test that a superseded five-part `atomic=true` entry is NOT flagged. (5) **`topic-hint` kept with a HARD invariant** (§3.4): it MAY influence region *organization* (`assign_regions` L318–322) but MUST NOT affect coverage/completeness/scope-soundness, and the reader MUST stay correct ignoring it entirely; the authoritative home for *semantic* topic assignment stays the DERIVED side-map, never the immutable log — a model-authored hint can mis-organize but can never hide an entry. (6) **Clean-ingest** fans out extraction in parallel but the authority write is **single-threaded** — parallel extract → canonical sequence + cross-agent edge resolution → serial `roeh record` (§6). Also stated as invariants (§3.5/4.1): single-live-successor-unless-conflict-linked (context-scoped supersession NOT modeled — use a conflict link), and no-edge-inheritance (a superseded entry's superseder MUST restate `augments`, else the target is flagged `augment lost`). NOTE: the hybrid on-disk format itself is already recorded at §3 L553 — this entry does not restate it, it only removes `class` from its field set. REJECTED: **log sharding / a global-logical-order layer** — RFC v2 already removed sharding as a net-negative (`docs/design/retrieval-at-scale.md` L44: *"One append-only markdown file … No sharding … only file-size hygiene the write-mostly log never needs"*, @ `0a85a60`), so file order *is* the logical sequence by decision; building a logical-sequence abstraction for a closed future is the speculative future-proofing roeh avoids. DEFERRED (P2, §8): a machine-readable typing-status/reason; an explicit claim-unit atomicity model; an external signed chain head; context-scoped supersession. GATES: the write-path build — order per spec §7: **`roeh record`** (the transaction) → the two **reader changes** (drop `class` from liveness; remove the atomic ≥2-clause heuristic + add the regression test) → clean-ingest wiring → dogfood (roeh, then upstream — the `[DECISION — owner]` above). The two reader changes are owed against `bin/roeh_map.py`. Cite: `0a85a60`; `docs/design/impl-write-path.md` v2 §0/§1/§2/§3.1/§3.3/§3.4/§3.5/§4/§6/§7/§8 and `docs/design/retrieval-at-scale.md` §2.1 L44 @ `0a85a60`; `bin/roeh_map.py` `compute_liveness` (`cls` clause L254, sound atomic check L270, removed heuristic L273–275) and `assign_regions` (topic-hint fold L318–322) @ `0a85a60`; `bin/roeh:456` (`cmd_append`, no lock/fsync); consumer-first `[DECISION]` §3 L551; hybrid-format `[DECISION]` §3 L553; owner turns *"you decide"*, *"commit and scribe"* (transcript `1ef25bff`).

## §5 — Resume state (superseding the §5 above, 2026-08-25)

*The §5 above (2026-08-25, Part A committed) is retained as written. This block supersedes it, recording that the v3 **read-path core + design docs are now COMMITTED** at `0a85a60` (were untracked/uncommitted working-tree in the §5 above and at §3 L551/L557) and that the **write-path spec (v2) is committed**, its producer-contract decisions being the two entries just above. It carries the scribe/refresh-architecture and Part A/Part B state forward unchanged.*

- **Where we are:** v0.4.3 shipped surface unchanged (retrieval layer, read-only mode, Python 3.8 floor). Branch `precompact-gate-fixes` now holds **FOUR commits** off main HEAD `f6689e7`, still UNMERGED: `cf89c7c` (two PreCompact hook bugs), `2f75bb3` (record: scribe/refresh architecture), `db57c2e` (Part A — charters/hooks conformed), and NEW **`0a85a60`** ("v3 (proposal): design docs + read-path core, and the write-path spec"), now branch HEAD. The working tree has uncommitted appends to `docs/decision-trace.md` (the Part A scribe entries at §3 L635/L637 and these entries) and `.claude/roeh-profile.md` — those trace entries are already present, do not re-record them.
- **STATUS CHANGE — the v3 read-path core + all four design docs are now COMMITTED at `0a85a60`.** This SUPERSEDES the §5 above (L643) and §3 L551/L557, which recorded `bin/roeh_map.py`, `tests/test_roeh_map.py`, `tests/fixtures/trace-v3.md` and `docs/design/*` as "untracked/uncommitted working-tree" — they are now committed: `bin/roeh_map.py` (the standalone read-path core), `tests/test_roeh_map.py` (78 tests), `tests/fixtures/trace-v3.md`, and `docs/design/{retrieval-at-scale,impl-read-path,impl-write-path,prior-art}.md`. **166 deterministic tests green** (88 `test_roeh.py` + 78 `test_roeh_map.py`). **Still NOT adopted** (`0a85a60` commit body): `roeh_map.py` is NOT wired into `bin/roeh`, and the log format is unchanged — v3 is banked as a proposal, not adopted, until the write path and a real clean ingest exist.
- **NEW this session — the write-path producer contract is SPECIFIED and committed** (`docs/design/impl-write-path.md` v2 @ `0a85a60`). Its decisions are the two entries above: (a) v3 is validated by clean RE-DERIVATION (roeh first, then upstream), the dirty trace as comparison baseline not a read-path input — `[DECISION — owner]`; (b) the producer contract — reader-defines-schema / writer-enforces-stronger-contract, mechanical-vs-epistemic split; 64-bit immutable content-`id`; a serialized fsync'd record-atomic transaction; `class` dropped; the atomic ≥2-clause heuristic removed; `topic-hint` kept with a never-affects-coverage invariant; parallel-extract / serial-write clean-ingest — `[DECISION]`.
- **Next (critical path) — build the v3 WRITE side, per `impl-write-path.md` §7:**
  1. **`roeh record`** — the immediate next step: the PREPARE/COMMIT transaction (canonicalize; 64-bit `id` + collision path; edge validation; `chain`; `flock`+`fsync`+record-atomicity; hybrid formatting).
  2. **Two reader changes against `bin/roeh_map.py`** — drop the `class`/`cls` clause from `compute_liveness` (L254); remove the atomic ≥2-clause heuristic (L273–275) and add the regression test.
  3. **Clean-ingest-under-v3 wiring** (parallel extract → canonical sequence → serial `roeh record`).
  4. **Dogfood** — clean-ingest roeh itself → a real v3 trace, diff coverage vs the current trace; **then upstream** (scale + dirty-vs-clean comparison, scratchpad-only, aggregate stats).
- **The OTHER track — unchanged:** Part B — the reconcile **detect/judge split + overdue signal** (net-new design, still UNSTARTED / deferred; see §3 L589 and the §5 above L645/L647). Part A (charter/hook conformance) is DONE (`db57c2e`).
- **Still a PROPOSAL:** the v3 architecture (RFC + impl specs) is not adopted; the owner has not ruled on adoption. Only the read-path *code* + the design specs exist; the write side is unbuilt.
- **Loose end (not gated):** `precompact-gate-fixes` (now four commits: `cf89c7c`, `2f75bb3`, `db57c2e`, `0a85a60`) is unmerged; merging to main is an open thread, separate from the v3 build.
- **Currently gated on:** nothing operational. GATED (carried forward): any liveness/supersession mechanism must type the overturn-vs-refine edge and fail LOUD on uncertain liveness (2026-08-24 `[LESSON]`); any migration must clean-start, never convert (2026-08-24 `[DECISION — owner]`); the PreCompact path stays capture-only (2026-08-25 Entry B, enforced @ `db57c2e`). GATED (new): the v3 build follows the `impl-write-path.md` §7 order — `roeh record` before the reader changes before clean-ingest before dogfood; and v3 validation is clean re-derivation, roeh before upstream (the `[DECISION — owner]` above).
- **Open questions:** carried forward — (1) bound retrieval cost as the log grows; (2) enforce append-only against *direct* (non-scribe) edits — the charter states the norm (`db57c2e`) but it is doc-enforced, not mechanical; (3) whether any lossy summarisation tier is acceptable given *under-claim beats confabulate*.
- **Do not re-derive:** everything in the previous §5, plus —
  - A 32-bit (`[:8]` hex) content-`id` — REJECTED; it birthday-collides at ~65k entries and is too small for a permanent foreign key, so the id is 64-bit `[:16]` (this chapter's `[DECISION]`, spec §3.1).
  - Log sharding / a global-logical-order layer — REJECTED; RFC v2 removed sharding, file order IS the logical sequence (this chapter's `[DECISION]`, `retrieval-at-scale.md` L44).
  - Feeding the existing dirty trace to the read path as the PRIMARY v3 correctness gate — REJECTED; v3 is validated by clean re-derivation, roeh first then upstream (this chapter's `[DECISION — owner]`).
  - Keeping `class` as a persisted field, or the reader's atomic ≥2-clause heuristic — both REMOVED in the write-path spec (this chapter's `[DECISION]`).

*Continuation of the 2026-08-25 v3 write-path track (the "v3 write-path spec" chapter, §3 L657/L663, and the consumer-first read-path chapter, §3 L543/L551). Appended at EOF per append-only (`roeh append` writes only at end-of-file), not inserted beside those chapters. These two entries capture the v3 **write side, build steps 1-2** — `roeh record` and the reader changes it assumes — now committed as `04d542d` ("write path: roeh record + the reader changes it needs"), the SIXTH commit off main HEAD `f6689e7` on branch `precompact-gate-fixes`, NOT merged to main. `[auto-recorded 2026-08-25]` by the scribe on the owner's ON-DEMAND capture instruction (*"code review first?"* → *"go"*, transcript `1ef25bff`), NOT the PreCompact gate. The write-path spec `[DECISION]` at §3 L663 already DECIDED the 64-bit id / `class`-dropped / atomic-heuristic-removed / the serialized fsync'd transaction; this chapter records their IMPLEMENTATION and what is NEW (two review passes, injection-hardening), and does not restate them. The superseding §5 below carries current resume state.*

- **[DECISION] The v3 write path — build steps 1-2 of `docs/design/impl-write-path.md` §7 — is BUILT and committed (`04d542d`): `roeh record`, the structured transactional producer, plus the two reader changes it assumes. This IMPLEMENTS the write-path spec decisions recorded at §3 L663 (the 64-bit `id`, `class` dropped, the atomic ≥2-clause heuristic removed, the serialized fsync'd transaction); those decisions are not restated here.** [auto-recorded 2026-08-25] What landed, verifiable in the diff @ `04d542d`: `cmd_record` (`bin/roeh:561`) takes a JSON entry on stdin, assigns the content-derived 64-bit `id`, validates edges against the reader (dangling / prose-only / competing-successor / augment-lost all refused), computes the tamper-evidence `chain` via the SHARED `chain_link` — extracted to `bin/roeh_map.py:888` so the writer and `verify_chain` (`:903`) compute ONE formula, not two that can drift — and appends ONE complete record under `flock` + `fsync` (`bin/roeh:645`/`:714`); `cmd_append` (`bin/roeh:458`) now takes the SAME advisory lock (`:484`), because an unlocked append landing between `record`'s read-tail and its write would leave record's freshly-computed `chain` pointing at the wrong predecessor (review P1-4, comment `bin/roeh:477–482`). The reader changes owed at §3 L663 are now DONE against `bin/roeh_map.py` @ `04d542d`: the atomic ≥2-clause heuristic is REMOVED (`compute_liveness`; the SOUND *superseded-non-atomic* check at `:269–270` kept), `class`/`cls` DROPPED from liveness (redundant with the tag), and `_toplevel` (`:304`) widened from `{1,4}` to `[A-Za-z0-9]{1,8}` so `.jsonl`/`.parquet` cites resolve. WHY: consumer-first (the `[DECISION]` §3 L551) means the reader's parser/liveness/verify IS the write contract, so `record` enforces at creation what the reader would merely tolerate — *"Refuses what the reader would merely tolerate: dangling/prose-only edges, competing successors, augment-lost, duplicates, bad tags/dates, overlong or multi-sentence leads, non-boolean atomic"* (`04d542d` message). Reviewed TWICE this session — an adversarial subagent pass and the owner's `/code-review` — *"all real findings fixed, efficiency-only ones declined"* (`04d542d` message); **187 deterministic tests green** (`TestRecord`, `tests/test_roeh.py:436`). REJECTED / NOTE — a status boundary, not an omission: `record` is NOT yet wired to the producers — *"the scribe/ingest still use `append`; moving them onto `record` is build step 3 (the clean-ingest wiring), and a v3 trace is created by a clean re-ingest, not by converting the legacy one"* (`04d542d` message). So on the live legacy trace `record`'s machinery is deliberately off the producer path until step 3, consistent with clean-start-always (§3 L527). GATES: build step 3 — wire the scribe/ingest onto `record` (the clean-ingest) — then the roeh-first clean-ingest dogfood (diff coverage vs the current trace), then upstream (the `[DECISION — owner]` §3 L661). Cite: `04d542d` (message + diff); `bin/roeh` `cmd_record`/`cmd_append` (`:561`/`:458`), `bin/roeh_map.py` `chain_link`/`verify_chain`/`compute_liveness`/`_toplevel` (`:888`/`:903`/`:206`/`:304`), `tests/test_roeh.py` `TestRecord` (`:436`) — all @ `04d542d`; `docs/design/impl-write-path.md` §7 build order; write-path spec `[DECISION]` §3 L663; consumer-first `[DECISION]` §3 L551; owner turns *"code review first?"* → *"go"* (transcript `1ef25bff`). NOTE: on branch `precompact-gate-fixes`, not yet merged to main.

- **[GOTCHA] A machine-comment INJECTION vector in the hybrid format: untrusted prose could forge an entry's machine identity — `cmd_record` now sanitises AND round-trip-verifies so it cannot.** [auto-recorded 2026-08-25] The finding, surfaced by the adversarial review this session and confirmed against the reader: the reader binds the FIRST `<!-- roeh … -->` in an entry block — `_META` is non-greedy (`<!--\s*roeh\s+(.*?)\s*-->`, `bin/roeh_map.py:34`) and `_parse_meta` (`:99`) takes `_META.search(block)`, i.e. the EARLIEST match. So a `<!-- roeh id=evil … -->` hidden inside an untrusted prose field (e.g. `why`) would PRECEDE the real trailing comment and WIN — the persisted entry's `id`/`date`/`atomic`/`chain` become attacker-controlled; a newline in prose could likewise inject a fake `Supersedes:` edge or a whole fake entry head. `cmd_record` is the ONLY code path that mutates the append-only authority, so it is the one place untrusted input must not reach unguarded. FIX (`04d542d`): `_reject_unsafe` (`bin/roeh:515`) rejects `<!--`/`-->`/`\n`/`\r` in every field (`_UNSAFE`, `:512`) plus `,` in id-lists and `,`/`=` in `topic-hint` (`:630`) — the one list that lands INSIDE the comment — AND a round-trip verify (`:682–689`): after formatting, the entry must `parse_entries` back to EXACTLY the intended `id`/`tag`/`date`/`atomic`/`chain`/`supersedes`/`augments`/`conflicts`/`cites`/`topic-hint`, or `record` refuses and writes nothing — the writer verifies that what it wrote is what the reader will read; the round-trip is the backstop (review P0-1) for anything a substring blacklist alone would miss. SECOND fix, same review: the newly-UNCERTAIN guard (review P1-3, `bin/roeh:696–709`) had OVER-corrected — refusing every append that introduced an UNCERTAIN entry made `record` unable to supersede ANY entry with no `atomic` stamp, i.e. every legacy / `append`-authored entry. *"non-atomic entry superseded"* is a property of the TARGET (an old entry `record` cannot retro-stamp), not a fault the new record can fix, so it now WARNS and allows, while the fixable cases — a competing successor, a dropped augment across supersession — still REFUSE (`:700–707`). Without this split `record` could not operate on a real/legacy trace at all (review #1). REJECTED: a substring blacklist ALONE (kept, but the round-trip verify is the backstop for what it misses); refusing legacy supersession outright (the whole reason `record` is usable against the current trace). Cite: `04d542d`; `bin/roeh` `_reject_unsafe`/`_UNSAFE` (`:515`/`:512`), the round-trip check (`:682–689`) and the warn/refuse split in `cmd_record` (`:696–709`) @ `04d542d`; `bin/roeh_map.py` `_META`/`_parse_meta` (`:34`/`:99`, first-comment-wins) and `compute_liveness` *"non-atomic entry superseded"* (`:262–270`) @ `04d542d`; regression tests `tests/test_roeh.py` `TestRecord` — `test_rejects_a_forged_machine_comment` (`:543`), `test_rejects_a_newline_injection` (`:554`), `test_can_supersede_a_non_atomic_entry_with_a_warning` (`:608`), `test_refuses_a_competing_successor` (`:576`) @ `04d542d`. GATES: nothing new — a STANDING security property of the hybrid on-disk format (§3 L553) that any future writer MUST preserve: a prose field can never be allowed to forge machine identity. NOTE: on branch `precompact-gate-fixes`, not yet merged to main.

## §5 — Resume state (superseding the §5 above, 2026-08-25)

*The §5 above (2026-08-25, write-path spec committed) is retained as written. This block supersedes it, recording that v3 write-path build **steps 1-2 are now COMMITTED at `04d542d`** (`roeh record` + the two reader changes), with the two entries just above scribed. It carries the scribe/refresh-architecture and Part A/Part B state forward unchanged.*

- **Where we are:** v0.4.3 shipped surface unchanged (retrieval layer, read-only mode, Python 3.8 floor). Branch `precompact-gate-fixes` now holds **SIX commits** off main HEAD `f6689e7`, still UNMERGED: `cf89c7c` (two PreCompact hook bugs), `2f75bb3` (record: scribe/refresh architecture), `db57c2e` (Part A — charters/hooks conformed), `0a85a60` (v3 design docs + read-path core + write-path spec), `30404e6` (record: Part A conformance + write-path-spec decisions), and NEW **`04d542d`** ("write path: roeh record + the reader changes it needs"), now branch HEAD. Working tree has uncommitted appends to `docs/decision-trace.md` (these entries) and `.claude/roeh-profile.md`.
- **STATUS CHANGE — v3 write-path build steps 1-2 are BUILT and committed at `04d542d`.** `roeh record` — the structured, transactional producer (64-bit content `id`, edge validation against the reader, `chain` via the shared `chain_link`, `flock`+`fsync` record-atomic append, injection-hardened by sanitise + round-trip verify) — plus the two reader changes it assumed (atomic ≥2-clause heuristic removed; `class` dropped from liveness; `_toplevel` widened to 5-8-char extensions; `chain_link` extracted). This IMPLEMENTS the write-path spec `[DECISION]` (§3 L663) and CLOSES its "the two reader changes are owed against `bin/roeh_map.py`" item. Twice-reviewed (adversarial + `/code-review`); **187 deterministic tests green** (was 166 at `0a85a60`; `TestRecord` added).
- **SUPERSEDES the §5 above's "Next (critical path)" list (L672–676):** its step 1 (`roeh record`) and step 2 (the two reader changes) are now **DONE** at `04d542d`. The immediate next step is therefore **build step 3 — wire the scribe/ingest onto `record` (the clean-ingest wiring: parallel extract → canonical sequence + cross-agent edge resolution → serial `roeh record`)** — then **step 4, the roeh-first clean-ingest dogfood** (produce a real v3 trace; diff coverage vs the current trace), then upstream (scale + dirty-vs-clean, scratchpad-only, aggregate stats), per the `[DECISION — owner]` §3 L661 and `impl-write-path.md` §7.
- **Not on the producer path yet (by design):** `record` is built but the scribe/ingest still write via `roeh append`; per clean-start-always (§3 L527) a v3 trace is created by a clean re-ingest, not by converting the legacy one, so `record`'s machinery is deliberately off the live legacy producer path until step 3 — a status boundary, not an omission.
- **The OTHER track — unchanged:** Part B — the reconcile **detect/judge split + overdue signal** (net-new design, still UNSTARTED / deferred; §3 L589, §5 L645/L647). Part A (charter/hook conformance) is DONE (`db57c2e`).
- **Still a PROPOSAL:** the v3 architecture (RFC + impl specs) is not adopted; the owner has not ruled on adoption. `bin/roeh_map.py` is not CLI-wired and `record` is not on the producer path; v3 is banked, not adopted, until the write side is wired and a real clean ingest exists.
- **Loose end (not gated):** `precompact-gate-fixes` (now six commits) is unmerged; merging to main is an open thread, separate from the v3 build.
- **Currently gated on:** nothing operational. GATED (carried forward): any liveness/supersession mechanism must type the overturn-vs-refine edge and fail LOUD on uncertain liveness (2026-08-24 `[LESSON]`); any migration must clean-start, never convert (2026-08-24 `[DECISION — owner]`); the PreCompact path stays capture-only (2026-08-25 Entry B, enforced @ `db57c2e`); the v3 build follows `impl-write-path.md` §7 order and v3 validation is clean re-derivation, roeh before upstream (2026-08-25 `[DECISION — owner]` §3 L661). GATED (new, standing): any future writer must preserve the injection guard — a prose field can never forge machine identity (this chapter's `[GOTCHA]`).
- **Open questions:** carried forward — (1) bound retrieval cost as the log grows; (2) enforce append-only against *direct* (non-scribe) edits — doc-enforced (`db57c2e`), not mechanical; (3) whether any lossy summarisation tier is acceptable given *under-claim beats confabulate*.
- **Do not re-derive:** everything in the previous §5, plus —
  - Building `roeh record` or the two reader changes — DONE at `04d542d` (this chapter's `[DECISION]`); the next step is build step 3, the clean-ingest wiring.
  - Letting untrusted prose reach the machine comment unguarded — the FIRST `<!-- roeh -->` wins, so `record` sanitises + round-trip-verifies every field (this chapter's `[GOTCHA]`).
  - Refusing to supersede a non-atomic/legacy entry outright — it WARNS and allows; only competing-successor / augment-lost refuse (this chapter's `[GOTCHA]`).
