#!/usr/bin/env python3
"""Acceptance check for pdd:archive — coverage, register integrity, deletion audit.

Mechanical half of the acceptance in SKILL.md. It reads `docs/history/` and the plans
that still exist, and answers five questions:

  1. is every plan on disk either covered by a record or excluded with a reason?
  2. is the register well formed — ids, subjects, dates, statuses, quoted reasons, commits?
  3. does the decision graph agree with the register, id for id?
  4. does the timeline account for every era the register cites?
  5. is every deleted plan recoverable at the commit the index names, and free of live references?

Usage:
    python3 check_history.py <project_root> [--render] [--quiet]

Exit 0 when no errors; 1 otherwise. Warnings never fail the run.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTER_ROW = re.compile(r"^\|\s*`?(D\d{3})`?\s*\|")
COVERAGE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")
HEX = re.compile(r"`?([0-9a-f]{7,40})`?")
CITE = re.compile(r"`?([A-Za-z0-9_@./\\-]+\.[A-Za-z0-9]+):(\d+)`?")
ERA = re.compile(r"\bE(\d{1,3})\b")
MERMAID = re.compile(r"```mermaid\s*\n(.*?)```", re.S)
DIAGRAM_TYPES = ("flowchart", "graph", "sequenceDiagram", "stateDiagram", "classDiagram", "erDiagram",
                 "gantt", "pie", "journey", "gitGraph", "requirementDiagram", "timeline", "mindmap",
                 "quadrantChart", "block-beta", "architecture-beta", "packet-beta", "radar-beta",
                 "kanban", "swimlane-beta", "treeView-beta", "xychart-beta", "sankey-beta", "C4Context")
STATUSES = {"accepted", "superseded", "unknown", "deleted", "archived", "excluded", "in_flight"}


def sh(cwd: str, *args: str) -> str:
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def read(path: str) -> str:
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def plans(root: str) -> list[dict]:
    out = sh(root, sys.executable, os.path.join(HERE, "find_plans.py"), root, "--json")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return []


def hex_in(cell: str) -> str:
    m = HEX.search(cell)
    return m.group(1) if m else ""


def split_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def check_register(text: str, errors: list[str], warnings: list[str]) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for line in text.splitlines():
        m = REGISTER_ROW.match(line)
        if not m:
            continue
        did = m.group(1)
        cells = split_cells(line)
        if len(cells) != 11:
            errors.append(f"{did}: {len(cells)} cells, the register has 11 (see decision-record.md §2.1)")
            continue
        (_id, subject, date, status, decided, rejected, because, evidence, source, commit, eras) = cells
        subject = subject.strip("`")
        status = status.strip("`").lower()
        rec = {"subject": subject, "status": status, "eras": ERA.findall(eras), "source": source.strip("`")}
        if did in rows:
            errors.append(f"{did}: duplicate id")
        rows[did] = rec
        if not subject:
            errors.append(f"{did}: empty subject — the conflict rule keys on it")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date) and date.lower() != "undated":
            errors.append(f"{did}: date must be YYYY-MM-DD or undated (got {date!r})")
        if status not in {"accepted", "superseded", "unknown"}:
            errors.append(f"{did}: status {status!r} is not one of accepted/superseded/unknown")
        if len(decided) < 12:
            errors.append(f"{did}: decided cell too short to be a decision")
        if len(rejected) < 8:
            errors.append(f"{did}: missing the rejected alternative — that is what makes it a decision")
        if '"' not in because and '"' not in because.replace("'", '"'):
            errors.append(f"{did}: because must quote the source, not paraphrase it")
        if not (CITE.search(because) or HEX.search(commit)):
            errors.append(f"{did}: because needs a path:line or the commit that carries it")
        if not CITE.search(evidence):
            errors.append(f"{did}: evidence must be `path:line` inside the plan")
        if not source:
            errors.append(f"{did}: no source plan")
        if not HEX.search(commit):
            errors.append(f"{did}: no commit — the citation would not survive the deletion")
        if not rec["eras"]:
            errors.append(f"{did}: no era — every decision belongs to a phase")
        if date.lower() == "undated":
            warnings.append(f"{did}: undated; it loses any conflict by rule (decision-record.md §4)")

    # the newest-wins rule, enforced: two accepted rows may not share a subject
    by_subject: dict[str, list[str]] = {}
    for did, rec in rows.items():
        if rec["status"] == "accepted":
            by_subject.setdefault(rec["subject"], []).append(did)
    for subject, ids in by_subject.items():
        if len(ids) > 1:
            errors.append(f"subject {subject!r} has {len(ids)} accepted rows ({', '.join(sorted(ids))}) — "
                          f"keep the newest and fold the older claim into its `conflict:` field")
    return rows


def check_graph(text: str, register: dict[str, dict], errors: list[str], warnings: list[str]) -> None:
    blocks = [b for b in MERMAID.findall(text)]
    if not blocks:
        errors.append("decisions.md has no mermaid block — the decision graph is part of the deliverable")
        return
    declared: set[str] = set()
    mentioned: set[str] = set()
    for graph in blocks:
        head = graph.strip().splitlines()[0].strip()
        if not head.startswith(("flowchart", "graph")):
            warnings.append(f"decisions.md graph starts with {head!r}; the decision graph is a flowchart")
        declared |= set(re.findall(r"^\s*(D\d{3})\s*\[", graph, re.M))
        mentioned |= set(re.findall(r"\b(D\d{3})\b", graph))
    undeclared = sorted(mentioned - declared)
    if undeclared:
        warnings.append("ids used in the graph without a labelled node: " + ", ".join(undeclared))
    missing = sorted(set(register) - declared)
    extra = sorted(declared - set(register))
    if missing:
        errors.append("register rows with no node in the decision graph: " + ", ".join(missing))
    if extra:
        errors.append("graph nodes with no register row: " + ", ".join(extra))


def check_timeline(text: str, register: dict[str, dict], errors: list[str], warnings: list[str]) -> None:
    eras = {e for rec in register.values() for e in rec["eras"]}
    if not text.strip():
        errors.append("timeline.md is missing or empty")
        return
    if "timeline" not in text:
        warnings.append("timeline.md has no mermaid timeline block")
    present = {f"{int(e):d}" for e in ERA.findall(text)}
    missing = sorted(eras - present, key=int)
    if missing:
        errors.append("eras cited by the register but absent from the timeline: "
                      + ", ".join("E" + m for m in missing))
    orphans = sorted(present - eras, key=int)
    if orphans:
        warnings.append("timeline eras with no decision citing them: " + ", ".join("E" + o for o in orphans))


def check_coverage(text: str, discovered: list[dict], register: dict[str, dict], root: str,
                   errors: list[str], warnings: list[str]) -> None:
    if not text.strip():
        errors.append("docs/history/index.md is missing")
        return
    rows: dict[str, dict] = {}
    for line in text.splitlines():
        m = COVERAGE_ROW.match(line)
        if not m:
            continue
        path = m.group(1).rstrip("/")
        cells = split_cells(line)
        if len(cells) < 8:
            warnings.append(f"index row for {path} has {len(cells)} cells; the template has 8")
        status = cells[5].strip("`").lower() if len(cells) > 5 else ""
        note = cells[7] if len(cells) > 7 else ""
        delete_commit = hex_in(cells[6]) if len(cells) > 6 else ""
        rows[path] = {"status": status, "note": note, "deleted_in": delete_commit}

    for plan in discovered:
        path = plan["path"].rstrip("/")
        if plan["flags"] and "template" in plan["flags"]:
            continue
        row = rows.get(path)
        if row is None:
            errors.append(f"plan not in the index: {path}")
            continue
        if row["status"] not in STATUSES:
            errors.append(f"{path}: status {row['status']!r} is not one of {sorted(STATUSES)}")
        if row["status"] in {"excluded", "in_flight", "archived"} and not row["note"].strip():
            errors.append(f"{path}: status {row['status']} needs a note saying why")
        if row["status"] == "deleted":
            deleted_rows.append((path, row))

    on_disk = {p["path"].rstrip("/") for p in discovered}
    for path in sorted(set(rows) - on_disk):
        if rows[path]["status"] != "deleted":
            warnings.append(f"index row with no plan on disk or in the inventory: {path}")

    # every row claiming deletion is audited, whether or not the plan is still inventoried:
    # after phase 4 the plan is gone from disk, so `discovered` no longer contains it.
    for path, row in sorted(rows.items()):
        if row["status"] != "deleted":
            continue
        if not row["deleted_in"]:
            errors.append(f"{path}: marked deleted with no deletion commit")
            continue
        # the deletion commit no longer contains the path, so recoverability is checked against
        # the newest commit that still did: any commit that added, modified, copied or renamed it.
        holder = sh(root, "git", "log", "--all", "--format=%H", "--diff-filter=AMCR", "--", path).split()
        holder = holder[0] if holder else ""
        blob = sh(root, "git", "ls-tree", "-r", "--name-only", holder, "--", path) if holder else ""
        if not (holder and blob.strip()):
            errors.append(f"{path}: not recoverable from any commit in the repository")
        removed = sh(root, "git", "log", "--all", "--format=%H", "--diff-filter=D", "--", path).split()
        if row["deleted_in"] not in removed:
            errors.append(f"{path}: {row['deleted_in']} is not a commit that deleted this path")
        if os.path.exists(os.path.join(root, path)):
            warnings.append(f"{path}: marked deleted but still present on disk")


def check_references(deleted: list[str], root: str, errors: list[str]) -> None:
    for path in deleted:
        out = sh(root, "git", "grep", "-n", "--fixed-strings", path, "--", "*.md",
                 ":!docs/history/*", ":!docs/history/**")
        for line in out.splitlines()[:5]:
            errors.append(f"live document still points at the deleted plan {path}: {line}")


def check_mermaid_blocks(root: str, render: bool, errors: list[str], warnings: list[str]) -> None:
    files = [os.path.join(root, "docs", "history", n)
             for n in ("index.md", "timeline.md", "decisions.md")]
    files += [os.path.join(root, "docs", "history", "eras", n)
              for n in (os.listdir(os.path.join(root, "docs", "history", "eras"))
                        if os.path.isdir(os.path.join(root, "docs", "history", "eras")) else [])]
    mmdc = shutil.which("mmdc") or (shutil.which("npx") and "npx")
    for f in files:
        if not os.path.isfile(f):
            continue
        for i, block in enumerate(MERMAID.findall(read(f)), 1):
            head = block.strip().splitlines()[0].strip() if block.strip() else ""
            if not head.startswith(DIAGRAM_TYPES):
                errors.append(f"{os.path.relpath(f, root)} block {i}: unknown diagram type {head[:30]!r}")
            if not render:
                continue
            if not mmdc:
                warnings.append("render skipped: no mmdc and no npx")
                return
            with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as fh:
                fh.write(block)
                tmp = fh.name
            cmd = ([mmdc, "-i", tmp, "-o", tmp + ".svg"] if mmdc != "npx"
                   else ["npx", "-y", "@mermaid-js/mermaid-cli", "-i", tmp, "-o", tmp + ".svg"])
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if proc.returncode != 0:
                tail = (proc.stderr or "").strip().splitlines()[-3:]
                errors.append(f"{os.path.relpath(f, root)} block {i} failed to render: {' | '.join(tail)[:200]}")
            for p in (tmp, tmp + ".svg"):
                if os.path.exists(p):
                    os.unlink(p)


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    root = os.path.abspath(args[0])
    render = "--render" in argv
    quiet = "--quiet" in argv
    hist = os.path.join(root, "docs", "history")

    errors: list[str] = []
    warnings: list[str] = []

    discovered = plans(root)
    register_text = read(os.path.join(hist, "decisions.md"))
    if not register_text.strip():
        errors.append("docs/history/decisions.md is missing")
    register = check_register(register_text, errors, warnings)
    check_graph(register_text, register, errors, warnings)
    check_timeline(read(os.path.join(hist, "timeline.md")), register, errors, warnings)
    index_text = read(os.path.join(hist, "index.md"))
    check_coverage(index_text, discovered, register, root, errors, warnings)
    check_mermaid_blocks(root, render, errors, warnings)

    # deleted plans: recoverability + no live references
    deleted: list[str] = []
    for line in index_text.splitlines():
        m = COVERAGE_ROW.match(line)
        if not m:
            continue
        cells = split_cells(line)
        if len(cells) > 5 and cells[5].strip("`").lower() == "deleted":
            deleted.append(m.group(1).rstrip("/"))
    check_references(deleted, root, errors)

    # every register row's source plan must be in the index
    indexed: set[str] = set()
    for line in index_text.splitlines():
        m = COVERAGE_ROW.match(line)
        if m:
            indexed.add(m.group(1).rstrip("/"))
    for did, rec in register.items():
        src = rec["source"].rstrip("/")
        if src and src not in indexed:
            warnings.append(f"{did}: source plan {src} has no row in the index")

    if not quiet:
        for e in errors:
            print(f"ERROR   {e}")
        for w in warnings:
            print(f"warn    {w}")
    print(f"plans: {len(discovered)}, register rows: {len(register)}, deleted: {len(deleted)}, "
          f"errors: {len(errors)}, warnings: {len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
