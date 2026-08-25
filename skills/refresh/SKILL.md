---
description: Reconcile the decision trace against reality — fold in new commits, unmined session transcripts and changed memory files, and draft [CORRECTION]/[REVERSAL] entries where the record and the code now disagree. Run when /roeh:status says the record is behind.
disable-model-invocation: true
---

# /roeh:refresh

Incremental ingest **plus** reconciliation. Ingest asks *"what happened?"*; refresh also
asks *"is what we wrote down still true?"* — which is the harder and more valuable half.

A stale record is more dangerous than no record, because an answer sourced from it reads
exactly like an answer sourced from a current one. That asymmetry is why this exists.

**You never write the trace yourself.** refresh runs two passes — CAPTURE (Phase 1) and
RECONCILE (Phase 2) — but it is not an author: **the scribe is the sole author, and every
trace write goes through it (Phase 3), including the §5 update (Phase 5).** The only file
refresh writes directly is the profile (`profile_abs`, Phase 4), which is not the trace.
Appending to the trace yourself — even §5 — is the wrong turn: it puts a second writer on
an append-only file whose integrity depends on having exactly one. If a phase below tells
you to "write" or "update" the trace, that means *hand it to the scribe*.

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

## Phase 1 — CAPTURE: fold in what's new

Same rules as `/roeh:ingest`, scoped to the delta. **Dispatch commit and memory mining
on `sonnet`** — it is bounded extraction, same as ingest. Session mining inherits.

- **Commits** — mine inline comments and docstrings for rationale, not the subject lines.
- **Transcripts** — distil to the owner's turns only; the assistant's own text is never a
  source (hall of mirrors). `roeh mark <id>` each one you fold in.
- **Memory files** — fold changes into §2 and note any that now contradict §2's existing
  digest.

**Dedupe against the whole trace before writing anything.** If it is already recorded,
the correct output is *"already recorded at <cite>"*.

## Phase 2 — RECONCILE: the drift check (the part that is not ingest)

This is reconciliation proper. Work through the trace's own citations:

1. **Do the `file:line` pointers still resolve?** `Read` a sample across chapters —
   weighted toward the entries the profile lists as LIVE, since those are the ones the
   oracle leads with. A pointer into code that has moved or been deleted is a finding.

2. **Comment-sourced entries first — they decay fastest.** Any entry citing
   `file:line@sha` took its rationale from an inline comment. **Comments go stale:**
   humans routinely change code without touching the comment above it, so the rationale
   the record captured may now describe something that no longer exists. Check each one
   against HEAD and sort the result into three, because they mean different things:

   - **Comment and code both unchanged** — the entry is live. Nothing to do.
   - **Code changed, comment did not** — the *comment* is now stale, but the entry may
     not be. It recorded what was believed at `<sha>`, and that stays true. What is
     missing is the later decision that changed the code. Write a `[REVERSAL]` for the
     change nobody recorded, and note the stale comment as a `[GOTCHA]` so the next
     reader does not trust it. **This is the case that matters most** — a divergence
     between a comment and the code beneath it is usually an unrecorded decision, which
     is exactly what this tool exists to catch.
   - **Comment removed or rewritten** — someone deliberately revised the rationale.
     Read the new one and record a `[CORRECTION]` if it contradicts the entry.

   Never silently "update" an entry to match a new comment. The record shows what was
   believed and when; a comment that changed is a second data point, not a replacement
   for the first.

3. **Do the recorded claims still hold?** Where an entry states an invariant, a schema
   shape, a threshold or a measurement, check it against the current code. A recorded
   number that reality has moved past is the highest-value `[CORRECTION]` you can write.
4. **Has anything recorded been silently reversed by later work?** A decision implemented
   one way and quietly rebuilt another way leaves the original entry reading as live.
   That needs a `[REVERSAL]` naming the entry it overturns.
5. **Does the staleness ledger still describe reality?** Resolved contradictions should
   be marked resolved — with a cite — not deleted.

## Phase 3 — write (through the scribe, always)

**Dispatch the scribe with everything to be recorded** — the Phase 1 capture entries and
the Phase 2 reconcile findings alike. refresh does not append; it hands the scribe the
findings and the scribe authors and appends them. Each reconcile finding becomes a NEW
entry:

- `[CORRECTION — to <entry>]` for a wrong number or claim
- `[REVERSAL — of <entry>]` for a decision that later work overturned
- `[GOTCHA]` for a citation that no longer resolves

**Never edit the original entry.** The record shows what was believed and when; that
history is the point, not noise to tidy away. The scribe appends via `roeh append`, which
cannot rewrite — and is the *only* writer, which is why the routing above is not optional.

## Phase 4 — refresh the profile

Update `profile_abs`: new vocabulary, new LIVE dead-ends, and — importantly — **remove
rows that are no longer live**, citing what retired them. A dead-end that has itself been
reversed but still sits in the profile makes the oracle warn people off the right answer.

## Phase 5 — update §5 and report

§5 RESUME STATE is what a post-compaction session reads first. **Have the scribe append
the updated §5** as part of Phase 3 — a new §5 block supersedes the old, never an in-place
edit — then report: what was folded in, what drifted, what you corrected, and **what you
could not verify**. An honest "I could not check these twelve citations" is a correct
result; a silent partial pass is how a record starts lying with confidence.
