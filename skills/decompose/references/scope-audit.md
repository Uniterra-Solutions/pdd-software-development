# Pre-handoff audit — scope, acceptance, boundary

The audit happens after the cut is finished (task files written, DAG drawn) and before handoff to
`pdd:implement`. Its object is the cut, not the PRD: three questions per task, evidence only, no rewrite.

Why it exists: a wrongly cut task is invisible to its author (the cut was made from the same understanding
that produced the error) and expensive to its reader (the mistake surfaces during implementation, after the
work behind it is sunk). A fresh reader with the class's acceptance criterion in hand catches it in minutes.

## 1. Grouping arithmetic

- `n` = number of tasks in the register (gate nodes are not tasks and are not audited).
- auditors = `ceil(n / 3)`, each auditing **at most three** tasks.
- partition the register **contiguously in dispatch order**: wave by wave, id ascending within a wave.
  Contiguity keeps both sides of every seam in front of one reader.
- at each group boundary the auditor also reads the task files immediately before and after its slice
  (read only) and reports a boundary defect when the seam across that boundary is wrong.
- check the arithmetic before dispatch: the union of slices equals the register, no id appears twice. `n = 4`
  gives two auditors (3 + 1), not one auditor and an unaudited remainder.

Write the partition into the main agent's ledger for the run (`A1: T1 V1 V0`, `A2: M1 R1 V2`, …), so the
coverage claim in the handoff report is a comparison, not an impression.

## 2. The brief

Paths, never pasted bodies — the same rule the implementation brief follows, for the same reason (a second
copy of the contract drifts).

```
role:        auditor. Read-only: you may not create, edit or delete any file in the repo or the plan.
repo:        <repo path>                       ← read-only
PRD:         <plan-dir>/PRD.md
contract:    <plan-dir>/TASKS.md               ← DAG, register, trace matrix, waves
task dir:    <plan-dir>/tasks/                 ← read any of it; audit only your slice
your slice:  <ids, at most three>              ← the only tasks you audit
neighbours:  <ids, read only>                  ← audit only the seam across the group boundary
rules:       references/task-splitting.md, references/ownership-rules.md,
             references/task-<class>.md       ← read-only, the criterion for each class
questions:   scope, acceptance, boundary (see §3) — nothing else
prohibit:    editing any file; re-cutting; inventing tasks; proposing a different DAG;
             style, wording or naming preferences
report:      the table in §4, raw output only; if a slice is clean say so in one line
```

`test -f` each path before dispatch, and record the hash of each task file in the slice. A task file whose
hash changed during the audit was edited by someone, and the finding no longer describes what is on disk.

## 3. The three questions

### Scope

- Is there exactly one purpose, stated as an observable outcome rather than an internal structure?
- Is the owned set minimal **and** sufficient: does every file serve that purpose, and is every file the
  work needs actually in it? A missing file turns into a mid-run stop; an extra file is a second task
  hiding inside this one.
- Does any file appear in two tasks' owned sets? (Two writers on one file is a defect in the cut, not a
  merge problem to be solved later.)
- Does the class match the action the file describes? A move written as "create the new module" is a
  construction task wearing a migration's name; a deletion written as "write a cleanup script" is the old
  thing surviving.

### Acceptance

The criterion must be the one its class demands, and decidable by a command the task names:

| Class | The criterion must read | Red flag |
| --- | --- | --- |
| construction | this purpose is observable from `<real entry point>` via `<command>` | "the module exists", "tests pass", a purpose only reachable from a unit test |
| verification A | model at `<path>`, property `<name>` falsifiable within `<budget>`, seeded, shrunk, pinned | a property that restates the implementation; no budget; no seed |
| verification B | baseline recorded at `<path>` **before** the change, rerun by `<command>`, compared bit for bit, **plus one perturbation that must make the comparison fail** | a baseline with no timestamp relative to the change; "behaviour unchanged" with no comparison; no perturbation step — a comparison nobody has seen fail |
| verification C | rule `<quoted REQ-A>`, check at `<path>`, green before the change, still green after, deliberate red recorded | "the check passes"; no injected-violation step; no phase-two emptiness for a rule already violated |
| migration | oracle `<path/command>` and retention list; source set → target set; old path removed or expiring | no oracle; a retention list of one item; "behaviour preserved" |
| removal | absence proof (`grep`, compile, dependency graph) prints zero; the tests that die with it are deleted | "removed"; references to a caller still present; tests left behind |

Also: is a numeric quota acting as the criterion anywhere (a file cap, a step cap, "no more than N lines")?
A criterion of that shape is satisfiable by mutilating the work.

Also: is the only observable something the command **produces** rather than something it **decides** — a file
it writes, a report it prints, an exit code from a tool nobody has seen fail? "The command wrote `out.json`",
"the module is present", "the checker is green" are satisfied by the artefact existing. The criterion must
name what would make it red.

### Boundary

- Are the declared dependencies sufficient — can the task be started with exactly those parents accepted?
- Do the dependencies point the right way (nothing upstream of its own prerequisite, no cycle, no
  construction task depending on its own verification)?
- Does any seam straddle two tasks, so that neither can be accepted alone? That is one task split in two,
  or two tasks that must be one group with a declared coupling.
- Is a shared file — registry, barrel, route table, fixture set, manifest — owned by nobody? That is the
  dispatcher's shared prerequisite, and the cut must say so.
- Is a gate satisfiable on this graph (who feeds it, whom it releases)?

## 4. Finding table

| # | task | question | clause violated (quoted) | evidence | smallest fix |
| --- | --- | --- | --- | --- | --- |
| F1 | `T03` | acceptance | "the handler is covered by tests" | task file §Acceptance; class is construction | restate as the CLI command whose output is observed, or reclassify as verification |
| F2 | `M02` | scope | "moves auth/* into core/auth and drops the legacy flag" | `TASKS.md` register row `M02` | split: move (M02) and flag removal (new removal task, parent M02) |

Rules for the table:

- **quote, never paraphrase** — the sentence in the task file, or `file:line` in the code. A finding whose
  evidence is a summary cannot be reproduced and will be rejected.
- **one row per defect**, naming the smallest affected id. A finding that would require re-cutting the plan
  is still reported against an id; the re-cut belongs to the main agent.
- **no style, wording or naming findings.** They cost a round trip and buy nothing.
- **a clean slice is a finding of zero rows**, reported as `tasks read: T04 T05 V01 — 0 findings`.

## 5. What the main agent does with the report

1. **Reproduce each finding** — open the file, check the quoted clause, run the command if one is named.
   Subagent reports are not acceptance in this step either.
2. **Adopt** by dated amendment on the affected task: id kept, the amended clause written, the DAG,
   register, waves and trace matrix refreshed to match.
3. **Reject** with the reason recorded next to the finding ("reproduced: the entry point is not reachable
   from the CLI, only from the test harness" and "not reproduced: the file is in `Owned files` line 12").
   A rejected finding is evidence too — it says the auditor's reading of the criterion was wrong.
4. **Re-audit only the amended tasks.** Their ids go back to a (smaller) audit round; the untouched tasks do
   not, because nothing about them changed.
5. **Record the audit in the handoff.** `TASKS.md`'s dispatch section or the run report carries: the number
   of auditors, the slices, the finding count, and the disposition of each finding. `pdd:implement` should
   not have to ask whether the cut was audited.
