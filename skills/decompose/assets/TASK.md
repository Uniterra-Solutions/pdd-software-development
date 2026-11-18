# <ID> — <task title>

| Field | Value |
| --- | --- |
| Task | `<ID>` |
| Class | `construction` \| `verification` \| `migration` \| `removal` |
| Requirement | `REQ-F-…` (functional) or `REQ-A-…` (architectural) |
| Depends on | <task id; the verification class also needs a gate> |
| Seam | `<file:function \| route \| command>` — construction, migration, removal |
| Flow | `<flow name>` — verification class |
| Owned files | <list, one per line> |
| REQs | `<REQ-...>` |
| Plan | `<plan-dir>/` |
| PRD | [`../PRD.md`](../PRD.md) — current statement |
| DAG and other tasks | [`../TASKS.md`](../TASKS.md) |
| Status | work contract |

**Self-sufficiency**: reading only this file and the PRD sections it references is enough to start work. The DAG, register and trace are in `../TASKS.md`; where the two disagree, the PRD prevails until the main agent rules.

**Boundaries**: write only the files listed in `Owned files`. Do not change `../PRD.md`, `../TASKS.md`, the files of tasks in the same batch, or the files of other tasks. When the spec contradicts itself or the scope is wrong, stop and report; the main agent handles it with a dated amendment. Do not weaken a requirement, and do not silently change the contract.

**Class boundaries**: construction does not write checks, models or pins; verification does not change production files; migration does not change behaviour along the way; removal leaves no coexisting artefact. The detailed spec for each of the four classes is in the matching `task-*.md` under `references/`.

**Path base**: the paths below are relative to the repo root, not to this file.

---

## Construction

- **Purpose**: <one newly appearing observable result; two results that can ship independently are two tasks>
- **Seam**: `<file:function | route | command>` — the entry point this task **creates**
- **Flow it feeds**: `<flow>` — which flow it adds commands to
- **Files owned**:
  - `<path>` — what changes here
- **Steps** (ordered; no code written per step):
  1. <locate the entry point, write down the observable contract>
  2. <change the behaviour, including boundaries, refusals, migration and compatibility>
  3. <state explicitly what is not touched>
- **Refusal**: `<refuse class>` — the corresponding behaviour
- **Untouched**: <what will not change; if it invalidates an existing assertion, list it in the report>

## Verification

- **Flow**: <command set × state × refusal class × invariant>
- **Covers**: `<list of production task ids>`
- **Shape**: `A modelling` (serves `REQ-F`) | `B behavioural guard` (baseline / rerun) | `C architecture check` (serves `REQ-A`)
- **Files owned**:
   - `<model path>` — the reference model: the decision tables transcribed (A)
   - `<PTEST path>`, `<NTEST path>` — the two generated arrays (A)
   - `<harness path>` — entry, `k`, class partition (A / B)
  - `<constraint path>` — constraint script and threshold (C)
- **Steps**:
   1. <A: read the landed seam, transcribe each operation's decision table | B: run the baseline and record the seed and an output digest>
   2. <A: declare k and the class partition, then generate PTEST (one row per term) and NTEST (strength-k array under the negation constraint) | B: do not touch the baseline artefact>
   3. <A: run and record the failing row verbatim | B: rerun the same command, compare bit for bit | C: run to all-green before the change, and after the change it must still pass>
- **Budget**: written in the harness file (`k`, class partition, both array sizes, runtime cap per flow)

## Migration

- **Source**: <the set to be moved: files, symbols, sections>
- **Target**: <where it moves to; the target structure is the deliverable>
- **Preserved**: <flow ids, constraint names, API surfaces that must be kept>
- **Oracle**: <which existing suite / model / baseline decides equivalence; without one it must not be dispatched>
- **Files owned**: <list both the source side and the target side>
- **Steps**:
  1. <one structural action>
  2. <the next structural action>
  3. <last: remove the old path, run the oracle>
- **Reversible**: <rollback point>
- **Performance** (performance-oriented migrations only): <measuring instrument and command, current baseline, target budget>

## Removal

- **Disappears**: <symbols, files, sections, flags, dependencies, item by item>
- **Replaced by**: <the replacement already in place and covered by verification>
- **Absence proof**: <which command must report zero references; compilation; dependency graph; link check>
- **Dies with it**: <the tests, fixtures, doc sections, config keys that die with it>
- **Files owned**: <the deleted files, plus every file whose references must be rewritten>
- **Steps**:
  1. <rewrite the referencing sites>
  2. <delete the body and its tests>
  3. <run the absence proof>
- **Guard**: <how to confirm the residue is at zero>

---

## Report format

Report four things when done; missing one means the task is not complete:

1. Result — construction: what a caller now sees; verification: which branches were walked and what was caught (trace, seed, shortest sequence); migration: evidence for each item of the retention list; removal: the raw output of the absence proof.
2. The files actually created or modified, item by item against `Owned files`.
3. Where you departed from this file and why — write `none` if nowhere.
4. What could not be delivered within the owned files, and what decision it needs; for the verification class also attach every production defect found and the seam it names.
