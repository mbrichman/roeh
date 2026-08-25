# Implementation spec (v2) — the read path (consumer side of RFC v3)

> **Status: implementation spec (buildable).** Implements the *read/consumer* side of
> `retrieval-at-scale.md` (RFC v3). v2 folds two independent reviews of v1: an implementation
> review (10 fixes) and the Oracle's clearance against the decision trace (VERDICT: CONSISTENT,
> 5 record-specific risks). Consumer-first: §5 (persisted vs. derived fields) is the output that
> defines the write-path spec. Buildable/testable against a hand fixture **and** required to be
> dogfooded on a real dirty trace (§6) before it counts as correct.

## 0. Artifacts, commands, fences

| Artifact | What | Freshness |
|---|---|---|
| `decision-trace.md` | append-only log (authority) | — |
| `decision-trace-map.md` | root **control plane** (human-readable), regenerated | `projection-id` (§2.0) |
| `decision-trace-bloom.json` | machine bloom sidecar (region → bitset + params) | same `projection-id` |
| `decision-trace-topics.md` | non-authoritative semantic side-map (input; staleness is observable) | versioned |

Commands (supersede `index`/`chapters`): `roeh map`, `roeh read`, `roeh verify`, `roeh scope`.
Nested CPs are computed on demand from the log; only the root map + bloom sidecar are materialized.

**Fences (from the record, non-negotiable):** everything on the hook/CLI path is **stdlib-only**
(`d8098d3`: a missing import fails a hook silently) and **Python-3.8-parseable** (`12aa744`).
The bloom filter, base64, and hashing therefore use `hashlib`/stdlib only — no third-party lib.

**Transition requirement (from the Oracle):** `map`/`read` supersede `index`/`chapters`, which
`agents/oracle.md` and `.claude/roeh-profile.md` currently hardcode. Adoption MUST update the
oracle charter and profile **in lockstep**, and record the supersession of the retrieval-primitives
decision (`09b0987`) **loudly** in the trace. Not done now — v3 is a PROPOSAL.

## 1. The control-plane (CP) file format

Every CP — root map and every sub-region from `read` — has the same shape.

```
# roeh map — decision-trace   (region: <key|ROOT>)
projection-id: <hash>            # §2.0 — the immutable context this CP was folded under
budget: <B_tokens> tokens   fits: yes | hierarchized
## preamble        # ROOT only; a *bounded* digest, LAST-wins per section (§1.1)
§0 <one line> · §1 <≤K principle slugs; overflow → `read §1`> · §5 <resume one line>
## live            # one line per LIVE entry in this region, up to the live allocation
- <id> `[<TAG>]` — <lead ≤90c> · cites <c1,…> [· ↑<supid> | +<augid> | ⚠<cflid>]
## ledger          # supersessions / conflicts / uncertainties / dead-ends for this region
- SUPERSEDED <deadid> superseded-by <directid> · current-tip <tipid>  (<why ≤6w>)
- DEAD-END   <id> — <lead>
- CONFLICT   <id> ⚠ <id>  (unresolved)          # symmetric: shown on read of either (§2.2)
- UNCERTAIN  <id> — <reason>                      # prose-only / dangling / double-supersede / non-atomic
## regions         # child regions (root) or entry-partition children (sub-levels)
- <key> · <L> live · <H> hist · <hot|settled|retired> · «<≤8 digest terms>» · bloom ✓ · read <key>
```

### 1.1 Bounded, last-wins preamble
The preamble is **bounded** (a token cap like every other section) — it is *not* an
"unbounded one-line list." If §1 has more principle slugs than fit, it shows the cap and
`read §1`. Each of §0/§1/§5 is digested from the **LAST** superseding block, never the first —
this trace has five §5 blocks; taking the first serves stale resume state (the recorded
`bin/roeh-sessionstart` bug `L352`, profile dead-end "Reading the FIRST §N").

## 2. Map generation (`roeh map`)

### 2.0 The projection context (determinism + freshness, done once)
A CP is folded under an **immutable projection context**, and every recursive `read` inherits
it verbatim — never current defaults (else a child binds a different D/topic-map/repo than its
root: a "fractured read").

```
projection-id = H( log-terminal-value, topic-map-hash, repo-head,
                   B, D, as-of, resolver-version, tokenizer-version, schema-version )
```

- **`log-terminal-value` is the log's own last entry-chain value / hash of exact log bytes —
  NOT git HEAD.** An uncommitted EOF append doesn't move HEAD, so HEAD-based freshness silently
  goes stale. Freshness (T0) = every input still equals the one baked into `projection-id`.
- `repo-head` is an input because generation consults git (SHA→paths via `git show --stat`,
  path-stability via `git log`). It was a hidden input in v1; now explicit.

### 2.1 Parse & graph
Dual-dialect parse (`- **[TAG]**` and `` - `[TAG]` `` — the 90%-under-report `[GOTCHA]`
`09b0987`). Build nodes + typed edges. Assert every edge targets an existing, strictly earlier
id (backward DAG; cycles impossible). Build a **symmetric conflict adjacency**: a stored
`conflicts_with: E1` on E2 means `read E1` surfaces E2 too, though E1 has no outgoing edge.

### 2.2 Liveness (mechanical; loud on every gap — §RFC 4)
`dead(e)` iff `∃ e'` with `e ∈ supersedes(e')`, or `e` is terminal (`DEAD-END`/`WITHDRAWN`).
`augments`/`conflicts-with` never kill. Fail **loud** (`UNCERTAIN`, surface both, force drill),
never resolve silently, on:
- **prose-only** supersession (no machine edge) or a **dangling** target;
- **≥2 unresolved `supersedes` of the same target** with no `conflicts-with` resolving them
  — *this*, not mere graph fan-out, is the suspicious case (two `augments` of one entry are
  legitimate and compatible);
- **suspected non-atomicity** (§2.2.1).

**2.2.1 Atomicity is a liveness surface (the Oracle's sharpest flag).** Whole-entry liveness is
sound only if an entry is the smallest independently-supersedable unit. Deciding atomicity is a
write-time judgment; when it is misjudged, superseding a multi-claim entry silently kills a
co-located live claim. So: the write path MUST emit atomic entries **and stamp an `atomic:true`
assertion**; the map treats a superseded entry lacking that assertion, or one whose text trips a
multi-claim heuristic (multiple `WHY`/measurement/`GATES` clauses), as `UNCERTAIN` — loud, not
silent. Read-side demands it; the write spec must *demonstrate* clean ingest produces atomic
entries (fixture + dogfood, §6).

**2.2.2 Augment inheritance.** If `A` is augmented by `B` and `C supersedes B`, the attachment to
`A` must not vanish: the write path MUST have `C` restate the augment (`C augments A`) when it
supersedes an augmenter. The read spec **requires** this restatement; a lost augment edge across
a supersession is a write-path defect, surfaced as `UNCERTAIN` if detected.

### 2.3 Regions, retirement, budget (partition entries, not sections)
- **Regions = topics:** path-provenance (cites → paths; bare SHA → `git show --stat`) ∪ semantic
  labels (side-map). Multi-membership allowed.
- **Retirement** (§RFC 6, over sets `E(r)`,`P(r)`,`IDs()`): `RETIRED` = zero live; `SETTLED` =
  age>`D` ∧ paths-stable>`D` ∧ no live inbound. Else `hot`.
- **Hierarchy partitions the entry set `E(r)`, never a presentation section.** A child is
  `hooks/<range>` with its *own* live+ledger+regions+bloom over that entry subset; cross-boundary
  edges appear as stubs. (v1 wrongly segmented `## live` alone, breaking the "same shape"
  invariant.)
- **Bounded fan-out:** if collapsing to child headers still exceeds budget, the header list is
  itself recursively grouped (`region → groups → segments → entries`) with a max branching
  factor, so `roeh map` exit-3 really is unreachable.
- **Budget control loop, in tokens:** the invariant is `estimated_tokens(CP) ≤ B` — **not lines**
  (100 lines can be 5KB or 500KB; the whole RFC exists because a "small" representation crossed a
  *physical* threshold). Every field has a serialization cap. While over budget:
  collapse `retired`→header, then `settled`→header, then partition the largest section's entry
  set (§2.3), regenerating deterministically under the fixed `projection-id`.

### 2.4 Bloom (per region; self-regulating; one tokenizer)
- **Tokenizer (versioned, single implementation):** lowercase; split on non-alphanumeric; keep
  tokens len≥3; **additionally** keep dotted/slashed identifiers whole (`roeh append`,
  `find_project_root`). **`scope` and `map` MUST call the identical tokenizer function** — the
  no-false-negative guarantee (§RFC 1C/8) rests entirely on this symmetry; "equivalent prose
  rules" is not enough.
- Region bloom = OR of its entries' + children's blooms (⇒ a token in any descendant sets every
  ancestor bit: no false negatives on descent).
- **Self-regulating:** if a region's estimated FPR/bit-density exceeds threshold `F`, it MUST be
  subdivided until each immediate child is below `F` — otherwise a large region saturates to
  all-ones and becomes a drill-everything machine (a scaling failure, not a correctness one).
- Sidecar stores, per region: bitset (base64), `tokenizer-version`, `hash-version`, `m`, `k`,
  bit-density, estimated FPR. Defaults `m=16384,k=7` are a recalibration knob, not a constant.

## 3. The drill protocol (enforced vs. policy; recursive)

```
read(Q):
  # enforced
  cp ← load root map;  T0: cp.projection-id inputs all still current? else regenerate / EXIT 6
       verify chain; on break → EXIT 7
  read cp.preamble, cp.live, cp.ledger IN FULL
  literalHits ← regions whose bloom matches any literal token of Q   # same tokenizer as map
  # policy
  scoped ← scope0(Q, cp.regions)                                     # seeds + lexical over digests
  # enforced
  frontier ← scoped ∪ literalHits                                    # M4 + bloom: MUST drill
  while frontier: for r in frontier:
        childcp ← read(r)          # recomputed under the SAME projection-id (§2.0)
        read childcp.live, childcp.ledger IN FULL
        frontier' ∪= scopeK(Q, childcp.regions) ∪ bloomHits(childcp)
     frontier ← frontier'
  for each supporting entry: readClosure(e)   # live augments (transitive) + symmetric conflicts
  answer; T5: state regions drilled / skipped
```
Enforced (testable): T0 freshness (projection-id), chain verify, always-read preamble/live/ledger,
bloom-mandatory + recursive M4, read-closure, no-citing-headers, fail-closed (§4). Policy (model):
`scope0/scopeK`, under-determination, broad/global (a truly global Q → *declared* full traversal).

## 4. CLI contracts (exit codes are the contract)

Reserve `0` ok / `1` usage-error / `2` precompact-block. New:
- **`roeh map [--budget T] [--dormancy D] [--as-of TS]`** → root map + bloom sidecar, stamped
  `projection-id`. `0` ok; **`3`** cannot fit `B` after full hierarchization (a bug signal).
- **`roeh read <region | region/child | id | §N>`** → a CP, or a leaf entry + its live augments.
  `0` found; **`4`** no such selector; **`5` UNREADABLE** — cannot recover the entry bytes.
  Provenance failures are **not** exit-5: a recovered entry with a dangling cite is returned `0`
  with an **`UNVERIFIED`** / **`UNRESOLVED-PATH`** marker. The Oracle fails closed on the
  *claim* that needs the broken provenance — never on retrieval of an intact entry. (v1 conflated
  content-loss with provenance-loss, letting one stale path poison a whole region.)
- **`roeh verify`** → `0` fresh+intact; **`6`** stale (projection-id inputs moved); **`7`** tamper
  (chain break). On the read path (T0=6, integrity=7).
- **`roeh scope "<Q>"`** → debug: seeds, lexical hits, bloom hits, mandatory drill set. `0`.

## 5. Entry fields — split persisted (authority) from derived (read-model)

The Oracle's boundary fix: semantic classification must not re-enter the immutable log.

**Persisted (in the append-only entry — the write-path schema):**
`id`, `chain`, `tag`+`class` (unknown ⇒ class `other` ⇒ live+always-visible), `supersedes[]`,
`augments[]`, `conflicts_with[]`, `date`, `cites[]` (plural — multi-file/commit provenance),
`lead`, `atomic:true` (§2.2.1), and an **optional author-supplied `topic-hint[]`** only.

**Derived at map time (never persisted; regenerable):** topic *membership* (path-derived +
semantic side-map), tokens, bloom, liveness, region membership, retirement state. `topic[]` as a
computed membership set lives *here*, not in the log.

## 6. Fixture, dogfood gate, tests

**Fixture** `tests/fixtures/trace-v3.md` (+ expected map/bloom): ~20 hand-typed atomic entries
across 3 topics covering every branch — live decision; chain `A←C`; double reversal `A←C←D`;
`augments` pair (+ a `C supersedes B` where `B augments A`, testing 2.2.2); `conflicts-with` pair
(test symmetric read); `DEAD-END`; `RETIRED` topic; `SETTLED` topic; **prose-only** supersession
(→ UNCERTAIN); a **deliberately non-atomic** entry then superseded (→ UNCERTAIN, 2.2.1); a rare
literal token; five superseding `§5` blocks (test last-wins preamble); both dialects.

**Dogfood gate (from `ddad17b`, mandatory — fixture-green ≠ correct):** the read path MUST also be
run against a **real, dirty, heterogeneous trace** (the upstream ~10k-entry artifact, as a test
fixture per the clean-start decision) and its recursion/budget/bloom/retirement behaviour
inspected. This is a **correctness** gate, distinct from RFC §13's parameter calibration. Clean
fixtures hide exactly the class of bug this dead-end records.

**Tests** — deterministic/exit-code except the one `(model)`, which lives in the **opt-in
`tests/eval-prompts` tier, never `tests/run`** (`b70483e`: the cheap suite must stay cheap):

| Test | Asserts |
|---|---|
| map-determinism | same `projection-id` inputs ⇒ byte-identical map + bloom |
| coverage (model-free) | every entry represented (live ∨ ledger ∨ region header) |
| projection-context | a child CP inherits the root's `projection-id`; a changed input ⇒ `verify` 6 |
| freshness / dirty-append | an *uncommitted* EOF append moves `log-terminal-value` ⇒ `verify` 6 |
| last-wins preamble | with five `§5` blocks, the map digests the LAST |
| token-budget | `estimated_tokens(CP) ≤ B` at every level; overflow hierarchizes; root fits |
| bounded fan-out | a region with huge child count regroups; no CP exceeds `B` |
| bloom-no-false-negative | every literal token's region is in `scope`; map/query tokenizer identical |
| bloom-saturation | a dense region subdivides below FPR `F` |
| uncertain-loud | prose-only, double-supersede, and non-atomic all ⇒ `UNCERTAIN`, both visible |
| read-closure | `read <id>` returns live augments (incl. the 2.2.2 restatement case) |
| conflict-symmetry | `read E1` surfaces `E2 conflicts_with E1` |
| supersede-not-live | superseded value never in `## live`; ledger shows `superseded-by`/`current-tip` |
| unreadable-vs-unverified | dangling cite ⇒ `0`+UNVERIFIED (not exit 5); byte-loss ⇒ exit 5 |
| dialect | both tag dialects counted |
| **cold-reversal (model, eval tier)** | a reversal in a cold region on the drill path returned over the tip |

## 7. Build order
1. Tokenizer (single impl) + parser + graph + liveness (incl. UNCERTAIN triggers) — pure, unit-first.
2. Regions + retirement + token-budget loop + bounded fan-out → `roeh map`; determinism + coverage + last-wins.
3. Bloom sidecar + saturation + `roeh scope` → no-false-negative + saturation.
4. `roeh read` recursion (projection-id inheritance) + read-closure + conflict-symmetry + unreadable/unverified split.
5. `roeh verify` + projection-id freshness (incl. dirty-append).
6. **Dogfood on the real dirty trace** (correctness gate) — before declaring the read path done.
7. The one model eval (cold-reversal), opt-in tier.

Only after this is green do the **write-path spec** (§5 persisted fields, atomicity + augment-restatement invariants) and a **clean ingest** follow — and adoption must update `agents/oracle.md` + the profile in lockstep and record the `09b0987` supersession loudly (§0).
