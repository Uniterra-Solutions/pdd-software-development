# Testing methodology — one decision table, exhaustive up to k

**Status: adopted.** This file is the only place in `pdd:decompose` where a test is specified. `SKILL.md`,
`assets/TASK.md` and `assets/TASKS.md` carry no test text, no expected values and no commands.

## 1. What this replaces

The regime this file previously carried sampled behaviour: generators over a flow, properties over traces, a
sample budget, shrinking, reachability measured from a transition log. It was replaced because the discrete
part of a decision was never sampled in the first place — it was enumerable, and sampling an enumerable
space produces a probabilistic claim about something already complete. Two judgements from that regime
survive: **the oracle is designed before the test is written**, and **a check that cannot go red proves
nothing**.

The method below is pseudo-exhaustive: for every decision, every combination of the variable values that
decision depends on is tested. The claim on a green run is bounded and complete — "no defect in this
decision outside a stated interaction strength" — not statistical.

## 2. The unit: a decision, and the flow that owns it

- The **unit of testing is a decision table's row set** — one table per operation, as `pdd:plan` §3 already
  requires: inputs, precondition, outcome (`apply`, or `refuse` with a named class), postcondition.
- The **unit of ownership is the flow** those operations belong to. One verification task owns one flow: its
  tables, its two arrays, its harness entry point. Two verification tasks may not own the same flow.
- Task count is not an input. Thirty construction tasks may land three flows; the test volume is a function
  of those flows' decision tables.

The table transcribed into an executable form is the **reference model**. The arrays are generated from it,
and the implementation is run against them. The reference model decides expected outcomes; it is never a
copy of the implementation's own logic.

## 3. Why enumerate rather than sample

A decision table's antecedent is a Boolean expression over a finite set of variables. If no conjunct in it
has more than `k` literals, then `k`-way combinations cover every combination that any single decision can
distinguish:

```
if all faults in a decision are triggered by <= k variables interacting,
then testing all k-tuples is equivalent to exhaustive testing of that decision
```

This is an assumption about the system, not a theorem about it, and it is the assumption a plan states
explicitly (`§11`). Where it holds, the suite is complete to `k`; where it does not, the suite is a sample
and must not be described as exhaustive.

Keep sampling only where the domain is genuinely unbounded **and** no class partition is declared — a
free-form string, a timestamp sequence. A decision table is not such a domain.

## 4. The transform: antecedents to k-DNF

1. Write each operation's table as one implication per row, plus a default row:

```
(R1 -> outcome1) (R2 -> outcome2) ... (Rm -> outcomem)   else -> default | refuse:<class>
```

2. **Rows must be mutually exclusive** — for any input at most one antecedent matches. If two rows can both
   match, stop: that is a finding against the table (two rules for one input, and whichever the engine
   evaluates first wins), not something a test can decide.
3. Convert each antecedent to DNF and split on the disjunctions. Every resulting conjunction is a **term**
   `Ti`. The number of literals in the longest term over the table is `k`: the table is in `k`-DNF.
4. Record `k` per table in the harness file. A table whose terms differ wildly in length (one term of 2, one
   of 9) sets an expensive `k` for the whole table; splitting the decision is the fix, not lowering `k`.

## 5. PTEST — one row per term

For the consequent under test, designate `(+)` as that outcome and `(-)` as everything else. For every term
`Ti` of the antecedents that produce `(+)`:

```
PTEST_i = Ti AND ( AND over j != i of NOT Tj )
```

One row per term, all literals of `Ti` positive and every *other* term's literals negative.

**Why the negations are there.** With a rule `ab + cd -> R1`, the inputs `1100`, `1101` and `1110` appear to
test `ab`. They do not: if the implementation ignores `a` and `b`, `cd` still holds and `R1` is returned, so
the fault is masked. Only `1100` with `c` and `d` forced false exposes it.

Cost is linear in the table: `|PTEST|` equals the sum of terms over the rows producing that outcome.

When several rows share an outcome, their antecedents are OR'd before splitting — `(R1 + R2) -> Q1` —
because the implementation owes `Q1` when either holds.

## 6. NTEST — a covering array constrained by NOT R

For the same consequent:

```
NTEST = covering array of strength k over the table's whole variable universe,
        with NOT R as a constraint,
        every row expecting (-)
```

`R` is the OR of the antecedents that produce `(+)`; the constraint removes exactly those combinations, so
every row is a combination that must **not** produce `(+)`. Rows retain all 1- through (`k`-1)-way
combinations of the remaining space.

The covering array is sound here for one reason: with mutually exclusive antecedents, masking can only
happen in the negative direction. A positive row that returns `(-)` is a defect; a negative row that returns
`(+)` is a defect; no row can be rescued by another matching first.

Size grows as `v^k · log n` for `v` values per variable and `n` variables — slowly in `n`, fast in `v` and
`k`. That is what `§7` and `§10` are for.

## 7. Numeric domains: equivalence classes, never raw values

A numeric input has thresholds. Its classes are defined by the decision, not by the type:

```
age > 18      classes: {..., 17}, {18}, {19, ...}      representatives 17, 18, 19
balance >= 0  classes: {..., -1}, {0}, {1, ...}        representatives -1, 0, 1
0 <= x <= 100 classes: {-1}, {0}, {1..99}, {100}, {101}
```

Rules:

- `v` in the covering array is the **number of classes**, not the number of representable values. An amount
  with two thresholds has three classes.
- Each class is represented by a boundary value in every array row — the threshold itself and its
  neighbours, never a random draw between boundaries.
- The class partition is written into the harness file with its thresholds. A class that is not declared is
  not tested, and the report says so.
- **The method is exhaustive over classes, not over numbers.** A defect that only fires at `x = 7` when the
  declared classes are `{<=6}`, `{>=8}` is outside the claim. Declaring classes is the modelling work; a
  partition with one class per variable is a sample wearing a table's clothes.

## 8. State is a variable, and the matrix is enumerated

The state an operation reads is a column in its antecedent universe, exactly like any other variable.

- Every operation's table names the states in which it applies and the states in which it must refuse.
- The `(operation x state)` matrix is enumerated: each cell is either an applicable row (a PTEST row or a
  positive row of another outcome) or a negative row expecting the named refusal class.
- **Forbidden moves are negative rows, not comments.** "Close on a suspended account is refused" is a row
  whose expected outcome is `refuse:<class>`; the class name is the oracle, and "an error" is not a class.
- **Sequences longer than one operation are out of scope** unless the relevant history becomes a state
  variable. A decision that depends on the previous three commands must either expose that history as a
  state, or accept that this method does not decide it (`§13`).

## 9. The oracle is free

Every row of one array carries the same expectation: PTEST rows expect their term's outcome, NTEST rows
expect the default or the named refusal class. No per-row expected value is written by hand.

That is why a large array is not a maintenance burden and why the arrays can be fully automated. It is also
why the reference model must be right: there is no per-row human check left to catch a wrong table.

## 10. Cost is declared before the arrays are generated

The harness file states, per table:

| Quantity | Formula | Ruling |
| --- | --- | --- |
| `k` | longest conjunct in the table's k-DNF | fixed by the table, not by preference |
| `|PTEST|` | sum of terms over the rows with that outcome | linear; no cap needed |
| `|NTEST|` | `v^k · log n` (measured after generation, not estimated) | cap the product, not `k` |
| runtime | median wall time per flow | a bloat signal, not a target |

**Never lower `k` to fit the budget.** If `v^k` is impractical, the fix is to partition values into fewer
classes (`§7`), split the decision into two tables, or record the decision as untested — in that order.
Lowering `k` silently turns the completeness claim into a false one, and the report cannot show it.

## 11. What the arrays prove, and the exact bound

PTEST ∪ NTEST detects faults caused by a **missing, added, or altered term of `<= k` literals**.

Beyond `k`, the guarantee is partial and stated as such: if the correct term has more than `k` literals and
is **not** a subset of the faulty term, the fault is still detected; if the correct term **is** a subset of
the faulty term, only some faults are detected.

So every report carries `k` and this bound sentence. "The decision table is exhaustively tested" without
`k` is an over-claim; with `k` it is a bounded, checkable statement.

The method tests the implementation against the table. It does not test the table against the business —
that is `pdd:plan`'s review and `pdd:review`'s job.

## 12. Preconditions, and the finding each one produces

| Precondition | Check | If it fails |
| --- | --- | --- |
| antecedents mutually exclusive | compare rows pairwise on shared literals; a pair that can both be true is a finding | report as a table defect; do not test |
| declared fan-in `<= k` | recompute the longest conjunct from the table text | the table or the `k` declaration is wrong; fix before generating |
| every operation has a table | `REQ-F` inventory vs tables present | return to `pdd:plan`; a guessed table pins a fiction |
| refusal classes named | every negative expectation is a class from the table | a row expecting "an error" is not a test |
| no cross-decision hidden input | every variable an operation reads appears in its universe | add it; an undeclared read is an untested branch |

## 13. Where the method does not hold

- **Long sequences.** Interaction histories beyond one operation are not covered unless modelled as state
  (`§8`). A flow whose correctness depends on a sequence needs a state-machine treatment with enumerated
  reachable states — a different object, and one that must not be described as pseudo-exhaustive.
- **Concurrency.** Interleavings are exponentially sparse in any array; `k`-way combinations do not touch
  them. Concurrent flows need explicit enumeration of linearization points.
- **Continuous values between declared classes.** Exhaustive over classes only (`§7`).
- **Architecture (`REQ-A`).** Decided by a C check — dependency direction, module boundaries, cycles,
  complexity, performance budget — because no array of behavioural rows makes a layering violation visible.
- **A decision with many variables and a large `k`.** `v^k` is a real wall; a decision with `k = 6` and six
  three-valued variables is `729 · log n` rows and should be split, not generated.

## 14. Gates — commands and reconciliations, no scoring scripts

Each gate is a reading or a command run in the turn. None of them scores wording.

1. **`k` is recomputable.** The longest conjunct in the transcribed table equals the `k` in the harness file.
2. **PTEST reconciles.** One row per term; the row count equals the number of terms for that outcome. Count
   both sides.
3. **NTEST reconciles.** Every generated row's expectation is a named class; no row's expectation is blank or
   "error".
4. **The matrix is complete.** Every `(operation x state)` cell that the flow model declares appears in
   some row; a declared state with no row is a hole.
5. **Boundaries appear.** Every declared class boundary appears in at least one row per variable.
6. **Negative control.** Change one literal in the reference model — a term loses a literal, or a class
   boundary moves — and the suite must go red. Restore, rerun, confirm green. A suite that survives a
   mutated table is testing nothing.

## 15. What a run reports

- `k`, the two array sizes, and the class partition used, per table;
- the failing row **verbatim** — the literal assignment is already the minimal combination, so no shrink step
  exists; whoever reads it can attribute it to one table row and therefore to one task;
- the table row the implementation contradicts, and the observed outcome (`apply`, or `refuse:<class>`);
- decisions recorded as untested, with the reason (`v^k` wall, sequence dependence, no table).

A failure reported as `assert false` with no row is not a test result; it is a bug report with the evidence
removed.

## 16. Still open

| # | Question | Candidates |
| --- | --- | --- |
| D1 | covering array generation | generate with ACTS/IPOG off-line and commit the array, or build it in the harness |
| D2 | `v^k` cap | a fixed row ceiling, or a per-plan ruling recorded in the task file |
| D3 | state enumeration depth | one-step matrix only, or enumerated reachable states for flow-critical sequences |
| D4 | who owns the class partition | the construction task that lands the operation, or the verification task that tests it |
| D5 | concurrency | declared out of scope per flow, or a separate harness class |
| D6 | what review checks | `k` recomputation, array reconciliation, matrix completeness, boundary coverage, negative control |
