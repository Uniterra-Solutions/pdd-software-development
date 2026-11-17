# Verification tasks (verification)

**Definition**: turn something already existing into something decidable — three shapes, with different acceptance objects.

| Shape | Used for | Deliverable |
| --- | --- | --- |
| **A modelling** | `REQ-F`: after construction lands, the flow has new commands | Model, property, pin |
| **B behavioural guard** | A migration or removal is about to touch a flow already covered by a model / existing suite | Baseline record, bit-for-bit comparison after the change |
| **C check / architecture check** | `REQ-A`: an architecture requirement is to be decided | An executable constraint check, all green before the change, and still all green after |

The C shape is the acceptance mechanism for "code obeys the architecture". What it checks is structure — dependency direction, module boundaries, public surface, cycles, complexity, performance budget — not behaviour, so it is not a test and should not be written as a test.

## When to use

- Construction of a `REQ-F` makes a new command appear in some flow → A.
- A migration or removal is about to touch an already covered flow → B, and the baseline must be completed **before** the change.
- The PRD has `REQ-A` (including performance requirements) → C. C usually has to land before the migration it decides, otherwise the migration has no termination condition.
- The method itself (flow, property, budget, negative control) is in `testing-methodology.md`; this file only covers how the task is written.

## Not this class

- Changing production code → construction or migration.
- Deleting production code → removal.
- Making a small model for a single seam → a slice is not the unit; one flow, one task.

## What to write in the file

1. **Flow** (A/B) or **Rule** (C) — A/B write the command set, states, refusal classes, invariants; C writes the original text of the `REQ-A` it decides.
2. **Covers** — which task ids it covers (the seams of production tasks, or the migration task it decides).
3. **Files owned** — A: model file, harness entry point, pin file. B: baseline artifact. C: constraint script and its config. **None of the three may contain production files.**
4. **Steps** — A: read the landed seam → transcribe the decision table → add properties for the new commands (each with a budget) → run → shrink → pin. B: run the baseline and record the seed and output digest → **inject one violation and confirm the comparison goes red, then restore** → (the change is done by another task) → rerun the same command → the difference is the defect. C: write the rule as pass/fail → run it to all green before the change → (the change is done by the migration task) → rerun, still must be all green.
5. **Budget** — A/B: sample count, seed, shrink bound, execution-time ceiling per flow, written in the harness file. C: threshold values (for example zero dependency violations, zero cycles, module public surface equal to the declared set, p95 within budget), written in the constraint script.

## Writing rules

- One flow, one A/B; one `REQ-A`, one C (three similar rules in the same scope may be merged into one, but this must be stated in the task file).
- One flow has only one model file and one harness entry point; a second verification task editing the same model is a conflict.
- A must start after the construction task it covers has been accepted. B/C must be completed and frozen (read-only) **before** the change they protect.
- Any task that wants to change a pin, a baseline or a constraint must first raise a dated amendment. A migration task modifying the check that decides it is self-exemption.
- Do not fix production defects when found: report the trace, seed and shortest sequence, and let the main agent open a construction or migration task.

## Report on completion

- A: which branches were reached, how much of the budget was used, what was caught (trace, seed, shortest sequence), corners not covered and why.
- B: the bit-for-bit comparison of the baseline and the rerun.
- C: the pass/fail of the check before and after the change, the violation list (if any), threshold values and measured values.

## Failure shapes

- **Modelling before construction** → the model describes an imagined implementation, and the property pins a design fantasy.
- **Changing the pin before comparing on a rerun** → the equivalence proof disappears, and what is left is just a new set of tests.
- **Writing the architecture check with tests** (running a few representative cases and then saying "the structure is fine") → what it decides is a sample of behaviour, not structure; violations happen on paths that were not sampled.
- **Loosening the check threshold after the fact** → the migration is automatically compliant, which amounts to no acceptance.
