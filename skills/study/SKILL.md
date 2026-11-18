---
name: study
description: "Use when a repo's business branches must become AGENTS.md."
version: 2.0.1
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
{project_root}/AGENTS.md                    ← main agent: index of every AGENTS.md
{member}/AGENTS.md                          ← round 1 subagent: branch map of the member
{member}/{package_root}/AGENTS.md           ← round 2 subagent
{member}/{package_root}/{deeper}/AGENTS.md  ← round 3, until no package root is left
```

The second run is not a rebuild. When the files already exist, the skill runs as a **delta**: it takes
every commit since each file's own recorded commit, sorts the changed paths by the unit that owns them,
and dispatches one subagent per affected unit, which rewrites only the rows whose evidence moved. A
first study is Workflow A; a refresh is Workflow B.

## Definitions

| Term | Meaning |
| --- | --- |
| **member** | A directory that is a building or shipping unit: `crates/{name}`, `packages/{name}`, a Cargo workspace member, an npm/pnpm workspace package, a Python import package root under `src/`. One subagent studies one member. |
| **package root** | A deeper directory inside a member that owns its own entry point and its own importable/buildable unit (`crates/api/src/server/` as a module tree, `packages/ui/src/components/` as a package root, `src/pkg/subpkg/`). It gets its own round and its own `AGENTS.md`. |
| **business branch** | A decision whose outcome the caller can observe: a different response, a different side effect, a different on-disk artefact, a different failure. Not every `if` — §1 of `references/branch-inventory.md` is the test. |
| **selection path** | The ordered conjunction of predicates that must hold for one entry point to reach one branch. Quoting those predicates is what makes a branch row decidable, and drawing them is what the mermaid graph is for. |
| **trigger** | The predicate in code, quoted verbatim with `file:line`, plus any config key and default that participates. "When the user asks for a stream" is not a trigger; "`if req.mode == Mode::Stream` at `handlers.rs:88`, `default = Mode::Batch` at `config.rs:31`" is. |
| **delta** | A refresh of a knowledge base that already exists: every commit since each file's own recorded commit, classified by the unit that owns each changed path, with only the rows whose evidence moved rewritten. Workflow B. |

## When to use

- A repo, a monorepo or an unfamiliar member must be understood well enough that an agent can change it
  without guessing which path a request takes.
- The knowledge base already exists and the tree has moved since: Workflow B re-derives the rows the diff
  touches and leaves every other row verbatim.
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
- In delta mode, the history from each file's recorded commit must still be reachable
  (`git merge-base --is-ancestor {base} HEAD`). A shallow clone or rewritten history is not a diff question:
  those units fall back to Workflow A and the report says which and why.

## Workflow A — first study

### 0. Recon: enumerate members and package roots (main agent, cheap)

Build one row per candidate member and package root — `path`, `kind` (`cargo-member` / `npm-package` /
`py-root` / `go-module` / `other`), `depth`, `loc`, existing `AGENTS.md` / `CLAUDE.md`, entry-point
candidates, and `round` (`1 + the number of enclosing units`, so the plan comes out of the table directly):

- **members are the manifests** — `git ls-files '*Cargo.toml' '*package.json' '*pyproject.toml' '*go.mod'`
  names every candidate, and the directory holding each file is the member, unless that file carries a
  `workspace` section (then its glob's directories are the members, not the root);
- **size and depth** come from `git ls-files {path} | wc -l` and the path's own separators;
- **entry points** are the greps of `references/branch-survey.md` §1: `main.rs`, `main.py`, `__main__.py`,
  `[[bin]]`, a `bin` field, a route or app factory. A manifest with neither entry point nor exported surface
  is a build unit only, and the round plan says so;
- **manifest-less units** are added by hand when a unit exists by convention alone (a `src/{pkg}/` with its
  own `__main__`, a directory whose siblings all carry manifests), with the evidence for calling it a member
  written beside the path.

Read the table before dispatching anything: it decides the number of rounds. A directory that is not a unit
of behaviour (generated code, `examples/`, vendored third-party trees) is removed from the round plan, with
the reason.

The round plan is the contract for the rest of the skill. Write it down in the run ledger:

```
round 1: {member} … ({n} subagents, one each)
round 2: {member}/{package_root} … ({m} subagents)   ← only what round 1 reports
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
3. `{member}/AGENTS.md`, assembled by `references/agents-md-format.md`.

Its brief carries the survey procedure (`references/branch-survey.md`) and the diagram guide
(`references/diagram-choice.md`), which are the two places a cartographer drifts: the first into linear reading,
the second into drawing a picture of the code.

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

- opens every `file:line` in the branch table and reads that line (`sed -n '{n}p' {file}`), confirming the
  quoted predicate is there — the table's shape is not evidence that the line says what the row claims;
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

When every round is accepted, the main agent writes `{project_root}/AGENTS.md`: the index of every
`AGENTS.md` in the tree, one row each — path, the member's one-line scope, the entry points it owns, the
count of branches — plus the repository-level facts no member owns (build system, toolchain pin, how to run
one member's tests, where the shared fixtures live).

Two rules make the index useful rather than decorative:

- **the index points, it does not duplicate.** A sentence that also appears in a member's file will drift
  from it; the root carries the map and the cross-member rules, each child carries its own detail.
- **the index is generated from `git ls-files`, not from memory.** Compare both directions before accepting:
  `git ls-files '*AGENTS.md'` against the paths the index names, and the paths the index names against the
  tree. A file the index omits and a row naming a deleted file are one defect seen from two sides.

## Workflow B — delta refresh (the knowledge base already exists)

Entry condition: `AGENTS.md` files that carry a study block and a resolvable `generated:` commit. The
question is no longer "what does this repository do" but "what does it do now that those files do not
say", and it is answered with one diff per unit instead of one study per unit. §1–§11 of
`references/delta-refresh.md` is the procedure in full; the steps below are the dispatch.

### 5. Delta recon: the ledger is the refresh's round plan

Derive the ledger yourself, one row per recorded unit — `unit`, the `base` its provenance names, commits
since, touched paths, `status`:

```
grep -rH --include=AGENTS.md 'generated:' .        # unit → base sha and date
git rev-list --count {base}..HEAD                  # commits since
git diff --name-only {base} HEAD                   # net: base against the working tree
git log --name-only --pretty=format: {base}..HEAD  # touched: every path any commit in the window named
```

`status` is `current` when the count is zero or no touched path falls under the unit, `moved` otherwise,
`missing-file` when the file is gone while its directory stands, `new` when a member carries no file. The
units that moved are then dispatched, and the paths no unit claims go to the root bucket.

**The base is the file's own provenance commit.** Files studied at different times are stale in different
amounts; a repository-wide base either re-dispatches units whose claims are still true or skips units that
moved after their own base.

**Two diffs, because they answer two questions.** `touched` is every path named by any commit in
`base..HEAD` plus the working tree; `net` is the base against the working tree. Dispatch reads `touched`
— a handler added in one commit and deleted in the next is still work the inventory predates. Row
preservation reads `net` — a branch renamed twice and renamed back allows no row to be rewritten. Dispatch
reads `touched`; every preservation claim is then checked with `net`.

Read the table before dispatching. It decides how many subagents there are, and a unit that is `current`
gets none: a rewrite whose content does not change buries the drift that does.

### 6. Classify every touched path: the deepest recorded unit owns it

`crates/api/src/server/handlers.rs` belongs to `crates/api/src/server`, not to `crates/api`, even though
the parent's directory contains it. Two exceptions keep the rule honest:

- a parent is refreshed when a file **it cites itself** moved, even inside a child's tree — the script
  reports those as `also cites, and it moved`. A handoff row cites a line in the child's directory.
- a path under no unit and under no discovered member is the **root bucket**: the main agent's own work,
  because the root index is its artefact.

| Bucket | Test | Who acts |
| --- | --- | --- |
| refresh | path under a recorded unit, or cited by one | one subagent for that unit |
| new | path under a member with a manifest and no `AGENTS.md` | one subagent, round-1 brief (§1) |
| retire | an `AGENTS.md` is gone and its directory too | the main agent edits the root index |
| root | path named by no unit | the main agent: root index, or nothing |

`missing-file` — an `AGENTS.md` gone while its directory stands — is not a retirement. It is a directory
that is now unstudied, and it is reported, not edited around.

### 7. Dispatch one subagent per affected unit

The delta brief is `references/subagent-brief.md` §5: the round-1 fields plus `base: {sha}`, the unit's
touched paths, and the diff-scoped obligations. In waves of about eight if there are more, deepest units
first, so a parent's brief names a child that already exists.

The obligations that make a refresh checkable rather than a rewrite:

- **read the diff before the code** — `git log -p {base}..HEAD -- {unit}` then the files it names; the
  diff says where to look, and reading the whole unit again is how rows get silently re-derived;
- **every row whose cited file ended the window unchanged is copied verbatim** — id, cells, spelling;
- **ids are stable**: a new branch takes the next free id, an existing id is never renumbered, and a
  branch that no longer exists is removed and named in the report, its id retired and not reused;
- **provenance moves to HEAD** — `generated: {sha} @ {date}` stays the exact line the §5 recon greps for,
  plus `by: pdd:study delta <base8>..<head8>` — even when no row changed, because that commit is the
  record that someone looked;
- **the sections nobody touched are not rewritten**, so the diff of the knowledge base reads as the diff
  of the code.

A `new` unit gets the round-1 brief, not this one: there is nothing to diff against.

### 8. Delta acceptance: nothing stale, no row lost

Three reads, run before the refresh is committed because each compares against the committed version:

```
git diff --name-only {base} HEAD -- {unit}     # the unit moved → this file must differ
git diff --stat -- '*AGENTS.md'                # this file moved → its unit must have moved
git ls-files '*AGENTS.md'                      # every file the root index names still exists
```

A file whose unit moved but whose content is byte-identical is a failed refresh; a file whose unit did not
move but whose rows changed is a silent rewrite (`git diff -- {file}` names the rows); a knowledge-base file
gone from disk while the root index still names it is a `missing-file`. Once the three reads are clean, one
commit per unit — `{unit}: study delta <base8>..<head8> — +{n} rows, ~{m} updated, -{k} retired` — which is
the durable record of what was read.

## Acceptance

Structural (main agent, one pass per file):

- every discovered `AGENTS.md` carries the required sections inside its `<!-- study:begin -->` block;
- every branch row has an id, a behaviour, a quoted trigger, a `site` that resolves to a real `file:line`, and
  an example;
- every `AGENTS.md` carries a provenance block naming a commit and a date, and no nested reference points at
  a missing file;
- the root index names every `AGENTS.md` in the tree and nothing else.

Judgement (the same pass, over the same files):

- [ ] every member in the round plan has exactly one `AGENTS.md`, and no directory has two;
- [ ] every branch passes the observability test, and the default/fallback path of each entry point is in the
      table — the behaviour on unmatched input is the one nobody documents and everybody depends on;
- [ ] every trigger is a quoted predicate plus its config key and default, not a paraphrase of intent;
- [ ] every branch in the table appears exactly once as a terminal in the graph, and every selection path in
      the graph reads back as the conjunction the table's trigger states;
- [ ] a branch whose predicate reads state owned by another member is recorded as `cross: {member}` and
      claimed by that member's file, not duplicated in both;
- [ ] unreachable branches are recorded as findings and routed, not deleted and not documented as live;
- [ ] each file's nested-roots section matches the next round's task list exactly;
- [ ] the root index names every file, and no sentence in it restates a child's content;
- [ ] `git status --short` shows only added `AGENTS.md` files — production code untouched.

Delta refresh adds the three reads of §8 and five judgement items:

- [ ] no file is stale: its provenance commit is HEAD, or no commit since it touches the unit;
- [ ] every row whose cited file ended the window unchanged is byte-identical to the committed version,
      and every row that changed is explained by a commit in its unit's ledger;
- [ ] no knowledge-base file is gone from disk without the root index dropping it — and a `missing-file`
      (the directory still stands) is reported, not edited around;
- [ ] the unit ledger's four buckets account for every touched path: refresh dispatched, new studied,
      retired indexed, root handled;
- [ ] a row that was dropped names the branch that disappeared, and no id was renumbered or reused.

## Decision rules

| Situation | Rule | Reason |
| --- | --- | --- |
| A member is huge (many entry points, several layers) | Split the study by entry point inside that member's round: several subagents, each owning one entry point's branch table, one of them owning the file | The file is the single writer; the tables can be written in parallel, the assembly cannot |
| A directory has a manifest but no behaviour | Exclude it in the round plan, with the reason | Generated code and vendored trees produce inventory rows that are true and useless |
| Two members share a branch (same predicate, same config key) | The member that owns the config key owns the row; the other records `cross:` | Duplicated rows drift and then contradict each other in the same review |
| An existing `AGENTS.md` / `CLAUDE.md` is present | Study writes only its marked block; human text is preserved verbatim above it; a conflicting human rule is reported, never edited | Overwriting onboarding notes destroys the one part of the file a human maintained |
| A branch's trigger cannot be resolved | Record `trigger: unknown` plus the searches performed, and report it | A guessed trigger is worse than a gap: it reads as evidence and gets used |
| The tree has one member | Still one subagent, still the root index | The protocol is what makes the output checkable; skipping it for a small repo gives an unverified file |
| The tree moved under an existing knowledge base | Run Workflow B: the §5 ledger decides the dispatch, one subagent per affected unit, rows with unchanged evidence copied verbatim | A full re-run rewrites files whose claims are still true, and the real drift drowns in the churn |
| A unit's diff is one line | Still its own subagent; its deliverable may be a provenance bump and no row change | "The rows still hold" is a finding, and it must be attributable to a reader |
| A unit's own `AGENTS.md` is the only file that changed | Not a change: the ledger ignores the file it describes | Counting the map as the territory re-dispatches every unit after every study |
| Two units cite the same moved file | The deepest recorded unit owns the row; the shallower one only re-resolves its citation | Two owners of one fact is how two files come to disagree |
| A unit directory was renamed | `git mv {old} {new}`, then refresh — the file travels with its directory — and update the root index in the same commit | A copy loses the provenance chain and `git log --follow` stops at it |
| The recorded base is not an ancestor of HEAD | Re-study that unit as Workflow A, and record why | A diff against a commit that is no longer an ancestor is fiction |

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
- **A delta that rebuilds the file.** A subagent re-reads the unit and rewrites the whole block, so rows the
  diff never touched disappear quietly and the knowledge base's own diff shows churn no code change explains
  → rows whose cited file ended the window unchanged are copied verbatim, and the knowledge base's own diff
  is read for exactly that: a verbatim row that moved is reverted, not accepted as an improvement.
- **Citations resolved against a unit directory instead of the repository root.** Every `site` and every
  auxiliary `path:line` is repository-relative, so reads made from `crates/x/` turn nine clean units into nine
  "cited file does not exist". Open every citation from `{project_root}` and attribute each miss to the row
  that carries it before calling the row wrong.
- **A preserved row carrying a dead auxiliary citation.** Preservation keys on the site cell's file, so a
  secondary `path:line` in the same row can rot while the row is frozen, and the two gates then contradict each
  other → `delta-refresh.md` §6b: repair the citation, freeze the site cell and the wording, and name the
  repair in the report.
- **A net diff read as the whole history.** A branch added in one commit and deleted in the next leaves no
  trace in `git diff base..HEAD`, so the unit looks untouched → dispatch on `touched`, verify preservation
  on `net`.
- **One subagent for the whole delta.** A wrong row no longer names a directory, so the repair becomes an
  investigation instead of a re-dispatch.
- **Provenance bumped without reading the diff.** The staleness read goes quiet, the file looks maintained,
  and the next reader trusts claims nobody checked.
- **A graph nobody rendered.** A stray `)` in a node label is invisible to every other check here (citations
  resolve, the row did not move), and the subagent that wrote it reported "lint only — no chromium here". As
  root, chromium needs `--no-sandbox`, so a bare `npx @mermaid-js/mermaid-cli` fails in a way that reads as
  "rendering unavailable" → render with an explicit puppeteer config (`-p puppeteer-config.json` carrying
  `args: ["--no-sandbox"]`) as the last step of every round, and treat "lint-verified only" as unverified.
- **Rows renumbered after a retirement.** Every mermaid terminal and every quoted id downstream now points
  at the wrong branch, and nothing errors.

## Verification


> A gate is only a gate while it can fail for the right reason. Before trusting a green run:
> `skill_view("pdd:report", "references/gate-discipline.md")`.

- [ ] the round plan exists, with a reason per excluded directory and a stop condition per unfinished one;
- [ ] every structural item in Acceptance was read against the files, not against a subagent's report;
- [ ] every accepted `AGENTS.md` was checked by the main agent against the code, not against the subagent's
      report;
- [ ] the root index names every file in the tree and restates none of them;
- [ ] no production file, test or fixture was modified: `git status --short` lists only added `AGENTS.md`.
- [ ] in a delta, the three reads of §8 were clean before each unit's commit, and the ledger's touched paths
      are all accounted for;
- [ ] every mermaid block in every study file was rendered by the main agent. "Lint-verified only" is not a
      verification, because mermaid reports a stray parenthesis as a lexical error and every other check in
      this skill passes straight over it.

> Cross-skill references name the sibling skill and the file separately:
> `skill_view("pdd:decompose", "references/task-splitting.md")`. Every sibling is registered under this
> plugin's namespace, so the skill argument always carries the `pdd:` prefix.

## References

- `references/branch-inventory.md` — what counts as a business branch, the row schema, trigger form,
  cross-member and unreachable handling.
- `references/branch-survey.md` — the field procedure: survey order, grep cheat sheet per ecosystem, the six
  counts that mean the survey is done, and the anti-patterns that cost the most time.
- `references/diagram-choice.md` — whether to draw at all, which shape answers which question, what each shape
  cannot show, and the rules that apply to every diagram.
- `references/mermaid-templates.md` — rendered, copy-paste sources for the ten shapes that are worth drawing.
- `references/mermaid-selection-path.md` — graph shape, node and edge conventions, size discipline, worked
  example, validation.
- `references/agents-md-format.md` — required sections, the marked-block merge rule, provenance, nesting,
  and the row lifecycle a delta obeys.
- `references/delta-refresh.md` — the refresh in full: two diffs, per-file bases, the deepest-owner
  classifier, the four task kinds, degenerate histories, and the anti-patterns.
- `references/subagent-brief.md` — the brief the main agent sends, and the report it demands back; §5 is the
  delta brief.
- `assets/AGENTS.template.md` — the file template, markers included.
