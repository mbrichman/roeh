---
description: Reconcile the decision trace against reality — fold in new commits, unmined session transcripts and changed memory files, and draft [CORRECTION]/[REVERSAL] entries where the record and the code now disagree. Run when /roeh:status says the record is behind.
disable-model-invocation: true
---

# /roeh:refresh

Incremental ingest **plus** reconciliation. Ingest asks *"what happened?"*; refresh also
asks *"is what we wrote down still true?"* — which is the harder and more valuable half.

A stale record is more dangerous than no record, because an answer sourced from it reads
exactly like an answer sourced from a current one. That asymmetry is why this exists.

**Model policy:** the delta mining in Phase 1 is extraction and runs on `sonnet`. **The
drift check in Phase 2 does NOT** — run it inline, or on the session model. Deciding
whether a recorded claim is *still true* is judgement against evidence, not retrieval,
and it is the pass whose silent failure mode is the worst available: reporting a record
as verified when it was only skimmed.

## Phase 0 — what is behind

```
roeh status --json
```

Gives you unrecorded commits, unmined transcripts, and memory files changed since the
trace was last written. If nothing is behind, run the drift check (Phase 2) anyway —
**the record can rot without anything new happening**, because the code moves under
citations that still look valid.

## Phase 1 — fold in what's new

Same rules as `/roeh:ingest`, scoped to the delta. **Dispatch commit and memory mining
on `sonnet`** — it is bounded extraction, same as ingest. Session mining inherits.

- **Commits** — mine inline comments and docstrings for rationale, not the subject lines.
- **Transcripts** — distil to the owner's turns only; the assistant's own text is never a
  source (hall of mirrors). `roeh mark <id>` each one you fold in.
- **Memory files** — fold changes into §2 and note any that now contradict §2's existing
  digest.

**Dedupe against the whole trace before writing anything.** If it is already recorded,
the correct output is *"already recorded at <cite>"*.

## Phase 2 — the drift check (the part that is not ingest)

This is reconciliation proper. Work through the trace's own citations:

1. **Do the `file:line` pointers still resolve?** `Read` a sample across chapters —
   weighted toward the entries the profile lists as LIVE, since those are the ones the
   oracle leads with. A pointer into code that has moved or been deleted is a finding.
2. **Do the recorded claims still hold?** Where an entry states an invariant, a schema
   shape, a threshold or a measurement, check it against the current code. A recorded
   number that reality has moved past is the highest-value `[CORRECTION]` you can write.
3. **Has anything recorded been silently reversed by later work?** A decision implemented
   one way and quietly rebuilt another way leaves the original entry reading as live.
   That needs a `[REVERSAL]` naming the entry it overturns.
4. **Does the staleness ledger still describe reality?** Resolved contradictions should
   be marked resolved — with a cite — not deleted.

## Phase 3 — write

Dispatch the **scribe** with the findings. Every drift finding becomes a NEW entry:

- `[CORRECTION — to <entry>]` for a wrong number or claim
- `[REVERSAL — of <entry>]` for a decision that later work overturned
- `[GOTCHA]` for a citation that no longer resolves

**Never edit the original entry.** The record shows what was believed and when; that
history is the point, not noise to tidy away. The scribe appends via `roeh append`, which
cannot rewrite.

## Phase 4 — refresh the profile

Update `profile_abs`: new vocabulary, new LIVE dead-ends, and — importantly — **remove
rows that are no longer live**, citing what retired them. A dead-end that has itself been
reversed but still sits in the profile makes the oracle warn people off the right answer.

## Phase 5 — update §5 and report

§5 RESUME STATE is what a post-compaction session reads first. Update it, then report:
what was folded in, what drifted, what you corrected, and **what you could not verify**.
An honest "I could not check these twelve citations" is a correct result; a silent
partial pass is how a record starts lying with confidence.
