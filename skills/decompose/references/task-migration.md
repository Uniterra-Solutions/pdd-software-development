# Migration tasks (migration)

**Definition**: move production code, tests or documentation from one structure to another structure, with observable behaviour unchanged.

## When to use

- Adjustments to module boundaries, directories, internal APIs, data flow, internal schema shape.
- Relocating and regrouping tests (not deleting them).
- Documentation reorganisation: moving sections, merging, rewriting into a new structure.

## Prerequisites (all required)

1. **Oracle present** — the existing suite is sufficient to decide, or a previous verification task has already established a model / baseline. A migration without an oracle must not be dispatched; that is blind editing. If there is none, spend one verification task first to buy an oracle; that is usually cheaper than the migration itself.
- **Architecture check present (`REQ-A`)** — if this migration serves an architecture requirement, the executable check for that requirement must already exist and be all green. That check is this task's acceptance; the behavioural oracle is only a guard.
2. **Retention list** — the flows, behaviours and structural constraints this relocation must retain (dependency direction, export surface, execution-time budget), listed one by one. Writing "behaviour unchanged" amounts to writing nothing.
3. **Slices and rollback points** — each step should be independently green; if any step is not green, stop and do not stack on top of it.

## What to write in the file

1. **Source** — where it is moved from (files, symbols, sections), expressed as a set.
2. **Target** — where it is moved to. The target structure is itself the deliverable, so write it clearly; this is the only task type in this project that is permitted to describe structure.
3. **Preserved** — the retention list (flow id, constraint name, API surface).
4. **Files owned** — both the source side and the target side belong to this task; one writer at a time.
5. **Steps** — each step is one structural action; the last step removes the old path (leaving no long-term coexistence, unless there is an explicit deprecation window and expiry condition).
6. **Reversible** — where the rollback points are.

## Writing rules

- Relocation and behaviour change must not be in the same task. To change behaviour at the same time, get the refactoring green first, then open a construction task.
- Move one layer at a time: interface first, then implementation, then data.
- Removal of the old path belongs to this task or to one removal task immediately after it; do not let "temporary coexistence" become a permanent state.
- Tests follow production code when it moves, but assertions must not be loosened; loosening is a behaviour change.
- After documentation relocation, internal links and cross-references must still resolve; this is a constraint that can be checked before dispatch.

## Performance-oriented migration

Performance improvement almost always belongs to architecture requirements: only a structural change brings an order-of-magnitude gain. Such tasks must therefore state three things — the measurement method (instrument and command), the current baseline, and the target budget — and report the measured value after the change. An "optimisation" without a baseline cannot be accepted, and cannot be rejected either.

## Report on completion

- The pass/fail of the architecture check after the change, and the `REQ-A` it decides.
- Evidence for each item of the retention list: which oracle shows it unchanged.
- Performance cases: baseline, budget, measured value, same instrument and same command.
- Structural contrast: source set → target set.
- Whether the old path has been removed.
- Coexisting artifacts deliberately left behind and their expiry conditions.

## Failure shapes

- **Starting work without an oracle** → after the change you can only say "it looks the same".
- **Moving files and changing behaviour in the same task** → the difference cannot be attributed, and no rollback point exists.
- **The old path is kept forever** → two structures coexist long term, which is more expensive than not changing at all.
