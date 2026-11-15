#!/usr/bin/env python3
"""Recon for pdd:archive — inventory the plan artefacts that exist on disk.

Format-agnostic on purpose. Plan artefacts in a real repository come in every shape:
a current `plans/<name>/PRD.md`, an older `.plan/` pile of propositions and proof
pairs, a single `docs/plan/2025-q3.md`, a `DESIGN.md` that is a plan in all but
name. The inventory reports what is there and never decides that an unfamiliar
shape is out of scope.

Read-only. Prints one TSV row per plan (or plan candidate):

    path            plan directory, or a single legacy document
    format          current-pdd | legacy-pdd | ad-hoc | unknown
    artefacts       the files found (PRD, TASKS, AMENDMENTS, …)
    md_files        number of markdown files under it
    first_commit    earliest commit date touching the path (YYYY-MM-DD, or empty)
    last_commit     latest such date
    tracked         yes | no   (git ls-files knows it)
    covered         yes | no   (docs/history/ already cites the path)
    flags           in_flight, template, empty, no_date — comma-separated

Usage:
    python3 find_plans.py <project_root> [--json] [--exclude-container NAME ...]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

SKIP_DIRS = {".git", "node_modules", "target", "dist", "build", "out", ".venv", "venv",
             "__pycache__", ".next", ".turbo", ".cache", "vendor", "third_party", "coverage"}

# Directories whose children are plans, whatever the children are called.
CONTAINERS = {".plan", ".plans", "plans", "plan", "specs", "spec", "prds"}

# File/dir names that mark a plan unit, upper- or lowercase, any extension.
ARTEFACT_HINTS = re.compile(
    r"^(prd|tasks?|amendments?|propositions?|proof[-_]?pair|test[-_]?site|freeze|design|"
    r"plan|notes|spec|requirement|decisions?)",
    re.I,
)
LEGACY_HINTS = re.compile(r"proposition|proof[-_]pair|test[-_]?site|freeze|batch", re.I)
TEMPLATE_HINTS = re.compile(r"(^|/)(assets|templates?|fixtures?|examples?|tests?|__tests__)(/|$)", re.I)
UNCHECKED = re.compile(r"^\s*[-*]\s*\[ \]", re.M)
DATE_IN_TEXT = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")


def sh(cwd: str, *args: str) -> str:
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def git_dates(root: str, path: str) -> tuple[str, str]:
    out = sh(root, "git", "log", "--format=%ad", "--date=short", "--", path).split()
    return (min(out), max(out)) if out else ("", "")


def is_tracked(root: str, path: str) -> bool:
    return bool(sh(root, "git", "ls-files", "--", path).strip())


def md_files(dirpath: str, limit: int = 400) -> list[str]:
    out: list[str] = []
    for cur, dirnames, filenames in os.walk(dirpath):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name.endswith(".md"):
                out.append(os.path.join(cur, name))
                if len(out) >= limit:
                    return out
    return out


def artefacts_of(base: str, files: list[str]) -> list[str]:
    """The document names a reader will find, relative to the plan root."""
    out: set[str] = set()
    for f in files:
        rel = os.path.relpath(f, base) if os.path.isdir(base) else os.path.basename(f)
        stem = os.path.splitext(rel)[0]
        out.add(stem + "/" if os.sep in stem else stem)
    return sorted(out)[:12]


def sniff_format(files: list[str], names: list[str]) -> str:
    lowered = [n.lower() for n in names]
    if any(n.startswith(("prd", "tasks")) for n in lowered):
        return "current-pdd"
    for f in files[:8]:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                head = fh.read(4000)
        except OSError:
            continue
        if LEGACY_HINTS.search(head) or LEGACY_HINTS.search(os.path.basename(f)):
            return "legacy-pdd"
    return "ad-hoc" if files else "unknown"


def row_for(root: str, path: str, kind: str, covered_text: str) -> dict:
    full = os.path.join(root, path)
    files = md_files(full) if os.path.isdir(full) else [full]
    names = [os.path.basename(f) for f in files]
    first, last = git_dates(root, path)
    flags: list[str] = []
    if TEMPLATE_HINTS.search(path):
        flags.append("template")
    if not files:
        flags.append("empty")
    if not first:
        text = ""
        for f in files[:3]:
            try:
                text += open(f, encoding="utf-8", errors="replace").read(2000)
            except OSError:
                pass
        if not DATE_IN_TEXT.search(text):
            flags.append("no_date")
    for f in files:
        if os.path.basename(f).lower().startswith("task"):
            try:
                if UNCHECKED.search(open(f, encoding="utf-8", errors="replace").read()):
                    flags.append("in_flight")
            except OSError:
                pass
            break
    return {
        "path": path,
        "kind": kind,
        "format": sniff_format(files, names),
        "artefacts": artefacts_of(full, files),
        "md_files": len(files),
        "first_commit": first,
        "last_commit": last,
        "tracked": is_tracked(root, path),
        "covered": path in covered_text,
        "flags": sorted(set(flags)),
    }


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    root = os.path.abspath(args[0])
    extra_excludes = set()
    if "--exclude-container" in argv:
        idx = argv.index("--exclude-container")
        extra_excludes = {a for a in argv[idx + 1:] if not a.startswith("--")}

    covered_text = ""
    for name in ("index.md", "decisions.md", "timeline.md"):
        p = os.path.join(root, "docs", "history", name)
        if os.path.isfile(p):
            covered_text += open(p, encoding="utf-8", errors="replace").read()

    rows: list[dict] = []
    seen: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        # dot directories are pruned, except the plan containers: `.plan/` is a container,
        # `.git/` is not, and a rule that cannot tell them apart silently drops the old plans
        dirnames[:] = sorted(d for d in dirnames
                             if d not in SKIP_DIRS and d not in extra_excludes
                             and (not d.startswith(".") or d in CONTAINERS))
        rel = os.path.relpath(dirpath, root)
        base = os.path.basename(dirpath)
        in_container = base in CONTAINERS or (rel.startswith("docs" + os.sep)
                                              and base in CONTAINERS)
        if in_container and dirpath != root:
            # every immediate child is a plan: a directory, or a single legacy document
            for child in sorted(os.listdir(dirpath)):
                cp = os.path.join(dirpath, child)
                if child.startswith(".") or child in SKIP_DIRS:
                    continue
                crel = os.path.relpath(cp, root)
                if crel in seen:
                    continue
                if os.path.isdir(cp):
                    seen.add(crel)
                    rows.append(row_for(root, crel, "container-child", covered_text))
                elif child.endswith(".md") and child.lower() != "readme.md":
                    seen.add(crel)
                    rows.append(row_for(root, crel, "legacy-doc", covered_text))
            dirnames[:] = []          # do not descend twice
            continue
        # the archive's own output is never a plan, whatever its filenames suggest
        if rel == os.path.join("docs", "history") or rel.startswith(os.path.join("docs", "history") + os.sep):
            dirnames[:] = []
            continue
        # a directory that declares itself a plan by its artefacts
        hits = [n for n in filenames if ARTEFACT_HINTS.match(os.path.splitext(n)[0])]
        if hits and rel != "." and rel not in seen:
            seen.add(rel)
            rows.append(row_for(root, rel, "artefact", covered_text))

    rows.sort(key=lambda r: (r["first_commit"] or "9999", r["path"]))
    if "--json" in argv:
        print(json.dumps(rows, indent=2))
        return 0

    print("path\tformat\tartefacts\tmd_files\tfirst_commit\tlast_commit\ttracked\tcovered\tflags")
    for r in rows:
        print("\t".join([
            r["path"], r["format"], ";".join(a for a in r["artefacts"] if a not in ("", ".", "src")),
            str(r["md_files"]), r["first_commit"] or "-", r["last_commit"] or "-",
            "yes" if r["tracked"] else "no", "yes" if r["covered"] else "no",
            ",".join(r["flags"]) or "-",
        ]))
    batches = (len(rows) + 2) // 3
    formats: dict[str, int] = {}
    for r in rows:
        formats[r["format"]] = formats.get(r["format"], 0) + 1
    print(f"# {len(rows)} plans → {batches} batches at ≤3 per subagent; formats "
          + ", ".join(f"{k}={v}" for k, v in sorted(formats.items()))
          + f"; untracked {sum(1 for r in rows if not r['tracked'])} (never deletable)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
