#!/usr/bin/env python3
"""Recon for pdd:study — list candidate members and package roots.

Read-only. Prints one TSV row per candidate unit so the main agent can plan the
dispatch rounds before reading any code:

    path            path relative to the project root
    kind            cargo | npm | py-dist | py-root | go | other
    depth           path components below the root (round number candidate)
    nested_in       nearest ancestor unit (empty for a top-level member)
    loc             source lines (*.rs *.py *.ts *.tsx *.js *.jsx *.go *.java *.kt *.c *.h *.cpp)
    agents          present | absent  (AGENTS.md in that directory)
    entries         entry-point candidates, ';'-separated
    note            why it is / is not a unit worth a subagent

Usage:
    python3 list_members.py <project_root> [--max-depth N] [--include-other] [--json]
"""

from __future__ import annotations

import json
import os
import re
import sys

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "target", "dist", "build", "out", ".next",
    ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".turbo", ".cache",
    "vendor", "third_party", ".idea", ".vscode", "coverage", ".gradle", "bin", "obj",
}
SRC_EXT = {".rs", ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go",
           ".java", ".kt", ".kts", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".rb", ".php"}
MANIFESTS = {
    "Cargo.toml": "cargo",
    "package.json": "npm",
    "pyproject.toml": "py-dist",
    "setup.py": "py-dist",
    "setup.cfg": "py-dist",
    "go.mod": "go",
}


def walk(root: str, max_depth: int):
    """Yield (dirpath, filenames) below root, pruning skip dirs and deep trees."""
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".") and depth < max_depth
        )
        yield dirpath, depth, filenames


def count_loc(dirpath: str) -> int:
    """Source lines of a unit: recursive, but a nested unit's lines are its own."""
    total = 0
    for cur, dirnames, filenames in os.walk(dirpath):
        if cur != dirpath and any(m in filenames for m in MANIFESTS):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if os.path.splitext(name)[1] in SRC_EXT:
                try:
                    with open(os.path.join(cur, name), "rb") as fh:
                        total += sum(1 for _ in fh)
                except OSError:
                    pass
    return total


def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def cargo_entries(dirpath: str) -> list[str]:
    out: list[str] = []
    manifest = read_text(os.path.join(dirpath, "Cargo.toml"))
    for m in re.finditer(r'^\s*\[\[bin\]\]\s*$(.*?)(?=^\s*\[|\Z)', manifest, re.M | re.S):
        block = m.group(1)
        name = re.search(r'^\s*name\s*=\s*"([^"]+)"', block, re.M)
        path = re.search(r'^\s*path\s*=\s*"([^"]+)"', block, re.M)
        if name:
            out.append(f"bin:{name.group(1)}" + (f"@{path.group(1)}" if path else ""))
    if re.search(r"^\s*\[lib\]", manifest, re.M):
        out.append("lib")
    if os.path.exists(os.path.join(dirpath, "src", "main.rs")):
        out.append("src/main.rs")
    bindir = os.path.join(dirpath, "src", "bin")
    if os.path.isdir(bindir):
        out += [f"src/bin/{n}" for n in sorted(os.listdir(bindir)) if n.endswith(".rs")]
    return out


def npm_entries(dirpath: str) -> list[str]:
    out: list[str] = []
    try:
        pkg = json.loads(read_text(os.path.join(dirpath, "package.json")) or "{}")
    except json.JSONDecodeError:
        return out
    for key in ("bin", "main", "module", "exports"):
        value = pkg.get(key)
        if isinstance(value, str):
            out.append(f"{key}:{value}")
        elif isinstance(value, dict):
            out += [f"{key}:{k}" for k in value]
    if "workspaces" in pkg:
        out.append("workspace-root")
    return out


def py_entries(dirpath: str) -> list[str]:
    out: list[str] = []
    for name in ("__main__.py", "main.py", "cli.py", "app.py", "server.py"):
        if os.path.exists(os.path.join(dirpath, name)):
            out.append(name)
    meta = read_text(os.path.join(dirpath, "pyproject.toml"))
    for m in re.finditer(r"^([\w.-]+)\s*=\s*\"([\w.]+):([\w.]+)\"", meta, re.M):
        out.append(f"script:{m.group(1)}")
    return out


def go_entries(dirpath: str) -> list[str]:
    out: list[str] = []
    if os.path.exists(os.path.join(dirpath, "main.go")):
        out.append("main.go")
    cmd = os.path.join(dirpath, "cmd")
    if os.path.isdir(cmd):
        out += [f"cmd/{n}" for n in sorted(os.listdir(cmd))
                if os.path.isdir(os.path.join(cmd, n))]
    return out


def classify(dirpath: str, filenames: list[str], include_other: bool) -> tuple[str, list[str], str]:
    names = set(filenames)
    for manifest, kind in MANIFESTS.items():
        if manifest in names:
            if kind == "cargo":
                entries = cargo_entries(dirpath)
                note = ""
                if re.search(r"^\s*\[workspace\]", read_text(os.path.join(dirpath, manifest)), re.M):
                    note = "workspace root — holds members, is not a unit itself"
                    if "src/main.rs" not in entries:
                        return "workspace", entries, note
                return kind, entries, note
            if kind == "npm":
                entries = npm_entries(dirpath)
                note = "" if entries else "no entry point declared — probably a container or config-only package"
                return kind, entries, note
            if kind == "py-dist":
                return kind, py_entries(dirpath), ""
            if kind == "go":
                return kind, go_entries(dirpath), ""
    if "__init__.py" in names:
        py_files = [n for n in names if n.endswith(".py") and n != "__init__.py"]
        if py_files:
            return "py-root", py_entries(dirpath), ""
    if include_other and any(n.endswith((".rs", ".py", ".ts", ".js", ".go")) for n in names):
        return "other", [], "source but no manifest — check by hand whether it owns an entry point"
    return "", [], ""


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    root = os.path.abspath(args[0])
    max_depth = 12
    if "--max-depth" in argv:
        max_depth = int(argv[argv.index("--max-depth") + 1])
    as_json = "--json" in argv

    rows = []
    for dirpath, depth, filenames in walk(root, max_depth):
        kind, entries, note = classify(dirpath, filenames, "--include-other" in argv)
        if not kind:
            continue
        rel = "." if dirpath == root else os.path.relpath(dirpath, root)
        rows.append({
            "path": rel,
            "kind": kind,
            "depth": depth,
            "loc": count_loc(dirpath),
            "agents": "present" if "AGENTS.md" in filenames else "absent",
            "claude": "present" if "CLAUDE.md" in filenames else "absent",
            "entries": entries,
            "note": note,
        })

    # nearest ancestor unit, and the round it implies: 1 + (number of unit ancestors)
    by_path = {r["path"]: r for r in rows}
    for row in rows:
        if row["path"] == ".":
            row["nested_in"] = ""
        else:
            parents = [r["path"] for r in rows
                       if r["path"] != "." and row["path"].startswith(r["path"] + os.sep)]
            row["nested_in"] = max(parents, key=len) if parents else ""
        chain, cur = 0, row["nested_in"]
        while cur and chain < 20:
            chain += 1
            cur = by_path.get(cur, {}).get("nested_in", "")
        row["round"] = chain + 1

    if as_json:
        print(json.dumps(rows, indent=2))
        return 0

    print("path\tkind\tdepth\tround\tnested_in\tloc\tagents\tentries\tnote")
    for r in rows:
        print("\t".join([
            r["path"], r["kind"], str(r["depth"]), str(r.get("round", "")),
            r.get("nested_in", ""), str(r["loc"]), r["agents"],
            ";".join(r["entries"]), r["note"],
        ]))
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    units = [r for r in rows if r["kind"] != "workspace"]
    per_round: dict[int, int] = {}
    for r in units:
        per_round[r["round"]] = per_round.get(r["round"], 0) + 1
    print(f"# {len(units)} units (+{kinds.get('workspace', 0)} workspace root): "
          + ", ".join(f"{k}={v}" for k, v in sorted(kinds.items()) if k != "workspace")
          + "; rounds " + ", ".join(f"r{k}:{v} subagents" for k, v in sorted(per_round.items())),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
