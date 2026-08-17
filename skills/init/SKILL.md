---
description: Set up roeh in this project — choose where the decision trace lives, write .claude/roeh.json, and create the trace skeleton and profile. Run once per project, before /roeh:ingest.
disable-model-invocation: true
---

# /roeh:init

Set this project up for a decision trace. Cheap and non-destructive; the expensive part
is `/roeh:ingest`, which comes after.

## 1. Decide placement — ask, don't assume

The one decision that matters, because it is annoying to change later:

**`repo` (default)** — trace at `docs/decision-trace.md`, committed. Versioned,
diffable, backed up, readable by teammates and CI, and git makes the append-only
property *provable* rather than promised. Right for almost every project.

**`local`** — trace at `~/.claude/projects/<slug>/memory/decision-trace.md`, never
committed. For projects whose *rationale* contains material that must not enter git:
real names of third parties, client confidences, bereavement or crisis content, anything
under an NDA. Note the asymmetry that motivates this mode — **an append-only record of
*why* is routinely more sensitive than the code it explains**, because the code was
written to be read and the reasoning was not.

Ask which one. If the answer is `local`, also confirm the owner understands there is no
backup and no sharing.

## 2. Write the config

```
roeh init            # repo mode
roeh init --local    # local mode
```

Then `roeh config` to show the resolved paths and confirm they look right.

## 3. Create the trace skeleton and the profile

Copy `${CLAUDE_PLUGIN_ROOT}/templates/decision-trace.skeleton.md` to the resolved
`trace_abs`, substituting `{{PROJECT}}`. Create the parent directory if needed.

Copy `${CLAUDE_PLUGIN_ROOT}/templates/profile.template.md` to the resolved
`profile_abs`, substituting `{{PROJECT}}`, `{{LOCAL_ONLY}}` and `{{GATE_ENABLED}}`. Fill
in what you can already tell from the repo (what the project is, where rationale hides);
leave the rest for `/roeh:ingest` to populate from evidence. **Do not invent principles
or dead-ends here** — an unearned entry in the profile is worse than an empty section,
because the oracle will lead with it.

If the trace already exists, stop and say so. Never overwrite a record.

## 4. Housekeeping

- **repo mode:** add `.claude/roeh-state.json` and `.claude/roeh-pending.json` to
  `.gitignore` — they are per-machine watermarks, not shared state.
- **local mode:** additionally confirm nothing under the resolved trace path is inside
  the repo.

## 5. Tell them what's next

Report the resolved paths, then: **`/roeh:ingest` builds the record from history.** Note
the harness gotcha — **a newly registered agent is not dispatchable until the session
restarts** (edits to an already-registered one hot-reload). So if `oracle` and `scribe`
were installed this session, `/roeh:ingest` works now but consulting the oracle by name
needs a restart.
