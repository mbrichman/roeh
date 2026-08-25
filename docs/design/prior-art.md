# Prior art — memory tools & the storage/retrieval survey

> **Reference, not a decision doc.** This is the prior-art survey that informed RFC v3
> (`retrieval-at-scale.md`). Captured so a future session doesn't re-run it — re-deriving a
> settled survey is the exact waste roeh exists to prevent. The *decisions* live in the RFC;
> this is the evidence behind them.

## The discriminator: completeness

roeh's hard requirement is **complete retrieval** — silently missing a relevant or superseding
entry is catastrophic (a wrong answer wearing citations). That single requirement rules out
the dominant mechanisms:

> *Every system that bounds retrieval reads from a **bounded derived view**. The ones that stay
> complete use a **deterministic projection + hard scoping**; embedding top-k and grep can
> silently miss.*

So the primary retrieval path **cannot** be semantic top-k or grep — it must be a deterministic
projection. (This also re-justifies roeh's "not a vector store" stance from the *scaling* side,
not just human-readability.)

## The 2×2 — almost everyone sacrifices one axis

|  | **Bounds growth** | **Unbounded** |
|---|---|---|
| **Complete** *(deterministic)* | **← the empty quadrant → roeh v3** | roeh-v0 · projectmem · Lore |
| **Incomplete** *(top-k / recency)* | mem0 · claude-mem · repomemory | Deciduous |

- **Complete-but-unbounded** (roeh-v0, projectmem, Lore): deterministic/path-scoped, but *no
  compaction* — read completely, pay linearly forever. The corner roeh-v0 got stuck in at 900KB.
- **Bounded-but-incomplete** (mem0, claude-mem, repomemory): stay small *by being willing to
  miss* — top-k, recency caps, or consolidate-by-**deleting**.
- **The both-quadrant is empty.** That's roeh v3's opportunity: a **collapsing deterministic
  projection** — bounded like mem0 (fact-not-event), complete like projectmem (deterministic
  fold), lossless like neither (log retained, projection derived). roeh reaches it *because* its
  supersession links are explicit, so it collapses model-free where mem0 needs an LLM + a delete.

## The tools

| Tool | Storage | Retrieval | Scale | Notable idea |
|---|---|---|---|---|
| **mem0** (arXiv 2504.19413) | vector DB (+ optional Neo4j graph) | top-k embeddings | write-time ADD/UPDATE/**DELETE** consolidation (~60% smaller, +22% precision) | store tracks *distinct facts, not events* — but **deletes** (collides with append-only) |
| **projectmem** (2606.12329) | append-only `events.jsonl` | **deterministic projection** (`summary.md` = idempotent fold, never authored) | none (token-budget slice only) | **roeh's near-twin** — log + deterministic fold; but its projection *slices*, never *collapses* |
| **Lore** (2603.15566) | git **trailers** (decision bound to its diff) | CLI over `git log --trailer` | punts (no index) | **path-scoped "decision shadow"** — retrieval cost tracks a *file's* history, not the repo's |
| **claude-mem** (v13, ~SQLite+Chroma) | LLM-summarized observations; **raw discarded from its own store** | recency-cap injection (`LIMIT 50`) + top-k FTS/semantic | none (LIMIT is the silent-omission mechanism) | **the cautionary opposite** — summary *is* the substrate; silent miss is the *default* failure |
| **repomemory** | `.context/` markdown by category | hybrid keyword+semantic | ~none | tunable hybrid recall |
| **Deciduous** | SQLite typed nodes/edges (decision graph) | graph traversal + status filters | weak (graph grows) | pre-edit hook bounds retrieval to the *active session tree* |

## CS mechanisms (the non-LLM ones that actually bound retrieval)

- **LSM leveled compaction** — many immutable runs; point read touches ~1 run/level → O(log N);
  merges physically drop superseded versions. Cost: write amplification.
- **Event sourcing + rolling snapshots** — append-only log is truth; a snapshot materializes
  state so replay covers only events-*since*-snapshot. **This is roeh v3's log↔map split.**
- **MemGPT/Letta** — OS-style tiers (fixed context ↔ external store); the model self-pages, with
  recursive summary-of-summaries on overflow → bounded context regardless of history.
- **Generative agents** (Park et al.) — NL memory stream scored by recency·relevance·importance;
  periodic **reflection** synthesizes higher-level insights back into the stream.
- **Git** — packfiles delta-compress (bound storage); the **commit-graph** + generation numbers
  prune ancestry walks (bound traversal to the relevant subgraph).

## What roeh v3 took from each

- **projectmem** → the log↔projection split (but make the projection *collapse*, not just slice).
- **mem0** → store size = distinct live facts, not events (but collapse model-free, never delete).
- **Lore** → path-scoping (roeh already carries `file:line@sha` / SHA→touched-files cites).
- **event sourcing / MemGPT** → snapshot-over-log, recursive/hierarchical rehydration.
- **generative-agents reflection** → the demoted, optional lossy-summary tier (over a retained
  log, never as substrate — the claude-mem line).
- **claude-mem** → the negative example: what "summary as substrate + recency retrieval" costs.
