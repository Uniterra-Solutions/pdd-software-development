# The subagent brief, and the report it owes back

One subagent, one directory. The brief gives paths, never pasted bodies — the same rule `pdd:implement`
follows, for the same reason: a second copy of the contract drifts, and implementation follows one copy while
acceptance reads the other.

## 1. The brief

```
role:        code cartographer. Read-only except for the ONE AGENTS.md you own.
project:     {project root}                      ← read-only
your unit:   {member or package_root path}       ← the whole of your assignment
your output: {unit}/AGENTS.md                    ← the only file you may create or edit
rules:       {plugin}/skills/study/references/branch-inventory.md    ← what a row must contain
             {plugin}/skills/study/references/branch-survey.md         ← how to find them fast
             {plugin}/skills/study/references/diagram-choice.md        ← whether and what to draw
             {plugin}/skills/study/references/mermaid-selection-path.md
             {plugin}/skills/study/references/mermaid-templates.md     ← copy-paste sources
             {plugin}/skills/study/references/agents-md-format.md
template:    {plugin}/skills/study/assets/AGENTS.template.md
parent file: <path, round ≥ 2 only>              ← read-only, your input
recorded commit: {sha}                           ← the tree you are reading

deliverables, in your report and in the file:
  1. branch inventory — every business branch of this unit's entry points, in the table schema
  2. selection paths   — one mermaid flowchart per entry point
  3. AGENTS.md         — the file, in the template's shape, inside the study markers

prohibited:  editing production code, tests, fixtures or config; any second AGENTS.md;
             any AGENTS.md outside your owned path; commands that mutate the tree
             (no cargo build --release, no test that writes fixtures, no formatters); git commit,
             push, merge, branch, stash, checkout
stop when:   an entry point cannot be identified; a trigger cannot be resolved; a parent claim
             contradicts the code; the owned path already holds a marked block from a different
             commit whose content you are not asked to refresh → report and leave the file alone
report:      §2 of this file, raw output pasted where a command was run
```

`test -f` every path in the brief before dispatch, including the three rule files and the template. A wrong
path blocks the subagent at its opening move, and it will report "the task is unclear" rather than "the path is
wrong".

Record the hash of the owned `AGENTS.md` (or its absence) before dispatch. A file that changed shape during the
study was edited by someone else, and the finding no longer describes what is on disk.

## 2. The report

```
unit:            {path}
entries:         {n} entry points, listed
branches:        {n} rows (B01..Bnn); excluded {n} conditionals, with the reason for each
unknown triggers: {n}, each with the searches performed
unreachable:     {n}, each with the evidence that no input takes it
cross-member:    {n}, each naming the member that owns the value
nested roots:    {n} candidates, each with the entry point that makes it a unit
graph:           {n} mermaid blocks; render run: yes (mmdc) / no (lint only)
citations:       {n} file:line references, all opened
contradictions:  {n}, each quoting the parent claim and the code
wrote:           {exactly one path}
touched anything else: no
```

Four parts of that report are load-bearing:

- **excluded conditionals, with reasons.** This is what distinguishes "there is no branch here" from "nobody
  looked". An inventory that silently drops half of a `match` looks the same as a complete one.
- **unknown triggers, with the searches.** A gap that names what was tried is usable; a guessed trigger reads
  as evidence and gets used.
- **nested root candidates, with the entry point.** This is the input to the next round; a directory name is
  not a candidate, an entry point is.
- **render run: yes/no.** A lint and a render are different strengths of evidence; the reader is entitled to
  know which one they got.

## 3. Round 2 and deeper

The same brief, plus its parent's file as a read-only input and three extra obligations:

1. **Verify, do not inherit.** Every parent claim about this directory is checked against the code; a claim
   that holds is not re-copied into the child file (the parent keeps it), and a claim that fails is reported.
2. **Stay below the boundary.** Branches the parent already records at the handoff stay in the parent; the
   child records what happens after the handoff. Neither file duplicates the other's rows.
3. **Do not re-study the parent.** If answering a question requires the parent's entry points, the answer
   belongs to the parent's file, and the child reports it instead of writing it.

## 4. Why one directory per subagent

- **Attribution.** A wrong row names one directory, one subagent, one file — so the fix is a re-dispatch, not an
  investigation.
- **Reading depth.** A subagent given five members reads the first properly, skims the second and infers the
  rest; the inference is indistinguishable from the reading in the report.
- **Write safety.** One directory is one writer. Two subagents on one `AGENTS.md` produce a file that is
  half one reading and half another, with no way to tell which sentence came from where.
- **Parallel cost.** The marginal cost of a subagent is a dispatch; the marginal cost of a merged one is an
  inventory nobody can check.

Large members are split by entry point, and the split keeps one writer: several subagents may each produce a
branch table for one entry point, and exactly one of them assembles the file from those tables. The assembler
owns the file; the others own tables, and their reports say so.

## 5. The delta brief

Dispatched by Workflow B, one per unit that moved. Same shape as §1, three extra fields, and no freedom
about what may change.

```
role:            code cartographer, refreshing an existing map. Read-only except for the ONE AGENTS.md you own.
project:         {project root}                      ← read-only
your unit:       {member or package_root path}       ← the whole of your assignment
your output:     {unit}/AGENTS.md                    ← the only file you may edit
base:            <40-char commit>                    ← the `generated:` line the file carries now
touched:         <the unit's paths from study_delta.py, one per line>
current file:    {unit}/AGENTS.md                     ← your input, not a draft to replace
rules:           {plugin}/skills/study/references/branch-inventory.md
                 {plugin}/skills/study/references/branch-survey.md
                 {plugin}/skills/study/references/diagram-choice.md
                 {plugin}/skills/study/references/mermaid-selection-path.md
                 {plugin}/skills/study/references/mermaid-templates.md
                 {plugin}/skills/study/references/agents-md-format.md   ← §7 is your write rule
                 {plugin}/skills/study/references/delta-refresh.md      ← §6 is the row life cycle

read in this order:
  1. `git log -p {base}..HEAD -- {unit}`   — the diff says where to look
  2. the files that diff names             — only those, only around the hunks
  3. the current AGENTS.md                 — the rows you must carry forward verbatim

deliverables:
  1. rows whose cited file ended the window unchanged: copied verbatim — id, cells, spelling
  2. rows whose evidence moved: same id, trigger re-quoted from the new line, site updated, behaviour re-read
  3. new branch: the next free id; a branch that no longer exists: deleted and named in the report
  4. provenance: `generated: <HEAD> @ {date}` plus `by: pdd:study delta <base8>..<head8>`
  5. the selection-path graph updated where a predicate changed; untouched graphs left as they are

prohibited:  renumbering ids; rewriting a row whose evidence did not move; re-deriving the unit from
             scratch; editing production code; touching any other AGENTS.md; git commit/push/checkout/stash
stop when:   the diff names a file you cannot find; a row's evidence moved but the code no longer shows
             the branch; the existing file and the diff disagree in a way you cannot resolve from the tree
             → report, do not guess
report:      §6 below
```

## 6. The delta report

```
unit:             {path}
base → head:      <base8> → <head8>  ({n} commits, {m} files touched)
rows unchanged:   {n}  — ids …
rows re-sited:    {n}  — {id}: {old site} → {new site}, predicate unchanged
rows rewritten:   {n}  — {id}: {what changed in the predicate or the behaviour}
rows added:       {n}  — {id}: trigger, site, the commit that introduced it
rows retired:     {n}  — {id}: the evidence that no input reaches it any more
graph:            updated {n} block(s), untouched {n}
sections changed: <Scope | Entry points | Invariants | Nested package roots | none>
provenance:       written, <base8>..<head8>
unresolved:       {n}, each with the searches performed
wrote:            {exactly one path}
touched anything else: no
```

`rows unchanged` is the load-bearing line. It is the only evidence that the subagent read the diff rather
than the tree, and a report without it cannot be told apart from a rebuild — the two produce the same file
and the same self-assessment.

A refresh that changes no row still writes its report: `rows unchanged: {all}`, provenance bumped. That is a
result, not a no-op, and the main agent records it in the commit message.
