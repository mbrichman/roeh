# RFC — Retrieval at scale (v3): a recursive control plane with mechanical literal recall

> **Status: PROPOSAL.** Not an owner decision; nothing implemented. v3 folds in a third review.
> Its single organizing correction over v2: **recursion, introduced in v2 only for storage,
> is now pervasive** — scope, mandatory drill, the completeness theorem, budget enforcement,
> and absence queries are all recursive. Plus a typed-edge/read-closure model and a
> per-region literal-existence index. See §14 for the v2→v3 diff.

## 0. The problem

The append-only log only grows. A flat index is O(entries) and eventually unreadable. The
log is the immutable single authority (owner's founding constraint); everything else is a
derived, regenerable view. The idea, unchanged: **don't summarize history away — shrink the
always-loaded control plane and use it to trigger lossless, bounded, recursive rehydration.**

## 1. Three separated guarantees

**1A — Coverage (mechanical, provable, model-free).**
> Every authoritative log entry is either represented directly at some level of the view, or
> is a member of a region represented (at its parent level) by a header from which it is
> **losslessly rehydratable**. The root view records the log head `H` it is valid through.

**1B — Conditional completeness (recursive).** For a target entry `E` relevant to `Q`, define
`SoundDrill(Q, E)`: there is a nested region path `root = r₀ ⊇ r₁ ⊇ … ⊇ r_m ∋ E` such that at
each level `k`, `scope_k(Q, CP(r_{k-1}))` selects `r_k`.
> Given Coverage, fresh views (T0), `SoundDrill(Q,E)`, recursive mandatory-drill (M4),
> read-closure (§4), and fail-closed (T6): the protocol surfaces `E` (and its live augments),
> or explicitly declares some region on the path unread. *Proof:* induct on the path. At each
> level Coverage represents `r_k` in `CP(r_{k-1})`; `SoundDrill` ⇒ `r_k ∈ scope_k`; M4 ⇒ `r_k`
> is drilled (or T6 declares it unread); at the leaf, lossless rehydration + read-closure
> surface `E` and its live augments. ∎

**1C — Scope recall (empirical goal).** `scope_k` should conservatively approximate the
per-level `SoundDrill` condition. **For literal query tokens this is mechanically guaranteed
(§8 Bloom); the residual is confined to *semantic* (non-literal) relevance.** False negatives
there are retrieval failures — bounded and made observable, never claimed away.

Boundary: **storage guarantees reachability (1A); the protocol mechanically guarantees literal
recall (§8); only non-literal semantic recall is best-effort (1C).**

## 2. Data model

### 2.1 The log
One append-only markdown file, git-tracked, sole authority. No sharding (removed in v2: it added
a shard-discovery completeness gap for only file-size hygiene the write-mostly log never needs).

### 2.2 Identity vs. tamper chain (two fields, two jobs)
- **`id = H(canonical_entry)`** — content-addressed identity. Canonicalization is explicit and
  **excludes the `id`/`chain` fields themselves** (no snake eating its own hash). A named hash,
  not an "unspecified shorthash"; uniqueness checked at append (collision = loud failure).
- **`chain = H(prev_chain ‖ id)`** — a genuine hash chain for tamper *sequencing*, separate from
  identity. (v2 called the id a "chain" but defined no `prev` link — fixed.)

### 2.3 Typed relation edges
Three relations, each pointing to an **existing, strictly earlier** entry (append-only ⇒ a
natural backward DAG; enforced at append, so cycles are impossible and detection is free):
- **`supersedes: [id…]`** — the prior proposition **no longer stands** (includes a corrected
  value: "timeout 30s" superseded by "45s" — 30 is dead). Target → dead.
- **`augments: [id…]`** — the prior proposition **remains independently true**; new information
  attaches (a consequence, a caveat, a second measurement). Target stays live.
- **`conflicts-with: [id…]`** — an **explicit, unresolved** incompatibility. Both stay live and
  are surfaced together as a conflict.

The scribe assigns the relation **at write time**, with context (the recorded `[LESSON]`:
overturn-vs-augment is semantic and cannot be a read-time guess). **Conflict is never inferred
from graph fan-out** — two augments of one entry are usually compatible; conflict is only the
explicit relation, or two `supersedes:` of the same target with incompatible content (→
`liveness-uncertain`, §4).

### 2.4 Metadata is written inline, at append
Every entry carries its `id`/`chain`/edges **inline, stamped at append** — no entry is ever
mutated to add them afterward. This is possible because **roeh always starts clean** (§2.6): the
record is ingested from primary evidence under the current model, so there is no legacy trace to
convert and no need for a side-car of after-the-fact ids/edges.

### 2.5 Atomic-entry invariant
An entry is the *smallest independently supersedable semantic unit* — what makes whole-entry
liveness correct. The write path emits atomic entries **and stamps `atomic:true`**. Because
*misjudging* atomicity is itself a write-time semantic call (the same class the `[LESSON]` says
can't be mechanical), a superseded entry that is not asserted atomic — or that trips a
multi-claim heuristic — is treated as `liveness-uncertain` (§4), loud, never a silent kill of a
co-located live claim. Atomicity is thus a liveness surface, not a mere authoring nicety.

### 2.6 Adoption: always start clean
roeh **never converts a legacy trace in place.** On any project it (re)ingests from primary
evidence under the current model; a pre-existing trace — an older roeh trace, another tool's, or
a hand-built one — is a **test fixture and a pointer to gaps**, never a source to copy and never
mangled into the schema. Holes a clean ingest leaves are filled by re-deriving from primary
evidence; a hole whose only support is the old trace's assistant-authored prose is recorded
`[OPEN]`, not imported (hall of mirrors). This removes the in-place legacy-conversion path
entirely. Rationale and empirical basis: decision-trace, 2026-08-24.

## 3. The recursive control plane (the unifying structure)

Everything the Oracle reads is a **control plane** `CP(r)` for a region `r` (the root region is
the whole trace), a bounded node containing, within a budget slice `B(r)`:

- **preamble** (root only) — a *fixed-size* structural digest of §0/§1/§5.
- **live slice** — live entries of `r`, shown directly up to the live allocation.
- **child headers** — for each sub-region `r'`: `id · L live · H historical · «keyword digest»
  · «bloom» · roeh read <r'>`.
- **ledger slice** — supersession/conflict/dead-end summaries for `r`, up to allocation.

`roeh read <r'>` returns `CP(r')`; leaves are individual entries by `id`. Recursion terminates
because each descent strictly shrinks the region.

**Child headers carry counts + a bounded keyword digest + a Bloom summary — never per-entry
enumeration.** That keeps every node's size independent of how much history sits beneath it
(the v2 fix), and gives scope both a lexical surface and a no-false-negative existence check
(§8).

### 3.1 The budget is structural (v2's remaining hole, closed)
> **Nothing except the fixed-size preamble is exempt from the budget.** Every section — live,
> ledger, dead-ends, *even principles and terminal-dead entries* — has a budget allocation or
> a manifest fallback. Any section that exceeds its allocation becomes a bounded
> sub-control-plane, **regardless of hot/cold/dormancy status.**

So "hot" means *expanded preferentially*, not *guaranteed flat in the live slice*. 20,000 live
recent decisions (none old enough to settle) do **not** blow the budget — the live slice
hierarchizes into sub-regions like any other. `|CP(r)| ≤ B(r)` holds by construction, not by
corpus behavior. (v2 wrongly exempted hot content, principles, and terminal-dead — each an
unbounded term.)

`B` is the primary knob; the dormancy threshold `D` is derived to help satisfy it. **To shed
size, *lower* `D`** (retire more aggressively) — note the direction: settlement uses `age >
now − D`, so a *smaller* `D` settles *more*. (v2 said "raise the bar," which is backwards.)

## 4. Liveness, read-closure, and loud failure

Sets per entry `e`: `M(e)` memberships, `C(e)` cited paths, `Sup(e)`/`Aug(e)`/`Cfl(e)` the
`supersedes`/`augments`/`conflicts-with` targets.

- `e` is **dead** iff `∃ e'` with `e ∈ Sup(e')`, or `e` bears a terminal tag
  `[DEAD-END]`/`[WITHDRAWN]`. Else **live**. `augments`/`conflicts-with` never kill.
- **Read-closure (v3, the `refines`/`augments` fix).** When a live entry `e` is surfaced as
  support, every **live** `e'` with `e ∈ Aug(e')` (reachable transitively) MUST be surfaced
  before `e` is cited, and every `e'` with `e ∈ Cfl(e')` MUST be surfaced as an open conflict.
  (Otherwise "timeout is 30s" is cited without its live augment/superseder.)
- **Liveness is mechanical only as far as the typing is complete; every gap fails LOUD**
  (`liveness-uncertain`, surface both entries, force a drill): prose-only supersession with no
  machine edge; a dangling target; two `supersedes:` of one target with incompatible content.
- **Dual-dialect tag recognition** is mandatory (the 90%-under-report bug, `09b0987`).
- **`[CLOSED]` is not a liveness terminal** (a completed decision can be wholly current); only
  supersession or `[DEAD-END]`/`[WITHDRAWN]` mean dead. Terminal-dead-with-no-successor stays
  reachable via the ledger/manifest (no live successor carries its concept).

## 5. Topics and the two floors

### 5.1 Path-provenance floor (deterministic, not a semantic floor)
`e` belongs to path-topics of `C(e)` (for a bare SHA, the commit's touched files). Property:
*if `Q` names path `P`, every entry whose recorded provenance includes `P` is reachable.* This
is **provenance, not semantic domain** — a decision *about* the daemon may be recorded in a
commit touching only `hooks/`. Not sufficient for recall on its own.

### 5.2 Semantic topics (non-authoritative annotation)
Cross-cutting/uncited entries get labels from an occasional `roeh topics --assign` pass into a
**side-map**; *non-authoritative* (a hand-edit is not recreatable from the log, so it is an
annotation, not a derivation). A label can only **add** membership, never remove a
path-membership → a bad label costs reads or recall (§9), never coverage.

### 5.3 Literal-existence floor (Bloom, mechanical, no false negatives)
Each region carries a **Bloom filter over its normalized tokens/symbols**; a parent's Bloom is
the OR of its children's, so **a token in any leaf is present in every ancestor's Bloom**. A
literal query token therefore drills to its leaf with **no false negatives** (only extra
reads). This is the mechanical backbone of §8 and the reason literal recall is *complete*.

> **Shipped status (2026-08-28) — read this as the boundary of the guarantee.** The
> leaf-level drill above is the DESIGN. The shipped `scope_literal` is **region-granular**:
> it returns the *parent region* of any matching Bloom (it collapses saturation segments
> back to the region), so mechanical literal recall is complete **to the region boundary**.
> Descending from a segmented region into the specific `region/N` segment or entry is
> currently read-protocol *policy* — the caller reads the region's segments — **not**
> mechanically enforced; the recursive-to-leaf M4 (§7) is not yet wired. Building it means
> aligning the two segmentations (saturation-by-FPR vs display-by-`SEGMENT_TOKENS`) or
> adding per-segment scope. Until then the honest claim is *"complete to the region
> boundary,"* which is what the tests pin.

## 6. Cold regions & retirement (formal)

For region `r`: `E(r)` = its entries, `P(r)` = its path footprint (`⋃_{e∈E(r)} C(e)`),
`IDs(E(r))` their ids.

- **RETIRED**: `E(r)` has zero live entries.
- **SETTLED** (dormant-but-live), over an explicit as-of time `now`:
  1. **age**: `max_{e∈E(r)} date(e) < now − D`;
  2. **path-stability**: no path in `P(r)` modified in `[now−D, now]`;
  3. **no live inbound** (v3 type-clean): `∄` live `e' ∉ E(r)` with
     `(Sup(e') ∪ Aug(e') ∪ Cfl(e')) ∩ IDs(E(r)) ≠ ∅` **or** `C(e') ∩ P(r) ≠ ∅`.

Both collapse to a child header (counts + digest + bloom). Retirement is a derived property
recomputed under the watermark; it self-heals. Structural budget (§3.1) may collapse a region
even when *not* retired — dormancy only decides *expansion preference*, never visibility or
reachability.

> **The crux:** dormancy (and budget) gate *expansion*, never *visibility* (headers always
> read) or *reachability* (M4 + Bloom drill). Same input as claude-mem's recency, opposite
> point in the pipeline, opposite safety.

## 7. The read protocol — recursive, split into enforced vs. policy

An **iterative drill**: `scope₀(Q, root) → drill → scope₁(Q, newly-exposed children) → drill →
… → leaf`. Scope is recomputed at each level over the children just exposed.

### 7.1 Mechanically enforced (model-free, testable)
- **T0 — Freshness.** The map stores `mapped-through: H`; the read path refuses a map whose
  watermark ≠ current log head / topic-map version, regenerating first (`roeh
  append` may atomically invalidate).
- **Coverage (1A)** by construction.
- **M4 — Recursive mandatory drill.** At each level, every child region in `scope_k` MUST be
  drilled before answering. Applies at *every* level, not just the root.
- **Bloom-mandatory drill.** Any child whose Bloom matches a **literal token of `Q`** MUST be
  drilled (no-false-negative literal recall), independent of semantic scope.
- **Read-closure (§4)** before any citation.
- **No citing headers/digests/blooms** — triggers only; a load-bearing claim rests on a
  rehydrated entry.
- **T6 — Fail closed.** If a required region can't be losslessly rehydrated or verified (SHA
  gone after a rewrite, shallow checkout, corrupt manifest, read over max, path unresolved
  after rename, watermark mismatch, chain-verify fail), mark it **unread** and make no claim
  that may depend on it.

### 7.2 Oracle policy (best-effort, declared)
`scope_k` **semantic** construction, under-determination judgment, and broad/global handling.
Bounded by the mechanical layer, so a policy error costs reads or a declared gap — except a
*semantic* `scope_k` false negative (the §1C residual; literal misses are excluded by Bloom).

### 7.3 Broad and global questions (v2 contradiction resolved)
Scope **re-narrows at each level**. A question whose terms match only some children drills only
those — it does *not* read the whole trace. A **genuinely global** question ("summarize every
decision ever") legitimately drills all children at all levels = a full traversal; that cost is
irreducible and is **declared**, not silent. (v2 wrongly claimed "scope=all rehydrates
manifests, not the trace" — if `scope=all` truly propagates, M4 reaches every leaf. The honest
statement: non-global questions narrow; global questions cost a declared full read.)

## 8. Scope, literal vs. semantic absence

- **Literal existence is decidable** via §5.3 Bloom: for a literal token `t`, drilling every
  Bloom-matching region reaches every entry containing `t` with no false negatives. So "is
  there any entry mentioning `t`?" is answered **soundly**.
- **Literal absence** ("no entry contains token `t`") is therefore provable: all Bloom-matching
  regions drilled and none contains `t` ⇒ genuinely absent.
- **Semantic absence** ("did we ever consider moving reconciliation off-thread?") is **not**
  provable from lexical metadata. The honest answer is *"no matching decision found under the
  retrieval strategy used"* — a full authoritative traversal is required to assert true
  semantic absence, and the protocol says which it did. This distinction is stated to the asker;
  conflating the two is exactly the silent-negative failure the design avoids elsewhere.

## 9. Robustness

- **9A — Classification robustness (corrected).** A wrong topic label or dormancy verdict
  **cannot destroy reachability or violate Coverage (1A)**. It may **increase reads _or reduce
  scope recall_ (1C)** — e.g., an uncited entry mislabelled into the wrong semantic topic can
  cause a *semantic* scope false negative (under-drilling). Literal recall is unaffected
  (Bloom, §5.3). (v2 said "over-drilling, never coverage loss" — the "over" was wrong.)
- **9B — Liveness robustness.** A liveness verdict may drop an entry from a live slice but never
  removes reachability (ledger stub, terminal-dead in the ledger, Bloom + digest in the
  header); any *uncertain* liveness fails loud (§4).

## 10. CLI / artifacts
- `roeh map` — fold log + topic-map under budget `B` into the recursive control plane (**the map**); stamp the `mapped-through`
  watermark + per-region Bloom/digest.
- `roeh read <r | r/child | id | §N>` — recursive bounded rehydration (returns a `CP`, or a leaf).
- `roeh topics [--assign]` — the non-authoritative semantic side-map.
- `roeh verify` — id/chain integrity + watermark; **on the read path** (T0/T6).
- `roeh scope "<Q>"` — debug per-level scope + Bloom hits.

## 11. Enforcement & integrity
- **PRIMARY: prevent at commit** — a commit-time check rejecting any diff that removes/edits
  existing log lines (append-at-EOF only). Binds the commit; would have caught both real
  historical breaches.
- **Anchor** — tamper-evidence needs a trusted value held elsewhere (signed head `chain` in CI
  / protected checkpoint / signed release); a bare chain an attacker can recompute end-to-end
  is not self-protecting. Git already hashes, so the direct-edit problem is policy + anchoring.
- **`chain`** (§2.2) is a secondary integrity aid with defined canonicalization — not the
  load-bearing guarantee.

## 12. Verification
- **Coverage (model-free):** enumerate log entries; assert each is represented at some level and
  the watermark = log head. *(v2's "Coverage (model)" test actually tested conditional
  completeness — renamed below.)*
- **Conditional-completeness / cold-reversal (model):** a `[REVERSAL]` in a cold region on the
  scoped drill path is rehydrated and returned over the superseded tip.
- **Recursive-drill bounded:** no `CP` at any level exceeds its read budget; a deep leaf is
  reached in bounded steps.
- **Structural budget under hot overflow:** N live recent entries with `N·line > B` ⇒ the live
  slice hierarchizes; `|CP(root)| ≤ B`.
- **Bloom no-false-negative:** a literal token in any leaf is found by the drill.
- **Literal vs semantic absence:** literal absence provable; semantic absence reported as
  strategy-limited, not asserted.
- **Augment read-closure:** citing E surfaces its live augments; a corrected value never returns
  stale.
- **Supersede-corrected-value:** superseded value is not returned as current.
- **Conflict is explicit:** two augments don't trip a conflict; `conflicts-with` does.
- **Determinism (full inputs):** `log + topic-map + D + B + repo-snapshot +
  as-of-time + resolver-version` ⇒ identical view.
- **Fail-closed (T6):** an unreadable required region is declared, not answered around.
- **DAG/cycle:** an edge to a non-existent or later entry is rejected at append.
- **Dialect:** both tag dialects counted.

## 13. Deferred / open
- **Semantic scope recall (§1C)** — the residual, now confined to non-literal relevance; the
  place to invest if a real trace shows semantic misses.
- **`B`, `D`, Bloom sizing** — one empirical calibration on the real ~900KB trace.
- **Entry classes** — a real trace mixes decisions with evals, scripts, assets, docs; the map's
  liveness/retirement must handle non-decision entry classes, and unknown tags must default to
  live + always-visible. Surfaced by fixture analysis of a real ~10k-line trace.
- **Adoption / transition** — `map`/`read` supersede `index`/`chapters`; adoption MUST update
  `agents/oracle.md` and the profile in lockstep, and record the `09b0987` retrieval-primitives
  supersession loudly (Oracle clearance, 2026-08-24). Fences: stdlib-only + 3.8-parseable
  (`d8098d3`, `12aa744`).
- **Correctness dogfood on the real dirty trace** — a distinct gate from `B`/`D` calibration;
  `ddad17b` warns fixtures have clean ancestors and hide the bug class a real 10k-entry trace
  exposes.
- **Lossy prose rendering** — demoted to an optional rendering of already-safe bounded segments;
  never a substrate.

## 14. What changed v2 → v3
| v2 | v3 |
|---|---|
| recursion in *storage* only | recursion pervasive: scope, drill, proof, budget, absence |
| theorem: region rehydrated ⇒ E surfaced | `SoundDrill` (recursive scope) + read-closure; theorem repaired |
| budget exempts hot/principles/terminal | **nothing but a fixed preamble is exempt**; any section hierarchizes |
| "raise the dormancy bar" to shed size | **lower `D`** (settlement uses `age > now − D`) |
| absence = scan lossy digests (unsound) | **Bloom per region** → sound literal absence; semantic absence caveated |
| `supersedes` vs `refines` | `supersedes` / `augments` / `conflicts-with` + **read-closure** |
| two successors = conflict | conflict is explicit only; augments are usually compatible |
| id called a "hash-chain" (no prev) | `id = H(entry)` **and** separate `chain = H(prev‖id)` |
| `no-live-inbound` mixed ids and paths | type-clean over `E(r)`, `P(r)`, `IDs()` |
| 9A: "over-drilling, never coverage loss" | reads↑ **or** recall↓ (1C); never coverage loss |
| — | edges must point to existing earlier entries (DAG, cycle-free at append) |
| literal & semantic recall both "best-effort" | **literal recall mechanically complete**; only semantic is 1C |

## 15. Provenance
v1 → v2 merged a five-lens adversarial red-team and an external owner-review. v3 folds a third
review whose central point — recursion was only half-propagated — reshaped the spec. Direction
reviewed as *approved*; remaining work is empirical calibration and implementation choices, not
conceptual holes. Still a PROPOSAL until the owner rules.
