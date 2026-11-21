#!/usr/bin/env python3
"""TypeScript branch map for pdd:study — the same table as the Rust front end.

Same row schema, same closure vocabulary, same purity rule, same limits
discipline as `branch_map_rust.py`; only the grammar walking differs. A study
subagent that was given a pnpm package and one that was given a cargo member
hand their main agent tables of the same shape.

    python3 branch_map_ts.py packages/uniterra-desktop/src
    python3 branch_map_ts.py --member uniterra-desktop --select 'src/**/*.ts'
    python3 branch_map_ts.py --member uniterra-provider --json

Selection: `--member NAME` resolves NAME against the nearest `package.json`
`workspaces` list, or `pnpm-workspace.yaml` `packages:` when that is what the
repository uses. `--select GLOB` narrows inside the unit — that is how a package
root is addressed.

What TypeScript adds to the Rust picture, and what it takes away:
  + a union of string literals is a *closed* state set at the type level, the
    closest thing either language has to an enumerable state
  − that set is erased at runtime; nothing stops `as Status` from producing a
    value outside it, so `closed` here means "closed if every writer respects
    the type", which the compiler checks only where types survive
  + optional chaining (`?.`), `??`, `&&`/`||` are decision sites with no `if`
  − decorators, `proxy`, and `x[k]()` dispatch hide decisions; `unresolved
    dispatch` and `any` are counted under `# limits`, never resolved

Exit: 0 ok · 2 dependency missing · 3 unit not found · 4 parse errors.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _branchmap as bm

EXT = (".ts", ".tsx", ".mts", ".cts")


# --------------------------------------------------------------------------- #
# unit resolution
# --------------------------------------------------------------------------- #

def workspace_members(start: str):
    """Nearest package.json `workspaces`, else pnpm-workspace.yaml `packages`."""
    cur = os.path.abspath(start)
    while True:
        pkg = os.path.join(cur, "package.json")
        if os.path.isfile(pkg):
            text = open(pkg, encoding="utf-8", errors="replace").read()
            m = re.search(r'"workspaces"\s*:\s*(\[[^\]]*\]|\{[^}]*"packages"\s*:\s*\[[^\]]*\])',
                          text, re.S)
            if m:
                # every quoted string here is a workspace pattern or a member path;
                # `workspaces` itself is a key, not a value, so it never matches
                patterns = [n for n in re.findall(r'"([^"]+)"', m.group(1)) if n != "packages"]
                if patterns:
                    return cur, patterns
        pnpm = os.path.join(cur, "pnpm-workspace.yaml")
        if os.path.isfile(pnpm):
            text = open(pnpm, encoding="utf-8", errors="replace").read()
            block = re.search(r"packages\s*:\s*\n((?:\s*-\s*.+\n?)+)", text)
            if block:
                names = re.findall(r"-\s*['\"]?([^'\"\n]+?)['\"]?\s*$", block.group(1), re.M)
                return cur, names
        parent = os.path.dirname(cur)
        if parent == cur:
            return None, []
        cur = parent


def resolve_unit(opts):
    unit = opts["unit"]
    member = opts["member"]
    root = opts["root"] or (unit or os.getcwd())
    if member:
        ws, patterns = workspace_members(root)
        if ws is None:
            bm.die(3, f"branch_map_ts: no package.json workspaces or "
                      f"pnpm-workspace.yaml above {root!r}")
        import glob as _glob
        hit = os.path.join(ws, member)
        if not os.path.isdir(hit):
            # a member may be addressed by bare name while the workspace declares a
            # glob (`packages/*`); expand the pattern before declaring it missing
            candidates = []
            for p in patterns:
                candidates.extend(d for d in _glob.glob(os.path.join(ws, p)) if os.path.isdir(d))
            match = [d for d in candidates
                     if os.path.basename(d) == member
                     or os.path.relpath(d, ws) == member.rstrip("/")]
            if not match:
                known = ", ".join(sorted(os.path.basename(d) for d in candidates)) or "(none)"
                bm.die(3, f"branch_map_ts: member {member!r} not found under {ws}\n"
                          f"  workspace patterns: {', '.join(patterns) or '(none)'}\n"
                          f"  known members: {known}")
            hit = match[0]
        return hit, ws
    if not os.path.isdir(unit):
        bm.die(3, f"branch_map_ts: not a directory: {unit!r}")
    ws, _ = workspace_members(unit)
    return os.path.abspath(unit), ws or os.path.abspath(unit)


# --------------------------------------------------------------------------- #
# tree helpers
# --------------------------------------------------------------------------- #

def walk(n):
    yield n
    stack = [n]
    while stack:
        cur = stack.pop()
        for c in cur.children:
            yield c
            stack.append(c)


def txt(src, n):
    return src[n.start_byte:n.end_byte].decode("utf-8", "replace")


def field(n, name):
    return n.child_by_field_name(name)


FUNCS = {"function_declaration", "function_expression", "arrow_function",
         "method_definition", "generator_function", "generator_function_declaration"}


def unwrap(node):
    """`(x)` -> `x`, so a predicate is compared without its parentheses."""
    cur = node
    while cur is not None and cur.type == "parenthesized_expression" and cur.named_children:
        cur = cur.named_children[0]
    return cur


def type_text(src, node):
    t = field(node, "type")
    if t is None:
        return None
    return bm.one_line(txt(src, t).lstrip(": "), 60)


def fn_params(src, fn):
    """Parameter name -> declared type. Destructured parameters contribute every
    identifier they bind, because the predicate reads the binding, not the object."""
    out = {}
    params = field(fn, "parameters") or field(fn, "parameter")
    if params is None:
        return out
    for p in params.named_children:
        if p.type in ("required_parameter", "optional_parameter"):
            pat = field(p, "pattern")
            if pat is not None and pat.type == "identifier":
                out[txt(src, pat)] = type_text(src, p)
            elif pat is not None:
                for d in walk(pat):
                    if d.type in ("identifier", "shorthand_property_identifier_pattern"):
                        out[txt(src, d)] = None
        elif p.type == "identifier":
            out[txt(src, p)] = None
        elif p.type in ("object_pattern", "array_pattern"):
            for d in walk(p):
                if d.type in ("identifier", "shorthand_property_identifier_pattern"):
                    out[txt(src, d)] = None
    return out


def fn_locals(src, fn):
    out = {}
    for n in walk(fn):
        if n.type != "variable_declarator":
            continue
        name_node = field(n, "name")
        if name_node is None or name_node.type != "identifier":
            continue
        t = type_text(src, n)
        if t is None:
            v = field(n, "value")
            if v is not None:
                if v.type == "true" or v.type == "false":
                    t = "boolean"
                elif v.type in ("number",):
                    t = "number"
                elif v.type == "string":
                    t = "string"
        out[txt(src, name_node)] = (t, n.start_byte)
    return out


# --------------------------------------------------------------------------- #
# carriers
# --------------------------------------------------------------------------- #

def union_members(src, node):
    """Every literal in a (possibly nested) union type."""
    out = []
    for n in walk(node):
        if n.type == "literal_type":
            inner = n.named_children[0] if n.named_children else None
            if inner is not None:
                if inner.type == "string":
                    frag = [c for c in inner.named_children if c.type == "string_fragment"]
                    out.append(bm.one_line(txt(src, frag[0]), 40) if frag
                               else bm.one_line(txt(src, inner), 40).strip("\"'"))
                elif inner.type in ("number", "true", "false", "null", "undefined"):
                    out.append(bm.one_line(txt(src, inner), 40))
    return out


def union_type_names(src, node):
    """Variant type names of a union (`NpmBuiltin | CopyBuiltin`), if that is what it is."""
    if node is None or node.type != "union_type":
        return []
    out = []
    for n in walk(node):
        if n.type in ("type_identifier", "nested_type_identifier"):
            out.append(bm.one_line(txt(src, n), 40))
    return out if len(out) >= 2 else []


def carriers_for_file(src, root, path, unit):
    rows = []
    for n in walk(root):
        if n.type == "type_alias_declaration":
            name_node = field(n, "name")
            name = txt(src, name_node) if name_node is not None else "?"
            val = field(n, "value")
            members = union_members(src, val) if val is not None else []
            shapes = union_type_names(src, val) if val is not None else []
            if not members and shapes:
                rows.append(bm.carrier_row(
                    unit, name, "union", path, n.start_point[0] + 1, "closed", shapes,
                    detail="discriminated union of types — the variants are the states; "
                           "the branch that selects one tests its discriminant"))
            elif members:
                rows.append(bm.carrier_row(
                    unit, name, "union", path, n.start_point[0] + 1, "closed", members,
                    detail="string/number literal union — closed at the type level, "
                           "erased at runtime"))
            else:
                vtext = bm.one_line(txt(src, val), 60) if val is not None else "?"
                if "=>" in vtext or vtext.startswith("("):
                    continue  # a callable is not a state bearer
                if vtext.startswith(("string", "number")):
                    closure, detail = "open", f"alias of {vtext} — any value of that type"
                else:
                    closure, detail = "declared", f"alias of {vtext} — states belong to that type"
                rows.append(bm.carrier_row(unit, name, "alias", path,
                                           n.start_point[0] + 1, closure, [], detail))
        elif n.type == "enum_declaration":
            name_node = field(n, "name")
            name = txt(src, name_node) if name_node is not None else "?"
            members = []
            body = field(n, "body")
            if body is not None:
                for m in walk(body):
                    if m.type == "enum_assignment":
                        v = field(m, "value")
                        nm = field(m, "name")
                        members.append(bm.one_line(txt(src, v), 40) if v is not None
                                       else (txt(src, nm) if nm is not None else "?"))
                    elif m.type == "property_identifier":
                        members.append(txt(src, m))
            rows.append(bm.carrier_row(
                unit, name, "enum", path, n.start_point[0] + 1, "declared", members,
                detail="TS enum: the members are declared, and any number/string can "
                       "be cast into the type"))
        elif n.type == "interface_declaration":
            name_node = field(n, "name")
            name = txt(src, name_node) if name_node is not None else "?"
            fields = []
            body = field(n, "body")
            if body is not None:
                for p in walk(body):
                    if p.type == "property_signature":
                        nm = field(p, "name")
                        if nm is not None:
                            fields.append(txt(src, nm))
            rows.append(bm.carrier_row(
                unit, name, "interface", path, n.start_point[0] + 1, "product", fields,
                detail=f"{len(fields)} fields — the state is their product, not one value"))
    return rows


# --------------------------------------------------------------------------- #
# branches
# --------------------------------------------------------------------------- #

def callee_of(src, fn):
    if fn.type == "member_expression":
        prop = field(fn, "property")
        return txt(src, prop) if prop is not None else "?"
    if fn.type in ("identifier", "property_identifier"):
        return txt(src, fn)
    if fn.type == "subscript_expression":
        return "[computed]"
    return bm.callee_name(bm.one_line(txt(src, fn), 60))


def base_origin(src, node):
    cur = node
    while cur is not None:
        if cur.type in ("identifier", "this", "super"):
            return txt(src, cur)
        if cur.type == "member_expression":
            cur = field(cur, "object")
        elif cur.type == "parenthesized_expression":
            cur = unwrap(cur)
        elif cur.type == "call_expression":
            cur = field(cur, "function")
        elif cur.type == "await_expression":
            cur = cur.named_children[0] if cur.named_children else None
        else:
            return None
    return None


def reads_of(src, cond, params, locals_, captured=()):
    reads, external, calls, captured_hits = [], [], [], []
    object_state = False

    def add(symbol, origin, typ=None, closure=None):
        reads.append({"symbol": symbol, "origin": origin, "type": typ, "closure": closure})
        if origin == "external":
            external.append(symbol)
        elif origin == "captured":
            captured_hits.append(symbol)

    def resolve(node):
        nonlocal object_state
        if node is None:
            return
        if node.type == "identifier":
            name = txt(src, node)
            if name in captured and name not in params and name not in locals_:
                add(name, "captured")
                return
            if name in ("true", "false", "null", "undefined", "this"):
                if name == "this":
                    object_state = True
                    add("this", "self")
                return
            origin, typ, closure = bm.classify_identifier(name, params, locals_, params, "this")
            if name == "this":
                object_state = True
                add("this", "self")
                return
            if name in bm.JS_GLOBALS:
                add(name, "global")
                return
            add(name, origin, typ, closure)
            return
        if node.type in ("this",):
            object_state = True
            add("this", "self")
            return
        if node.type == "member_expression":
            whole = bm.one_line(txt(src, node), 60)
            base = base_origin(src, node)
            if base == "this":
                object_state = True
                add(whole, "self")
            elif base in params or base in locals_:
                add(whole, "param" if base in params else "local",
                    params.get(base) or (locals_.get(base) or (None,))[0])
            elif base in captured:
                add(whole, "captured")
            elif base and base[0].isupper():
                add(whole, "type")   # `Kind.A` — a member of a type/namespace
            else:
                add(whole, "external")
            return
        if node.type == "call_expression":
            fn = field(node, "function")
            if fn is not None:
                name = callee_of(src, fn)
                qualified = name
                if fn.type == "member_expression":
                    obj = field(fn, "object")
                    base = base_origin(src, obj)
                    if base:
                        qualified = f"{base}.{name}"
                    if base in bm.JS_GLOBALS:
                        pass  # a library call on a language binding
                    elif base not in params and base not in locals_ and base != "this":
                        resolve(obj)
                if name not in bm.TS_PURE_CALLS and qualified not in bm.TS_PURE_CALLS:
                    calls.append(qualified if qualified != name else name)
                elif fn.type == "subscript_expression":
                    calls.append("[computed dispatch]")
            args = field(node, "arguments")
            if args is not None:
                for a in args.named_children:
                    resolve(a)
            return
        for c in node.named_children:
            resolve(c)

    resolve(cond)
    seen, uniq = set(), []
    for r in reads:
        if r["symbol"] in seen:
            continue
        seen.add(r["symbol"])
        uniq.append(r)
    return uniq, sorted(set(external)), sorted(set(calls)), object_state, sorted(set(captured_hits))


def effects_of(src, node, limit=6):
    out = {"returns": [], "writes": [], "throws": [], "awaits": [], "calls": []}
    body = consequence_of(node)
    if body is None:
        return out
    for n in walk(body):
        if n.type == "return_statement":
            out["returns"].append(bm.one_line(txt(src, n), 100))
        elif n.type in ("assignment_expression", "augmented_assignment_expression"):
            out["writes"].append(bm.one_line(txt(src, n), 100))
        elif n.type == "await_expression":
            out["awaits"].append(bm.one_line(txt(src, n), 100))
        elif n.type == "throw_statement":
            out["throws"].append(bm.one_line(txt(src, n), 100))
        elif n.type == "call_expression":
            fn = field(n, "function")
            if fn is not None:
                out["calls"].append(callee_of(src, fn))
    for k in out:
        seen, uniq = set(), []
        for v in out[k]:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        out[k] = uniq[:limit]
    return {k: v for k, v in out.items() if v}


def consequence_of(node):
    if node.type == "if_statement":
        return field(node, "consequence")
    if node.type == "switch_case" or node.type == "switch_default":
        return node
    if node.type == "catch_clause":
        return node
    if node.type == "ternary_expression":
        return field(node, "consequence")
    return None


def path_condition(src, node, stop):
    parts = []
    cur = node.parent
    while cur is not None and cur.id != stop.id:
        if cur.type == "if_statement":
            c = unwrap(field(cur, "condition"))
            if c is not None:
                parts.append(bm.one_line(txt(src, c), 100))
        elif cur.type in ("switch_case", "switch_default"):
            parts.append(bm.one_line(txt(src, cur), 80).rstrip(":"))
        elif cur.type == "ternary_expression":
            c = field(cur, "condition")
            if c is not None:
                parts.append(bm.one_line(txt(src, c), 80))
        cur = cur.parent
    return " && ".join(reversed(parts))


def nested_in_short_circuit(src, node):
    """A `&&` inside another `&&`, or one that is exactly a branch's condition,
    is already represented by the row for that outer site."""
    cur = node.parent
    while cur is not None:
        if cur.type == "binary_expression":
            op = field(cur, "operator")
            if op is not None and txt(src, op) in ("&&", "||", "??"):
                return True
        if cur.type in ("if_statement", "ternary_expression", "while_statement",
                        "do_statement"):
            c = unwrap(field(cur, "condition"))
            if c is not None and bm.one_line(txt(src, c)) == bm.one_line(txt(src, node)):
                return True
        if cur.type in FUNCS:
            return False
        cur = cur.parent
    return False


def is_else_if(node):
    p = node.parent
    return p is not None and p.type == "else_clause"


def fn_name(src, fn):
    name_node = field(fn, "name")
    if name_node is not None:
        return txt(src, name_node)
    parent = fn.parent
    if parent is not None and parent.type == "variable_declarator":
        nm = field(parent, "name")
        if nm is not None and nm.type == "identifier":
            return txt(src, nm)
    if parent is not None and parent.type == "pair":
        key = field(parent, "key")
        if key is not None:
            return txt(src, key)
    if parent is not None and parent.type == "assignment_expression":
        left = field(parent, "left")
        if left is not None and left.type in ("identifier", "member_expression"):
            return bm.one_line(txt(src, left), 60)
    return "<anonymous>"


def walk_own(fn, skip):
    """Descendants of one function, not descending into nested functions.

    A nested arrow has its own parameters, so attributing its branches to the
    enclosing function's parameter list mislabels every read in them.
    """
    stack = [fn]
    while stack:
        cur = stack.pop()
        for c in cur.children:
            if c.id == fn.id:
                continue
            if c.type in skip and c.id != fn.id:
                yield c
                continue
            yield c
            stack.append(c)


def captured_names(src, fn):
    """Locals of every enclosing function: closure state, not arguments."""
    out = set()
    cur = fn.parent
    while cur is not None:
        if cur.type in FUNCS:
            out.update(fn_locals(src, cur))
            out.update(fn_params(src, cur))
        cur = cur.parent
    return out


def branches_for_fn(src, fn, unit, path):
    params = fn_params(src, fn)
    captured = captured_names(src, fn)
    locals_ = fn_locals(src, fn)
    fname = fn_name(src, fn)
    rows = []
    for n in walk_own(fn, FUNCS):
        kind = None
        cond = None
        if n.type == "if_statement":
            kind = "else_if" if is_else_if(n) else "if"
            cond = unwrap(field(n, "condition"))
        elif n.type == "switch_case":
            kind = "switch_case"
            cond = field(n, "value")
        elif n.type == "switch_default":
            kind = "switch_default"
        elif n.type == "ternary_expression":
            kind = "ternary"
            cond = field(n, "condition")
        elif n.type == "catch_clause":
            kind = "catch"
            cond = field(n, "parameter")
        elif n.type == "binary_expression":
            op = field(n, "operator")
            if op is not None and txt(src, op) in ("&&", "||", "??"):
                if nested_in_short_circuit(src, n):
                    continue
                kind = f"short_circuit_{txt(src, op)}"
                cond = n
        elif n.type == "member_expression" and "?." in txt(src, n):
            kind = "optional_chain"
            cond = n
        if kind is None:
            continue

        local_types = {k: v[0] for k, v in locals_.items()}
        reads, external, calls, obj, cap = ([], [], [], False, [])
        if cond is not None:
            reads, external, calls, obj, cap = reads_of(src, cond, params, local_types,
                                                        captured)
            reads = [r for r in reads if r["origin"] != "local"
                     or (locals_.get(r["symbol"]) or (None, 0))[1] < n.start_byte] or reads

        rows.append(bm.branch_row(
            unit, path, n.start_point[0] + 1, fname, kind,
            bm.one_line(txt(src, cond), 200) if cond is not None else "(default)",
            path_condition(src, n, fn), reads, external, calls,
            effects_of(src, n), reads_object_state=obj, captured_reads=cap))
    return rows


def scan_file(path, unit, mods):
    src = open(path, "rb").read()
    from tree_sitter import Language, Parser
    lang = Language(mods["tsx"].language_tsx() if path.endswith(".tsx")
                    else mods["ts"].language_typescript())
    root = Parser(lang).parse(src).root_node
    errors = sum(1 for n in walk(root) if n.type == "ERROR" or n.is_missing)
    rows, carriers = [], carriers_for_file(src, root, path, unit)
    for n in walk(root):
        if n.type in FUNCS:
            rows.extend(branches_for_fn(src, n, unit, path))
    limits = {
        "any_annotations": len(re.findall(rb":\s*any\\b|as any\\b", src)),
        "ts_ignore": len(re.findall(rb"@ts-(?:ignore|nocheck|expect-error)", src)),
        "computed_dispatch": sum(1 for n in walk(root)
                                 if n.type == "call_expression"
                                 and field(n, "function") is not None
                                 and field(n, "function").type == "subscript_expression"),
    }
    return rows, carriers, errors, limits


def main(argv):
    opts = bm.parse_args(argv, "ts")
    mods = bm.require_tree_sitter("typescript",
                                 {"ts": "tree_sitter_typescript",
                                  "tsx": "tree_sitter_typescript"})
    unit, ws = resolve_unit(opts)
    files = bm.discover_files(unit, EXT, opts["select"], opts["include_tests"],
                              opts["max_files"])
    if not files:
        bm.die(3, f"branch_map_ts: no TypeScript files under {unit!r}"
                  + (f" matching {opts['select']!r}" if opts["select"] else ""))

    rows, carriers, total_errors = [], [], 0
    limits = {"any_annotations": 0, "ts_ignore": 0, "computed_dispatch": 0}
    for f in files:
        try:
            scanned = scan_file(f, unit, mods)
        except Exception as exc:
            bm.die(4, f"branch_map_ts: failed on {f}: {exc}")
        r, c, errs, lim = scanned
        rows.extend(r)
        carriers.extend(c)
        total_errors += errs
        for k, v in lim.items():
            limits[k] = limits.get(k, 0) + v

    if total_errors and not opts["allow_parse_errors"]:
        bm.die(4, f"branch_map_ts: {total_errors} parse error node(s) across "
                  f"{len(files)} file(s). The tree is incomplete, so the table is not "
                  f"evidence. Re-run with --allow-parse-errors to see what parsed.")
    limits["parse_errors"] = total_errors
    rows.sort(key=lambda r: (r["file"], r["line"]))
    if opts["max_branches"]:
        rows = rows[:opts["max_branches"]]
    bm.emit(f"{unit} (workspace {ws})", rows, carriers, files, limits, opts)


if __name__ == "__main__":
    main(sys.argv[1:])
