# DECISION TRACE — {{PROJECT}}

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
ignorance, it is **confident re-derivation** of something already settled, often
reaching the opposite conclusion with no memory of the first one.

Memory indexes compact. Summaries summarise summaries. This file is the durable layer
*beneath* that: append-only, un-compacted, and cited. When something here disagrees with
a fresh re-derivation, this file is the record and the re-derivation is a hypothesis.

**How to extend it:** never rewrite. Append a dated entry under §3 with a tag, the why,
what was rejected, citations, and what it gates. Update §5 when the resume state moves.

---

## §1 — Standing principles

*The commitments that must survive every compaction. Each carries its `[PRINCIPLE]` tag
and, crucially, its **why** — a principle without its reasoning gets re-litigated.*

<!-- [PRINCIPLE] <name> — <the commitment>. WHY: <the reasoning>. Origin: <cite> -->

---

## §2 — Rehydration & the staleness ledger

*Sources outside this file — memory files, specs, prior art — distilled with their
substance intact rather than re-summarised into pointers. Cross-linked.*

### Contradictions & staleness ledger

*Where the record disagrees with itself, or with the code. The oracle reads this in full
every time, at any trace size. An unrecorded contradiction is worse than a gap: the
reader cannot tell which claim is live.*

| Claim | Conflicts with | Status |
|---|---|---|

---

## §3 — Chronological decision trace

*Dated chapters, newest appended at the bottom. Tags: `[DECISION]` `[DEAD-END]`
`[REVERSAL]` `[LESSON]` `[GOTCHA]` `[EVAL]` `[OPEN]` `[GATE]` `[CORRECTION]`.*

*Dead-ends and reversals are the most valuable entries here. A merge records what we do;
a withdrawal records what we already tried and why it failed — which is exactly what a
future session would otherwise pay to rediscover.*

---

## §4 — Artifact & script index

*What each load-bearing doc, script, eval and module IS, WHY it exists, and its gotchas —
so a future session never has to rediscover them.*

---

## §5 — Resume state

*What the next session must know. This is what a post-compaction context reads first, so
a stale §5 is worse than none — it is trusted.*

- **Where we are:**
- **Currently gated on:**
- **Next:**
- **Do not re-derive:**
