"""roeh v3 read-path core — step 1: tokenizer, parser, graph, liveness.

Pure functions over text passed in; no I/O of its own. **Stdlib-only and Python-3.8-parseable**
by contract (see docs/design/impl-read-path.md §0 fences: a hook that hits a missing import or a
3.9 SyntaxError fails silently — `d8098d3`, `12aa744`).

This is the consumer core the map/read commands are built on. Steps 2+ (regions/retirement,
bloom, recursive read, verify) layer on top; this module deliberately stops at liveness so it can
be unit-tested with no I/O, no git, and no model.
"""

import re
import hashlib
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple

# Bump when the normalization changes: the no-false-negative bloom guarantee (impl §2.4) holds
# only because map-side and query-side call THIS one function. A silent divergence would
# reintroduce literal false-negatives, so the version is part of the projection context.
TOKENIZER_VERSION = "1"

# An identifier joined by . _ or / is kept WHOLE, so `hooks/precompact.py` and
# `find_project_root` survive as single high-value literal tokens (their split parts are also
# emitted by _WORD below — more tokens only ever adds recall, never a false negative).
_IDENTIFIER = re.compile(r"[A-Za-z0-9]+(?:[._/][A-Za-z0-9]+)+")
_WORD = re.compile(r"[a-z0-9]+")

# Entry heads, both dialects: `- **[TAG]` and `` - `[TAG]` ``. Capture the tag word, allowing the
# internal hyphen of DEAD-END. `(?!\[)` keeps `[[wikilinks]]` from matching (the index's bug).
_ENTRY = re.compile(r"^[ \t]*[-*][ \t]+(\*\*|`)?\[(?!\[)([A-Z][A-Z0-9-]{1,18})")  # digits too ([V2],[M4]) (review #9)
_HEADING = re.compile(r"^#")
_FENCE = re.compile(r"^\s*```")
_META = re.compile(r"<!--\s*roeh\s+(.*?)\s*-->", re.S)
_FIELD = re.compile(r"^[ \t]*(Supersedes|Augments|Conflicts|Cites)\s*:\s*(.+?)\s*$", re.I | re.M)

TERMINAL = {"DEAD-END", "WITHDRAWN"}
OVERTURN_TAGS = {"REVERSAL", "CORRECTION"}


def tokenize(text: str):
    """The single canonical tokenizer (map and scope MUST both call this). Returns a set."""
    toks = set()
    for m in _IDENTIFIER.finditer(text):
        toks.add(m.group(0).lower())
    for w in _WORD.findall(text.lower()):
        if len(w) >= 3:
            toks.add(w)
    return toks


@dataclass
class Entry:
    id: str
    tag: str
    cls: str
    atomic: Optional[bool]
    date: str
    lead: str
    dialect: str
    line: int
    missing_id: bool = False
    dup_id: bool = False
    chain: str = ""
    cites: List[str] = field(default_factory=list)
    supersedes: List[str] = field(default_factory=list)
    augments: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    topic_hint: List[str] = field(default_factory=list)
    text: str = ""


def _split_list(v: str) -> List[str]:
    # Dedupe while preserving order: a field that lists the same id twice must not inflate the
    # supersession graph into a false "competing successor" (review finding #7).
    out = []
    for x in (p.strip() for p in v.split(",")):
        if x and x not in out:
            out.append(x)
    return out


def _strip_fences(block: str) -> str:
    # Drop fenced code so a `Supersedes:`/`Cites:`/`<!-- roeh -->` line shown as an EXAMPLE inside
    # an entry body is not parsed as a real edge or as the entry's identity (review round 2, #1).
    out, in_fence = [], False
    for l in block.splitlines():
        if _FENCE.match(l):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(l)
    return "\n".join(out)


_META_KV = re.compile(r"([\w-]+)=(.*?)(?=\s+[\w-]+=|\s*$)", re.S)


def _parse_meta(block: str) -> Dict[str, str]:
    # Parse `k=v` pairs where a value may contain spaces/commas (`topic-hint=alpha, beta`): each
    # value runs up to the next ` key=` or the end, so a spaced value is not truncated (review #3).
    m = _META.search(block)
    if not m:
        return {}
    return {k: v.strip() for k, v in _META_KV.findall(m.group(1))}


def _lead(head_line: str) -> str:
    # Strip bullet, then the `[TAG]` (with its optional ** / ` wrapper), then ALL bold/backtick
    # markup — otherwise a bold entry's closing `**` glues to the sentence period and the split
    # never fires, dragging the WHY clause into the lead (review finding #4).
    s = re.sub(r"^[ \t]*[-*][ \t]+", "", head_line)
    s = re.sub(r"^(\*\*|`)?\[[^\]]*\]", "", s)
    s = s.replace("**", "").replace("`", "").strip()
    return s.split(". ")[0][:90].rstrip(" .")


def _fenced_lines(text):
    """Line indices inside CLOSED ``` fence pairs. An UNCLOSED trailing fence contributes nothing —
    so a malformed/unclosed fence can never suppress structure past itself. Combined with
    fence-immune entry heads (below), no real entry is ever silently hidden (round-6 #1)."""
    lines = text.splitlines()
    fenced, open_at = set(), None
    for i, l in enumerate(lines):
        if _FENCE.match(l):
            if open_at is None:
                open_at = i
            else:
                fenced.update(range(open_at, i + 1))
                open_at = None
    return fenced


def parse_entries(text: str) -> List[Entry]:
    """Parse tagged entries (both dialects) with their hybrid metadata. Each entry spans from its
    head bullet to the next entry head or heading — but NOT to a `#` inside a fenced code block,
    which would otherwise sever the trailing metadata comment (review finding #6)."""
    lines = text.splitlines()
    heads = []
    # Entry heads are FENCE-IMMUNE: a code fence can never hide a real entry, so no entry is ever
    # silently dropped (round-6 #1). Headings, by contrast, are skipped inside a closed fence pair
    # so a fenced `# comment` doesn't sever an entry (round-2 #6). Unclosed fences suppress nothing.
    fenced = _fenced_lines(text)
    for i, ln in enumerate(lines):
        m = _ENTRY.match(ln)
        if m:
            heads.append((i, m))
        elif i not in fenced and _HEADING.match(ln):
            heads.append((i, None))
    entries = []
    for idx, (i, m) in enumerate(heads):
        if m is None:
            continue
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        block = "\n".join(lines[i:end])
        clean = _strip_fences(block)   # meta + fields read from the un-fenced text only
        meta = _parse_meta(clean)
        rels = {"supersedes": [], "augments": [], "conflicts": [], "cites": []}
        for fm in _FIELD.finditer(clean):
            # Accumulate across repeated/wrapped field lines, then dedupe — a second `Cites:` line
            # must not clobber the first (review finding #5).
            for v in _split_list(fm.group(2)):
                if v not in rels[fm.group(1).lower()]:
                    rels[fm.group(1).lower()].append(v)
        atomic = None
        if "atomic" in meta:
            atomic = meta["atomic"].lower() == "true"
        # A missing id must NOT collapse every such entry into one phantom node (review finding #1,
        # the trace's own worst failure). Assign a unique synthetic id and flag it loud.
        raw_id = meta.get("id", "")
        missing = not raw_id
        entries.append(Entry(
            id=raw_id or ("noid-L%d" % (i + 1)),
            tag=m.group(2),
            cls=meta.get("class", ""),
            atomic=atomic,
            date=meta.get("date", ""),
            chain=meta.get("chain", ""),
            lead=_lead(lines[i]),
            dialect="tick" if m.group(1) == "`" else ("bold" if m.group(1) == "**" else "plain"),
            line=i + 1,
            missing_id=missing,
            cites=rels["cites"],
            supersedes=rels["supersedes"],
            augments=rels["augments"],
            conflicts=rels["conflicts"],
            topic_hint=_split_list(meta.get("topic-hint", "")),
            text=block,
        ))
    counts = {}
    for e in entries:
        counts[e.id] = counts.get(e.id, 0) + 1
    for e in entries:
        if counts.get(e.id, 0) > 1:      # explicit duplicate id — disambiguate + flag loud (review #5)
            e.dup_id = True
            e.id = "%s~dupL%d" % (e.id, e.line)
    return entries


def _conflict(a: str, b: str, by_id: Dict[str, Entry]) -> bool:
    # Symmetric: an unresolved conflict is acknowledged if EITHER side declares it (review #2/§2.1).
    ea, eb = by_id.get(a), by_id.get(b)
    return bool((ea and b in ea.conflicts) or (eb and a in eb.conflicts))


def compute_liveness(entries: List[Entry]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Mechanical liveness over typed edges, with EVERY gap surfaced LOUD as 'uncertain' rather
    than silently resolved (impl §2.2). Returns (status, reasons) keyed by entry id.

    status ∈ {live, dead, uncertain}. 'uncertain' overrides for surfacing. Reasons accumulate —
    one entry can trip several gaps, and dropping any of them is the silent-failure this module
    exists to prevent (review finding #3)."""
    by_id = {e.id: e for e in entries}
    order = {e.id: e.line for e in entries}
    superseded_by: Dict[str, List[str]] = {}
    for e in entries:
        for t in e.supersedes:
            superseded_by.setdefault(t, []).append(e.id)

    status: Dict[str, str] = {}
    reasons: Dict[str, str] = {}
    uncertain: Dict[str, List[str]] = {}

    def flag(eid, msg):
        uncertain.setdefault(eid, []).append(msg)

    for e in entries:
        if e.missing_id:
            flag(e.id, "missing id (synthetic %s assigned)" % e.id)
        if e.dup_id:
            flag(e.id, "duplicate id (disambiguated)")
        for name, targets in (("supersedes", e.supersedes),
                              ("augments", e.augments),
                              ("conflicts", e.conflicts)):
            for t in targets:
                if t not in by_id:
                    flag(e.id, "dangling %s target %s" % (name, t))
                elif name != "conflicts" and order[t] >= order[e.id]:
                    flag(e.id, "%s target %s is not strictly earlier" % (name, t))
        if e.tag in OVERTURN_TAGS and not e.supersedes and not e.augments:
            flag(e.id, "prose-only supersession (no machine edge)")

    # Competing successors, evaluated PER successor (review #2): a successor is unresolved unless
    # it is symmetrically conflict-linked to another successor of the same target. So among three
    # successors where only two conflict, the lone third is still surfaced.
    for t, srcs in superseded_by.items():
        usrcs = list(dict.fromkeys(srcs))
        if len(usrcs) >= 2:
            for a in usrcs:
                if not any(_conflict(a, b, by_id) for b in usrcs if b != a):
                    flag(a, "competing successor of %s (unresolved)" % t)

    for e in entries:
        if e.tag in TERMINAL:   # `class` dropped (impl-write-path §2): terminal-ness is the tag's alone
            status[e.id], reasons[e.id] = "dead", "terminal"
        elif e.id in superseded_by:
            status[e.id] = "dead"
            reasons[e.id] = "superseded by " + ",".join(superseded_by[e.id])
        else:
            status[e.id] = "live"

    # Non-atomic entry superseded: dead, but surface it — this is where whole-entry supersession
    # can kill a co-located live claim. `atomic` is a PRODUCER assertion (impl-write-path §3.3): we
    # keep this sound check but NOT the old ≥2-clause-marker heuristic, which flagged every
    # well-formed five-part entry (WHY:+REJECTED:+GATES: = 3 markers) as UNCERTAIN and so eroded the
    # signal — a guard that fires on every valid entry is noise, not a guard.
    for t in superseded_by:
        et = by_id.get(t)
        if et and et.atomic is not True:
            flag(t, "non-atomic entry superseded (co-located live claim may be lost)")
    # Augment lost across a supersession (§2.2.2): B augments A, B superseded, and no superseder of
    # B restates `augments A` — A silently loses its augmentation unless we flag it (review #5).
    for e in entries:
        if e.id in superseded_by:
            for a in e.augments:
                if a in by_id and a not in superseded_by and not any(a in by_id[c].augments for c in superseded_by[e.id] if c in by_id):
                    flag(a, "augment lost: %s augmented it, then was superseded without restatement" % e.id)

    for i, msgs in uncertain.items():
        joined = "UNCERTAIN: " + "; ".join(msgs)
        reasons[i] = (reasons[i] + "; " + joined) if i in reasons else joined
        status[i] = "uncertain"
    return status, reasons


# ─── step 2: regions, retirement, and the token-budget map fold ────────────────

MAX_FANOUT = 12
_SEC_ANY = re.compile(r"^##(?!#)")


def _est_tokens(s: str) -> int:
    # The budget unit is estimated tokens, NOT lines (100 lines can be 5KB or 500KB — impl §2.3).
    return max(1, len(s) // 4)


def _threshold(as_of: str, D: int) -> str:
    try:
        return (date.fromisoformat(as_of) - timedelta(days=D)).isoformat()
    except ValueError:
        return as_of


def _toplevel(cite: str) -> Optional[str]:
    if "/" in cite:
        return cite.split("/", 1)[0]
    if re.search(r"\.[A-Za-z0-9]{1,8}$", cite):   # extension up to 8 chars so `.jsonl`/`.parquet` count
        return cite.rsplit(".", 1)[0]
    return None  # a bare SHA needs `git show --stat` to yield a path-topic (real trace, not fixture)


def assign_regions(entries: List[Entry]):
    """id -> {regions}; region -> [ids]. Path-topics (from cites) ∪ author topic-hints. An entry
    with neither is `unclassified` (which is always hot, never retired)."""
    id_regions, region_ids = {}, {}
    for e in entries:
        regs = set(e.topic_hint)
        for c in e.cites:
            tp = _toplevel(c)
            if tp:
                regs.add(tp)
        if not regs:
            regs = {"unclassified"}
        id_regions[e.id] = regs
        for r in regs:
            region_ids.setdefault(r, []).append(e.id)
    return id_regions, region_ids


def _live_inbound(entries, id_regions, status):
    inbound = {}
    for e in entries:
        if status.get(e.id) != "live":
            continue
        er = id_regions.get(e.id, set())
        for t in e.supersedes + e.augments + e.conflicts:
            for r in id_regions.get(t, ()):
                if r not in er:
                    inbound[r] = True
    return inbound


def _region_state(rids, by_id, status, as_of, D, modified_paths, has_live_inbound):
    ents = [by_id[i] for i in rids if i in by_id]
    if ents and all(status.get(e.id) == "dead" for e in ents):
        return "retired"                       # zero live/uncertain → fully historical
    has_live = any(status.get(e.id) == "live" for e in ents)
    newest = max((e.date for e in ents if e.date), default="")
    old_enough = bool(newest) and newest < _threshold(as_of, D)
    paths = set(c for e in ents for c in e.cites)
    stable = not (paths & set(modified_paths))
    if has_live and old_enough and stable and not has_live_inbound:
        return "settled"                       # dormant-but-live; collapses but stays reachable
    return "hot"


def _last_section_block(text, n):
    """The LAST `## §N` block — never the first. In an append-only file a section is superseded by
    appending a new copy, so the first §5 is the OLDEST (the recorded `roeh-sessionstart` bug).

    Fences are ignored for BOUNDARY detection (a fenced `## §5` must not become last-wins) but the
    returned bytes are the ORIGINAL section, fenced code intact — stripping content would be silent
    loss in a retrieval primitive (review #1)."""
    lines = text.splitlines()
    # `(?![\d.])` so `read §1` does not also match `## §1.2` or `## §12` (round-5 #2). Headings
    # inside a closed fence pair are skipped (a fenced `## §5` must not become last-wins); unclosed
    # fences suppress nothing, so a malformed fence can't hide a real section (round-6 #1).
    pat = re.compile(r"^##\s*(?:§\s*)?%s(?![\d.])" % re.escape(n))
    fenced = _fenced_lines(text)
    hits = [i for i, l in enumerate(lines) if i not in fenced and pat.match(l)]
    if not hits:
        return ""
    start = hits[-1]
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if j not in fenced and _SEC_ANY.match(lines[j]):
            end = j
            break
    return "\n".join(lines[start + 1:end])


def _first_content_line(block):
    for l in block.splitlines():
        if l.strip():
            return l.strip()
    return "(none)"


def _first_bullet(block):
    for l in block.splitlines():
        if l.lstrip().startswith("- "):
            return l.lstrip()[2:].strip()
    return "(none)"


def _preamble(text):
    princ = [_lead(l) for l in _last_section_block(text, "1").splitlines() if _ENTRY.match(l)]
    p1 = ", ".join(princ[:8]) + (" … read §1" if len(princ) > 8 else "")
    return "§0 %s · §1 %s · §5 %s" % (
        _first_content_line(_last_section_block(text, "0")),
        p1 or "(none)",
        _first_bullet(_last_section_block(text, "5")),
    )


def _digest(rids, by_id):
    joined = " ".join(by_id[i].lead for i in rids if i in by_id)
    return " ".join(sorted(tokenize(joined))[:8])


@dataclass
class MapModel:
    rendered: str
    fits: bool
    live_ids: set
    ledger_ids: set
    header_regions: set
    states: Dict[str, str]
    id_regions: Dict[str, set]
    region_ids: Dict[str, List[str]]
    collapsed: set
    blooms: Dict[str, dict] = field(default_factory=dict)
    projection_id: str = ""


def _group_regions(hdrs):
    """Group the header list when it exceeds MAX_FANOUT so the root's `## regions` never exceeds
    MAX_FANOUT lines. Returns None when no grouping is needed. Shared by the renderer AND by
    `read group:N`, so the two always agree (review #2)."""
    hdrs = sorted(hdrs)
    if len(hdrs) <= MAX_FANOUT:
        return None
    size = -(-len(hdrs) // MAX_FANOUT)
    return [hdrs[g:g + size] for g in range(0, len(hdrs), size)]


def _assemble(text, entries, by_id, status, reasons, id_regions, region_ids, states, collapsed,
              budget, collapse_ledger=False, pid="", note=""):
    expanded = {r for r in region_ids if states[r] == "hot" and r not in collapsed}
    header_regions = {r for r in region_ids if states[r] in ("retired", "settled")} | set(collapsed)

    def in_expanded(eid):
        return any(r in expanded for r in id_regions.get(eid, ()))

    live_lines, live_ids = [], set()
    ledger_lines, ledger_ids = [], set()
    for e in entries:
        st = status.get(e.id)
        terminal = e.tag in TERMINAL   # `class` dropped (impl-write-path §2)
        if st == "live" and in_expanded(e.id):
            live_ids.add(e.id)
            parts = []                                   # show ALL edges, not just the first (review #6)
            if e.supersedes:
                parts.append("↑" + ",".join(e.supersedes))
            if e.augments:
                parts.append("+" + ",".join(e.augments))
            if e.conflicts:
                parts.append("⚠" + ",".join(e.conflicts))
            edge = (" · " + " ".join(parts)) if parts else ""
            live_lines.append("- %s [%s] %s — %s%s" % (
                e.id, e.tag, ",".join(sorted(id_regions.get(e.id, ()))), e.lead, edge))
        elif st == "uncertain" or terminal or (st == "dead" and in_expanded(e.id)):
            # UNCERTAIN is ALWAYS surfaced — a settled/retired/collapsed region must NEVER hide a
            # liveness gap (the silent-resolution failure this module exists to prevent). Dead-ends
            # are always visible too (§6.3). Only plain-dead entries collapse into a cold header.
            ledger_ids.add(e.id)
            ledger_lines.append("- %s %s — %s" % (st.upper(), e.id, reasons.get(e.id, e.lead)))

    # Conflicts surface SYMMETRICALLY: an explicit `conflicts-with` becomes a ledger line visible
    # from either side, so a live tip can never hide that it is contradicted (review #1).
    seen_pairs = set()
    for e in entries:
        for c in e.conflicts:
            pair = tuple(sorted((e.id, c)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            ledger_lines.append("- CONFLICT %s ⚠ %s (unresolved)" % pair)
            ledger_ids.add(e.id)
            if c in by_id:
                ledger_ids.add(c)

    hdrs = sorted(header_regions)

    def region_hdr(r):
        rids = region_ids[r]
        L = sum(1 for i in rids if status.get(i) == "live")
        H = sum(1 for i in rids if status.get(i) == "dead")
        U = sum(1 for i in rids if status.get(i) == "uncertain")
        unc = " · %d unc" % U if U else ""
        return "- %s · %d live · %d hist%s · %s · «%s» · read %s" % (
            r, L, H, unc, states[r], _digest(rids, by_id), r)

    groups = _group_regions(hdrs)
    if groups is not None:
        region_lines = ["- group %s…%s · %d regions · read group:%d" % (g[0], g[-1], len(g), gi)
                        for gi, g in enumerate(groups)]
    else:
        region_lines = [region_hdr(r) for r in hdrs]

    # The ledger obeys the budget too: past its allocation it collapses to a manifest (`read
    # @ledger` drills it), so a flood of uncertain/dead-end entries can't push `fits` false — the
    # exit-3-unreachable invariant holds for realistic budgets (review #3).
    if collapse_ledger:
        ledger_render = ["- LEDGER collapsed: %d entries (uncertain/dead/conflict) — read @ledger"
                         % len(ledger_lines)]
    else:
        ledger_render = ledger_lines or ["(none)"]
    body = "\n".join(
        (["# roeh map — decision-trace   (region: ROOT)",
          "projection-id: %s   budget: %d tokens" % (pid, budget)]
         + ([note] if note else [])
         + ["", "## preamble", _preamble(text),
            "", "## live"]) + (live_lines or ["(none)"]) +
        ["", "## ledger"] + ledger_render +
        ["", "## regions"] + (region_lines or ["(none)"]))
    return body, live_ids, ledger_ids, header_regions


def build_map(text, budget_tokens=1500, D=180, as_of=None, modified_paths=frozenset(),
              topic_map="", repo_head="", m=None, k=None):
    """Deterministic fold: log text -> the root control plane, under a token budget maintained by
    collapsing regions (retired/settled are always headers; hot regions collapse largest-first
    when over budget). Same inputs -> identical bytes.

    `as_of` is the retirement 'now'; it defaults to today (never a frozen literal). Callers that
    need reproducibility pass it explicitly — it is part of the projection context (impl §2.0)."""
    if as_of is None:
        as_of = date.today().isoformat()
    if m is None:                          # BLOOM_* are defined later in the module (step 3)
        m = BLOOM_M
    if k is None:
        k = BLOOM_K
    pid = projection_id(text, budget_tokens, D, as_of, m, k, topic_map, repo_head)
    entries = parse_entries(text)
    status, reasons = compute_liveness(entries)
    by_id = {e.id: e for e in entries}
    # Legacy-trace diagnosis: if almost nothing carries a v3 id, say so ONCE, loudly, instead of a
    # ledger full of per-entry "missing id" lines — the map is telling you to run a clean ingest
    # (surfaced by dogfooding roeh's own pre-v3 trace).
    missing = sum(1 for e in entries if e.missing_id)
    note = ("⚠ %d/%d entries lack v3 metadata (no id) — this looks like a PRE-V3 trace; run a "
            "clean ingest and do not trust the map as-is." % (missing, len(entries))
            if entries and missing >= 0.8 * len(entries) else "")
    id_regions, region_ids = assign_regions(entries)
    inbound = _live_inbound(entries, id_regions, status)
    states = {r: ("hot" if r == "unclassified"      # unclassified is always hot, never retired
                  else _region_state(region_ids[r], by_id, status, as_of, D, modified_paths,
                                     inbound.get(r, False)))
              for r in region_ids}
    blooms = build_blooms(by_id, region_ids, m, k)
    hot_by_size = sorted(
        (r for r in region_ids if states[r] == "hot"),
        key=lambda r: (-sum(1 for i in region_ids[r] if status.get(i) == "live"), r))
    collapsed = set()
    collapse_ledger = bool(note)     # a pre-v3 flood collapses to one note + a ledger manifest (round-6 #5)
    while True:
        body, live_ids, ledger_ids, header_regions = _assemble(
            text, entries, by_id, status, reasons, id_regions, region_ids, states, collapsed,
            budget_tokens, collapse_ledger, pid, note)
        if _est_tokens(body) <= budget_tokens:
            return MapModel(body, True, live_ids, ledger_ids, header_regions,
                            states, id_regions, region_ids, collapsed, blooms, pid)
        remaining = [r for r in hot_by_size if r not in collapsed]
        if remaining:
            collapsed.add(remaining[0])
            continue
        if not collapse_ledger:
            collapse_ledger = True         # last resort before giving up: collapse the ledger
            continue
        return MapModel(body, False, live_ids, ledger_ids, header_regions,
                        states, id_regions, region_ids, collapsed, blooms, pid)


# ─── step 3: the per-region Bloom literal-existence index ──────────────────────
#
# The design's headline guarantee — literal recall is *complete* — rests entirely on this layer:
# a region's bloom is the OR of its entries' (and, once segmented, its children's) token bits, so
# a token present in ANY descendant sets every ancestor bit. Membership therefore has NO false
# negatives on descent (only false positives → extra reads). CRITICAL: `scope` and `build_blooms`
# BOTH tokenize via `tokenize()` — the guarantee is void if the two ever diverge (impl §2.4).
# Stdlib-only: bitset is a Python int; positions come from `hashlib.sha256` (no third-party lib).

HASH_VERSION = "sha256-1"
SCHEMA_VERSION = "v3"
RESOLVER_VERSION = "1"
BLOOM_M = 16384          # bits per filter — a recalibration knob once real-trace data exists
BLOOM_K = 7              # hashes (~1% FP at ~1.5k tokens)
SATURATION_FPR = 0.10    # a region above this MUST subdivide, or it becomes a drill-everything filter
SEGMENT_TOKENS = 500     # fixed segment granularity — a projection constant, so `region/N` is stable
                         # regardless of the display budget used to view it (review #7)


def _positions(token: str, m: int, k: int):
    out = []
    for i in range(k):
        h = hashlib.sha256(("%d:%s" % (i, token)).encode("utf-8")).digest()
        out.append(int.from_bytes(h[:8], "big") % m)
    return out


def bloom_of_tokens(tokens, m: int = BLOOM_M, k: int = BLOOM_K) -> int:
    b = 0
    for t in tokens:
        for p in _positions(t, m, k):
            b |= (1 << p)
    return b


def bloom_contains(b: int, token: str, m: int = BLOOM_M, k: int = BLOOM_K) -> bool:
    return all((b >> p) & 1 for p in _positions(token, m, k))


def _density(b: int, m: int) -> float:
    return bin(b).count("1") / m


def _fpr(density: float, k: int) -> float:
    return density ** k


def _region_token_set(rids, by_id):
    toks = set()
    for i in rids:
        if i in by_id:
            toks |= tokenize(by_id[i].text)   # full entry text → richest literal index
    return toks


def build_blooms(by_id, region_ids, m: int = BLOOM_M, k: int = BLOOM_K, F: float = SATURATION_FPR):
    """One filter per region — but a SATURATED region (fpr > F) is represented by its segment
    filters instead, each below F (or an irreducible singleton — one entry is a leaf, not a
    drill-everything trap), and its match-everything aggregate is NOT stored as queryable.
    This is what actually EXERCISES the saturation guard (review #4): a guard never called is not
    a guard. No false negatives either way, since a segment's bloom still ORs its tokens."""
    out = {}
    for r, rids in region_ids.items():
        toks = _region_token_set(rids, by_id)
        b = bloom_of_tokens(toks, m, k)
        d = _density(b, m)
        fpr = _fpr(d, k)
        if fpr > F and len(rids) > 1:
            for i, seg in enumerate(subdivide_for_saturation(rids, by_id, m, k, F)):
                st = _region_token_set(seg, by_id)
                sb = bloom_of_tokens(st, m, k)
                sd = _density(sb, m)
                out["%s/%d" % (r, i)] = {
                    "bloom": sb, "m": m, "k": k, "density": sd, "fpr": _fpr(sd, k),
                    "ntokens": len(st), "region": r, "segment": i,
                    "tokenizer": TOKENIZER_VERSION, "hash": HASH_VERSION}
        else:
            out[r] = {"bloom": b, "m": m, "k": k, "density": d, "fpr": fpr,
                      "ntokens": len(toks), "region": r,
                      "tokenizer": TOKENIZER_VERSION, "hash": HASH_VERSION}
    return out


def scope_literal(query: str, blooms) -> set:
    """Regions whose bloom matches ANY literal token of the query — the mechanically-complete
    literal drill set (no false negatives). Region-granular even when a region is stored as
    segments. Uses the SAME tokenizer as build_blooms."""
    hits = set()
    for t in tokenize(query):
        for bl in blooms.values():
            if bloom_contains(bl["bloom"], t, bl["m"], bl["k"]):
                hits.add(bl["region"])
    return hits


def subdivide_for_saturation(rids, by_id, m: int = BLOOM_M, k: int = BLOOM_K, F: float = SATURATION_FPR):
    """Chronologically halve a region until each segment's bloom FPR ≤ F (or is a singleton), so no
    filter saturates into a match-everything drill trap. Deterministic; returns a partition of rids."""
    ents = sorted((by_id[i] for i in rids if i in by_id), key=lambda e: (e.date, e.id))

    def fpr_of(sub):
        return _fpr(_density(bloom_of_tokens(_region_token_set([e.id for e in sub], by_id), m, k), m), k)

    def split(sub):
        if len(sub) <= 1 or fpr_of(sub) <= F:
            return [sub]
        mid = len(sub) // 2
        return split(sub[:mid]) + split(sub[mid:])

    return [[e.id for e in seg] for seg in split(ents)]


# ─── step 4: the recursive read / drill ────────────────────────────────────────
#
# `read` turns the map into the actual retrieval loop: resolve a selector to a section, an entry
# (with read-closure), a region (a sub control-plane), or a chronological segment of one. It fails
# CLOSED — an unresolvable selector is UNREADABLE — but distinguishes that from a recovered entry
# whose *provenance* can't be verified (an UNRESOLVED-PATH marker, still returned): you fail closed
# on the claim that needs the broken cite, never on retrieval of an intact entry (impl §4).


@dataclass
class ReadResult:
    kind: str                 # section | entry | region | unreadable
    selector: str
    rendered: str
    entry_id: str = ""
    augments: list = field(default_factory=list)    # live augments surfaced (read-closure)
    conflicts: list = field(default_factory=list)    # symmetric conflicts surfaced
    markers: list = field(default_factory=list)       # UNRESOLVED-PATH / UNVERIFIED


def _read_closure(eid, by_id, status):
    """Live augments of eid (transitively) + symmetric conflicts — surfaced BEFORE eid is cited,
    so a corrected value never comes back stale and a live tip never hides a contradiction."""
    aug_by = {}                                   # target -> [live augmenters], built once (linear)
    for e in by_id.values():
        if status.get(e.id) == "live":
            for a in e.augments:
                aug_by.setdefault(a, []).append(e.id)
    seen, frontier, augments = {eid}, [eid], []
    while frontier:
        cur = frontier.pop()
        for src in aug_by.get(cur, ()):
            if src not in seen:
                seen.add(src)
                augments.append(src)
                frontier.append(src)
    conflicts = set(by_id[eid].conflicts) if eid in by_id else set()
    for e in by_id.values():
        if eid in e.conflicts:                       # symmetric: inbound conflicts count too
            conflicts.add(e.id)
    return sorted(augments), sorted(conflicts)


def _chrono_segments(ents, seg_budget=SEGMENT_TOKENS):
    # Segment boundaries use the FIXED SEGMENT_TOKENS (a projection constant), NOT the caller's
    # display budget — so `region/N` indices are stable across reads (review #7).
    ents = sorted(ents, key=lambda e: (e.date, e.id))

    def size(sub):
        return _est_tokens("\n".join(e.text for e in sub))

    def split(sub):
        if len(sub) <= 1 or size(sub) <= seg_budget:
            return [sub]
        mid = len(sub) // 2
        return split(sub[:mid]) + split(sub[mid:])

    return [[e.id for e in s] for s in split(ents)]


def _region_cp_result(name, rids, by_id, status, reasons, budget, segmentable):
    ents = [by_id[i] for i in rids if i in by_id]
    live = [e for e in ents if status.get(e.id) == "live"]
    other = [e for e in ents if status.get(e.id) != "live"]
    full = "\n".join(
        ["# region %s   (%d entries)" % (name, len(ents)), "", "## live"]
        + (["- %s [%s] — %s" % (e.id, e.tag, e.lead) for e in live] or ["(none)"])
        + ["", "## ledger"]
        + (["- %s %s — %s" % ((status.get(e.id) or "dead").upper(), e.id, reasons.get(e.id, e.lead))
            for e in other] or ["(none)"]))
    if segmentable and _est_tokens(full) > budget and len(ents) > 1:
        segs = _chrono_segments(ents)
        body = "\n".join(
            ["# region %s   (%d entries, segmented)" % (name, len(ents)), "", "## segments"]
            + ["- %s/%d · %d entries · read %s/%d" % (name, i, len(s), name, i)
               for i, s in enumerate(segs)])
        return ReadResult("region", name, body)
    return ReadResult("region", name, full)


def read(text, selector, D=180, as_of=None, m=BLOOM_M, k=BLOOM_K,
         modified_paths=frozenset(), budget_tokens=1500, resolve_cite=None):
    """Resolve a selector against the log. Sub-region/segment reads inherit the SAME projection
    context (D/as_of/m/k AND budget/segment granularity) — segment boundaries use the fixed
    SEGMENT_TOKENS, so `region/N` is stable regardless of the display budget (impl §2.0)."""
    if as_of is None:
        as_of = date.today().isoformat()
    entries = parse_entries(text)
    by_id = {e.id: e for e in entries}
    status, reasons = compute_liveness(entries)
    _, region_ids = assign_regions(entries)
    sel = selector.strip()

    if sel.startswith("§"):
        blk = _last_section_block(text, sel.lstrip("§"))
        if not blk.strip():
            return ReadResult("unreadable", selector, "no section %s" % selector)
        return ReadResult("section", selector, blk)

    if sel.startswith("group:"):                      # drill a fan-out group (recursive & bounded, round-6 #6)
        try:
            path = [int(x) for x in sel[len("group:"):].split("/") if x != ""]
        except ValueError:
            return ReadResult("unreadable", selector, "bad group %r" % selector)
        cur = sorted(build_map(text, budget_tokens, D, as_of, modified_paths, m=m, k=k).header_regions)
        for idx in path:
            groups = _group_regions(cur)
            if groups is None or not (0 <= idx < len(groups)):
                return ReadResult("unreadable", selector, "no group %r" % selector)
            cur = groups[idx]
        sub = _group_regions(cur)     # if the reached level is STILL over MAX_FANOUT, sub-group it
        if sub is not None:
            body = ["# %s   (%d regions, grouped)" % (selector, len(cur)), "", "## groups"] + [
                "- group %s…%s · %d regions · read %s/%d" % (g[0], g[-1], len(g), selector, gi)
                for gi, g in enumerate(sub)]
        else:
            body = ["# %s   (%d regions)" % (selector, len(cur)), "", "## regions"] + [
                "- %s · read %s" % (r, r) for r in cur]
        return ReadResult("region", selector, "\n".join(body))

    if sel == "@ledger":                              # drill the full ledger (its manifest points here)
        L = ["# ledger (full)", ""]
        for e in entries:
            st = status.get(e.id)
            if st in ("uncertain", "dead") or e.tag in TERMINAL:
                L.append("- %s %s — %s" % ((st or "dead").upper(), e.id, reasons.get(e.id, e.lead)))
        seen = set()
        for e in entries:
            for c in e.conflicts:
                p = tuple(sorted((e.id, c)))
                if p not in seen:
                    seen.add(p)
                    L.append("- CONFLICT %s ⚠ %s (unresolved)" % p)
        return ReadResult("region", "ledger", "\n".join(L))

    if sel in by_id:
        e = by_id[sel]
        augs, cfls = _read_closure(sel, by_id, status)
        markers = ["UNRESOLVED-PATH " + c for c in e.cites if resolve_cite and not resolve_cite(c)]
        L = ["# entry %s [%s]  (%s)" % (e.id, e.tag, status.get(e.id)), e.lead]
        if e.cites:
            L.append("cites: " + ", ".join(e.cites))
        if augs:
            L.append("live augments (read-closure): " + ", ".join(augs))
        if cfls:
            L.append("conflicts (unresolved): " + ", ".join(cfls))
        if reasons.get(sel):
            L.append("note: " + reasons[sel])
        if markers:
            L.append("markers: " + "; ".join(markers))
        L += ["", e.text]
        return ReadResult("entry", selector, "\n".join(L), entry_id=sel,
                          augments=augs, conflicts=cfls, markers=markers)

    if "/" in sel:                                   # region/segment
        base, _, si = sel.partition("/")
        rids = region_ids.get(base)
        if not rids:
            return ReadResult("unreadable", selector, "no region %r" % base)
        segs = _chrono_segments([by_id[i] for i in rids if i in by_id])
        try:
            idx = int(si)
        except ValueError:
            return ReadResult("unreadable", selector, "bad segment %r" % selector)
        if not (0 <= idx < len(segs)):
            return ReadResult("unreadable", selector, "no segment %r" % selector)
        return _region_cp_result(selector, segs[idx], by_id, status, reasons, budget_tokens, False)

    if sel in region_ids:
        return _region_cp_result(sel, region_ids[sel], by_id, status, reasons, budget_tokens, True)

    return ReadResult("unreadable", selector, "no section, entry, or region matching %r" % selector)


# ─── step 5: projection-id (freshness / T0) and chain integrity (tamper) ───────
#
# The map is a cache; the log is the authority. The read path must REFUSE a map that no longer
# matches its inputs (the stale-projection race the reviews flagged). Freshness is a single
# projection-id: hash every input the fold depends on. Tampering is a separate chain check.


def projection_id(text, budget, D, as_of, m=BLOOM_M, k=BLOOM_K, topic_map="", repo_head=""):
    """The immutable context a map was folded under. Freshness (T0) = recompute and compare. The
    log component hashes the EXACT log bytes — NOT git HEAD — so even an uncommitted EOF append
    moves it and the map is correctly seen as stale (impl §2.0)."""
    log_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    tm_hash = hashlib.sha256(topic_map.encode("utf-8")).hexdigest()[:16]
    payload = "|".join(str(x) for x in [
        log_hash, tm_hash, repo_head, budget, D, as_of, m, k, SEGMENT_TOKENS,
        TOKENIZER_VERSION, HASH_VERSION, RESOLVER_VERSION, SCHEMA_VERSION])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def verify(model, text, budget, D, as_of, m=BLOOM_M, k=BLOOM_K, topic_map="", repo_head=""):
    """T0 freshness gate: (0, 'fresh') if the map still matches its inputs, else (6, 'stale …').
    The CLI `roeh verify` runs this AND `verify_chain`; the read path must refuse a stale map."""
    if projection_id(text, budget, D, as_of, m, k, topic_map, repo_head) != model.projection_id:
        return (6, "stale: projection inputs changed since the map was built")
    return (0, "fresh")


def chain_link(prev: str, eid: str) -> str:
    """One tamper-evidence link: chain_i = H(prev ‖ NUL ‖ id_i)[:16]. The SINGLE source of the
    chain formula — `_expected_chains` (verify) and the write path (`roeh record`, which stamps a
    new entry's chain) both call this, so a producer and the verifier can never drift."""
    return hashlib.sha256((prev + "\x00" + eid).encode("utf-8")).hexdigest()[:16]


def _expected_chains(entries):
    out, prev = {}, ""
    for e in entries:
        prev = chain_link(prev, e.id)
        out[e.id] = prev
    return out


def verify_chain(entries):
    """Tamper check over the id chain (chain_i = H(prev_chain ‖ id_i)): (0, 'intact') or (7, …).
    Meaningful only where chains are real (the write path stamps them); an entry with no chain is
    skipped rather than falsely flagged. NOTE the anchoring caveat (impl §11): a chain an attacker
    can recompute end-to-end needs an external signed head to be truly tamper-evident."""
    exp = _expected_chains(entries)
    for e in entries:
        if e.chain and e.chain != exp[e.id]:
            return (7, "chain break at %s" % e.id)
    return (0, "intact")
