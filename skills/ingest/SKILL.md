---
description: Build this project's decision trace from history — fan out reader agents over git commits (mining inline comments), memory files, docs/scripts, and Claude Code session transcripts, then assemble the record and generate the profile. Run once after /roeh:init.
disable-model-invocation: true
---

# /roeh:ingest

Archaeology. You are reconstructing **why** this project is the way it is, from the
evidence that survives, and writing it into an append-only record.

Accepts `--quick` (single-pass, cheap), `--since <date>` (history floor), and
`--deep` (force maximum fan-out).

> **Where ingest sits in the model.** ingest is the CAPTURE pass at *bootstrap* scope —
> the one-time genesis of the record. It builds the initial trace by fanning out reader
> agents that emit **v3 record-proposals**, then canonical-sequencing them and writing each
> through **`roeh record`** (Phase 3) — append-only, typed edges, content ids, never
> rewriting. This is the one trigger that writes the record wholesale; **after ingest, the
> scribe is the sole author, and every incremental write — `/roeh:refresh`, the gate,
> on-demand — routes through it.**

## Phase 0 — resolve and scope

1. `roeh config`. If not initialized, stop and point at `/roeh:init`.

2. **`roeh ingest status` — then branch. Do NOT just start.** A full fan-out over
   already-mined history is expensive and produces mostly duplicates, and starting a
   second run over a live one double-writes into an append-only file. Read the state
   first:

   | State | What to do |
   |---|---|
   | `none` | Fresh project. Continue to step 3. |
   | `running` | **Stop.** Another ingest is in progress (started under 6h ago). Report which units are outstanding and let it finish. Only override if the owner confirms that run is dead. |
   | `abandoned` | A run died partway. **Offer to RESUME**: name the units that never landed and re-dispatch only those. This is almost always what they want — the alternative re-mines history already in the file. |
   | `complete` | **ASK. Do not proceed on your own initiative.** See below. |
   | `unknown` | A trace exists but predates lifecycle tracking. Treat as `complete` and ask the same question. |

3. **When an ingest is already complete, ask — with a recommendation, not a menu.**
   Present these three, in this order:

   - **`/roeh:refresh` (recommended, and say so).** Folds in new commits, unmined
     transcripts and changed memory files, *and* runs the drift check. This is the right
     answer nearly every time someone reaches for a second ingest — they want the record
     current, which is refresh's job, not ingest's.
   - **Extend the floor** — re-ingest an *earlier* range they previously excluded, e.g.
     `--since 2026-06-01` when the original floor was July. Genuinely additive; run it
     scoped to the new range only.
   - **Full re-ingest** — only when the record is known-bad or the repo's history was
     rewritten. Say plainly what this costs: the full fan-out again, and because the
     trace is append-only, **it cannot replace the old chapters — it appends beside
     them.** A duplicated history is worse than a thin one, because the oracle then has
     two accounts and no way to tell which is live. If they truly want a clean rebuild,
     the honest path is a new trace file and archiving the old one — say that rather
     than quietly doubling the record.

   Whatever they choose, if you do proceed over an existing trace: **dedupe against what
   is already there and append only what is net-new. Never rebuild the file in place.**

4. **Establish the floor with the owner.** Show them the commit history and ask how far
   back matters:
   ```
   git log --all --date=short --format='%ad %h %s' | tail -40
   ```
   Do not guess. In the project this tool came from, the owner's first instinct
   ("mid-July") was wrong on inspection and they moved it forward a week — the floor is
   a judgement about what they still care about, and only they hold it. Skip the ask
   only if `--since` was given.

## Phase 1 — survey before spending

Measure, then size the fan-out. Report these numbers before dispatching anything:

- commits in range, and their date distribution
- `memory/` files, if any (`~/.claude/projects/<slug>/memory/`) — count and total size
- `docs/`, `scripts/`, `evals/` or equivalent — what exists
- `roeh sessions` — transcripts, with sizes

## Phase 2 — declare the plan, then fan out

**Adaptive sizing.** Split the commit range into **dated chapters of roughly 20–40
commits or one week, whichever is denser**, capped at 8 chapter agents. Denser coverage
is higher fidelity, and fidelity is the entire point — but past ~8 the synthesis cost
exceeds the marginal recall. With `--quick`, skip the split and run one sequential pass.

**Slice by an explicit date window or SHA range — never by `git log --skip N … --reverse`.**
`--skip`/`--max-count` are applied in git's default *newest-first* traversal, *before*
`--reverse` reverses the output — so a `--skip`-based chapter silently selects the WRONG
window, and the fan-out reads complete while missing whole ranges (the exact failure this
phase guards against). Give each chapter an explicit `--since <date> --until <date>` window,
or a `<sha>..<sha>` range, computed from the plan, then **verify the union tiles the full
range with no gap and no overlap** before dispatching — one `git log … | wc -l` per chapter
against the total is enough.

**Register the plan before dispatching anything:**

```
roeh ingest begin --floor <date> --plan C1,C2,C3,M,A,S
```

This is what makes an interrupted run recoverable. Without it, a fan-out that dies at
chapter 4 of 7 leaves a trace that reads exactly like a finished one — same sections,
same voice, silently missing whole ranges of history. The Oracle would then answer *"not
recorded"* for decisions that **are** recorded, just never mined, and it would sound
exactly as confident as when it is right.

Mark each unit off **as its chapter is appended**, not when its agent returns:

```
roeh ingest done C1
```

Dispatch in parallel:

| Agent | Job | Model |
|---|---|---|
| **C1…Cn** | one dated chapter each — commits, diffs, and above all inline comments | `sonnet` |
| **M** | memory rehydration — every memory file read IN FULL, clustered, cross-linked, with a contradictions ledger | `sonnet` |
| **A** | artifact index — docs, scripts, evals, key modules: what each IS, why it exists, its gotchas | `sonnet` |
| **S** | session mining — the largest unmined transcripts (see below) | *inherit* |

### Why the models differ — do not "upgrade" this

**Extraction runs on `sonnet`.** C/M/A are bounded retrieval: read this range, quote
the rationale that is already written down, return it tagged and cited. The source text
does the reasoning; the agent transcribes and organises it. This is the split the
original archaeology used — six Sonnet agents produced the trace this tool generalises —
and paying frontier rates for transcription buys nothing while making a first ingest
expensive enough that people skip it.

**Session mining inherits the session model** (do not pin it down). It is the one pass
that requires real judgement: deciding what in a transcript is a *net-new* learning
against a trace you must hold in full, and applying the hall-of-mirrors rule to
material where the owner's turns and the assistant's are interleaved. Getting that
wrong writes the system's own reflection into the record as history.

If the caller's session is pinned to a small model, say so in the report — the session
mining will be weaker than the rest and the owner should know which pass to distrust.

### Every subagent prompt MUST carry these, verbatim in spirit

- **Read-only git ONLY** — `log`, `show`, `diff`, `blame`. **NEVER** `checkout`,
  `switch`, `reset`, `branch`, `stash`, `commit`, `restore`, or anything that moves HEAD
  or mutates the tree. *The working tree is shared.* This guardrail exists because an
  archaeology agent once moved HEAD out from under live work.
- **Mine the inline comments and docstrings, not just the diff or the subject line.**
  The commit message says *what*; the code comment says *why*. This is the single
  highest-yield instruction in the whole pass — quote the rationale with a `file:line`.

- **Read the comment AT THE COMMIT (`git show <sha>`), never at HEAD.** This matters more
  than it looks. **Comments go stale**: code changes, the comment above it does not, and
  a rationale that was true in March is quietly describing something that no longer
  exists. Reading at the commit that introduced the change is the mitigation — at that
  moment the author wrote the code and the comment together, so they are maximally in
  sync. A comment read at HEAD carries an unknown amount of drift; the same comment read
  at its own commit is a dated statement of intent.

  So cite comment-sourced claims as **`file:line@sha`** — the pointer *and* the commit it
  was true at. An entry that says "because Y (`walk.py:88@a1b2c3d`)" is making a claim
  about what was believed at `a1b2c3d`, which stays true forever, rather than a claim
  about what the code does now, which may not.

- **If the comment and the code it sits above already disagree at that commit, say so.**
  That is a `[GOTCHA]` worth recording, and it is a signal about how much the rest of
  this file's comments can be trusted.
- **Capture DECISIONS, DEAD-ENDS, REVERSALS, LESSONS — with rationale**, not a changelog.
  A restatement of what changed is worthless; the record already has the diff.
- **What was REJECTED and why** wherever the evidence shows an option was weighed.
- **Sovereignty** — if `local_only`, no web or network tools, nothing leaves the machine.
- **Emit v3 record-proposals, not prose.** Each proposal is the JSON `roeh record` accepts:
  `{tag, lead, why, rejected, gates, supersedes, augments, conflicts, cites, atomic, date}`.
  The `lead` is ONE atomic claim ≤90 chars (no `. ` inside); `why`/`rejected`/`gates` are its
  facets; `cites` carry `file:line@sha` / SHA provenance; `atomic:true` unless the entry
  genuinely bundles claims. Fields are single-line (no newlines, no `<!--`/`-->`).
- **TYPE the edges at write time, or leave them off — never guess.** Where the evidence shows
  this entry overturns an earlier one, name the target (its `date`+`tag`+`lead`, or its
  content-id via `roeh id`) in `supersedes`; a refinement/extension is `augments`; a symmetric
  tension is `conflicts`. If you cannot type an overturn with confidence, do NOT tag it
  `REVERSAL`/`CORRECTION` — `roeh record` refuses an edgeless overturn, and that is correct;
  record a plain `[DECISION]`/`[LESSON]` and note the uncertainty in `why`. Overturn-vs-refine
  is decided at write time and must fail loud, never be reconstructed later from stale prose.

### Session mining — the hall-of-mirrors rule is non-negotiable

Transcripts hold real-time rationale and abandoned roads that never reach a commit
message. They are the richest vein and the most dangerous one.

1. Transcripts are large (tens of MB). **Distil first, never read raw.** Strip tool
   inputs, tool results, file-history and meta events.
2. Then distil again, to **the owner's turns only**, each with a short snippet of what it
   responded to for context.
3. **Source rule — inherited from `agents/scribe.md`.** A FACT — a measurement, an
   invariant, what-is-true — comes only from the owner's turns, the commits, or the code:
   never from the assistant's own text (the hall-of-mirrors failure — the record feeds
   itself its own reflection and reads it back as fact), and never from text the owner
   *pasted* in, a review or an article, whoever pasted it (a lesson from the upstream project). A fact tracing
   only to an assistant or a pasted review: **drop it.** BUT one relaxation (owner decision,
   2026-08-25): a **process lesson** — a dead-end, a recurring regression, a principle
   earned in review — MAY cite co-produced in-session turns **as supporting evidence**,
   self-marked: `Cite: co-produced in-session (transcript <id>) — supporting evidence; not
   independently verified` (semicolon — a comma is the `Cites:` delimiter and `roeh record`
   refuses it). The tag marks it an observation, the citation marks its weight.
   That is the difference between keeping a hard-won lesson and losing it — never for a fact,
   never for pasted text.
4. `roeh mark <session-id>` for each transcript folded in, so `/roeh:refresh` stays
   incremental.

## Phase 3 — canonical-sequence, resolve edges, then `roeh record`

The agents return v3 record-proposals; you do NOT append them raw. Collect them all, then:

1. **Canonical sequence.** Sort every proposal chronologically by `date`, and within a date
   put edge TARGETS before the entries that reference them — `roeh record` enforces
   strictly-earlier by file order and refuses an edge whose target is not yet recorded. A
   `conflicts` edge is symmetric, so it needs that same target-first ordering but only from ONE
   side: attach it to whichever of the two entries records LATER (the earlier already exists by
   then), and never emit the same conflict from both sides.
2. **Resolve edges.** Every id is content-derived, so compute each proposal's id with
   `roeh id` and rewrite `supersedes`/`augments`/`conflicts` from named targets to ids. This
   is where a **cross-agent edge** — D in one chapter overturns B in another — is resolved:
   B's id is computable from its `date`+`tag`+`lead` without B being recorded yet.
   **Chain multi-step supersessions; never fan them.** When two or more entries supersede the
   SAME target (a decision refined, then later reversed), the reader flags "competing successors
   (unresolved)" and `roeh record` refuses — correctly, because a fan is ambiguous. Re-point
   them into a CHAIN in date order: the root superseded by the first successor, the first by the
   second, so each entry has exactly one superseder. (A genuine symmetric tension is not a fan —
   link it with `conflicts`.)
3. **Dedupe.** If two agents proposed the same entry (same `date`+`tag`+`lead`), keep the
   denser and drop the other — `roeh record` refuses the second as a duplicate anyway.
4. **Record serially.** `roeh record` each proposal in sequence. A refusal is a FINDING, not
   a silent skip: an edgeless overturn, a dangling target, an introduced UNCERTAIN — fix the
   proposal (type the edge, add the conflict link) or report it; never work around it.

**A v3 trace is a flat append-only log — NOT the legacy §0–§4 skeleton.** The derived *map*
(`roeh map`) is the structure now: it regenerates the ledger, the liveness, and the topic
regions from the log, so do not hand-scaffold a §1 principles digest (that lives in the
profile, Phase 4), a §2 memory digest, §3 chapters, or a §4 staleness ledger. Start the trace
from `${CLAUDE_PLUGIN_ROOT}/templates/decision-trace-v3.skeleton.md` — a short **§0 header**
(what this is + "read via `roeh map`") and a **§5 RESUME STATE**; `roeh record` appends the
**flat run of entries** after it, and a new §5 is appended when the resume state moves (readers
take the LAST §5). Append-only makes EOF the honest home for every entry; the map gives them
their shape. *(`roeh doctor` now requires only §0 + §5, so a flat v3 trace passes.)*

## Phase 4 — the profile

Write `profile_abs` from `${CLAUDE_PLUGIN_ROOT}/templates/profile.template.md`. This is
what makes the agents project-aware without editing them: the vocabulary an agent would
otherwise misread, the §1 digest, and above all the **LIVE dead-ends** table the oracle
leads with. Every row needs a citation into the trace.

## Phase 5 — close the ingest

```
roeh ingest end
```

This refuses to close while units remain unfinished — deliberately. If some genuinely
cannot be completed (a range with no recoverable history, an agent that failed twice),
close with `--force` and it is recorded as `partial-closed`, which `roeh doctor` then
reports as a failure until it is resolved. **Never leave a run neither closed nor
finished:** after six hours it reads as `abandoned`, and a half-built record that nobody
knows is half-built is the exact failure this whole tool exists to prevent.

## Phase 6 — report

Size and line count, chapters written, what each agent found that nothing else had, and
**anything you could not source**. Then state plainly what the record still does not
cover — the gaps are the most useful thing you can hand back, because they are what the
owner can still fill from memory while they have it.
