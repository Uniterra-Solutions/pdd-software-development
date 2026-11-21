#!/usr/bin/env python3
"""Shared engine for the two branch-map front ends (Rust, TypeScript).

The point of this module is that both languages emit **the same row schema and
the same closure vocabulary**, so a study subagent reads one table shape no
matter which member it was given. `branch_map_rust.py` and `branch_map_ts.py`
only supply grammar-specific walking; everything below is language-neutral.

What a row is:

  carrier  — a state bearer declared in the unit: an enum, a struct, a type
             alias, a boolean/Option/numeric parameter. Its `closure` says how
             complete the state list is:
               closed        the language or the declaration closes the set
                             (bool, Rust enum without #[non_exhaustive],
                             TS union of string literals)
               declared      someone wrote these values down, nothing enforces
                             that they are all of them (const blocks, TS enum)
               open          the legal set is not in this source (string, any)
               partitioned   not enumerable; the state is an interval boundary
                             (numeric compared against thresholds)
               product       a record: the state is the product of its fields
               registered    the legal set is the set of implementations the
                             unit registers (trait objects, interfaces)
  branch   — a decision site: the predicate, what it reads and where those
             reads come from, and what the branch does (returns, writes, calls).

`purity` is the load-bearing field. A pure predicate reads only parameters and
locals that the function itself assigned; its trigger is a statement about the
input. An impure predicate reads state owned by someone else — a field of self,
a config value, the clock, another module's function — and then "what input
triggers this" is not a question this file can answer. Reporting an impure
branch as if its trigger were input-determined is the failure mode this script
exists to prevent, so the field is never inferred away.

Neither script decides meaning. They emit facts with their provenance and their
limits; the model disposes of them.

Exit codes: 0 ok · 2 dependency missing · 3 unit not found · 4 parse errors
(a misparse is a broken gate, never a skipped one).
"""

from __future__ import annotations

import json
import os
import sys
from typing import NoReturn

SCHEMA = "branch-map/1"
CLOSURES = ("closed", "declared", "open", "partitioned", "product", "registered")
ORIGINS = ("param", "local", "self", "external", "callee", "unknown")

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "target", "dist", "build", "out", ".next",
    ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".turbo", ".cache",
    "coverage", ".gradle", "obj", "bin", "vendor", "third_party", "generated",
}

# Language-provided bindings: reading one is not reading someone's state. A
# predicate that mentions `Array.isArray` is still a function of its arguments.
JS_GLOBALS = {
    "Array", "Object", "Math", "JSON", "String", "Number", "Boolean", "Symbol",
    "Promise", "Reflect", "RegExp", "Date", "Intl", "BigInt", "Buffer", "process",
    "undefined", "NaN", "Infinity", "globalThis",
}

# Callees that cannot change observable state; anything else makes a predicate
# impure until someone proves otherwise.
RUST_PURE_CALLS = {
    "matches!", "vec!", "len", "is_empty", "is_some", "is_none", "is_ok", "is_err",
    "as_str", "as_ref", "as_bytes", "to_string", "clone", "get", "contains", "starts_with",
    "ends_with", "unwrap_or", "unwrap_or_default", "unwrap_or_else", "min", "max", "abs",
    "to_lowercase", "to_uppercase", "trim", "cmp", "saturating_sub", "saturating_add",
    "checked_sub", "checked_add", "hash", "eq", "fmt", "is_finite", "is_nan",
    "is_infinite", "is_sign_positive", "is_sign_negative", "contains_key",
    "get_or_insert", "iter", "count", "any", "all", "matches", "starts_with_char",
}
TS_PURE_CALLS = {
    "Boolean", "Number", "String", "parseInt", "parseFloat", "isNaN", "isFinite",
    "Array.isArray", "Object.keys", "Object.values", "Object.entries", "Math.abs",
    "Math.min", "Math.max", "Math.floor", "Math.round", "Math.trunc", "JSON.stringify",
    "String.raw", "hasOwnProperty", "includes", "startsWith", "endsWith", "slice",
    "indexOf", "toLowerCase", "toUpperCase", "trim", "some", "every", "filter", "map",
    "find", "join", "concat", "padStart", "padEnd", "charAt", "at",
}


# --------------------------------------------------------------------------- #
# CLI plumbing
# --------------------------------------------------------------------------- #

def die(code: int, message: str) -> NoReturn:
    sys.stderr.write(message.rstrip() + "\n")
    raise SystemExit(code)


def require_tree_sitter(language: str, modules: dict) -> dict:
    """Import the grammar or fail loudly. A silent fallback is not allowed."""
    try:
        import tree_sitter  # noqa: F401
    except ImportError:
        die(2, "branch-map: missing dependency 'tree_sitter'.\n"
               "  python3 -m pip install tree_sitter " + " ".join(modules.values()))
    out = {}
    for key, mod in modules.items():
        try:
            out[key] = __import__(mod)
        except ImportError:
            die(2, f"branch-map: missing grammar '{mod}' for {language}.\n"
                   f"  python3 -m pip install tree_sitter {mod}")
    return out


def parse_args(argv, language: str):
    """Minimal flag parser: the script is invoked by a skill, not by a human."""
    opts = {
        "unit": None, "member": None, "root": None, "select": None,
        "json": False, "include_tests": False, "max_files": 0, "max_branches": 0,
        "allow_parse_errors": False, "quiet": False,
    }
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            print(__doc__ or "")
            raise SystemExit(0)
        elif a == "--member":
            i += 1; opts["member"] = argv[i]
        elif a == "--root":
            i += 1; opts["root"] = argv[i]
        elif a == "--select":
            i += 1; opts["select"] = argv[i]
        elif a == "--json":
            opts["json"] = True
        elif a == "--include-tests":
            opts["include_tests"] = True
        elif a == "--max-files":
            i += 1; opts["max_files"] = int(argv[i])
        elif a == "--max-branches":
            i += 1; opts["max_branches"] = int(argv[i])
        elif a == "--allow-parse-errors":
            opts["allow_parse_errors"] = True
        elif a == "--quiet":
            opts["quiet"] = True
        elif a.startswith("-"):
            die(1, f"branch-map: unknown flag {a!r}")
        else:
            opts["unit"] = a
        i += 1
    if not opts["unit"] and not opts["member"]:
        die(1, f"usage: branch_map_{language}.py <unit-path> | --member NAME "
               f"[--root DIR] [--select GLOB] [--json]")
    return opts


def discover_files(unit: str, exts: tuple, select: str | None,
                   include_tests: bool, max_files: int) -> list[str]:
    import fnmatch

    found = []
    for dirpath, dirnames, filenames in os.walk(unit):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if not name.endswith(exts):
                continue
            if select and not fnmatch.fnmatch(os.path.join(dirpath, name), select) \
                    and not fnmatch.fnmatch(name, select):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), unit)
            parts = rel.split(os.sep)
            is_test = ("tests" in parts or "test" in parts or "__tests__" in parts
                       or name.endswith(("_test.rs", ".test.ts", ".spec.ts", ".d.ts")))
            if is_test and not include_tests:
                continue
            found.append(os.path.join(dirpath, name))
    found.sort()
    return found[:max_files] if max_files else found


# --------------------------------------------------------------------------- #
# Rows
# --------------------------------------------------------------------------- #

def branch_row(unit, path, line, fn, kind, predicate, path_cond, reads,
               external, calls, effects, macro_context="", reads_object_state=False,
               captured_reads=None):
    captured_reads = captured_reads or []
    return {
        "unit": unit,
        "file": path,
        "line": line,
        "fn": fn,
        "kind": kind,
        "predicate": predicate,
        "path_condition": path_cond,
        "purity": "impure" if (external or calls or captured_reads) else "pure",
        "reads": reads,
        "external_reads": external,
        "captured_reads": captured_reads,
        "calls": calls,
        "effects": effects,
        "macro_context": macro_context,
        "reads_object_state": reads_object_state,
    }


def carrier_row(unit, name, kind, path, line, closure, states=None,
                detail="", evidence=""):
    return {
        "unit": unit,
        "name": name,
        "kind": kind,
        "declared_at": f"{path}:{line}",
        "closure": closure,
        "states": states or [],
        "detail": detail,
        "evidence": evidence,
    }


def summarize(rows, carriers, files, limits):
    by_closure = {c: 0 for c in CLOSURES}
    for c in carriers:
        by_closure[c["closure"]] = by_closure.get(c["closure"], 0) + 1
    pure = sum(1 for r in rows if r["purity"] == "pure")
    state = sum(1 for r in rows if r["purity"] == "pure" and r.get("reads_object_state"))
    return {
        "schema": SCHEMA,
        "files_parsed": len(files),
        "branches": len(rows),
        "pure": pure,
        "impure": len(rows) - pure,
        "pure_percent": round(pure / len(rows) * 100) if rows else 0,
        "state_dependent": state,
        "carriers": len(carriers),
        "carriers_by_closure": {k: v for k, v in by_closure.items() if v},
        "limits": limits,
    }


def emit(unit, rows, carriers, files, limits, opts) -> None:
    summary = summarize(rows, carriers, files, limits)
    if opts["json"]:
        print(json.dumps({
            "summary": summary,
            "carriers": carriers,
            "branches": rows,
        }, indent=1, ensure_ascii=False))
        return

    print(f"# {SCHEMA} — {unit}")
    print(f"# files {summary['files_parsed']}  branches {summary['branches']}  "
          f"pure {summary['pure']} ({summary['pure_percent']}%)  "
          f"impure {summary['impure']}  "
          f"of the pure ones read receiver state: {summary['state_dependent']}")
    if summary["carriers_by_closure"]:
        print("# carriers " + "  ".join(f"{k} {v}"
                                        for k, v in summary["carriers_by_closure"].items()))
    if limits:
        print("# limits " + "  ".join(f"{k} {v}" for k, v in limits.items() if v))

    if carriers:
        order = {"enum": 0, "const_vocabulary": 1, "alias": 2, "registered": 3,
                 "struct": 8}
        carriers = sorted(carriers, key=lambda c: (order.get(c["kind"], 5),
                                                   c["name"].lower()))
        print("\n## carriers (state bearers)")
        for c in carriers:
            states = "{" + ",".join(c["states"]) + "}" if c["states"] else "-"
            print(f"C {c['name']} [{c['kind']}/{c['closure']}] {states} "
                  f"@ {c['declared_at']}" + (f" — {c['detail']}" if c["detail"] else ""))

    if rows:
        print("\n## branches")
        for r in rows:
            reads = ", ".join(
                f"{x['symbol']}={x['origin']}:{x.get('type') or '?'}" for x in r["reads"]
            ) or "-"
            print(f"\nB {r['file']}:{r['line']} {r['fn']} [{r['kind']}] {r['purity']}")
            print(f"  when: {r['predicate']}")
            if r["path_condition"] and r["path_condition"] != r["predicate"]:
                print(f"  path: {r['path_condition']}")
            print(f"  reads: {reads}")
            if r["external_reads"]:
                print(f"  ext: {', '.join(r['external_reads'])}")
            if r.get("captured_reads"):
                print(f"  captured: {', '.join(r['captured_reads'])} — closure state, "
                      f"not an argument")
            if r["calls"]:
                print(f"  calls: {', '.join(r['calls'])}")
            if r.get("reads_object_state"):
                print("  state: reads self.*/this.* — the trigger depends on the "
                      "receiver's state, not only on the arguments")
            eff = r["effects"]
            parts = []
            for key in ("returns", "writes", "throws", "awaits"):
                if eff.get(key):
                    parts.append(f"{key} {'; '.join(eff[key])}")
            print("  out: " + (" | ".join(parts) if parts else "-"))
            if r["macro_context"]:
                print(f"  macro: {r['macro_context']}")


# --------------------------------------------------------------------------- #
# Purity
# --------------------------------------------------------------------------- #

def classify_identifier(name, params, locals_, typed, self_name):
    """Return (origin, type, closure) for one identifier read in a predicate."""
    t = typed.get(name)
    if name in params:
        return "param", t, closure_for_type(t)
    if name in locals_:
        return "local", t, closure_for_type(t)
    if name == self_name:
        return "self", None, None
    return "external", None, None


def callee_name(text: str) -> str:
    """`a.b.c::<T>(` -> `c`, so whitelists match the method, not the receiver."""
    t = text.split("(")[0].strip()
    t = t.split("::<")[0]
    for sep in ("::", "."):
        if sep in t:
            t = t.split(sep)[-1]
    return t.strip()


def closure_for_type(t):
    if not t:
        return None
    t = t.strip()
    if t in ("bool", "boolean"):
        return "closed"
    if t.startswith("Option<") or t.startswith("Result<"):
        return "closed"
    if t.endswith(" | undefined") or t.endswith("| undefined"):
        return "closed"
    if t in ("number", "f64", "f32", "i8", "i16", "i32", "i64", "i128", "u8", "u16",
             "u32", "u64", "u128", "usize", "isize", "u64", "&str", "String", "string"):
        return "open"
    if t.startswith("Vec<") or t.endswith("[]"):
        return "open"
    return None


def one_line(s: str, limit: int = 220) -> str:
    s = " ".join(s.split())
    return s if len(s) <= limit else s[:limit - 1] + "…"
