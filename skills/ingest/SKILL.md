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
2. If the trace already has §3 chapters, this is a re-run: everything below must
   **dedupe against what is already there and append only what is net-new**. Never
   rebuild the file.
3. **Establish the floor with the owner.** Show them the commit history and ask how far
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

## Phase 2 — fan out

**Adaptive sizing.** Split the commit range into **dated chapters of roughly 20–40
commits or one week, whichever is denser**, capped at 8 chapter agents. Denser coverage
is higher fidelity, and fidelity is the entire point — but past ~8 the synthesis cost
exceeds the marginal recall. With `--quick`, skip the split and run one sequential pass.

Dispatch in parallel:

| Agent | Job |
|---|---|
| **C1…Cn** | one dated chapter each — commits, diffs, and above all inline comments |
| **M** | memory rehydration — every memory file read IN FULL, clustered, cross-linked, with a contradictions ledger |
| **A** | artifact index — docs, scripts, evals, key modules: what each IS, why it exists, its gotchas |
| **S** | session mining — the largest unmined transcripts (see below) |

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

## Phase 5 — report

Size and line count, chapters written, what each agent found that nothing else had, and
**anything you could not source**. Then state plainly what the record still does not
cover — the gaps are the most useful thing you can hand back, because they are what the
owner can still fill from memory while they have it.
