# Worked examples and boundaries of task splitting

`references/task-splitting.md` gives the criteria; this file gives examples, counterexamples and the conditions for relaxing them. The skeleton of the criteria is: one observable purpose, one identifiable entry point or one flow, one set of files owned alone, one subagent finishing it in one go. **No numeric ceiling** — size is a judgement, not a quota.

## 1. The three questions

1. **Which entry point?** One `file:function`, one route, one CLI command, one migration file. If you can list several, it is probably several tasks.
2. **Which result?** One change a caller or reader can observe.
3. **When it breaks, can it be named?** If the failure makes the reader suspect the one next door, the cut is in the wrong place.

The header of the task file must be able to answer these three questions (`Seam` / `Purpose` / `Files owned`). If it cannot, the split is not finished.

## 2. Four worked examples

### 2.1 Construction: "admin routes need an API key"

Done as one task it gets three things wrong: five routes, two behaviours, one shared guard. Split:

- `T1` the guard itself — `auth/require-key.ts:requireKey`, not wired into any route yet. It owns the refusal classes and the refusal body, and there is exactly one copy.
- `T2`..`T4` one per route family — each imports the guard, each makes its own surface reachable from the real router.
- `T5` registry registration — makes `T2`..`T4` actually get walked, observed through the real entry point (a request in `server.ts`), without hand-assembling the app.

The shape of the refusal body lives only in `T1`; the route tasks do not restate it. Five tasks restating one predicate are five copies that each drift on their own.

### 2.2 Construction: "settings page redesign"

Do not cut by CSS file: one stylesheet, one owner. Cut by "where a wrong implementation would break":

- `T1` the token sheet — every later task imports it; the values are transcribed from the table in the PRD.
- `T2` the form components on the page.
- `T3` page layout and spacing.

### 2.3 Migration: "move the settlement calculation into core"

- Settle the oracle first: an existing suite covers this calculation, or dispatch a verification task first to build the model.
- `M1` move the interface first (call sites point at the new module, the inside is still the old implementation), green.
- `M2` move the implementation next (the new module takes over the calculation), green, running the same oracle for a bit-for-bit comparison.
- `R1` finish: the old module and its tests disappear together (`references/task-removal.md`).

Three rollback points, with only one thing changing at a time. Merge `M1` and `M2` into one task and a failure cannot be told apart between interface and algorithm.

### 2.4 Removal: "remove the old helper"

- Prerequisite: the new helper is already in place and covered by a flow model.
- Run the evidence that references are at zero first: `git grep -n "legacyHelper"`, and paste the result into the task.
- `R1` rewrite the referencing sites → delete the body and its tests → run the absence proof (grep returns zero, compilation passes, link check passes).

If this task deletes production code but leaves the tests in place, the suite starts testing something that does not exist, and it may still be green, because what it tests is a mock.

## 3. Shapes that must not be cut

- **One rule cut in two.** "never write back the old stamp after writing the new one" is the same rule across two observations; cut apart, you get two halves that are each true on their own, and the pair is never looked at.
- **A task that exists only to compile.** The files belong to the task that needs them.
- **Two files that must change together.** A schema and the types generated from it, a component and the stylesheet only it uses: one seam, two owned files, one task.
- **A task that "writes checks for the previous one".** It moves the description away from the flow it describes, so there is one model per seam instead of one model per flow.
- **Cutting mechanically by symbol, by file, by layer.** That is diff partitioning, not decomposition; none of the pieces in it can break on its own and name a behaviour.

## 4. Counters for fragmentation

When the node count grows but the width does not, check each of these:

- **Siblings, not a chain.** Two tasks cut out of one coarse task have no edge between them. If you need an edge, ask whether the second one is the same behaviour read from a later point.
- **A shared prerequisite needs its own unit.** fixture, guard, registry, migration baseline: one task, the rest depend on it, the rule is written once.
- **Separating a verification unit from a construction unit is legitimate.** When a flow covers so much behaviour that one model struggles, let another verification task own an adjacent flow — it adds no production writer, and each flow still has only one model file.
- **Only if the width grew was the cut right.** Recompute the waves after cutting; if the number of members in the second wave is unchanged, this split bought only a handover, and the original coarse task was right.

## 5. When to relax, and when not to

**An objective constraint is three things holding at once:**

1. **Identifiable.** You can point at the thing, not feel it: the generated client and its schema are checked in together; the repo's layering threshold rejects the import a smaller cut needs; the compiler pulls the constraint into a single translation unit.
2. **Not further divisible.** The reason the smaller shape fails is the product or the toolchain, not the plan's convenience. If a re-cut exists that preserves the same attributability, the re-cut wins.
3. **Still attributable.** After relaxing, a failure is still absorbed by one behaviour. If the larger unit delivers two results that can ship separately, it is not one task.

**Legitimate examples** (put in the task file's coupling exception field, stating which constraint, which files, which oracle covers the whole in one pass): a generated client and its schema must land at the same time; a migration must backfill before it creates the index, in the same file and the same order.

**Illegitimate reasons**: "splitting into two adds two tasks" — task count is not the cost model, handovers are; "it's one commit anyway" — a commit is not a unit of work; "the model is hard to place" — that means the flow's boundary is wrong, not that the criteria are wrong; "the diff is already written" — written code is not a constraint on the split; "everything touches the router" — then the router is a shared prerequisite, and the behaviour tasks depend on it.

## 6. Per-task check before dispatch

- [ ] the header names one task's seam or flow;
- [ ] the class is one of the four, and no task owns both production files and model files;
- [ ] the owned set is the minimal sufficient set for this thing; larger ownership is traded for identifiable coupling;
- [ ] the steps are ordered, each step changes one thing and can be rolled back independently;
- [ ] a multi-step task declares its checkpoints — which steps commit separately, and the step a failed run
      resumes from — so a failure costs the failing step, not the whole task;
- [ ] every owned path is named after the function it performs and contains no task id (`tests/t3_router.spec.ts`, `T03-x`, `guard_t3`, `test_t3`, `task_3` are all disallowed);
- [ ] when a task breaks, it does not make the reader suspect its siblings.
