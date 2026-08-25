# DECISION TRACE — fixture (v3 read-path)

*Hand-built fixture for the read-path build. Hybrid entry format: relations + cites visible in
prose; id/chain/class/atomic/date/topic-hint in a trailing `<!-- roeh … -->` comment. Both tag
dialects appear on purpose. Ids are hand-assigned (e01…); real ids are content hashes.*

## §0 — why
Fixture, not a real record.

## §1 — principles
- **[PRINCIPLE] Append-only is structural.** Never edited.
  <!-- roeh id=p01 chain=cp01 class=principle atomic=true date=2026-01-01 topic-hint=core -->

## §3 — trace

### 2026-08-10 — hooks & the supersession chains
- **[DECISION] PreCompact blocks manual compaction, never auto.** WHY: auto fires when the window is full.
  Cites: hooks/precompact.py, b8de529
  <!-- roeh id=e01 chain=c01 class=decision atomic=true date=2026-08-10 topic-hint=hooks -->
- **[DECISION] Ingest splits commits into fixed 20-commit chapters.** WHY: bounded fan-out.
  Cites: ingest/plan.py
  <!-- roeh id=e02 chain=c02 class=decision atomic=true date=2026-08-10 topic-hint=ingest -->
- `[CORRECTION]` Chapters are 20–40 commits or one week, whichever is denser. WHY: density is fidelity.
  Supersedes: e02
  Cites: ingest/plan.py
  <!-- roeh id=e03 chain=c03 class=correction atomic=true date=2026-08-11 topic-hint=ingest -->
- **[REVERSAL] Chapters cap at 8; past that synthesis cost exceeds recall.** WHY: measured. The live rule: ≤8 chapters, 20–40 commits each.
  Supersedes: e03
  Cites: ingest/plan.py
  <!-- roeh id=e04 chain=c04 class=reversal atomic=true date=2026-08-12 topic-hint=ingest -->

### 2024-03-01 — retrieval (old, stable → settled candidate)
- `[DECISION]` The oracle reads the index in full at any trace size. WHY: global awareness.
  Cites: retrieval/oracle.py
  <!-- roeh id=e05 chain=c05 class=decision atomic=true date=2024-03-01 topic-hint=retrieval -->
- **[DECISION] The index lists one line per entry.** WHY: compact map.
  Augments: e05
  Cites: retrieval/index.py
  <!-- roeh id=e06 chain=c06 class=decision atomic=true date=2024-03-02 topic-hint=retrieval -->
- **[CORRECTION] The index also carries a supersessions block up front.** WHY: check liveness first. Still augments the oracle-reads-in-full decision.
  Supersedes: e06
  Augments: e05
  Cites: retrieval/index.py
  <!-- roeh id=e07 chain=c07 class=correction atomic=true date=2024-03-03 topic-hint=retrieval -->

### 2026-08-13 — conflicts, dead-ends, and uncertain cases
- **[DECISION] Store the trace in repo mode by default.** WHY: git makes append-only provable.
  Cites: config.py
  <!-- roeh id=e08 chain=c08 class=decision atomic=true date=2026-08-13 topic-hint=config -->
- `[DECISION]` Store the trace in local mode by default. WHY: rationale is sensitive.
  Conflicts: e08
  Cites: config.py
  <!-- roeh id=e09 chain=c09 class=decision atomic=true date=2026-08-13 topic-hint=config -->
- **[DEAD-END] Do not build a `roeh update` command.** WHY: the harness owns updates.
  Cites: 20914b6
  <!-- roeh id=e10 chain=c10 class=dead-end atomic=true date=2026-08-13 topic-hint=cli -->
- **[REVERSAL] We stopped mining comments at HEAD.** WHY: they drift. (No machine edge on purpose — prose-only.)
  Cites: 391d34c
  <!-- roeh id=e11 chain=c11 class=reversal atomic=true date=2026-08-13 topic-hint=ingest -->
- **[DECISION] The scribe writes and the doctor repairs and the index regenerates.** WHY: one entry, three claims — non-atomic on purpose.
  Cites: scribe.py, doctor.py
  <!-- roeh id=e12 chain=c12 class=decision atomic=false date=2026-08-14 topic-hint=core -->
- `[CORRECTION]` The scribe writes via append only. WHY: narrower than the bundled claim above.
  Supersedes: e12
  Cites: scribe.py
  <!-- roeh id=e13 chain=c13 class=correction atomic=true date=2026-08-15 topic-hint=core -->

### 2026-08-16 — competing successors & a dangling edge
- **[DECISION] Model split: extraction on sonnet.** WHY: bounded transcription.
  Cites: models.py
  <!-- roeh id=e14 chain=c14 class=decision atomic=true date=2026-08-16 topic-hint=models -->
- **[CORRECTION] Extraction runs on the cheap tier.** WHY: cost.
  Supersedes: e14
  Cites: models.py
  <!-- roeh id=e15 chain=c15 class=correction atomic=true date=2026-08-16 topic-hint=models -->
- `[REVERSAL]` Extraction runs on the mid tier. WHY: quality. (No conflicts-with e15 — competing.)
  Supersedes: e14
  Cites: models.py
  <!-- roeh id=e16 chain=c16 class=reversal atomic=true date=2026-08-16 topic-hint=models -->
- **[CORRECTION] Revert the tokenizer change.** WHY: regressions. (Target absent — dangling.)
  Supersedes: e99
  Cites: retrieval/token.py
  <!-- roeh id=e17 chain=c17 class=correction atomic=true date=2026-08-16 topic-hint=retrieval -->
- **[DECISION] Bloom filters index literal tokens like quokka_flag per region.** WHY: no-false-negative literal recall.
  Cites: retrieval/bloom.py
  <!-- roeh id=e18 chain=c18 class=decision atomic=true date=2026-08-16 topic-hint=retrieval -->

### 2024-01-01 — a fully retired topic
- **[DECISION] Use the deprecated preflight daemon.** WHY: at the time.
  Cites: deprecated/preflight.py
  <!-- roeh id=e19 chain=c19 class=decision atomic=true date=2024-01-01 topic-hint=deprecated -->
- **[WITHDRAWN] The deprecated preflight daemon is removed.** WHY: replaced wholesale.
  Supersedes: e19
  Cites: deprecated/preflight.py
  <!-- roeh id=e20 chain=c20 class=withdrawn atomic=true date=2024-02-01 topic-hint=deprecated -->

## §5 — Resume state
- first §5 block (oldest).

## §5 — Resume state
- second §5 block.

## §5 — Resume state
- third §5 block.

## §5 — Resume state
- fourth §5 block.

## §5 — Resume state
- fifth §5 block (newest — last-wins must pick THIS).
