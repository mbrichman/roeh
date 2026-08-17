---
description: Build this project's decision trace from history — fan out reader agents over git commits (mining inline comments), memory files, docs/scripts, and Claude Code session transcripts, then assemble the record and generate the profile. Run once after /roeh:init.
disable-model-invocation: true
---

# /roeh:ingest

Archaeology. You are reconstructing **why** this project is the way it is, from the
evidence that survives, and writing it into an append-only record.

Accepts `--quick` (single-pass, cheap), `--since <date>` (history floor), and
`--deep` (force maximum fan-out).

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
- **Capture DECISIONS, DEAD-ENDS, REVERSALS, LESSONS — with rationale**, not a changelog.
  A restatement of what changed is worthless; the record already has the diff.
- **What was REJECTED and why** wherever the evidence shows an option was weighed.
- **Sovereignty** — if `local_only`, no web or network tools, nothing leaves the machine.
- **Return structured entries**, not prose. Tagged, dated, cited.

### Session mining — the hall-of-mirrors rule is non-negotiable

Transcripts hold real-time rationale and abandoned roads that never reach a commit
message. They are the richest vein and the most dangerous one.

1. Transcripts are large (tens of MB). **Distil first, never read raw.** Strip tool
   inputs, tool results, file-history and meta events.
2. Then distil again, to **the owner's turns only**, each with a short snippet of what it
   responded to for context.
3. **The assistant's own text is NOT a source.** It is the system's own emission; filing
   it as history is the hall-of-mirrors failure — the record feeds itself its own
   reflection, and every future session reads it back as fact. Legitimate sources are
   the owner's turns and the code. If a candidate learning traces only to something an
   assistant said, **drop it**.
4. `roeh mark <session-id>` for each transcript folded in, so `/roeh:refresh` stays
   incremental.

## Phase 3 — assemble by appending

As each agent lands, place its chapter in **chronological position** and append. Rules:

- **Never rewrite an existing entry.** If two agents cover the same commits, take the
  denser one and say so — do not emit both.
- Decode any HTML entities the agents return.
- Cross-check: if an agent's finding contradicts an entry already in the file, that goes
  in the **staleness ledger**, not silently into the prose.
- Fill §1 from what the chapters actually establish. A principle is only load-bearing if
  you can cite where it was learned — **do not seed §1 with plausible-sounding
  engineering virtues.**
- Fill §5 last: where the project stands, what is gated, what must not be re-derived.

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
