#!/usr/bin/env python3
"""Render every mermaid block in the given AGENTS.md files. A graph that does not parse is a broken map.

Usage:
    render_graphs.py <project_root> [unit-path ...]

With no unit paths, every `AGENTS.md` under the root is rendered — that is the acceptance sweep.
With unit paths, only those files are rendered — that is the per-task self-check.

Why a script and not `npx @mermaid-js/mermaid-cli` by hand: as root, chromium refuses to start without
`--no-sandbox`, so the naive invocation fails with a puppeteer launch error that reads like a network
problem, and the natural conclusion is "rendering is unavailable here" — which is how a stray paren
survived a whole refresh. The puppeteer config below is the difference between "not rendered" and "rendered".

Exit 0 only when every block parses and renders. Prints one line per block, plus the parse error text.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def blocks(md: Path) -> list[str]:
    return re.findall(r"```mermaid\n(.*?)```", md.read_text(), re.S)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1]).resolve()
    units = [root / u for u in sys.argv[2:]] or sorted(root.rglob("AGENTS.md"))
    units = [u / "AGENTS.md" if u.is_dir() else u for u in units]

    work = Path(tempfile.mkdtemp(prefix="mmd-"))
    (work / "puppeteer.json").write_text(
        json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}))
    total = failed = 0
    for md in units:
        if not md.exists():
            print(f"missing  {md}")
            failed += 1
            continue
        n = 0
        for i, body in enumerate(blocks(md)):
            n += 1
            total += 1
            stem = f"{md.parent.name or 'root'}-{i}"
            src = work / f"{stem}.mmd"
            src.write_text(body)
            proc = subprocess.run(
                ["npx", "-y", "@mermaid-js/mermaid-cli", "-p", "puppeteer.json",
                 "-i", src.name, "-o", f"{stem}.svg"],
                cwd=work, capture_output=True, text=True, timeout=180)
            if proc.returncode != 0:
                failed += 1
                first = next((l for l in (proc.stdout + proc.stderr).splitlines()
                              if "Error" in l or "error" in l), "unknown failure")
                print(f"FAIL     {md.relative_to(root)} block {i}: {first.strip()[:160]}")
        if n:
            print(f"ok       {md.relative_to(root)} ({n} block(s))")
    print(f"\nblocks {total} | failed {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
