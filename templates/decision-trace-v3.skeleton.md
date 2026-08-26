# DECISION TRACE (v3) — {{PROJECT}}

> **APPEND-ONLY.** Every entry is added at the end by `roeh record` and never edited or
> deleted — content-id'd, chained, with typed edges. A superseded decision gets a new
> entry with a `Supersedes:` edge; a wrong number a new `[CORRECTION]`. The history of
> what we believed and when is part of the record, not noise in it.
>
> Written by `roeh record` (the ingest, then the `scribe`). **Read via `roeh map`** — do
> not read the raw log top to bottom. Consult the oracle *before* re-deriving any
> architecture, eval, model choice or design decision.

---

## §0 — Why this file exists

A model that lives in a context window does not forget randomly. It forgets the
expensive, hard-won thing and keeps the cheap recent thing — so the failure mode is not
ignorance, it is **confident re-derivation** of something already settled, often reaching
the opposite conclusion with no memory of the first one.

Memory indexes compact. Summaries summarise summaries. This file is the durable layer
*beneath* that: append-only, un-compacted, cited. When something here disagrees with a
fresh re-derivation, this file is the record and the re-derivation is a hypothesis.

**Structure is derived, not hand-filled.** This is a flat append-only log of entries. The
`roeh map` projection is the structure — it regenerates liveness, the supersession ledger,
and topic regions from the log at read time. The **profile** holds the standing-principles
digest and the LIVE dead-ends the oracle leads with. There are no §1–§4 sections to
maintain: they were the legacy layout, and the map/profile replace them.

**How to extend it:** never rewrite. `roeh record` appends one typed entry at the end (id,
chain, `Supersedes:`/`Augments:`/`Conflicts:`/`Cites:`). Append a new §5 when the resume
state moves — the readers take the LAST §5.

<!-- ── entries below, appended by `roeh record` ── -->

---

## §5 — Resume state

*What the next session must know. This is what a post-compaction context reads first, so a
stale §5 is worse than none — it is trusted. A new §5 is appended (never edited); the last
one wins.*

- **Where we are:**
- **Currently gated on:**
- **Next:**
- **Do not re-derive:**
