#!/usr/bin/env python3
"""Acceptance check for pdd:study — resolve every citation, table row and index entry.

Mechanical half of the acceptance in SKILL.md §3: the file's shape, the table's
shape, every `file:line` the study claims, the mermaid/table agreement, the
provenance block, and the root index's coverage. Judgement (is the behaviour
description true, does the row pass the observability test) is not checkable
here and is not attempted.

Usage:
    python3 check_agents_md.py <project_root> [--stale] [--render] [--root-only] [--quiet]

Exit code 0 when no errors were found; 1 when at least one was.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

MARK_BEGIN = "<!-- study:begin -->"
MARK_END = "<!-- study:end -->"
REQUIRED_HEADINGS = ["Scope", "Entry points", "Branches", "Selection paths", "Verify", "Provenance"]
SKIP_DIRS = {".git", "node_modules", "target", "dist", "build", "out", ".venv", "venv",
             "__pycache__", ".next", ".mypy_cache", ".pytest_cache", ".turbo", "vendor"}

CITE = re.compile(r"`([A-Za-z0-9_@./\\-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`")
CITE_LOOSE = re.compile(r"([A-Za-z0-9_@./\\-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?")
PROVENANCE = re.compile(r"generated:\s*`?([0-9a-f]{7,40})`?\s*@\s*`?(\d{4}-\d{2}-\d{2})`?")
BRANCH_ROW = re.compile(r"^\|\s*`?B(\d+)`?\s*\|")
NESTED_REF = re.compile(r"([A-Za-z0-9_@./\\-]+)/AGENTS\.md")
MERMAID = re.compile(r"```mermaid\s*\n(.*?)```", re.S)


def find_agents(root: str) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        if "AGENTS.md" in filenames:
            out.append(os.path.join(dirpath, "AGENTS.md"))
    return sorted(out)


def split_block(text: str) -> str | None:
    start = text.find(MARK_BEGIN)
    end = text.find(MARK_END)
    if start == -1 or end == -1 or end < start:
        return None
    return text[start:end]


def resolve(path: str, from_dir: str, root: str) -> str | None:
    for base in (from_dir, root):
        candidate = os.path.normpath(os.path.join(base, path))
        if os.path.isfile(candidate):
            return candidate
    return None


def check_citation(site: str, from_dir: str, root: str) -> str | None:
    m = CITE_LOOSE.search(site)
    if not m:
        return "site is not a `path:line`"
    rel, line_s, line_e = m.group(1), m.group(2), m.group(3)
    target = resolve(rel, from_dir, root)
    if not target:
        return f"cited file does not exist: {rel}"
    try:
        with open(target, encoding="utf-8", errors="replace") as fh:
            total = sum(1 for _ in fh)
    except OSError as exc:
        return f"cannot read {rel}: {exc}"
    hi = int(line_e or line_s)
    if not (1 <= int(line_s) <= hi <= total):
        return f"line out of range: {rel}:{line_s}" + (f"-{line_e}" if line_e else "")
    return None


def check_mermaid(block: str, branch_ids: set[str]) -> list[str]:
    errs: list[str] = []
    blocks = MERMAID.findall(block)
    if not blocks:
        return ["no ```mermaid block"]
    seen_ids: dict[str, str] = {}
    declared: set[str] = set()
    for i, graph in enumerate(blocks, 1):
        head = graph.strip().splitlines()[0].strip() if graph.strip() else ""
        if not re.match(r"^(flowchart|graph)\s+(TD|TB|LR|RL|BT)\b", head):
            errs.append(f"mermaid block {i} does not start with flowchart/graph + direction")
        for node_id, open_br, label in re.findall(
            r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*(\[|\{|\(\()\s*\"?(.*?)\"?\s*(?:\]|\}|\)\)|\))\s*$",
            graph, re.M,
        ):
            if not label:
                continue
            if node_id in seen_ids and seen_ids[node_id] != label:
                errs.append(f"node {node_id} declared twice with different labels")
            seen_ids[node_id] = label
            declared.update(re.findall(r"\bB(\d+)\b", label))
    missing = sorted(branch_ids - declared)
    extra = sorted(declared - branch_ids)
    if missing:
        errs.append("branch rows with no terminal in the graph: " + ", ".join("B" + m for m in missing))
    if extra:
        errs.append("graph terminals with no table row: " + ", ".join("B" + e for e in extra))
    if not re.search(r"--\s*\"?[^\n|]+?", block) and "-->" not in block:
        errs.append("no labelled edges: every edge must carry its predicate outcome")
    return errs


def check_file(path: str, root: str, stale: bool, render: bool) -> tuple[list[str], list[str], bool]:
    errors: list[str] = []
    warnings: list[str] = []
    rel = os.path.relpath(path, root)
    from_dir = os.path.dirname(path)
    text = open(path, encoding="utf-8", errors="replace").read()
    block = split_block(text)
    if block is None:
        return errors, ["no study block (human-written file; not checked)"], False

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"^##\s+{re.escape(heading)}\s*$", block, re.M):
            errors.append(f"missing section: ## {heading}")
    if not re.search(r"^##\s+Nested package roots\s*$", block, re.M):
        warnings.append("no ## Nested package roots section")

    rows = [line for line in block.splitlines() if BRANCH_ROW.match(line)]
    branch_ids: set[str] = set()
    table_sites: set[tuple[str, str]] = set()
    if not rows:
        errors.append("no branch rows (| B01 | … |)")
    for line in rows:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        row_match = BRANCH_ROW.match(line)
        if row_match is None:      # guarded by the filter above; kept for the type checker
            continue
        bid = "B" + row_match.group(1)
        branch_ids.add(bid[1:])
        if len(cells) != 7:
            errors.append(f"{bid}: {len(cells)} cells, the schema has 7")
            continue
        _, _, behaviour, trigger, site, example, _notes = cells
        if len(behaviour) < 8:
            errors.append(f"{bid}: behaviour cell too short to be an observable outcome")
        if len(trigger) < 4:
            errors.append(f"{bid}: trigger cell empty — quote the predicate")
        if len(example) < 4:
            errors.append(f"{bid}: no example input")
        problem = check_citation(site, from_dir, root)
        site_match = CITE_LOOSE.search(site)
        if site_match:
            table_sites.add((site_match.group(1), site_match.group(2)))
        if problem:
            errors.append(f"{bid}: {problem}")

    # every loose citation anywhere in the block must resolve too (table sites are done above)
    for rel_path, line_s, _line_e in {c for c in CITE.findall(block)}:
        if (rel_path, line_s) in table_sites:
            continue
        problem = check_citation(f"{rel_path}:{line_s}", from_dir, root)
        if problem:
            errors.append(f"citation {rel_path}:{line_s}: {problem}")

    errors += check_mermaid(block, branch_ids)

    prov = PROVENANCE.search(block)
    if not prov:
        errors.append("no provenance block (`generated: <commit> @ <date>`)")

    for nested in set(NESTED_REF.findall(block)):
        if not resolve(os.path.join(nested, "AGENTS.md"), from_dir, root):
            errors.append(f"nested reference to a missing file: {nested}/AGENTS.md")

    if stale and prov:
        head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        if head and not head.startswith(prov.group(1)):
            changed = subprocess.run(
                ["git", "-C", root, "diff", "--name-only", f"{prov.group(1)}..HEAD", "--", from_dir],
                capture_output=True, text=True).stdout.strip().splitlines()
            note = f"stale: recorded {prov.group(1)[:8]}, HEAD {head[:8]}"
            note += f", {len(changed)} file(s) changed under this unit" if changed else ", unit untouched"
            warnings.append(note)

    if render:
        mmdc = shutil.which("mmdc") or (shutil.which("npx") and "npx")
        if not mmdc:
            warnings.append("render skipped: no mmdc and no npx")
        else:
            for i, graph in enumerate(MERMAID.findall(block), 1):
                with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as fh:
                    fh.write(graph)
                    tmp_in = fh.name
                tmp_out = tmp_in + ".svg"
                cmd = ([mmdc, "-i", tmp_in, "-o", tmp_out] if mmdc != "npx"
                       else ["npx", "-y", "@mermaid-js/mermaid-cli", "-i", tmp_in, "-o", tmp_out])
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode != 0:
                    errors.append(f"mermaid block {i} failed to render: {proc.stderr.strip()[:200]}")
                for f in (tmp_in, tmp_out):
                    if os.path.exists(f):
                        os.unlink(f)
    return errors, warnings, True


def check_root(root: str, studied: list[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    root_file = os.path.join(root, "AGENTS.md")
    if not os.path.isfile(root_file):
        return ["no root AGENTS.md — the index is part of the deliverable"], warnings
    text = open(root_file, encoding="utf-8", errors="replace").read()
    if MARK_BEGIN in text:
        # scanning a unit directory: its AGENTS.md is a unit file, not an index
        return [], ["AGENTS.md here is a studied unit, not an index — index coverage not checked"]
    named = set()
    for nested in NESTED_REF.findall(text):
        named.add(os.path.normpath(nested + "/AGENTS.md"))
        if not resolve(os.path.join(nested, "AGENTS.md"), root, root):
            errors.append(f"root index names a missing file: {nested}/AGENTS.md")
    for rel in studied:
        if os.path.normpath(rel) not in named:
            errors.append(f"root index does not name {rel}")
    if not re.search(r"^##\s+", text, re.M):
        warnings.append("root AGENTS.md has no sections; is it an index?")
    return errors, warnings


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    root = os.path.abspath(args[0])
    stale = "--stale" in argv
    render = "--render" in argv
    quiet = "--quiet" in argv

    files = find_agents(root)
    total_err = 0
    total_warn = 0
    studied: list[str] = []
    root_file = os.path.normpath(os.path.join(root, "AGENTS.md"))
    for path in files:
        if os.path.normpath(path) == root_file:
            text = open(path, encoding="utf-8", errors="replace").read()
            if MARK_BEGIN not in text:
                continue                  # a plain index: check_root judges it, not the unit checks
        errors, warnings, has_block = check_file(path, root, stale, render)
        rel = os.path.relpath(path, root)
        if has_block:
            studied.append(rel)
        total_err += len(errors)
        total_warn += len(warnings)
        if not quiet and (errors or warnings):
            print(f"\n=== {rel}")
            for e in errors:
                print(f"  ERROR   {e}")
            for w in warnings:
                print(f"  warn    {w}")
    if "--root-only" not in argv:
        errors, warnings = check_root(root, studied)
        total_err += len(errors)
        total_warn += len(warnings)
        for e in errors:
            print(f"\n=== AGENTS.md (root)\n  ERROR   {e}")
        for w in warnings:
            print(f"\n=== AGENTS.md (root)\n  warn    {w}")

    print(f"\nfiles: {len(files)}, studied: {len(studied)}, errors: {total_err}, warnings: {total_warn}")
    return 1 if total_err else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
