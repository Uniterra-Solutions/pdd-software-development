#!/usr/bin/env python3
"""Rust branch map for pdd:study — mechanical facts about decisions and state.

Reads a cargo workspace member (or a package root inside one) and prints, for
every decision site, the predicate it evaluates, where each symbol in that
predicate comes from, and what the branch does; plus every state bearer the
unit declares and how complete its state list is.

What this script is for: the model does not read the member to find out *which*
conditional it is looking at — it reads this table and decides *which of these
sites the caller can observe*, and names the behaviour. The table is the raw
material, never the answer.

    python3 branch_map_rust.py crates/api/src/server
    python3 branch_map_rust.py --member crates/api --select 'src/server/*.rs'
    python3 branch_map_rust.py --member fissura-core --json

Selection: `<unit-path>` is any directory. `--member NAME` resolves NAME against
the nearest Cargo.toml `members` list (walking up from --root or the cwd), so
`--member fissura-core` finds `crates/fissura-core`. `--select GLOB` narrows
inside the unit, which is how a package root is addressed.

Known limits, printed with every run (`# limits`), never silently absorbed:
  macros      macro bodies are not expanded, so a decision written inside
              `macro_rules!` or a derives-generated branch is invisible here
  dyn/impl    calls through `dyn Trait` or a generic bound have no target in
              this file; they are counted, not resolved
  cfg         `#[cfg(feature = ...)]` alternatives are read as written; the
              build matrix is not consulted, so mutually exclusive arms appear
              side by side
  cfg(test)   test modules are skipped unless --include-tests

Exit: 0 ok · 2 dependency missing · 3 unit not found · 4 parse errors.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _branchmap as bm

EXT = (".rs",)
SKIP_MOD_ATTRS = ("cfg(test)", "cfg(all(test")


# --------------------------------------------------------------------------- #
# unit resolution
# --------------------------------------------------------------------------- #

def workspace_members(start: str):
    """Parse `members = [...]` from the nearest Cargo.toml, walking upward."""
    cur = os.path.abspath(start)
    while True:
        manifest = os.path.join(cur, "Cargo.toml")
        if os.path.isfile(manifest):
            text = open(manifest, encoding="utf-8", errors="replace").read()
            m = re.search(r"members\s*=\s*\[(.*?)\]", text, re.S)
            if m:
                names = re.findall(r'"([^"]+)"', m.group(1))
                return cur, [n for n in names if not any(c in n for c in "*?[")]
        parent = os.path.dirname(cur)
        if parent == cur:
            return None, []
        cur = parent


def resolve_unit(opts):
    unit = opts["unit"]
    member = opts["member"]
    root = opts["root"] or (unit or os.getcwd())
    if member:
        ws, names = workspace_members(root)
        if ws is None:
            bm.die(3, f"branch_map_rust: no Cargo.toml with a [workspace] members "
                      f"list above {root!r}")
        import glob as _glob
        candidates = []
        for n in names:
            if any(c in n for c in "*?["):
                candidates.extend(d for d in _glob.glob(os.path.join(ws, n)) if os.path.isdir(d))
            else:
                candidates.append(os.path.join(ws, n))
        hit = [d for d in candidates if d.rstrip("/") == member.rstrip("/")
               or os.path.basename(d.rstrip("/")) == member.rstrip("/")]
        if not hit:
            bm.die(3, f"branch_map_rust: member {member!r} is not in {ws}/Cargo.toml\n"
                      f"  known members: {', '.join(names) or '(none)'}")
        return os.path.join(ws, hit[0]), ws
    if not os.path.isdir(unit):
        bm.die(3, f"branch_map_rust: not a directory: {unit!r}")
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


FUNCS = {"function_item", "closure_expression"}
TYPE_NODES = {"type_identifier", "generic_type", "primitive_type", "scoped_type_identifier",
              "reference_type", "tuple_type", "array_type", "unit_type",
              "never_type", "dynamic_type", "bounded_type"}


def txt(src, n):
    return src[n.start_byte:n.end_byte].decode("utf-8", "replace")


def field(n, name):
    return n.child_by_field_name(name)


def nth_named(n, i):
    kids = n.named_children
    return kids[i] if i < len(kids) else None


def has_attr(src, node, needles):
    """True when a preceding attribute_item contains one of `needles`."""
    prev = node.prev_named_sibling
    while prev is not None and prev.type in ("attribute_item", "line_comment", "block_comment"):
        if prev.type == "attribute_item" and any(s in txt(src, prev) for s in needles):
            return True
        prev = prev.prev_named_sibling
    return False


def fn_params(src, fn):
    """name -> declared type text, for parameters of one function."""
    out = {}
    params = field(fn, "parameters")
    if params is None:
        return out
    for p in params.named_children:
        if p.type == "self_parameter":
            out["self"] = "self"
            continue
        if p.type != "parameter":
            continue
        name = None
        typ = None
        for c in p.named_children:
            if c.type == "identifier" and name is None:
                name = txt(src, c)
            elif c.type == "type_identifier" or c.type in TYPE_NODES:
                typ = bm.one_line(txt(src, c), 60)
            elif c.type == "mut_pattern":
                name = bm.one_line(txt(src, c).replace("mut ", ""), 40)
        if name:
            out[name] = typ
    return out


def fn_locals(src, fn):
    """name -> (type text | inferred, byte offset). Only lets, which is enough:
    a local mutably assigned without a let is a pattern we report as unknown."""
    out = {}
    for n in walk(fn):
        if n.type != "let_declaration":
            continue
        pat = field(n, "pattern")
        typ = field(n, "type")
        val = field(n, "value")
        if pat is None:
            continue
        name = None
        if pat.type == "identifier":
            name = txt(src, pat)
        elif pat.type in ("tuple_pattern", "struct_pattern", "ref_pattern"):
            ids = [txt(src, c) for c in pat.named_children if c.type == "identifier"]
            name = ids[0] if ids else None
        if not name:
            continue
        t = bm.one_line(txt(src, typ), 60) if typ is not None else None
        if not t and val is not None:
            if val.type in ("boolean_literal",):
                t = "bool"
            elif val.type in ("integer_literal", "float_literal"):
                t = "number"
            elif val.type == "call_expression":
                f = field(val, "function")
                t = bm.one_line(txt(src, f), 60) if f is not None else None
        out[name] = (t, n.start_byte)
    return out


# --------------------------------------------------------------------------- #
# carriers
# --------------------------------------------------------------------------- #

def carriers_for_file(src, root, path, unit):
    rows = []
    consts = []
    for n in walk(root):
        if n.type == "enum_item":
            name = txt(src, field(n, "name")) if field(n, "name") is not None else "?"
            variants = []
            body = field(n, "body")
            if body is not None:
                for v in walk(body):
                    if v.type == "enum_variant":
                        vn = field(v, "name")
                        if vn is not None:
                            variants.append(txt(src, vn))
            closure = "declared" if has_attr(src, n, ("non_exhaustive",)) else "closed"
            rows.append(bm.carrier_row(
                unit, name, "enum", path, n.start_point[0] + 1, closure, variants,
                detail="non_exhaustive: downstream crates may not match exhaustively"
                if closure == "declared" else ""))
        elif n.type == "struct_item":
            name = txt(src, field(n, "name")) if field(n, "name") is not None else "?"
            fields = []
            body = field(n, "body")
            if body is not None:
                for f in walk(body):
                    if f.type == "field_declaration":
                        fn_ = field(f, "name")
                        if fn_ is not None:
                            fields.append(txt(src, fn_))
            rows.append(bm.carrier_row(
                unit, name, "struct", path, n.start_point[0] + 1, "product", fields,
                detail=f"{len(fields)} fields — the state is their product, not one value"))
        elif n.type == "type_item":
            name = txt(src, field(n, "name")) if field(n, "name") is not None else "?"
            rhs = field(n, "type")
            rhs_text = bm.one_line(txt(src, rhs), 60) if rhs is not None else "?"
            # an alias borrows another type's closure; without cross-file resolution
            # the honest label is `declared`, with the target named so the next
            # reader resolves it in that type's own declaration.
            closure = "closed" if rhs_text.startswith(("Option<", "Result<")) else "declared"
            rows.append(bm.carrier_row(
                unit, name, "alias", path, n.start_point[0] + 1, closure, [],
                detail=f"alias of {rhs_text} — its states are that type's"))
        elif n.type == "const_item":
            name = field(n, "name")
            val = field(n, "value")
            if name is not None and val is not None and val.type == "string_literal":
                raw = txt(src, val).strip('"')
                # only token-shaped values: a message string is not a state name
                if re.fullmatch(r"[a-z][a-z0-9_.:-]{2,60}", raw):
                    consts.append((txt(src, name), raw))
    if consts:
        rows.append(bm.carrier_row(
            unit, f"{os.path.basename(path)}:consts", "const_vocabulary", path, 1,
            "declared", [v for _, v in consts],
            detail="string constants: declared, not enforced — any literal may appear elsewhere"))
    return rows


# --------------------------------------------------------------------------- #
# branches
# --------------------------------------------------------------------------- #

def predicate_of(src, node):
    """The expression a branch tests, without the `if`/`while` keyword."""
    if node.type in ("if_expression", "while_expression"):
        return field(node, "condition")
    if node.type == "match_arm":
        return field(node, "pattern")
    if node.type == "let_declaration":
        return field(node, "pattern")
    return None


def consequence_of(node):
    if node.type == "if_expression":
        return field(node, "consequence")
    if node.type == "while_expression":
        return field(node, "body")
    if node.type == "match_arm":
        return field(node, "value")
    if node.type == "let_declaration":
        alt = field(node, "alternative")
        return alt
    return None


def match_arm_guard(src, arm):
    """`Pattern if guard => ...` — return the guard expression text, if any."""
    seen_pattern = False
    for c in arm.children:
        if c.type == "match_pattern":
            seen_pattern = True
            # a guard may live inside the pattern node
            for g in c.children:
                if g.type not in ("match_pattern",) and g.parent is not None:
                    pass
            for g in c.named_children:
                if g is not c and g.type not in ("match_pattern",):
                    return c, g
            continue
        if seen_pattern and c.type == "=>":
            return c, None
        if seen_pattern and c.is_named and c.type != "block":
            return arm, c
    # fall back: scan for the `if` keyword after the pattern
    kids = arm.children
    for i, c in enumerate(kids):
        if c.type == "match_pattern":
            if i + 2 < len(kids) and kids[i + 1].type == "if":
                return kids[i], kids[i + 2]
    return (kids[0] if kids else arm), None


def effects_of(src, node, limit=6):
    out = {"returns": [], "writes": [], "throws": [], "awaits": [], "calls": []}
    body = consequence_of(node)
    if body is None:
        return out
    for n in walk(body):
        if n.type == "return_expression":
            out["returns"].append(bm.one_line(txt(src, n), 100))
        elif n.type in ("assignment_expression", "compound_assignment_expr"):
            out["writes"].append(bm.one_line(txt(src, n), 100))
        elif n.type == "await_expression":
            out["awaits"].append(bm.one_line(txt(src, n), 100))
        elif n.type == "macro_invocation":
            mac = field(n, "macro")
            name = bm.one_line(txt(src, mac), 40) if mac is not None else "?"
            if name.rstrip("!") in ("panic", "unreachable", "todo", "unimplemented",
                                    "assert", "assert_eq", "assert_ne", "bail", "ensure"):
                out["throws"].append(name)
        elif n.type == "call_expression":
            f = field(n, "function")
            if f is not None:
                out["calls"].append(bm.one_line(txt(src, f), 50))
        if n.type == "call_expression":
            f = field(n, "function")
            if f is not None and bm.one_line(txt(src, f), 50) in ("unwrap", "expect"):
                out["throws"].append(bm.one_line(txt(src, f), 50))
    for k in out:
        seen, uniq = set(), []
        for v in out[k]:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        out[k] = uniq[:limit]
    return {k: v for k, v in out.items() if v}


def callee_of(src, fn):
    """The name being called, taken from the tree rather than from the text:
    `a.b::<T>(x)` -> `b`, `(0.0..=1.0).contains(x)` -> `contains`, `foo!(x)` -> `foo!`."""
    if fn.type == "field_expression":
        fld = field(fn, "field")
        return txt(src, fld) if fld is not None else "?"
    if fn.type == "identifier":
        return txt(src, fn)
    if fn.type == "scoped_identifier":
        last = fn.named_children[-1] if fn.named_children else fn
        return txt(src, last)
    if fn.type == "generic_function":
        inner = fn.named_children[0] if fn.named_children else fn
        return callee_of(src, inner)
    return bm.callee_name(bm.one_line(txt(src, fn), 80))


def reads_of(src, cond, params, locals_, captured=()):
    """Split the reads in a predicate into params / locals / object state / external.

    A method call is one read, not a read of its receiver plus a mystery symbol:
    `share.is_finite()` reads `share` and calls `is_finite`. The call list keeps
    only callees that are not on the pure whitelist, which is what decides
    `purity`.
    """
    reads, external, calls, captured_hits = [], [], [], []
    object_state = False

    def add(symbol, origin, typ=None, closure=None):
        reads.append({"symbol": symbol, "origin": origin, "type": typ, "closure": closure})
        if origin == "external":
            external.append(symbol)
        elif origin == "captured":
            captured_hits.append(symbol)

    def base_origin(node):
        """Left-most identifier of a chain: `self.cfg.cap` -> self."""
        cur = node
        while cur is not None:
            if cur.type in ("identifier", "self", "super", "crate"):
                return txt(src, cur)
            if cur.type == "field_expression":
                cur = field(cur, "value")
            elif cur.type == "index_expression":
                cur = cur.named_children[0] if cur.named_children else None
            elif cur.type == "call_expression":
                cur = field(cur, "function")
            elif cur.type == "parenthesized_expression":
                cur = cur.named_children[0] if cur.named_children else None
            elif cur.type == "await_expression":
                cur = cur.named_children[0] if cur.named_children else None
            else:
                return None
        return None

    def resolve(node):
        nonlocal object_state
        if node.type == "identifier":
            name = txt(src, node)
            if name in ("true", "false", "None", "Some", "Ok", "Err"):
                return
            origin, typ, closure = bm.classify_identifier(name, params, locals_, params,
                                                          "self")
            if name == "self":
                object_state = True
                add("self", "self")
                return
            if name in captured and name not in params and name not in locals_:
                add(name, "captured")
                return
            add(name, origin, typ, closure)
            return
        if node.type == "field_expression":
            base = base_origin(node)
            whole = bm.one_line(txt(src, node), 60)
            if base == "self":
                object_state = True
                add(whole, "self")
            elif base in params or base in locals_:
                add(whole, "param" if base in params else "local",
                    params.get(base) or locals_.get(base))
            elif base in captured:
                add(whole, "captured")
            elif base and base[0].isupper():
                add(whole, "type")   # `Mode::A` / `Foo::BAR` under a namespace
            else:
                add(whole, "external")
            return
        if node.type in ("scoped_identifier", "scoped_type_identifier"):
            # `Mode::Stream` is a variant path, not a read of someone's state
            add(bm.one_line(txt(src, node), 60), "type")
            return
        if node.type == "call_expression":
            fn = field(node, "function")
            if fn is not None:
                name = callee_of(src, fn)
                if name.rstrip("!") not in {x.rstrip("!") for x in bm.RUST_PURE_CALLS}:
                    calls.append(name)
                receiver = None
                if fn.type == "field_expression":
                    receiver = field(fn, "value")
                elif fn.type == "scoped_identifier":
                    receiver = None
                if receiver is not None and receiver.type != "identifier":
                    resolve(receiver)
                elif receiver is not None:
                    name0 = txt(src, receiver)
                    if name0 not in params and name0 not in locals_ and name0 != "self":
                        add(name0, "external")
                elif fn.type == "identifier" and txt(src, fn) not in params:
                    pass  # a free function call: listed in `calls`, not a read
            for a in field(node, "arguments").named_children if field(node, "arguments") else []:
                resolve(a)
            return
        if node.type in ("macro_invocation", "closure_expression", "block", "match_expression"):
            return  # not a value read; expanding it here would be a guess
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


def path_condition(src, node, stop):
    """The conjunction of enclosing if/match predicates, outermost first."""
    parts = []
    cur = node.parent
    while cur is not None and cur.id != stop.id:
        if cur.type == "if_expression":
            c = field(cur, "condition")
            if c is not None:
                parts.append(bm.one_line(txt(src, c), 120))
        elif cur.type == "match_arm":
            pat, guard = match_arm_guard(src, cur)
            if pat is not None:
                parts.append(f"match {bm.one_line(txt(src, pat), 80)}")
            if guard is not None:
                parts.append(bm.one_line(txt(src, guard), 80))
        cur = cur.parent
    return " && ".join(reversed(parts))


def walk_own(fn):
    """Descendants of one function, not descending into closures or nested fns."""
    stack = [fn]
    while stack:
        cur = stack.pop()
        for c in cur.children:
            yield c
            if c.type in FUNCS and c.id != fn.id:
                continue
            stack.append(c)


def captured_names(src, fn):
    """Locals and parameters of every enclosing function: closure state."""
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
    name_node = field(fn, "name")
    fname = txt(src, name_node) if name_node is not None else "<closure>"
    rows = []
    for n in walk_own(fn):
        kind = None
        if n.type == "if_expression":
            kind = "else_if" if (n.parent is not None and n.parent.type == "else_clause") else "if"
        elif n.type == "match_arm":
            kind = "match_arm"
        elif n.type == "while_expression":
            kind = "while"
        elif n.type == "let_declaration" and field(n, "alternative") is not None:
            kind = "let_else"
        elif n.type == "try_expression":
            kind = "try_question"
        if kind is None:
            continue

        if kind == "try_question":
            inner = n.named_children[0] if n.named_children else n
            rows.append(bm.branch_row(
                unit, path, n.start_point[0] + 1, fname, kind,
                f"{bm.one_line(txt(src, inner), 80)} is Err",
                path_condition(src, n, fn), [], [], [],
                {"returns": ["Err propagated with `?`"], "throws": ["returns early on Err"]}))
            continue

        pat, guard = (match_arm_guard(src, n) if kind == "match_arm" else (None, None))
        cond = guard if kind == "match_arm" and guard is not None else predicate_of(src, n)
        pred_text = bm.one_line(txt(src, cond), 200) if cond is not None else ""
        if kind == "match_arm" and pat is not None:
            ptext = bm.one_line(txt(src, pat), 120)
            pred_text = f"{ptext}" + (f" if {pred_text}" if guard is not None else "")

        local_types = {k: v[0] for k, v in locals_.items()}
        reads, external, calls, obj, cap = ([], [], [], False, [])
        if cond is not None:
            reads, external, calls, obj, cap = reads_of(src, cond, params, local_types,
                                                        captured)
            # a local declared after the branch cannot inform its trigger
            before = [r for r in reads if r["origin"] != "local"
                      or locals_.get(r["symbol"], (None, 0))[1] < n.start_byte]
            reads = before or reads

        rows.append(bm.branch_row(
            unit, path, n.start_point[0] + 1, fname, kind, pred_text,
            path_condition(src, n, fn), reads, external, calls,
            effects_of(src, n), reads_object_state=obj, captured_reads=cap))
    return rows


def scan_file(path, unit):
    src = open(path, "rb").read()
    tree = bm.require_tree_sitter("rust", {"rust": "tree_sitter_rust"})["rust"]
    from tree_sitter import Language, Parser
    parser = Parser(Language(tree.language()))
    root = parser.parse(src).root_node
    errors = sum(1 for n in walk(root) if n.type == "ERROR" or n.is_missing)
    rows, carriers = [], carriers_for_file(src, root, path, unit)
    for n in walk(root):
        if n.type in FUNCS:
            if n.type == "function_item" and has_attr(src, n, SKIP_MOD_ATTRS):
                continue
            rows.extend(branches_for_fn(src, n, unit, path))
        if n.type == "mod_item" and has_attr(src, n, SKIP_MOD_ATTRS):
            continue
    return rows, carriers, errors, {
        "macros_unexpanded": sum(1 for n in walk(root) if n.type == "macro_invocation"),
        "dyn_or_impl_trait": sum(1 for n in walk(root)
                                 if n.type in ("dynamic_type", "bounded_type")),
    }


def main(argv):
    opts = bm.parse_args(argv, "rust")
    unit, ws = resolve_unit(opts)
    files = bm.discover_files(unit, EXT, opts["select"], opts["include_tests"],
                              opts["max_files"])
    if not files:
        bm.die(3, f"branch_map_rust: no .rs files under {unit!r}"
                  + (f" matching {opts['select']!r}" if opts["select"] else ""))

    rows, carriers, total_errors = [], [], 0
    limits = {"macros_unexpanded": 0, "dyn_or_impl_trait": 0}
    for f in files:
        try:
            scanned = scan_file(f, unit)
        except Exception as exc:  # a crash must not look like "no branches"
            bm.die(4, f"branch_map_rust: failed on {f}: {exc}")
        r, c, errs, lim = scanned
        rows.extend(r)
        carriers.extend(c)
        total_errors += errs
        for k, v in lim.items():
            limits[k] += v

    if total_errors and not opts["allow_parse_errors"]:
        bm.die(4, f"branch_map_rust: {total_errors} parse error node(s) across "
                  f"{len(files)} file(s). The tree is incomplete, so the table is not "
                  f"evidence. Re-run with --allow-parse-errors to see what parsed.")
    limits["parse_errors"] = total_errors
    rows.sort(key=lambda r: (r["file"], r["line"]))
    if opts["max_branches"]:
        rows = rows[:opts["max_branches"]]
    bm.emit(f"{unit} (workspace {ws})", rows, carriers, files, limits, opts)


if __name__ == "__main__":
    main(sys.argv[1:])
