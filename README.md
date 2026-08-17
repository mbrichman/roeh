# roeh

**רואה** — *the seer.* The one you go to consult.

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
| **The Oracle** (`oracle` agent) | Reads the record in full and answers "why", with citations. Escalates dead-ends and reversals. Says *"not recorded"* rather than inventing a rationale. Optionally a formal `VERDICT:` gate on changes. |
| **The scribe** (`scribe` agent + PreCompact hook) | Writes what the work owes the record — automatically, at the moment compaction would otherwise discard it. |

Plus **reconciliation** (`/roeh:refresh`): folds in new commits, unmined transcripts and
changed memory files, *and* checks whether what's already written is still true.

## Install

```bash
git clone <this repo> ~/projects/roeh
claude --plugin-dir ~/projects/roeh
```

Then, in your project:

```
/roeh:init        # choose where the trace lives; write config + skeleton
/roeh:ingest      # build the record from history
```

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

Deliberate, and split along one line: **judgement is pinned, extraction is cheap.**

| Component | Model | Why |
|---|---|---|
| `oracle` | **`opus`** (pinned) | Its two hardest jobs fail *quietly*: noticing a later `[REVERSAL]` supersedes the entry it is about to quote, and refusing to supply a rationale the record does not contain. A gate that fails softly is worse than no gate. |
| `scribe` | **`opus`** (pinned) | Dispatched unattended by the pre-compaction gate, writing to a file that cannot be cleaned up. A fabricated rationale is permanent — only supersedable, after the Oracle has already cited it. |
| ingest chapter / memory / artifact passes | `sonnet` | Bounded extraction. The source text does the reasoning; the agent transcribes and cites it. The original archaeology ran six Sonnet agents and produced the trace this generalises. |
| ingest & refresh session mining | *inherits* | The one pass needing real judgement — what is *net-new* against a full trace, and the hall-of-mirrors rule on interleaved turns. |
| refresh drift check | *inherits* | "Is this recorded claim still true" is judgement against evidence, not retrieval. |

The two agents are pinned by **alias**, not version, so they track the current Opus.

> **If your org pins Claude to a smaller model by default**, that is exactly why these
> two are pinned rather than inheriting — otherwise the Oracle and scribe are silently
> downgraded and you cannot tell from their output. If your org *restricts* rather than
> defaults, the pin will fail to resolve and the agents fall back; check that before
> relying on a `VERDICT:` as a gate.

## Hooks

| Event | Behaviour |
|---|---|
| `PreCompact` *(manual)* | Dispatches the scribe in RECORD mode to write what's owed. Blocks compaction (`exit 2`) if the record is still behind — you typed `/compact`, so there is room to record first. Bypass with `ROEH_SKIP=1`. |
| `PreCompact` *(auto)* | Never blocks. Auto-compact fires when the window is already full; refusing it there can wedge the session. Injects a loud, evidence-bearing reminder instead. |
| `SessionStart` *(compact/clear/fork)* | Re-injects the trace pointer and **§5 RESUME STATE** verbatim. This is the half that makes an append-only record *work* — writing it is pointless if nothing reads it back. |
| `SessionStart` *(startup/resume)* | Cheap staleness line, plus the standing instruction to consult the oracle before re-deriving anything. |

Hook handlers within one event have no documented execution order, so the design is
order-independent: the command hook drops a sentinel the scribe reads (`roeh pending`),
and if the scribe runs first, its `roeh append` makes the record current so the blocking
check passes. Either order is correct.

## CLI

```
roeh init [--local] [--trace PATH]   write .claude/roeh.json
roeh config                          resolve effective paths
roeh status [--json]                 is the record behind the work?
roeh append [file|-]                 APPEND to the trace (the only write path)
roeh sessions [--unmined]            this project's transcripts
roeh mark <session-id>               record a transcript as folded in
roeh pending [--clear]               the PreCompact → scribe handshake
roeh slug [path]                     Claude Code project-directory slug
```

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

## Provenance

Generalised from a working system built for one project, where the trace was assembled by
six parallel archaeology agents over three weeks of history and then extended by mining
session transcripts. The design constraints here are that system's recorded lessons —
including the ones it learned the expensive way.
