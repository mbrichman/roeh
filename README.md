# roeh

**Roeh** (רואה) — *the seer*. The one you go to consult.

A Claude Code plugin that gives a project an append-only **decision trace**, an **Oracle**
that answers *"why did we do X"* from that record with citations, and a **scribe** that
writes to it before compaction throws the reasoning away.

---

## The problem

A model that lives in a context window does not forget randomly. It forgets the
expensive, hard-won thing and keeps the cheap recent thing.

So the failure mode is not ignorance — it is **confident re-derivation**. A session
rebuilds an evaluation from scratch and reaches the opposite conclusion from the one
already on record. A PR re-implements something that exists. A settled dead-end gets
walked again, at full cost, because only the chosen option was ever written down and the
rejected one wasn't.

Memory indexes compact. Summaries summarise summaries. Commits record *what* changed and
almost never *why*. This plugin builds the durable layer beneath all of that.

## The three parts

| | What it does |
|---|---|
| **Ingestion** (`/roeh:ingest`) | Fans out reader agents over git history, memory files, docs and session transcripts — mining **inline comments and docstrings**, where the rationale actually lives — and assembles the trace. |
| **The Oracle** (`oracle` agent) | Reads the record — through a derived **map** and targeted reads once it outgrows a single pass — and answers "why", with citations. Escalates dead-ends and reversals. Says *"not recorded"* rather than inventing a rationale. Optionally a formal `VERDICT:` gate on changes. |
| **The scribe** (`scribe` agent) | The record's **sole writer**: distils decisions from evidence (always naming what was rejected) and can append, never rewrite. It doesn't decide *when* to run — the operations below do. |

**The scribe writes; the operations decide what it writes.** `/roeh:ingest` hands it the
whole history at bootstrap; `/roeh:refresh` hands it what's happened *since* (new commits,
unmined transcripts, changed memory files); the PreCompact gate hands it the current session
before compaction discards it. These aren't alternatives to the scribe — they're the triggers
that dispatch it, and it is the only thing that ever appends.

What sets **`/roeh:refresh`** apart from the other two is its second half, the **drift
check**. Ingest and the gate only ask *"what did this work decide?"* (forward: work →
record). Refresh also asks *"is what we already wrote still true?"* (backward: record →
world) — re-checking citations, comment-sourced entries and recorded numbers against the code
as it is *now*, and handing the scribe a `[CORRECTION]`, `[REVERSAL]` or `[GOTCHA]` for each
one that has moved. That backward pass is the harder, more valuable half, and it is why a
record needs refreshing even when no new work has landed: code drifts out from under a
citation that still looks valid.

## What ingest actually does

Most memory tooling is **prospective**: you install it, and it starts recording from that
moment. Everything that happened before — every constraint discovered the hard way, every
approach tried and abandoned, every "we chose X because Y" — stays lost. You get a record
that begins the day you decided you needed one, which is always months after the day you
actually needed one.

`/roeh:ingest` is **retrospective**. It reconstructs the record from evidence that already
exists in your repo, then hands it to the Oracle. On a three-week-old project that has
never had a memory layer, you end the first run with a cited history of how the thing got
this way.

### The sources, and why each one

| Source | What it yields | Why |
|---|---|---|
| **Commit messages** | The shape of the history: what changed, when, in what order. | Cheap and structured. But it tells you *what*, and usually not *why*. |
| **Diffs** | What the change actually did — the surfaces it touched, what moved. | A commit subject is a claim; the diff is the evidence. They disagree more often than anyone likes. |
| **Inline comments & docstrings** ⭐ | **The rationale.** Why-this-not-that, the constraint that forced it, the gotcha that bit someone. | This is the highest-yield source in the whole pass. See below. |
| **Session transcripts** (`.jsonl`) | Real-time reasoning, and the roads not taken — options weighed and rejected that never reached a commit at all. | The richest and most dangerous vein. Mined under the hall-of-mirrors rule below. |
| **Memory files** | Whatever the lossy index already holds, read in full rather than as one-line pointers. | Rehydration: recover the fidelity compaction threw away. |
| **Docs, specs, evals, scripts** | What each artifact *is*, why it exists, its gotchas. | So a future session never rediscovers the tool it already has. |

### Why the diff body, and especially the comments

**The commit message says what. The code comment says why.**

That instruction — *"when you're looking at commits and diffs I want you to be sure to
especially look at comments, that should contain a lot of the rationale"* — came from the
owner of the project roeh was generalised from, and it turned out to be one of the
highest-yield instructions in the whole archaeology. Codebases carry their reasoning
inline: the docstring that quotes a design ruling, the comment explaining why the obvious
approach doesn't work, the `# NOTE:` above a guard that exists because of an outage
nobody wrote up.

That material is **written at the moment of the decision**, by the person making it, with
the context still loaded — not reconstructed later from memory — and it is **attached to
the exact line it explains**, so it cites itself.

#### But comments go stale — and that shapes how they're read

This is the honest objection to the whole approach, and it is correct: humans change code
and leave the comment above it untouched, sometimes forever. A rationale that was true in
March can end up quietly describing something that no longer exists. Any tool that mines
comments naively will confidently report fiction.

Two things make this workable, and neither is a claim that the problem doesn't exist.

**Comments are read at their commit, never at HEAD.** Chapter agents use `git show <sha>`,
so they read the comment as it was written *when the change was made* — the one moment the
author wrote code and comment together and they were maximally in sync. Comment-sourced
claims are cited as **`file:line@sha`**: the pointer *and* the commit it was true at. That
turns a fragile claim about what the code does *now* into a durable claim about what was
believed *then*, which stays true regardless of what happened afterwards.

**Drift is the signal, not just the noise.** `/roeh:refresh` checks comment-sourced
entries first, precisely because they decay fastest, and sorts what it finds:

| Found | Means |
|---|---|
| Comment and code both unchanged | Entry is live. |
| **Code changed, comment did not** | The comment is stale — but the entry isn't wrong, it's *incomplete*. Something changed the code and nobody recorded it. That gets a `[REVERSAL]`, and the stale comment gets a `[GOTCHA]`. |
| Comment rewritten | Someone revised the rationale deliberately. Read it; `[CORRECTION]` if it contradicts. |

That middle row is the interesting one. **A comment that has drifted from its code is
usually an unrecorded decision**, which is the exact thing this tool exists to surface. The
staleness that makes comments unreliable as a live source makes them a useful tripwire as
a historical one.

**What this does not fix:** a comment that was wrong *when it was written*, or aspirational
("this will be replaced by…" — it never was). Nothing recovers that, and roeh will record
it faithfully as what someone believed at the time. Which is, at least, what it claims to
be recording.

One observation from using this in anger: **AI-written comments drift less**, because the
agent rewriting a function tends to rewrite its comment in the same pass. On a codebase
built substantially with a coding agent — increasingly the case, and roeh's likely home —
the source is fresher than the general reputation of code comments suggests. On a
decade-old human codebase, weight commit messages and transcripts higher.

### The hall-of-mirrors rule

Transcripts hold rationale nothing else does, and they are the one source that can poison
the record. Legitimate sources are **the owner's turns and the code**. The assistant's own
prose is the system's own emission — file that as history and the record starts feeding on
its own reflection, which every future session then reads back as fact.

So transcripts are distilled twice: strip tool I/O and meta events, then reduce to the
owner's turns with just enough surrounding context to read them. If a candidate learning
traces only to something an assistant said, it is dropped.

### How the pass runs

Adaptive. Commits are split into dated chapters of roughly 20–40 commits or one week,
whichever is denser, capped at 8 — plus memory-rehydration, artifact-index and
session-mining passes, all in parallel. Denser chapters mean higher fidelity, which is the
entire point; past ~8 the synthesis cost exceeds the marginal recall. A small repo
collapses to a single sequential pass, and `--quick` forces it.

Extraction agents run on `sonnet`; session mining — the one judgement pass — inherits the
session model (see [Models](#models)). Every agent carries a hard read-only-git guardrail, because an archaeology agent moving
`HEAD` out from under live work is a mistake this lineage has already made once.

The run declares its plan up front and marks units off as chapters land, so an ingest that
dies partway is a recorded fact rather than a trace that merely *looks* finished. See
[Running ingest twice](#running-ingest-twice).

## Design choices

Persistent memory for coding agents is a crowded space, and much of the work in it solves a
genuinely different problem well. These are the choices roeh makes — described as choices,
not claims to be first at any of them:

**Retrospective, not prospective.** A memory layer you install today tends to start
recording today, and everything before that stays lost. roeh's first act is to mine the
history you already have, so the record begins where the project did rather than where you
happened to adopt a tool.

**It reads the diff and the comments, not just the commit message.** A commit subject says
*what*; the reasoning more often sits in the diff body and the inline comments inside it.
roeh excavates that, which needs no change to how anyone already works.

**Provenance is enforced, not assumed.** Every claim carries a tag, a section and a SHA or
`file:line`. "The record does not cover this" is a supported answer, and the Oracle is
instructed to prefer it over a plausible reconstruction. The rule that only the owner's
decisions count — not the assistant's suggestions — is structural, not a matter of trust.

**Append-only, with supersession.** roeh never edits in place. A superseded decision gets a
`[REVERSAL]` beside it and a wrong number a `[CORRECTION]`, so the record shows what was
believed and when. The Oracle checks forward for supersession before quoting anything,
because in an append-only file the wrong answer is still sitting there reading as true.

**One file a human can read.** The record is markdown in your repo, diffable in review and
readable without the tool — not a vector store, a graph database or a cloud service. Past a
point it outgrows a single read, which is what the derived **map** and retrieval primitives
are for (below).

Some of this is common and some less so; the point is the combination, not any one part.
Gating compaction to force a save, for instance, is a shared instinct — roeh's own take is
to **not** block by default: it records what's owed and lets `/compact` proceed, because a
gate people find irritating is a gate they learn to route around.

## Install

**Requires:** Claude Code, `git`, and **Python 3.8+** on `PATH` as `python3`. No
third-party packages — `bin/roeh` runs inside hooks, where a missing import is a silent
failure at the worst possible moment. macOS ships a suitable `python3` once the Xcode
Command Line Tools are present (`xcode-select --install`).

Setup has **two levels**, and conflating them is the usual source of confusion: you
install the plugin **once per machine**, then enable it **per project**.

### 1. Once per machine

```bash
claude plugin marketplace add mbrichman/roeh
claude plugin install roeh@roeh
```

Restart Claude Code afterwards. A newly registered agent is not dispatchable until the
session restarts — edits to an already-registered one hot-reload, but the first install
needs the restart before you can consult the Oracle by name.

For development against a clone, point the marketplace at a **directory** instead. This
also works with no network, which matters when GitHub is having a bad day:

```bash
git clone https://github.com/mbrichman/roeh ~/projects/roeh
claude plugin marketplace add ~/projects/roeh
claude plugin install roeh@roeh
```

(`claude --plugin-dir ~/projects/roeh` also works, but only for sessions where you
remember the flag — and forgetting it silently disables the compaction gate at exactly
the moment you would want it.)

### 2. Once per project

> **`roeh` is not on your login shell PATH.** The plugin's `bin/` is added to the PATH of
> Claude Code's Bash tool while the plugin is enabled. So you run `roeh …` *from inside a
> Claude Code session*, not from your terminal. Everything below assumes you are in one.

```
cd ~/projects/whatever && claude
```

then:

```
/roeh:init        # asks where the trace lives; writes the config
/roeh:ingest      # builds the record from history — the expensive step
```

That is the whole per-project setup. `/roeh:init` is cheap and non-destructive;
`/roeh:ingest` fans out and costs real money on a long history, so it asks for a history
floor first and accepts `--quick` for a cheap look.

**Adding roeh to a project that already has a curated record?** Point `init` at it and
turn off automatic writes — see [read-only mode](#read-only-mode). Nothing is
regenerated, and no agent gets a write path.

### Updating

The harness handles the plugin itself — there is no `/roeh:update`, deliberately:

```bash
claude plugin marketplace update roeh   # refresh the marketplace (directory or GitHub)
claude plugin update roeh@roeh          # restart to apply
```

Note the `@marketplace` suffix on `update` — plain `claude plugin update roeh` fails with
`Plugin "roeh" not found`. If your marketplace is a local clone, `git pull` first; if it
is GitHub, `marketplace update` does the fetching.

What the harness does **not** handle is your *project's* artifacts. `claude plugin
update` moves the plugin; nothing migrates a `.claude/roeh.json` written by an older
version, or a trace that predates a change to the sections the agents depend on. A
half-migrated record is the worst failure available to a tool whose premise is that the
record can be trusted — so:

```
roeh doctor          # check this project against the running plugin
roeh doctor --fix    # apply the safe repairs
```

`doctor` checks the config schema version against the plugin, flags missing and
unrecognised keys, verifies the trace still has §0/§1/§3/§5 and a staleness ledger,
fails when the trace has outgrown a single read but has no **map** and warns when the map
has fallen behind it, notices a profile
drifting behind the trace, and catches two placement mistakes worth catching: a
`repo`-mode trace that is not actually tracked by git (append-only is then a promise,
not a property), and a `local`-mode trace sitting **inside** the repo, where one
`git add -A` publishes it.

`--fix` touches config and `.gitignore` only. **It never touches the trace** — repairing
an append-only record is a contradiction in terms. `SessionStart` surfaces `doctor`
failures automatically, but only failures: warnings on every session start are how a
check gets tuned out.

> **Harness gotcha:** a newly registered agent is not dispatchable until the session
> restarts. Edits to an *already-registered* definition hot-reload. So after a first
> install, restart before consulting the oracle by name.

## Where the trace lives

`/roeh:init` asks, and writes the answer to `.claude/roeh.json`.

- **`repo`** (default) — `docs/decision-trace.md`, committed. Versioned, diffable, backed
  up, readable by teammates and CI. Git makes append-only *provable* rather than
  promised.
- **`local`** — `~/.claude/projects/<slug>/memory/decision-trace.md`, never committed.
  For projects where the *rationale* holds material that must not enter git. Note the
  asymmetry: an append-only record of **why** is routinely more sensitive than the code
  it explains, because the code was written to be read and the reasoning was not.

## How it stays honest

The record is the one artifact everything else trusts, so the design is mostly about the
ways it could quietly start lying:

- **Append-only, structurally.** The scribe has no `Write` or `Edit` tool. `roeh append`
  opens in append mode and never seeks — rewriting an entry is not *expressible*. A
  superseded decision gets a new `[REVERSAL]` beside it; a wrong number gets a
  `[CORRECTION]`. What we believed and when is part of the record.
- **Assistant prose is never a source.** Mining the model's own summaries for "learnings"
  makes the record feed itself its own reflection, which every future session then reads
  back as fact. Sources are the owner's turns, the code, PR artifacts, and measurements.
- **Under-claim beats confabulate.** "The trace does not record a rationale for this" is
  a correct and valuable answer. A plausible-sounding invented *why* poisons everything
  downstream.
- **Supersession is checked before quoting.** In an append-only file a corrected claim
  still sits there reading as true. The Oracle scans forward for a later `[REVERSAL]` or
  `[CORRECTION]` before citing anything.
- **Staleness is surfaced, not assumed away.** A stale record is more dangerous than no
  record, because an answer sourced from it reads exactly like an answer sourced from a
  current one.

## Models

The two agents are pinned so an org default can't silently swap them; the fan-out
extraction runs cheap.

| Component | Model | Why |
|---|---|---|
| `oracle` | **`sonnet`** (pinned) | Its two hardest jobs fail *quietly*: noticing a later `[REVERSAL]` supersedes the entry it is about to quote, and refusing to supply a rationale the record does not contain. Pinned so an org default can't downgrade it without that showing in the output; Sonnet was judged sufficient here against Opus's cost and latency. |
| `scribe` | **`sonnet`** (pinned) | Dispatched unattended by the pre-compaction gate, writing to a file that cannot be cleaned up — a fabricated rationale is permanent, only supersedable. Pinned for the same reason as the oracle, and judged sufficient against the cost. |
| ingest chapter / memory / artifact passes | `sonnet` | Bounded extraction. The source text does the reasoning; the agent transcribes and cites it. The original archaeology ran six Sonnet agents and produced the trace this generalises. |
| ingest & refresh session mining | *inherits* | The one pass needing real judgement — what is *net-new* against a full trace, and the hall-of-mirrors rule on interleaved turns. Run the session on your strongest model when this matters. |
| refresh drift check | *inherits* | "Is this recorded claim still true" is judgement against evidence, not retrieval. |

The two agents are pinned by **alias**, not version, so they track the current Sonnet.

> **If your org pins Claude to a smaller model by default**, that is exactly why these
> two are pinned rather than inheriting — otherwise the Oracle and scribe are silently
> downgraded and you cannot tell from their output. If your org *restricts* rather than
> defaults, the pin may fail to resolve and the agents fall back; check that before
> relying on a `VERDICT:` as a gate.

## Hooks

| Event | Behaviour |
|---|---|
| `PreCompact` *(manual)* | Dispatches the scribe in RECORD mode to write what's owed, then lets compaction proceed — no interruption (the default). Opt into a hard block on a still-behind record with `precompact.block_manual: true` (`exit 2`); `ROEH_SKIP=1` bypasses that block. |
| `PreCompact` *(auto)* | Never blocks. Auto-compact fires when the window is already full; refusing it there can wedge the session. Injects a loud, evidence-bearing reminder instead. |
| `SessionStart` *(compact/clear/fork)* | Re-injects the trace pointer and **§5 RESUME STATE** verbatim. This is the half that makes an append-only record *work* — writing it is pointless if nothing reads it back. |
| `SessionStart` *(startup/resume)* | Cheap staleness line, plus the standing instruction to consult the oracle before re-deriving anything. |

### Read-only mode

For a project with a mature, hand-curated record that no unattended agent should append
to, set in `.claude/roeh.json`:

```json
"precompact": { "record": false, "block_manual": false, "nag_auto": true }
```

`record: false` withholds the sentinel the scribe reads, so the scribe still runs but
finds nothing pending and returns **draft** entries instead of writing them. You stay the
only writer. `roeh append` keeps working — the line is drawn at automation, not at
writing. `block_manual: false` stops roeh from blocking `/compact`, which matters if the
project already has its own compaction hook and you do not want two gates.

Hook handlers within one event have no documented execution order, so the design is
order-independent: the command hook drops a sentinel the scribe reads (`roeh pending`),
and if the scribe runs first, its `roeh append` makes the record current so the blocking
check passes. Either order is correct.

## CLI

Available inside a Claude Code session (see [above](#2-once-per-project)) — the plugin
puts `bin/` on the Bash tool's PATH, not your login shell's.

```
roeh init [--local] [--trace PATH]   write .claude/roeh.json
roeh config                          resolve effective paths
roeh status [--json]                 is the record behind the work?
roeh doctor [--fix]                  check artifacts against the running plugin

roeh map [--budget T]                regenerate <trace>-map.md + -bloom.json
roeh read <region | id | §N>         pull one control plane or entry, exactly
roeh scope "<query>"                 the regions a query's tokens drill into
roeh verify                          map freshness + chain integrity (6 stale / 7 tamper)

roeh record [-]                      APPEND one structured entry (JSON on stdin): id + edges + chain
roeh id [-]                          compute an entry's content-id, without writing
roeh append [file|-]                 APPEND raw text — the low-level write primitive
roeh sessions [--unmined]            this project's transcripts
roeh mark <session-id>               record a transcript as folded in
roeh ingest status|begin|done|end|abandon
                                     ingest lifecycle (see below)
roeh pending [--clear]               the PreCompact → scribe handshake
roeh slug [path]                     Claude Code project-directory slug
```

The middle group is what keeps the Oracle honest once the record outgrows a single read —
see [What happens when the trace outgrows a single
read](#what-happens-when-the-trace-outgrows-a-single-read).

## Running ingest twice

`/roeh:ingest` **asks before doing anything** when a trace already exists, because the
answer is usually not "ingest again":

- **already complete** → it offers `/roeh:refresh` first and recommends it. Refresh is
  what people actually want when they reach for a second ingest: new commits, unmined
  transcripts, changed memory files, plus the drift check. The other options are
  extending the floor to an *earlier* range, or a full re-ingest — and it says plainly
  what that last one costs, because **the trace is append-only, so a re-ingest cannot
  replace the old chapters, only append beside them.** A doubled history is worse than a
  thin one: the Oracle then holds two accounts and cannot tell which is live.
- **already running** → it stops. Starting a second fan-out over a live one double-writes.
- **abandoned partway** → it offers to *resume* the units that never landed, rather than
  re-mining history already in the file.

That last state is why the lifecycle exists. An ingest that dies at chapter 4 of 7
leaves a trace that reads exactly like a finished one — same sections, same voice,
silently missing whole ranges. The Oracle would then answer *"not recorded"* for
decisions that **are** recorded, just never mined, and sound exactly as confident as when
it is right. So a run declares its plan up front (`roeh ingest begin --plan …`), marks
units off as their chapters land, and refuses to close with work outstanding. `roeh
doctor` reports an abandoned or force-closed run as a **failure**, and `SessionStart`
surfaces it unprompted.

## Layout

```
roeh/
├── .claude-plugin/plugin.json
├── agents/{oracle,scribe}.md      invariant method; project specifics come from the profile
├── skills/{init,ingest,refresh}/  the operations
├── hooks/hooks.json               PreCompact + SessionStart
├── bin/roeh, roeh-precompact, roeh-sessionstart
└── templates/                     trace skeleton + profile template
```

The **profile** (`.claude/roeh-profile.md`, generated by ingest) is what makes the agents
project-aware without editing them: this project's vocabulary, its principles digest, and
the table of **live dead-ends** the Oracle leads with. The agent definitions hold only the
invariant method.

## Tests

Two tiers, split by what they cost.

**Deterministic** — the CLI, the hooks, and the read-path core. Free, fast, no model. Run
on every commit and in CI on Linux and macOS:

```bash
tests/run                                  # suite + manifest validation
python3 -m unittest discover -s tests -v
```

200 cases covering slug computation, init and its refusals, status, append and structured
`record`, the pre-compaction sentinel, the ingest lifecycle, `doctor`, both hooks, the
`map`/`read`/`scope`/`verify` read path, and structural checks on the shipped manifests.
Tests drive the CLI as a **subprocess**, because the
exit code *is* the contract — `PreCompact` blocking compaction is `exit 2` and nothing
else, and a test that imported the module would pass while the real integration was
broken.

`HOME` is sandboxed per test. roeh resolves transcripts, the memory directory and
`local`-mode traces through `~`, so without that the suite deposits directories in your
real `~/.claude` tree — an early version of it did exactly that.

**Prompt contracts** — the agents. Calls a model, so it costs money and is opt-in:

```bash
tests/eval-prompts               # all cases
tests/eval-prompts --case verdict
```

Each case asserts a *mechanical* property against a fixture trace, never a judgement
about answer quality — quality drifts with the model, but these contracts are what other
code depends on:

| Case | Contract |
|---|---|
| `verdict` | Gate mode opens with `VERDICT: <one of five words>` on line one. The single most-failed instruction in the Oracle, by its own docs. |
| `supersede` | A `[CORRECTION]`-superseded figure is not returned as current. The one way the Oracle actively misleads — and it arrives wearing citations. |
| `deadend` | A recorded `[DEAD-END]` is surfaced, not silently re-walked. |
| `notrecorded` | Silence is reported as silence rather than filled with a plausible rationale. |

`claude plugin eval` is the eventual home for this tier — it has graders, ablation
baselines and cost ceilings — but it is in early access at time of writing.

### Why this exists

Three real bugs shipped here before the suite did, and all three had the same shape: **a
guard that was written but never exercised.** `SCHEMA_VERSION` was stamped into every
config and never read back. `last_ingest` was declared in the state dict and never
written. `init --force` reset the config wholesale, silently downgrading a
sovereignty-critical `local` project to `repo` and orphaning its record.

The suite found a fourth on its first run: `status` counted a commit made in the *same
second* as the trace write as unrecorded, so a project read as "behind" the instant after
it was recorded — spuriously blocking `/compact`. Earlier manual checks had missed it
because they happened to include a `sleep 1`.

## What happens when the trace outgrows a single read

The record is append-only, so it only grows. Past roughly **1,500 lines or 400KB** it no
longer fits one comfortable read — and the naive fallback, grepping, is worse than it
looks: **you cannot grep for what you do not know to look for.** You get a confident
answer sourced from the two chapters you happened to match, with no sign of the entry
that overturns it. Silent, and indistinguishable from a complete answer.

So roeh gives the Oracle a derived **map** and retrieval primitives instead of an
instruction to be careful:

```bash
roeh map                   # fold the log into <trace>-map.md + -bloom.json
roeh verify                # is the map fresh + the chain intact? (6 stale / 7 tamper)
roeh scope "cascade"       # which REGIONS a query's tokens drill into, no false negatives
roeh read cascade          # pull one region (a sub control plane), exactly
roeh read <id>             # or one entry, with its live augments + conflicts (read-closure)
roeh read §5               # or one section (the LAST one, if superseded)
```

`roeh map` writes `<trace>-map.md`, the root **control plane**: a bounded digest of §0/§1/§5,
one line per LIVE entry, and a **ledger** of supersessions, conflicts, dead-ends and
uncertainties — because an entry is only live if nothing later overturns it, and that is the
list you check before quoting anything. It is a *collapsing projection*: retired and settled
regions collapse to headers and the whole thing is held under a token budget, so it stays a
comfortable read at any trace size. The Oracle reads its preamble/live/ledger in full, then
`roeh scope`s the question and `roeh read`s only the regions that matter. A per-region **bloom**
(`-bloom.json`) makes the literal drill set mechanically complete: no region holding a matching
token is ever missed.

`roeh verify` is the freshness gate — `6` if a projection input moved (regenerate with
`roeh map`), `7` if the entry chain no longer recomputes (tamper). Freshness hashes the log
*bytes*, so even an uncommitted append is correctly seen as stale. `roeh doctor` **fails** past
the threshold if no map exists, and warns if the map is older than the trace — the honest
signal that the Oracle is about to answer from a partial view.

The parser recognises both tag dialects — `- **[DECISION]**` and `` - `[DECISION]` `` — and
ignores `[[wikilinks]]`. Recognising only one dialect under-reports without saying so, which
for a map is the worst available failure: it looks complete.

## Limitations — read before trusting it

The record is an artifact built from evidence, and it inherits every weakness of that
evidence. Where it can mislead:

- **Comments go stale.** The big one, addressed at length
  [above](#but-comments-go-stale--and-that-shapes-how-theyre-read): mined at their commit
  rather than at HEAD, cited as `file:line@sha`, and re-checked by `/roeh:refresh`. But a
  comment that was wrong when written is recorded as written.

- **It records what was *believed*, not what was *true*.** A `[DECISION]` faithfully
  captures reasoning that may have been mistaken. That is the intended behaviour — you
  need to know why something was done in order to overturn it — but it means the trace is
  a history, not an oracle about reality. The Oracle's name is a joke about consulting it,
  not a claim about omniscience.

- **Garbage in.** A repo with `wip` commit messages, no comments and no docs yields a thin
  trace, and ingest cannot conjure rationale that was never written down anywhere. The
  first run's report tells you what it *couldn't* source — read that part.

- **Transcripts are filed by working directory.** If you work on a project from outside its
  own directory, its session transcripts sit under a different slug and session mining
  finds nothing. roeh has this problem about itself, recorded as an `[OPEN]` in its own
  trace.

- **The full read is on a clock.** Past roughly 1,500 lines or 400KB the record no longer
  fits one read. See [What happens when the trace outgrows a single
  read](#what-happens-when-the-trace-outgrows-a-single-read) — the Oracle reads through the
  **map** and targeted reads, not by grepping, and `roeh doctor` fails if the map is missing.

- **A first ingest on a large history costs real money.** Extraction runs on `sonnet` to
  keep it sane, but a year of commits is still a fan-out. `--quick` exists for a cheap
  first look.

- **The prompt layer is not deterministic.** `tests/eval-prompts` pins the mechanical
  contracts — the `VERDICT:` line, supersession, surfacing dead-ends, admitting silence —
  but the quality of any given answer depends on the model.

## License

MIT — see [LICENSE](LICENSE).

## Provenance

Generalised from a working system built for one project, where the trace was assembled by
six parallel archaeology agents over three weeks of history and then extended by mining
session transcripts. The design constraints here are that system's recorded lessons —
including the ones it learned the expensive way.
