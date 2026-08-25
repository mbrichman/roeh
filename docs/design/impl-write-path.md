# Implementation spec (v2) — the write path (producer side of RFC v3)

> **Authority split.** The *reader* (`bin/roeh_map.py`) defines the persisted schema and how it is
> interpreted. The *writer* enforces a **stronger validity contract at creation**: it refuses inputs
> the reader would merely tolerate. So this is not "the writer implements the reader" — the reader
> asks *"can I interpret this?"*, the writer asks *"will I allow this into the authority?"*. Every
> reader-derived rule below cites its function; every writer-only invariant is marked **[producer]**.
> Companion: `impl-read-path.md` §5. v2 folds an external review (P0 id/serialization/atomic-append;
> P1 class/topic-hint/inheritance; the atomic collision).

## 0. What the write path is
Two producers, both through the one write path (the scribe is sole author):
- **`ingest` / clean re-ingest** — bootstrap capture; emits a whole v3 trace with typed edges
  *natively at write time* (clean-start decision, trace L527).
- **the scribe** — incremental capture/reconcile, one entry at a time.

Both must produce entries that (a) parse, (b) resolve edges without spurious `UNCERTAIN`, (c)
chain-verify. Append-only: entries are only ever added at EOF; nothing rewrites.

## 1. Mechanical facts vs epistemic assertions
Every entry carries two kinds of claim, and the writer treats them differently:
- **Mechanical** (deterministically checkable ⇒ *refused* on failure, never emitted): syntax parses;
  `id` unique; edge targets exist and are strictly-earlier; `chain` correct; competing successors
  conflict-linked; augments restated across supersession.
- **Epistemic** (only the producer can assert; later testable, never mechanically "true"): *this
  overturns X* (`supersedes`) vs *refines X* (`augments`); *these conflict*; *this is one claim*
  (`atomic`). The writer records these as producer assertions and the reader surfaces them; neither
  fabricates nor silently trusts. This is roeh's "don't convert model judgment into authority" line,
  drawn at the write boundary.

## 2. The entry format — pinned by the reader
Hybrid split (confirmed, keep): relations + cites **visible in prose**; bookkeeping in a trailing
machine comment.

```
- **[TAG] <lead: one atomic claim, ≤90 chars>.** WHY: … REJECTED: … GATES: …
  Supersedes: <id>[, <id>…]
  Augments: <id>[, <id>…]
  Conflicts: <id>[, <id>…]
  Cites: <file:line[@sha]>[, <sha>…]
  <!-- roeh id=<id16hex> atomic=<true|false> date=<YYYY-MM-DD> chain=<16hex> topic-hint=<a, b> -->
```

| Element | Reader rule (cite) | MUST |
|---|---|---|
| Head | `_ENTRY` L31 | `- **[TAG]`; `TAG` = `[A-Z][A-Z0-9-]{1,18}`. Emit the **bold** dialect. |
| Lead | `_lead` L108 | first sentence, ≤90 chars, ends before first `". "`. The atomic claim. |
| Relations | `_FIELD` L35 | visible `Supersedes:`/`Augments:`/`Conflicts:`/`Cites:` lines, comma-separated, un-fenced. |
| Comment | `_META`/`_META_KV` L34/96 | `<!-- roeh k=v … -->`, keys **`id`, `atomic`, `date`, `chain`, `topic-hint`**. |

**`class` is DROPPED** (was redundant with the tag). Terminal-ness derives from the tag alone.
*Reader change:* remove the `or e.cls in ("dead-end","withdrawn")` clause (`compute_liveness` L254);
the writer never emits `class`.

## 3. Write-time computations
### 3.1 `id` — 64-bit, canonical, immutable **[producer]**
`id = sha256( NFC(date) · "\0" · TAG · "\0" · NFC(collapse_ws(lead)) )[:16]` — **16 hex = 64 bits**
(32 bits birthday-collides at ~65k entries; too small for a permanent foreign key). Tag included so
`[DECISION] Use X` and `[LESSON] Use X` on one day differ. Canonicalize before hashing (NFC + collapse
runs of whitespace) so two implementations agree.

- **An id's textual representation is immutable once written.** Never lengthen or re-derive it — edges
  and the chain are permanent foreign keys to it.
- **Collision path (before emission):** compute candidate → scan existing ids. If it exists and the
  canonical `(date,tag,lead)` is identical ⇒ this is a **duplicate; refuse the write**. If it exists
  but content differs (astronomically rare at 64 bits) ⇒ append a deterministic disambiguator to the
  canonical input and recompute. Write exactly one final id; never mutate it after.

### 3.2 `chain` — tamper-evidence over id order (pinned)
`_expected_chains` L893: `chain_i = sha256(chain_{i-1} · "\0" · id_i)[:16]`, seeded `""`, in file
order; hashes **ids only**. To append, read the last entry's `chain`, compute the next.
- The log is **one append-only file, sole authority — no sharding** (RFC v2, L44: sharding was removed
  as a net-negative). So "file order" *is* the logical sequence, by decision — not an incidental
  coupling. If sharding were ever revisited (it is closed), the chain would need an explicit logical
  sequence; we do not build that now.
- Tamper-*evident*, not tamper-*proof*: an editor who recomputes end-to-end defeats it; true evidence
  needs an external signed head (`verify_chain` L901 caveat; out of scope, P2). Legacy entries with no
  `chain` are skipped, not failed.

### 3.3 `atomic` — a producer assertion, trusted **[producer]**
`atomic=true` asserts one claim. The reader keeps only the **sound** check: a *superseded* entry with
`atomic≠true` ⇒ `UNCERTAIN` (whole-entry supersession may kill a co-located claim, `compute_liveness`
L270). **The ≥2-clause-marker heuristic (L273–275) is REMOVED** — it flagged every well-formed
five-part entry (WHY:+REJECTED:+GATES: = 3 markers), turning `UNCERTAIN` into noise; and second-
guessing a valid producer assertion with a bad proxy violates §1. *Reader change + a regression test:
a superseded five-part `atomic=true` entry is NOT flagged.* (A real multi-claim signal — an explicit
claim-unit — is a P2 future, not a marker count.)

### 3.4 `topic-hint` — an organizational hint, never authority **[invariant]**
Persisted, optional, author-supplied; folded into region membership (`assign_regions` L318–322).
**Hard invariant:** a topic-hint MAY influence region *organization* but MUST NOT affect **coverage,
completeness, or scope-soundness**, and the reader MUST remain correct if it ignores it entirely
(the coverage guarantee — every entry in live ∨ ledger ∨ region-header — already ensures this). The
authoritative home for *semantic* topic assignment is the **derived side-map** (regenerable, not in
the log), never a persisted field. A model-authored hint therefore can mis-organize but can never
hide an entry.

## 4. The write transaction — serialized and atomic **[producer]**
"The scribe is sole author" is a *role*, not a concurrency primitive. `roeh record` MUST be a
two-phase transaction; a lightweight file lock + fsync, not a transaction manager:

```
PREPARE (no file mutation)
  canonicalize (date, tag, lead)         # 3.1
  resolve + validate edges               # exist, strictly-earlier (3.5), conflict/augment rules
  allocate id (collision path)           # 3.1
  serialize the complete record string

COMMIT
  flock(trace)                           # exclusive
    re-read tail; recompute prev_chain
    if tail moved since PREPARE → recompute id-independent chain (id is content-derived, unaffected)
    append EXACTLY ONE complete record (single write of the whole entry)
    fsync
  unlock
```

- **Serialization** closes the chain race: two writers reading the same tail would both chain off the
  same `prev`, and the second's `chain` would lie. The lock makes read-tail→append atomic.
- **Record atomicity:** a successful append adds exactly one complete record; a failed/crashed one
  adds **zero** bytes (build the full string, one `write`, then fsync). Process-kill is covered by
  the single-write+fsync; a next-open truncate-partial-tail recovery for **power-loss torn writes** is
  deferred (P2 — hard to do safely on a mixed legacy/v3 trace). `roeh append` takes the **same** lock
  and fsync, or an unlocked append between record's read-tail and its write would break record's chain.

### 4.2 Input validation & injection defense (as built; two review passes)
The entry's fields come from **untrusted JSON**, and are interpolated into the sole authoritative log.
- **Type gate:** the body must be a JSON object; `tag`/`lead`/`why`/`rejected`/`gates`/`date` must be
  strings — else a clean refusal, never a traceback.
- **Sanitize:** reject `<!--`, `-->`, or a newline in any field (a newline injects a fake edge line /
  entry head / heading; a comment forges the machine identity, because the reader binds the **first**
  `<!-- roeh -->` in a block). `topic-hint` items additionally reject `,` and `=` (it is the one list
  that lands *in* the comment, where ` word=` would forge a meta key). `date` is `YYYY-MM-DD` and a
  real calendar date; `lead` ≤90 chars.
- **Round-trip backstop:** after formatting, the entry MUST `parse_entries` back to exactly one entry
  carrying the intended `id`/`tag`/`date`/`atomic`/`chain`/edges/**cites**/**topic-hint**, or it is
  refused. This catches anything the blacklist missed — the writer verifies what it wrote is what the
  reader will read.

### 3.5 / 4.1 Edge rules the writer MUST honour (pinned, `compute_liveness` L232–282)
- Targets resolve (no dangling) and are **strictly earlier** for `supersedes`/`augments`; `conflicts`
  is symmetric, order-exempt.
- A `REVERSAL`/`CORRECTION` with no typed edge ⇒ `prose-only supersession` — so overturns MUST carry a
  typed edge (write-time typing is mandatory here).
- **Competing successors** (≥2 superseding one target) MUST be `conflicts`-linked, else each unlinked
  one is flagged. **[ontology, stated]** roeh models **one live successor unless successors are
  conflict-linked**; context-scoped supersession (A supersedes X in C1, B in C2) is *not* modeled —
  if it arises, use a conflict link. (Scope/context modeling is deferred as premature.)
- **No edge inheritance [invariant].** A live entry carries its **full attachment set**. When B
  augments A and B is superseded, B's superseder MUST restate `augments A`, or A is flagged
  `augment lost` (L278–282). Edges never inherit across a supersession — every live proposition owns
  its complete set of edges.
- **Enforcement = diff liveness across the append.** `record` computes liveness before/after and
  **refuses** any record that introduces a new UNCERTAIN it can fix — competing successor (add a
  conflict link), augment-lost (restate), dangling/prose-only (fix the edge). The **one exception is
  "non-atomic entry superseded"**: that is the *target's* missing `atomic` stamp, not a fault the new
  record can fix (it cannot retro-stamp a legacy/`append`-authored entry), so it **warns and allows** —
  otherwise `record` could never supersede any pre-v3 entry (review #1).

## 5. Fail-loud typing (the L511 rule)
The overturn-vs-refine call is semantic and made at write time. When the producer genuinely cannot
type an overturn, it MUST NOT fabricate an edge: **leave it prose-only** (⇒ reader `UNCERTAIN`, loud)
and **state the uncertainty reason in the visible WHY** (ambiguous / conflicting / insufficient
evidence). No new machine field for this now — the prose carries it; a machine-readable
`typing-status` is P2. (Native typing beats backfill: ~97.5% auto-typable vs ~58% from stale prose,
trace L527.)

## 6. Clean-ingest under v3 — parallel extract, serial write
Reuse the `/roeh:ingest` fan-out, but writes are **not** independent appends:
```
parallel extraction (dated-chapter / memory / artifact / session agents, emit typed proposals)
      → canonical sequencing (by date, then deterministic tiebreak) + cross-agent edge resolution
      → serialized `roeh record` appends (one at a time; chain computed in true order)
```
Semantic analysis fans out; the authority write is single-threaded. Uncertain relations stay
prose-only, never guessed. Topic *membership* is not emitted (derived). Profile + §5 as today.

## 7. Build order
1. **`roeh record`** — PREPARE/COMMIT (§3–4): canonicalize, id+collision, edge validation, chain,
   flock+fsync+record-atomicity, hybrid formatting. Tests: round-trips `parse_entries`; chain ==
   `_expected_chains`; dangling/late edge refused; concurrent writers don't corrupt the chain (two
   serialized appends verify intact); a killed append leaves zero bytes.
2. **Reader changes** (§2/§3.3): drop `class` from liveness; remove the atomic ≥2-clause heuristic +
   regression test. Re-run the full read suite.
3. **Clean-ingest-under-v3 wiring** (§6) — agents emit `record` proposals; canonical-sequence; a small
   end-to-end that ingests a toy repo and maps with no spurious `UNCERTAIN`.
4. **Dogfood: clean-ingest roeh itself** → a real v3 trace; map it; diff coverage vs the current trace
   (what the strict assistant-prose rule drops — the deferral's revisit signal).
5. **Then upstream** (scale + dirty-vs-clean comparison), scratchpad-only, aggregate stats.

## 8. Decisions & deferrals
**Decided (this spec):** id = 64-bit canonical immutable content-hash (+tag); serialized fsync'd
record-atomic append; `class` dropped; atomic heuristic removed (keep the sound check); topic-hint
kept with the never-affects-coverage invariant; single-successor-unless-conflict ontology stated;
no-edge-inheritance invariant stated; reader-is-schema / writer-is-stronger-contract framing.
**Deferred (P2):** machine-readable typing-status/reason; explicit claim-unit atomicity model;
external signed chain head; context-scoped supersession. **Downstream (adoption, not now):** wire
`roeh map/read/scope/verify` into `bin/roeh`, supersede the `09b0987` retrieval primitives, update
`agents/oracle.md` + profile in lockstep.
