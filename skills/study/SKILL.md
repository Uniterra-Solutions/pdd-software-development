---
name: study
description: "Use when a repo's business branches must become AGENTS.md."
version: 1.0.0
author: Tsz Kin Lai (LaiTszKin), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [software-development, codebase-mapping, subagents, mermaid, agents-md]
    related_skills: [plan, decompose, review]
---

# Study a codebase — every business branch becomes a cited AGENTS.md

`pdd:study` reconstructs what a repository actually does, branch by branch, and leaves the result where an
agent will read it: one `AGENTS.md` per workspace member and per package root, each carrying a branch table,
a mermaid graph of the paths that select those branches, and a provenance block.

The unit of work is the **member**, and the unit of correctness is the **branch**. One subagent studies one
member: it reads that member's entry points, follows each conditional to the behaviour behind it, and writes
down the trigger for each. The main agent accepts nothing on a self-report — it re-resolves every cited
`file:line` itself — and at the end writes a root `AGENTS.md` that indexes every file the rounds produced.

```
<project_root>/AGENTS.md                        ← main agent: index of every AGENTS.md
<member>/AGENTS.md                              ← round 1 subagent: branch map of the member
<member>/<package_root>/AGENTS.md               ← round 2 subagent
<member>/<package_root>/<deeper>/AGENTS.md      ← round 3, until no package root is left
```

## Definitions

| Term | Meaning |
| --- | --- |
| **member** | A directory that is a building or shipping unit: `crates/<name>`, `packages/<name>`, a Cargo workspace member, an npm/pnpm workspace package, a Python import package root under `src/`. One subagent studies one member. |
| **package root** | A deeper directory inside a member that owns its own entry point and its own importable/buildable unit (`crates/api/src/server/` as a module tree, `packages/ui/src/components/` as a package root, `src/pkg/subpkg/`). It gets its own round and its own `AGENTS.md`. |
| **business branch** | A decision whose outcome the caller can observe: a different response, a different side effect, a different on-disk artefact, a different failure. Not every `if` — §1 of `references/branch-inventory.md` is the test. |
| **selection path** | The ordered conjunction of predicates that must hold for one entry point to reach one branch. Quoting those predicates is what makes a branch row decidable, and drawing them is what the mermaid graph is for. |
| **trigger** | The predicate in code, quoted verbatim with `file:line`, plus any config key and default that participates. "When the user asks for a stream" is not a trigger; "`if req.mode == Mode::Stream` at `handlers.rs:88`, `default = Mode::Batch` at `config.rs:31`" is. |

## When to use

- A repo, a monorepo or an unfamiliar member must be understood well enough that an agent can change it
  without guessing which path a request takes.
- A branch inventory is wanted as evidence: what the code does today, quoted, before a plan rewrites it.
- Onboarding documentation is wanted that survives re-generation (`pdd:study` re-runs replace only its own
  marked block, never human-written text).
- Handoff: a single file's control flow, one function's contract, or a design document belongs elsewhere —
  this skill maps directories, not ideas.

## Preconditions

- The repo is on disk and readable. The study is **read-only with respect to production code**: the only
  files this skill writes are `AGENTS.md` files, one per studied directory, plus the root index.
- A build that would mutate artefacts is not run. Entry points are read, not exercised, unless a cheap
  read-only command exists to confirm one (`--help`, a route table dump, a test that names its cases).
- Git is available: the provenance block records the commit the study was made from, and re-running needs to
  know whether the tree moved.

## Workflow

### 0. Recon: enumerate members and package roots (main agent, cheap)

`python3 scripts/list_members.py <project_root>` prints one row per candidate member and package root:
`path`, `kind` (`cargo-member` / `npm-package` / `py-root` / `go-module` / `other`), `depth`, `loc`,
existing `AGENTS.md` / `CLAUDE.md`, and entry-point candidates (bin targets, `[[bin]]`, `main.rs`,
`main.py`, `__main__.py`, `bin` fields, exported route/app factories). Its `round` column is
`1 + (number of enclosing units)`, so the plan comes out of the table directly; `--include-other` adds
manifest-less source directories when a unit is defined only by convention.

Read the output before dispatching anything: it decides the number of rounds. A member the script misses (a build unit with no manifest, a package root defined only by
convention) is added by hand to the round plan, with the evidence for why it is a member. A directory the
script lists that is not a unit of behaviour (generated code, `examples/`, vendored third-party trees) is
removed from the round plan, with the reason.

The round plan is the contract for the rest of the skill. Write it down in the run ledger:

```
round 1: <member> … (<n> subagents, one each)
round 2: <member>/<package_root> … (<m> subagents)   ← only what round 1 reports
round 3: …
```

Round 2 cannot be planned before round 1 finishes: a nested package root is discovered by reading the
member's own tree, and inventing it from directory names alone produces rounds for things that are not units.

### 1. Round 1: one subagent per member

Dispatch with `delegate_task`, one task per member, in a single call. Each brief is path-shaped
(`references/subagent-brief.md`); each subagent is read-only except for the one `AGENTS.md` path it owns and
produces three things:

1. the **branch inventory** table (`references/branch-inventory.md`);
2. the **selection-path graph** in mermaid, one graph per entry point (`references/mermaid-selection-path.md`);
3. `<member>/AGENTS.md`, assembled by `references/agents-md-format.md`.

Its report also names the nested package roots it found, the cross-member dependencies it saw, and the
branches whose trigger it could not resolve. Those three lists are the input to the next phase — a round-1
subagent reports nested roots, it does not study them, because one subagent per directory is what keeps the
owned set to one directory.

**One member per subagent is the whole point.** A subagent given three members reads the first, skims the
second and infers the third, and its report cannot be attributed when one of the three is wrong. The cost of
the extra subagent is a dispatch; the cost of a merged one is an inventory nobody can trust.

### 2. Rounds 2..N: nested package roots

After round 1 is accepted, every reported package root becomes one task in round 2, with the same three
deliverables and its own `AGENTS.md`. The recursion stops at a package root that

- has no entry point of its own (a leaf library covered by its parent's inventory), or
- contains no decision that changes observable behaviour (pure data, types, constants, asset trees).

Stop conditions are stated per directory in the round plan, with the reason; a directory left unstudied is a
decision, and an unrecorded decision is indistinguishable from an omission. Everything deeper that qualifies
is another round: `src/`, `crates/`, `packages/` nesting is common enough that a fixed two-round rule will
miss the third level.

A round-N subagent is given its parent's inventory as a read-only input and one extra obligation: where the
parent's table claims a behaviour and the code contradicts it, it reports the contradiction rather than
silently writing a different answer. Two files disagreeing is a finding for the main agent, not something a
subagent fixes by choosing the more recent reading.

### 3. Acceptance: the main agent re-resolves every citation

A subagent's self-report is not acceptance, here as in `pdd:implement`. For each `AGENTS.md`, the main agent:

- opens every `file:line` in the branch table and confirms the quoted predicate is at that line
  (`scripts/check_agents_md.py` does the mechanical half: the file exists, the line is in range, the
  table's shape is right);
- confirms each branch passes the observability test, and that its row is not a transcription of an
  unrelated `if` (`references/branch-inventory.md` §2);
- renders each mermaid block and reads the graph against the table: every table branch appears once as a
  terminal, every terminal is reachable, no edge lacks its predicate;
- confirms the file's nested-roots section lists exactly the children the next round will study, and no more;
- confirms the write stayed inside the owned set (`git status --short`: one new `AGENTS.md`, nothing else).

A finding here is routed, not patched by the main agent: a branch with no resolvable trigger goes back to the
same subagent with the specific gap; a branch that is unreachable in code is recorded in the inventory as
`unreachable` and routed as a removal candidate to `pdd:decompose`, because deleting it is work with its own
acceptance and its own commit.

### 4. The root index

When every round is accepted, the main agent writes `<project_root>/AGENTS.md`: the index of every
`AGENTS.md` in the tree, one row each — path, the member's one-line scope, the entry points it owns, the
count of branches — plus the repository-level facts no member owns (build system, toolchain pin, how to run
one member's tests, where the shared fixtures live).

Two rules make the index useful rather than decorative:

- **the index points, it does not duplicate.** A sentence that also appears in a member's file will drift
  from it; the root carries the map and the cross-member rules, each child carries its own detail.
- **the index is generated from `git ls-files`, not from memory.** `scripts/check_agents_md.py --root-only`
  fails when an `AGENTS.md` exists that the root index does not name, or names one that does not exist.

## Acceptance

Mechanical (`scripts/check_agents_md.py <project_root>`, exit 0):

- every discovered `AGENTS.md` carries the required sections inside its `<!-- study:begin -->` block;
- every branch row has an id, a behaviour, a quoted trigger, a `site` that resolves to a real `file:line`, and
  an example;
- every `AGENTS.md` carries a provenance block naming a commit and a date, and no nested reference points at
  a missing file;
- the root index names every `AGENTS.md` in the tree and nothing else.

Judgement (read by the main agent):

- [ ] every member in the round plan has exactly one `AGENTS.md`, and no directory has two;
- [ ] every branch passes the observability test, and the default/fallback path of each entry point is in the
      table — the behaviour on unmatched input is the one nobody documents and everybody depends on;
- [ ] every trigger is a quoted predicate plus its config key and default, not a paraphrase of intent;
- [ ] every branch in the table appears exactly once as a terminal in the graph, and every selection path in
      the graph reads back as the conjunction the table's trigger states;
- [ ] a branch whose predicate reads state owned by another member is recorded as `cross: <member>` and
      claimed by that member's file, not duplicated in both;
- [ ] unreachable branches are recorded as findings and routed, not deleted and not documented as live;
- [ ] each file's nested-roots section matches the next round's task list exactly;
- [ ] the root index names every file, and no sentence in it restates a child's content;
- [ ] `git status --short` shows only added `AGENTS.md` files — production code untouched.

## Decision rules

| Situation | Rule | Reason |
| --- | --- | --- |
| A member is huge (many entry points, several layers) | Split the study by entry point inside that member's round: several subagents, each owning one entry point's branch table, one of them owning the file | The file is the single writer; the tables can be written in parallel, the assembly cannot |
| A directory has a manifest but no behaviour | Exclude it in the round plan, with the reason | Generated code and vendored trees produce inventory rows that are true and useless |
| Two members share a branch (same predicate, same config key) | The member that owns the config key owns the row; the other records `cross:` | Duplicated rows drift and then contradict each other in the same review |
| An existing `AGENTS.md` / `CLAUDE.md` is present | Study writes only its marked block; human text is preserved verbatim above it; a conflicting human rule is reported, never edited | Overwriting onboarding notes destroys the one part of the file a human maintained |
| A branch's trigger cannot be resolved | Record `trigger: unknown` plus the searches performed, and report it | A guessed trigger is worse than a gap: it reads as evidence and gets used |
| The tree has one member | Still one subagent, still the root index | The protocol is what makes the output checkable; skipping it for a small repo gives an unverified file |
| The study is re-run after the code moved | Re-dispatch only members whose diff touches them (`git diff --name-only <recorded-commit>..HEAD`), replace only the marked block | A full re-run rewrites files whose claims are still true and buries the real drift |

## Pitfalls

- **The inventory becomes a transcript of every `if`.** A table with two hundred rows, most of them validation
  guards, is unusable and unverifiable → apply the observability test; a branch earns a row only if the caller
  can tell which one ran.
- **Triggers written as intent.** "When the user prefers streaming" instead of the predicate and its config
  default → the next agent cannot act on it and the row cannot be checked.
- **A graph that is a picture of the code, not of the selection.** Nodes labelled with function names and
  edges with "else" → the graph must let a reader walk entry → predicates → branch and read the conjunction.
- **Nested files that contradict their parent.** Both files are read by agents, and the deeper one wins by
  proximity → the parent's inventory is the input to the child's round, and a contradiction is a reported
  finding.
- **Overwriting a human-written `AGENTS.md`.** The marked-block rule is the only safe write into a file this
  skill did not create.
- **Study drifting into repair.** A subagent that finds a dead branch fixes it, and the diff now mixes a map
  with a change nobody reviewed → findings are routed to `pdd:decompose`.
- **Rounds planned from directory names.** Rounds 2..N are planned from round 1's report, because a package
  root is defined by an entry point, not by a folder.
- **The root index duplicated into the children and the children's content into the root.** Two copies, one
  edit, silent divergence.
- **Claims with no commit.** A file whose provenance block is absent cannot be told apart from one written
  against a tree that no longer exists.

## Verification

- [ ] the round plan exists, with a reason per excluded directory and a stop condition per unfinished one;
- [ ] `scripts/check_agents_md.py <project_root>` exits 0;
- [ ] every accepted `AGENTS.md` was checked by the main agent against the code, not against the subagent's
      report;
- [ ] the root index names every file in the tree and restates none of them;
- [ ] no production file, test or fixture was modified: `git status --short` lists only added `AGENTS.md`.

> Cross-skill references name the sibling skill and the file separately:
> `skill_view("pdd:decompose", "references/task-splitting.md")`. Every sibling is registered under this
> plugin's namespace, so the skill argument always carries the `pdd:` prefix.

## References

- `references/branch-inventory.md` — what counts as a business branch, the row schema, trigger form,
  cross-member and unreachable handling.
- `references/mermaid-selection-path.md` — graph shape, node and edge conventions, size discipline, worked
  example, validation.
- `references/agents-md-format.md` — required sections, the marked-block merge rule, provenance, nesting.
- `references/subagent-brief.md` — the brief the main agent sends, and the report it demands back.
- `assets/AGENTS.template.md` — the file template, markers included.
- `scripts/list_members.py` — recon: members, package roots, depths, entry-point candidates.
- `scripts/check_agents_md.py` — acceptance: citations resolve, table shape, provenance, index coverage.
