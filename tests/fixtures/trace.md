# DECISION TRACE — fixture

> **APPEND-ONLY.** A superseded decision gets a new `[REVERSAL]` beside it.

## §0 — Why this file exists

A model in a context window forgets the expensive thing and keeps the cheap one, so the
failure mode is confident re-derivation. This file is the durable layer beneath that.

## §1 — Standing principles

- **[PRINCIPLE] source-is-truth** — a derived value is a regenerable view; the source is
  the asset. WHY: a pipeline that treats its own output as input compounds its errors.
  Origin: `aaa1111`.

## §2 — Rehydration & the staleness ledger

### Contradictions & staleness ledger

| Claim | Conflicts with | Status |
|---|---|---|
| batch size 512 (§3 `ccc3333`) | §3 `[CORRECTION]` below | superseded |

## §3 — Chronological decision trace

### 2026-01-10

- **[DECISION]** Chose SQLite over Postgres for the local index. WHY: single-file
  backup matters more than concurrent writes here. REJECTED: Postgres — operationally
  heavier for one user. Cite: `aaa1111`.
- **[DEAD-END]** Tried resolving identity by name-cosine similarity. It scores every
  pair 0.90+ in a single-topic corpus because it measures subject matter, not identity.
  **Do not re-walk this.** Cite: `bbb2222`.

### 2026-02-02

- **[EVAL]** Measured batch size 512 as optimal. Cite: `ccc3333`.
- **[CORRECTION — to `ccc3333`]** 512 was measured on the old tokenizer. The current
  figure is **128**. Cite: `ddd4444`.

## §4 — Artifact & script index

- `index.py` — builds the local index. Gotcha: assumes the tokenizer in `tok.py`.

## §5 — Resume state

- **Where we are:** index rebuilt on the new tokenizer.
- **Currently gated on:** nothing.
- **Do not re-derive:** the name-cosine identity dead-end (§3 `bbb2222`).
