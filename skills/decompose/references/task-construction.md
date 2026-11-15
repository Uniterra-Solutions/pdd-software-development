# Construction tasks (construction)

**Definition**: add one observable behaviour that did not exist before. **Serves `REQ-F` only.**

Architecture requirements (`REQ-A`) do not produce construction tasks: they are achieved by refactoring and removal, and are decided by the C check / architecture check. If the purpose of a "construction" task can only be written as "make some piece of code conform to a structural rule", it is actually a migration task.

## When to use

- Some flow in the PRD has a command, state or guarantee that is not yet implemented.
- Some surface becomes usable for the first time.

## Not this class

| Situation | Should be classified |
| --- | --- |
| Changing existing behaviour | Not construction. The model of the original flow must be updated, and usually a new `REQ` is needed |
| Moving code from A to B | Migration |
| Making anything disappear | Removal |
| Establishing a check or model for new behaviour | Verification, and after the construction has been accepted |

## What to write in the file

1. **Purpose** — one newly appearing observable result. Two independently shippable results are two tasks.
2. **Seam** — the entry point this class of task **creates** (`file:function`, route, command).
3. **Files owned** — the minimal sufficient set for one behaviour: the source file and the supporting pieces it directly needs (types, migration, config, registration entries) belong to the same task.
4. **Steps** — each step does one thing; the last step makes the surface reachable from a real entry point.
5. **Boundary** — boundaries that must be handled at write time; list only those the PRD specifies as changing business results (nothing to do, upper limit, duplicate, out of order, bad input, interruption).
6. **Refusal** — the named refuse class, and its corresponding behaviour.
7. **Untouched** — explicitly state what will not change. If your change invalidates an existing assertion, list it in the report, and handle it in the same task per the removal rules of `ownership-rules.md`.
8. **Flow it feeds** — which flow it adds commands to. This line gives the verification task something to model.

## Writing rules

- One task, one new behaviour.
- Do not split "make it compile", "hook it up to the registry", "add the types" into separate tasks — those are parts of the same behaviour.
- The task file contains no checks, no models, no pin.
- If two new behaviours must change the same file at the same time, they share one seam: merge them into one task, or do one shared prerequisite first (the shared prerequisite is itself construction).
- Describe up to "a subagent can start work without reading other task files"; leave module layout to it.

## Report on completion

- The added observable behaviour (what the caller now sees).
- The file list, item by item against `Files owned`.
- Deviations from this file and the reasons.
- Which flow the added commands belong to, and whether any refuse class is not yet implemented.

## Failure shapes

- **Purpose written as internal structure** ("add XxxService") → the surface is still unreachable; rewrite the purpose.
- **Two tasks changing one registry at the same time** → a shared prerequisite is missing.
- **A check slipped into a construction task** → it will conflict with the verification phase, and no one is responsible for it when removing.
