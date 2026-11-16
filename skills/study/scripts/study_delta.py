#!/usr/bin/env python3
"""Delta recon and acceptance for pdd:study — refresh a knowledge base that already exists.

Two modes, one job: turn "the tree moved since the knowledge base was written" into a
per-unit dispatch table, and then check that the refresh obeyed its rules.

    python3 study_delta.py <project_root>              # ledger: the refresh's round plan
    python3 study_delta.py <project_root> --verify     # acceptance: nothing stale, no row lost

Two diffs, because they answer different questions:

    touched   every path named by any commit between the base and HEAD, plus the working
              tree — a path that was created and deleted inside the window still appears
    net       the base against the working tree — what is true now

Dispatch reads `touched`: a commit that added a handler and a later one that deleted it is
still work somebody did against a file the inventory describes. Row preservation reads
`net`: a row whose cited file ended the window unchanged may not be rewritten, however many
commits it took to get back there.

The base of each file is its own provenance commit, not a repository-wide one: files studied
at different times are stale in different amounts, and a single base either re-runs units
whose claims are still true or skips units that moved.

Ledger mode prints, per discovered `AGENTS.md`:

    unit        the directory that file describes
    base        the provenance commit it was written against (abbreviated)
    commits     commits touching the unit since that base
    files       touched paths under the unit
    status      current | refresh | retired | missing-file | unknown-base

plus the changed paths no unit claims (the root bucket), the knowledge-base files that
disappeared, and the members that have no `AGENTS.md` yet.

Verify mode reads the committed version of each file (`git show HEAD:<path>`) and errors
when a file was not refreshed although its unit moved, or when a row whose cited file ended
the window unchanged came back altered or missing. Ids are never reused, so a dropped row is
either a retirement the report must name or a silent loss, and the cited file tells which.

Read-only: no file is written, no git command mutates anything.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

MARK_BEGIN = "<!-- study:begin -->"
MARK_END = "<!-- study:end -->"
SKIP_DIRS = {".git", "node_modules", "target", "dist", "build", "out", ".venv", "venv",
             "__pycache__", ".next", ".mypy_cache", ".pytest_cache", ".turbo", "vendor"}
PROVENANCE = re.compile(r"generated:\s*`?([0-9a-f]{7,40})`?")
CITE = re.compile(r"`([A-Za-z0-9_@./\\-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`")
BRANCH_ROW = re.compile(r"^\|\s*`?(B\d+)`?\s*\|")
STATUS_LINE = re.compile(r"^([RCAMD])(\d{0,3})\t(.+)$")
MAX_LISTED = 40


# --------------------------------------------------------------------------- git

def sh_ok(root: str, *args: str) -> str:
    proc = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else ""


def head(root: str) -> str:
    return sh_ok(root, "rev-parse", "HEAD").strip()


def resolve_commit(root: str, ref: str) -> str:
    return sh_ok(root, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()


# ------------------------------------------------------------------- file shape

def find_agents(root: str) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        if "AGENTS.md" in filenames:
            out.append(os.path.join(dirpath, "AGENTS.md"))
    return sorted(out)


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def split_block(text: str) -> str | None:
    start = text.find(MARK_BEGIN)
    end = text.find(MARK_END)
    if start == -1 or end == -1 or end < start:
        return None
    return text[start:end]


def unit_of(root: str, agents_path: str) -> str:
    rel = os.path.relpath(os.path.dirname(agents_path), root)
    return "." if rel == "." else rel


def prefix(unit: str) -> str:
    return "" if unit == "." else unit.rstrip("/") + "/"


def resolve_cite(rel_path: str, root: str, unit: str) -> str:
    for base in (os.path.join(root, unit), root):
        candidate = os.path.normpath(os.path.join(base, rel_path))
        if os.path.isfile(candidate):
            return os.path.relpath(candidate, root)
    return os.path.normpath(rel_path)


def cites(block: str, root: str, unit: str) -> set[str]:
    """Repo-relative paths the block cites, resolved the way a reader resolves them."""
    return {resolve_cite(m[0], root, unit) for m in CITE.findall(block)}


def norm(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


SITE_CELL = 4          # `| id | behaviour | consequence | trigger | site | example | note |`


def norm_offsite(line: str) -> str:
    """The row with every `path:line` token OUTSIDE the site cell replaced by a placeholder.

    Preservation protects the claim -- behaviour, trigger, site -- not a dead pointer buried
    in a note. Without this, a row whose site file did not move cannot have a secondary
    citation repaired, and the two gates contradict each other: `--verify` calls the repair a
    rewrite, `check_agents_md.py` calls the unrepaired citation a missing file.
    """
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    for i, cell in enumerate(cells):
        if i != SITE_CELL:
            cells[i] = re.sub(r"[\w./-]+\.rs:\d+(?:-\d+)?", "\u27e8cite\u27e9", cell)
    return norm(" | ".join(cells))


def rows(block: str, root: str = "", unit: str = ".") -> dict[str, tuple[str, str, str, str]]:
    """id -> (normalised row text, repo-relative cited file, off-site-normalised row, site cell)."""
    out: dict[str, tuple[str, str, str, str]] = {}
    for line in block.splitlines():
        m = BRANCH_ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        site = cells[4] if len(cells) > 4 else ""
        cite = CITE.search(site)
        out[m.group(1)] = (norm(line), resolve_cite(cite.group(1), root, unit) if cite else "",
                           norm_offsite(line), norm(site))
    return out


# --------------------------------------------------------------- changed paths

class Changes:
    """Touched paths (every commit + working tree) and net paths (base → working tree)."""

    def __init__(self, root: str, base: str) -> None:
        self.touched: dict[str, str] = {}
        self.net: dict[str, str] = {}
        if base:
            for line in sh_ok(root, "diff", "--name-status", "-M", base).splitlines():
                self._record(line, self.net, self.touched)
            log = sh_ok(root, "log", "--no-renames", "--name-status", "--format=",
                        f"{base}..HEAD")
            for line in log.splitlines():
                self._record(line, None, self.touched)
        for line in sh_ok(root, "status", "--porcelain", "--untracked-files=all").splitlines():
            if len(line) < 4:
                continue
            st, path = line[:2].strip(), line[3:].strip().strip('"').rstrip("/")
            code = "??" if st == "??" else st[0].replace("R", "A").replace("C", "A")
            self.net[path] = code
            self.touched.setdefault(path, code)

    def _record(self, line: str, *targets: dict[str, str] | None) -> None:
        if not line.strip():
            return
        parts = line.split("\t")
        st = parts[0][:1]
        if st in {"R", "C"} and len(parts) >= 3:
            pairs = [(parts[1], "D"), (parts[2], st)]
        elif len(parts) >= 2:
            pairs = [(parts[1], st)]
        else:
            return
        for path, code in pairs:
            for target in targets:
                if target is not None:
                    target.setdefault(path, code)

    def under(self, unit: str) -> dict[str, str]:
        p = prefix(unit)
        own = p + "AGENTS.md"
        # the knowledge base file itself is not evidence about behaviour: a study commit
        # that only adds it must not make the unit look changed
        return {k: v for k, v in self.touched.items() if k.startswith(p) and k != own}

    def moved(self, path: str) -> bool:
        """The cited file ended the window in a different state than the file records."""
        return path in self.net


# ------------------------------------------------------------------- the ledger

def deepest(path: str, units: list[str]) -> str:
    hits = [u for u in units if path.startswith(prefix(u))]
    return max(hits, key=len) if hits else ""


def discover_new(root: str, paths: set[str]) -> list[tuple[str, str, str]]:
    """Members with no AGENTS.md that own at least one touched path."""
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "list_members.py")
    if not os.path.isfile(script):
        return []
    proc = subprocess.run([sys.executable, script, root, "--include-other"],
                          capture_output=True, text=True)
    found: dict[str, tuple[str, str]] = {}
    for line in proc.stdout.splitlines():
        cells = line.split("\t")
        if len(cells) < 9 or cells[0] == "path":
            continue
        path, kind, agents, entries = cells[0], cells[1], cells[6], cells[7].strip()
        if agents != "absent" or kind == "workspace":
            continue
        if kind == "other" and not entries:
            continue                       # a manifest-less source dir with no entry point
        if any(p == path or p.startswith(prefix(path)) for p in paths):
            found[path] = (kind, cells[8] if len(cells) > 8 else "")
    # a nested candidate is covered by its shallower parent: one dispatch per unit
    for path in list(found):
        parents = [p for p in found if p != path and path.startswith(prefix(p))]
        if parents:
            found.pop(path)
    return sorted((p, k, n) for p, (k, n) in found.items())


def exclude_own(unit: str) -> list[str]:
    """Pathspec that keeps the unit's own AGENTS.md out of its commit walk."""
    return [f":(exclude){prefix(unit)}AGENTS.md"]


def build(root: str) -> dict:
    units: list[dict] = []
    bases: dict[str, Changes] = {}
    on_disk: set[str] = set()
    for path in find_agents(root):
        block = split_block(read(path))
        unit = unit_of(root, path)
        rel = os.path.relpath(path, root)
        on_disk.add(rel)
        if block is None:
            units.append({"unit": unit, "file": rel, "base": "", "status": "index",
                          "commits": [], "files": {}, "cited": set()})
            continue
        m = PROVENANCE.search(block)
        base = resolve_commit(root, m.group(1)) if m else ""
        if base not in bases:
            bases[base] = Changes(root, base)
        ch = bases[base]
        under = ch.under(unit)
        cited = {c for c in cites(block, root, unit) if ch.moved(c)} if base else set()
        commits: list[str] = []
        if base:
            log = sh_ok(root, "log", "--format=%h\t%ad\t%s", "--date=short", f"{base}..HEAD",
                        "--", unit, *exclude_own(unit))
            commits = [line for line in log.splitlines() if line.strip()]
        status = "unknown-base" if not base else ("refresh" if (under or cited) else "current")
        units.append({"unit": unit, "file": rel, "base": base[:8], "status": status,
                      "commits": commits, "files": under, "cited": cited})

    # every path any commit or the working tree named, whichever base saw it first
    glob: dict[str, str] = dict(Changes(root, "").touched)
    for ch in bases.values():
        for path, st in ch.touched.items():
            glob.setdefault(path, st)

    known = [u["unit"] for u in units if u["status"] != "index"]
    for path, st in glob.items():
        if st != "D" or not path.endswith("AGENTS.md") or path in on_disk:
            continue                       # a surviving file is what the block says it is
        unit = os.path.dirname(path) or "."
        if any(u["unit"] == unit for u in units):
            continue
        units.append({"unit": unit, "file": path, "base": "", "commits": [], "files": {},
                      "cited": set(),
                      "status": "retired" if not os.path.isdir(os.path.join(root, unit))
                      else "missing-file"})
        known.append(unit)

    new_units = [u for u in discover_new(root, set(glob)) if u[0] not in known]
    new_paths = {p for p, _, _ in new_units}
    unclaimed = sorted({(path, st) for path, st in glob.items()
                        if deepest(path, known) == ""
                        and not any(path.startswith(prefix(p)) for p in new_paths)})
    return {"root": root, "units": units, "unclaimed": unclaimed, "new": new_units}


def print_ledger(d: dict) -> None:
    units = d["units"]
    print(f"# {d['root']}  HEAD {head(d['root'])[:8]}")
    studied = [u for u in units if u["status"] != "index"]
    if not studied:
        print("\n# no study block on disk — this repository has no knowledge base yet.\n"
              "# That is Workflow A (a first study), not a delta: dispatch §0 of SKILL.md.")
        if d["unclaimed"]:
            print("\n=== paths with no unit at all")
            for path, st in d["unclaimed"][:MAX_LISTED]:
                print(f"  [{st}] {path}")
        return
    print(f"\n=== units ({len(studied)})")
    print("unit\tbase\tcommits\tfiles\tstatus")
    for u in sorted(studied, key=lambda u: u["unit"]):
        print("\t".join([u["unit"], u["base"] or "-", str(len(u["commits"])),
                         str(len(u["files"])), u["status"]]))

    stale = [u for u in studied if u["status"] in {"refresh", "unknown-base"}]
    if stale:
        print("\n=== commits and touched paths per unit (the diff you dispatch on)")
        for u in stale:
            print(f"\n{u['unit']}   base {u['base'] or '?'} → HEAD")
            for line in u["commits"][:MAX_LISTED]:
                print(f"  {line}")
            if len(u["commits"]) > MAX_LISTED:
                print(f"  … {len(u['commits']) - MAX_LISTED} more commit(s)")
            for st, path in sorted((v, k) for k, v in u["files"].items())[:MAX_LISTED]:
                print(f"  [{st}] {path}")
            if len(u["files"]) > MAX_LISTED:
                print(f"  … {len(u['files']) - MAX_LISTED} more path(s)")
            if u["cited"]:
                print(f"  also cites, and it moved: {', '.join(sorted(u['cited']))}")

    print(f"\n=== unclaimed (root bucket, {len(d['unclaimed'])})")
    for path, st in d["unclaimed"]:
        print(f"  [{st}] {path}")

    retired = [u for u in studied if u["status"] in {"retired", "missing-file"}]
    if retired:
        print(f"\n=== knowledge-base files gone from disk ({len(retired)})")
        for u in retired:
            print(f"  [{u['status']}] {u['file']}")

    if d["new"]:
        print(f"\n=== members with no AGENTS.md yet ({len(d['new'])})")
        for path, kind, note in d["new"]:
            print(f"  {path}\t{kind}\t{note}")

    refresh = len([u for u in studied if u["status"] == "refresh"])
    print(f"\n# dispatch: {refresh} refresh subagent(s), {len(d['new'])} new unit(s), "
          f"{len(d['unclaimed'])} root path(s), {len(retired)} file(s) gone")


# ---------------------------------------------------------------------- verify

def verify(root: str) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    hd = head(root)
    if not hd:
        print("ERROR  not a git repository with a HEAD")
        return 1

    for path in find_agents(root):
        rel = os.path.relpath(path, root)
        unit = unit_of(root, path)
        work = split_block(read(path))
        if work is None:
            warnings.append(f"{rel}: no study block (human file; not checked)")
            continue
        committed = sh_ok(root, "show", f"HEAD:{rel}")
        old = split_block(committed) if committed else None
        base = ""
        if old is None:
            warnings.append(f"{rel}: no committed version — row preservation not checkable "
                            "(commit the refresh, then verify)")
        else:
            om = PROVENANCE.search(old)
            base = resolve_commit(root, om.group(1)) if om else ""

        ch = Changes(root, base)
        under = ch.under(unit)
        cited = {c for c in cites(work, root, unit) if ch.moved(c)}
        moved = bool(under or cited)

        wm = PROVENANCE.search(work)
        new_base = resolve_commit(root, wm.group(1)) if wm else ""
        if not wm:
            errors.append(f"{rel}: no provenance block")
        elif not new_base:
            errors.append(f"{rel}: provenance commit {wm.group(1)} does not resolve")
        elif moved and old is not None and new_base == base:
            errors.append(f"{rel}: stale — {len(under)} file(s) changed under the unit since "
                          f"{base[:8]}, provenance not refreshed")
        elif new_base and new_base != hd:
            after = sh_ok(root, "log", "--format=%h", f"{new_base}..HEAD", "--",
                          unit, *exclude_own(unit)).split()
            if after:
                errors.append(f"{rel}: stale again — {len(after)} commit(s) touch the unit after "
                              f"the refresh at {new_base[:8]}")

        if old is None or not base:
            continue
        old_rows = rows(old, root, unit)
        new_rows = rows(work, root, unit)
        dropped: list[str] = []
        modified: list[str] = []
        for bid, (text, site, offsite, site_cell) in old_rows.items():
            if site and ch.moved(site):
                continue                       # its evidence moved: the row may change
            got = new_rows.get(bid)
            if got is None:
                dropped.append(bid)
            elif got[0] != text and (got[2] != offsite or got[3] != site_cell):
                # a `path:line` token outside the site cell may be repaired; the site cell,
                # the behaviour and the trigger stay frozen (see norm_offsite)
                modified.append(bid)
        if dropped:
            errors.append(f"{rel}: row(s) dropped although their cited file ended unchanged: "
                          + ", ".join(dropped))
        if modified:
            errors.append(f"{rel}: row(s) rewritten although their cited file ended unchanged: "
                          + ", ".join(modified))

    d = build(root)
    if d["unclaimed"]:
        warnings.append(f"{len(d['unclaimed'])} changed path(s) under no unit (root bucket): "
                        + ", ".join(p for p, _ in d["unclaimed"][:8])
                        + (" …" if len(d["unclaimed"]) > 8 else ""))
    gone = [u for u in d["units"] if u["status"] in {"retired", "missing-file"}]
    if gone:
        errors.append(f"{len(gone)} knowledge-base file(s) gone from disk — the root index must "
                      "stop naming them: " + ", ".join(u["file"] for u in gone[:8]))

    for w in warnings:
        print(f"warn   {w}")
    for e in errors:
        print(f"ERROR  {e}")
    print(f"\nfiles: {len(find_agents(root))}, errors: {len(errors)}, warnings: {len(warnings)}")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    root = os.path.abspath(args[0])
    if "--verify" in argv:
        return verify(root)
    print_ledger(build(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
