# Machine pass: branch and state extraction (Rust, TypeScript)

Two scripts emit the mechanical half of a branch row and the unit's state vocabulary:

```
python3 scripts/branch_map_rust.py <unit-path> | --member NAME [--root DIR]
python3 scripts/branch_map_ts.py   <unit-path> | --member NAME [--root DIR]
        [--select GLOB] [--json] [--include-tests] [--max-files N] [--max-branches N]
        [--allow-parse-errors] [--quiet]
```

`--member NAME` resolves a cargo workspace member or a pnpm/npm workspace package by
name; `--select GLOB` is how a package root inside a member is addressed. Both scripts
emit the same row schema and the same closure vocabulary — a subagent handed a crate
and one handed a package produce tables the main agent reads the same way.

Requirements: `python3 -m pip install tree_sitter tree_sitter_rust tree_sitter_typescript`.
Install into the interpreter that will run the script, and check that they are the same one —
`python3 -c 'import sys, tree_sitter; print(sys.executable)'`. On a machine with several
interpreters `python3` may resolve to one without the grammars; the script then exits 2 rather
than reporting a smaller table. There is no degraded fallback, because a parse that silently
returns fewer branches is a gate that cannot fail.

## What the table is

- **carriers** — state bearers the unit declares, each with a `closure` label (§2). This is
  the answer to "which values can this thing legally hold", per type, not per repository.
- **branches** — decision sites with the predicate quoted, the reads it depends on and
  where each comes from, and the writes / returns / calls the branch produces.
- **limits** — the count of constructs the pass could not see through (unexpanded macros,
  `dyn`/generic dispatch, `any`, computed dispatch, parse errors). Printed with every run.

The table is a **lower bound and a disposition list**. It is not the inventory, and pasting
it into `AGENTS.md` is a defect: a row in that file must state a behaviour, and no machine
pass can name a behaviour.

## 1. Purity is the load-bearing field

| value | meaning | what may be written from it |
| --- | --- | --- |
| `pure` | the predicate reads only parameters and locals the function assigned | "When `<predicate>`, the caller sees `<effect>`" — the trigger is a statement about the input |
| `reads object state` | the predicate reads `self.*` / `this.*` (also flagged when the branch reads a closure's locals — `captured`) | the trigger is a statement about the receiver's state; say which field, and that the state was set elsewhere |
| `impure` | the predicate reads something outside the call (another module, config, clock, a callee not on the pure list) | the trigger is **not** answerable from this file; write `trigger: partial` and name the missing owner |

`purity: pure` is the only case where "under what input" has a complete answer. Presenting
an impure predicate as though the input determined it is the failure this field exists to
prevent — a guessed trigger reads as evidence and gets used.

## 2. The closure vocabulary

Per carrier, chosen by the kind of thing the carrier is:

| closure | carrier | how complete the state list is |
| --- | --- | --- |
| `closed` | `bool`, Rust enum without `#[non_exhaustive]`, TS union of string/number literals, discriminated union of types, `Option`/`Result` | the set is the whole set. `bool` is `{true,false}`; no declaration is needed |
| `declared` | string-constant blocks, TS `enum`, type aliases | someone wrote these values down; nothing enforces that they are all of them, and any literal can appear elsewhere |
| `open` | `String`/`&str`/`string`, `number`, `any`, `Vec`/`T[]` | not enumerable from source. The legal set is a schema or data-dictionary question |
| `partitioned` | numerics compared against literals | the state is not a set but an interval boundary; the thresholds are the carrier |
| `product` | structs, interfaces | the state is the product of the fields; enumerate the fields, never the product |
| `registered` | trait objects, interfaces with several implementations | the set is what the unit registers |

A `declared` list read as `closed` is how a map acquires an authoritative-looking set that
a typo leaves. When a row needs a closed set and the carrier is `declared` or `open`, the
study records the closure with the claim.

## 3. What the pass cannot see, by construction

- **data-driven routing** — a policy table, a route table, a DI registry, a state machine
  stored in data. The `if` is absent because the decision is a lookup. A repository whose
  behaviour lives in configuration will look sparse here; that sparseness is information,
  not a licence to report "few branches".
- **unexpanded macros** (`macro_rules!`, derives) and computed dispatch (`obj[key]()`),
  counted under `# limits` per file.
- **`dyn Trait` / generic** call targets: counted, not resolved.
- **cross-file state**: a predicate reading `config.mode` is `impure` here whatever the
  config file says; the legal set lives in the config's schema.
- **`#[cfg]` alternatives** are read as written, so mutually exclusive arms appear side by side.
- **grammar gaps.** `tree_sitter_typescript` does not yet parse `export type * from '…'` (TypeScript 5), so a
  package using it exits 4 with that count under `# limits`. `--allow-parse-errors` shows what parsed; the
  gap belongs in the run ledger rather than in a silently smaller table.

## 4. How a round uses it

1. Run it once per unit before dispatching (`--json` when the brief is machine-assembled).
2. Put the table in the subagent's brief as **evidence to dispose of**, not as content to
   copy. The brief's obligation: every branch site is either a row, merged into a row (with
   the site named), or excluded with a reason.
3. The round's own acceptance then covers what the pass cannot: observability, the behaviour's
   name, the config key and default behind an `open` carrier, and the media the pass never
   read (config, schema, prompt).
4. Machine coverage is per medium, never "all branches". A study that claims completeness
   must name the media it enumerated and the ones it declared out of scope.

## Exit codes

`0` ok · `2` missing dependency · `3` unit not found · `4` parse errors (re-run with
`--allow-parse-errors` to see what parsed; the table is not evidence while the tree is broken).
