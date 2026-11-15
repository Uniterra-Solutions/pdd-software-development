#!/usr/bin/env python3
"""Prove a verification test can fail: mutate, run, restore, re-run.

A named wrong implementation is a hypothesis; a recorded red run is the evidence. This script makes
that check one command instead of a hand-written harness per task.

Usage:
  python3 mutate_check.py --file src/x.ts --old 'anchor' --new 'mutant' \
      --cmd 'npx vitest run tests/x.test.ts' [--repo .] [--shell]

Exit codes: 0 the mutation separates the trees (mutated red, restored green, bytes identical),
            1 it does not (the test cannot see that wrong implementation),
            2 the anchor is missing or ambiguous — nothing was changed.
"""
import argparse
import hashlib
import os
import pathlib
import shlex
import subprocess
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--file", required=True, help="path relative to --repo")
    ap.add_argument("--old", required=True, help="exactly-one-occurrence anchor")
    ap.add_argument("--new", required=True, help="the wrong implementation to inject")
    ap.add_argument("--cmd", required=True, help="the task's verification command")
    ap.add_argument(
        "--shell",
        action="store_true",
        help="run --cmd through /bin/sh (needed for pipes, &&, redirection); default is argv splitting",
    )
    ap.add_argument("--tail", type=int, default=6, help="lines of mutated output to show")
    args = ap.parse_args()
    cmd = args.cmd if args.shell else shlex.split(args.cmd)
    # A same-size mutation written inside the same second can leave a stale .pyc
    # behind: the restored run would then execute the mutant's bytecode and look
    # red for the wrong reason. Never let the child write bytecode.
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    root = pathlib.Path(args.repo).resolve()
    target = root / args.file
    if not target.is_file():
        print(f"[refused] no such file: {target}", file=sys.stderr)
        return 2

    original = target.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    hits = text.count(args.old)
    if hits != 1:
        print(
            f"[refused] anchor occurs {hits} time(s) in {args.file}; widen it until it is unique",
            file=sys.stderr,
        )
        return 2

    for cache in root.rglob("__pycache__"):
        if target.stem in {c.name.split(".")[0] for c in cache.glob("*.pyc")} or target.parent == cache.parent:
            for stale in cache.glob("*.pyc"):
                stale.unlink(missing_ok=True)
    target.write_text(text.replace(args.old, args.new, 1), encoding="utf-8")
    try:
        mutated = subprocess.run(cmd, shell=args.shell, cwd=root, capture_output=True, text=True, env=env)
        tail = (mutated.stdout + mutated.stderr).strip().splitlines()[-args.tail :]
    finally:
        target.write_bytes(original)

    restored_identical = hashlib.sha256(target.read_bytes()).hexdigest() == digest
    restored = subprocess.run(cmd, shell=args.shell, cwd=root, capture_output=True, text=True, env=env)

    separates = mutated.returncode != 0 and restored.returncode == 0 and restored_identical
    print(
        f"mutated exit={mutated.returncode}  "
        f"restored byte-identical={restored_identical}  "
        f"restored exit={restored.returncode}"
    )
    for line in tail:
        print(f"  | {line}")

    if not separates:
        if restored_identical is False:
            print("[FAIL] the restore did not reproduce the original bytes", file=sys.stderr)
        elif restored.returncode != 0:
            print("[FAIL] the restored tree is already red — fix that before testing discrimination", file=sys.stderr)
        else:
            print("[FAIL] the mutation stayed green: this test cannot see that wrong implementation", file=sys.stderr)
        return 1

    print("[ok] the test discriminates: red under the mutation, green after restore")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
