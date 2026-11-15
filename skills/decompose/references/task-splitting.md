# Task splitting — normative criteria

This file is the whole of what `pdd:decompose` says about "how to cut". SKILL reads the PRD, assigns classes and orders the sequence; where to cut, and why a cut is allowed, is here.

Task splitting serves one thing only: **a failure must be attributable to a single unit.** Parallelism is a by-product. Thirty tasks that cannot say which one broke are worse than eight that can.

**There is no numeric ceiling here.** File counts, step counts and line counts are not criteria: they can be padded, and a padded split costs more than a coarse one. What follows are descriptive criteria.

## 1. The shape of a unit

A task is: one observable purpose, one identifiable entry point or one flow, one set of files it owns alone, one subagent finishing it in one go.

The criteria are three questions:

1. **Which entry point does it change?** Two entry points = two seams = two tasks (or one task with an explicit coupling reason).
2. **Which result does it deliver?** Two results that can ship independently = two tasks.
3. **When it breaks, can the failure name it?** If a task breaking makes the reader suspect the one next door, the cut is in the wrong place.

## 2. Why a unit may exceed "looks small"

Coupling is identifiable, not felt. Each of the following is enough for a unit to keep every file it needs:

- artifacts generated together with the code (client, types, schema) must land at the same time as their source;
- the repo's layering threshold forbids the import path a smaller cut would need;
- a seam's success and its refusal cannot be observed separately;
- the harness collects fixtures only from that file, or the registry recognises only that one registration point.

**Convenience is not a reason.** "two more tasks", "the diff is already written", "one commit is tidier" change nothing in the criteria.

For a unit that exceeds "it takes two seams to say it", write in the task file's coupling exception field: which constraint, which files, and what compensates (which oracle covers the whole in one pass). An exception must be something the next reader can take up and refute.

## 3. Signals that it should be cut

Each signal is a reason to "go and look once"; decide after measuring the actual repo:

- the purpose shows two results that can ship separately ("X and Y", "X first, then Y");
- the owned files span layers that do not import each other (migration + route, schema + component);
- some step says "also", "likewise", "repeat the above" — that is talking about a second instance;
- a task's result can be read only through a surface owned by another task;
- a task's owned set has grown too large to be read within one session of one subagent.

## 4. Shapes that should not be cut

Five shapes that look atomic but in fact strip the plan of attributability:

- **One behaviour cut in half.** The two halves land separately and the pair is never looked at; this cut is the most tempting, hence said twice.
- **A task that exists only so another one compiles.** That is a dependency, and the files belong to the earlier task.
- **Cutting by file.** Two files that must change together to keep one behaviour are one seam.
- **A string of small tasks.** Units with no real ordering are siblings; ten small tasks buy handovers rather than parallelism. After cutting, recompute the waves and see whether the width grew.
- **Scattering a shared prerequisite among its consumers.** A guard, fixture, registry registration or generator that two tasks both need gets its own unit, declared once.

## 5. Every edge must be probed against a live seam

For every dependency A → B ask: can the result A declares be reached with only A landed and the downstream absent?

If A's result needs a production change owned by B, A cannot come before B: move the behaviour into B, turn A into an explicit fixture/contract prerequisite, or invert the dependency.

A counterexample that can be fixed only by editing a production file nobody owns is a contradiction in the split, not an implementation failure.

## 6. Assigning classes (done at the same time as the cut)

Requirements are divided into two classes first, and the task class is derived from that (`pdd:plan` v2.1):

| Requirement | Acceptance object | Corresponding task |
| --- | --- | --- |
| `REQ-F` functional requirement | falsifiable once the behaviour is modelled | construction + verification A |
| `REQ-A` architectural requirement | the code obeys the declared architecture | migration / removal + verification C |

| Task class | Criterion | Files owned |
| --- | --- | --- |
| construction | a new observable behaviour appears (serves `REQ-F` only) | production code, schema, migration, config |
| verification | turns something already present into something decidable | A: model, harness, pin; B: baseline; C: constraint script |
| migration | structure changes, behaviour does not | production files on the source and target sides, tests, docs |
| removal | something disappears | the deleted files, plus every file whose references are rewritten, plus the tests that die with it |

When one requirement needs both new behaviour and new structure, it should be two requirements in the PRD (`REQ-F` plus `REQ-A`). If this is discovered only at the splitting stage, go back to `pdd:plan` and add one; do not mix the two classes at the task level.

Three rules follow from this:

1. **Editing production code is construction or migration, even when the motive is a defect found by verification, even when it is one line.** There is no mixed class.
2. **One verification task, one flow.** Two flows, two tasks, because the failure report and the model file are both per flow.
3. **A prerequisite shared by two verification tasks** (harness entry, generator, fixture loader) is itself a verification task and lands first, otherwise both sides edit it.

## 7. Ownership

One file, one writer is the invariant all the rules above serve. manifest, lockfile, shared enum/type module, migration chain, harness entry go to the root task; hot files each get one owner; shared guards, fixtures and objects carrying helpers each get one owner; every exported hook needs an owner that owns the call site. The complete list (declaration points, barrels, registries, the oracle that pins the set, harness collection) is in `references/ownership-rules.md`.

## 8. How a unit is written down

purpose, seam or flow, dependencies, owned set, ordered steps. That is the whole contract; `assets/TASK.md` is the table. Two things decided at splitting time that the writer must not lose:

- **a seam is a production entry point** (`file:function`, route, command), because the trace matrix has to map `REQ`s onto it, and the failure report has to name it too;
- **a unit can start from its own files alone**: state the seam and every boundary; module layout and implementation are left to the subagent.

## 9. Per-task check before dispatch

- [ ] one purpose, one seam or flow, dependencies written;
- [ ] one writer per file, dependencies explicit, no task needs an undeclared file;
- [ ] every module the steps import belongs to it or to a declared dependency;
- [ ] every edge has been probed against a live seam;
- [ ] the class is one of the four, and no single task owns both production files and model files;
- [ ] every surface the PRD lists has a construction task that builds it in its purpose or owned files — merely being mentioned does not count;
- [ ] one subagent can start from reading only this file.
