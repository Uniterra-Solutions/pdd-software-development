# PDD 3.0 — Design Philosophy

**An automated code-production process whose binding constraint is evidence, not throughput**

---

## 1. The asymmetry that motivates the design

Two costs move in opposite directions.

**The cost of producing a change has collapsed.** Agent frameworks write code at a rate that is now limited by dispatch breadth rather than by human typing speed; a second attempt at a failed edit costs tokens, not days; five parallel worktrees are a routine configuration. Whatever the absolute number, the direction is unambiguous: production throughput per engineer-hour has risen by a large factor and continues to rise.

**The cost of verifying a change has not collapsed.** It is bounded by three things that no amount of generation speed touches:

| Component | Why it resists automation |
| --- | --- |
| The oracle | Someone must state what "correct" means in a form a machine can decide. That statement is design work, not inference. |
| The acceptance act | A human must accept that the evidence implies the claim. Reading a diff and a log is not compressible by generating more code. |
| Systems without an oracle | Where behaviour is not mechanised — naming, layering intent, migration risk — review bandwidth is the only instrument, and it is human-bound. |

Three consequences follow, and they determine the whole design.

1. **Throughput is not the binding constraint; evidence is.** A pipeline optimised for production rate increases the volume of *unverified* change, and defects pushed downstream cost more than defects caught in place.
2. **Production must therefore be constrained to what verification can absorb.** A task that cannot be accepted by a decision procedure is not ready to be dispatched, regardless of how easy it is to implement.
3. **Verification is the design object.** The architecture of the process is the architecture of its acceptance criteria; everything else — task splitting, DAG order, dispatch parallelism — is downstream of that.

This is the premise the rest of the document reasons from: *code has become cheap to write and remains expensive to trust.*

---

## 2. The thesis: formal modelling as bounded-step falsification

We do not aim to prove programs correct. We aim to make every claim **refutable in a bounded number of steps, with a reproducible witness**.

A claim qualifies for the process only if it satisfies three conditions:

| Condition | Meaning | Failure mode it excludes |
| --- | --- | --- |
| **Decidable** | A command returns pass or fail; no judgement call at the moment of acceptance. | "Looks right", "seems reasonable", reviewer mood as an oracle. |
| **Bounded** | The search space is finite, or is a sampled space with a declared budget (draws, seeds, wall-clock). | "Tested thoroughly"; unbounded coverage claims that no one can audit. |
| **Attributable** | A failure names the cause — a seed, a minimal sequence, a rule, a file. | "Something broke"; failures that survive as anecdotes rather than as evidence. |

Formal modelling is the instrument, not the objective. A model of a business flow — its command set, its state machine, its invariants — converts an unbounded question (*does this work?*) into a finite one (*do these properties hold over these generators, within this budget?*). Property-based testing supplies the decision procedure; shrinking supplies the witness; pinning supplies the regression. The result is not a proof but something operationally stronger than a test suite: **a search that terminates with either a counterexample or an explicit statement of what was searched.**

What modelling does not supply is completeness. A green model means *no counterexample was found inside the stated budget* — never *the code is correct*. The design absorbs this limitation in three ways:

- a green claim never carries more weight than its budget, which is why budgets are written down rather than assumed;
- where behaviour cannot discriminate between correct and incorrect designs (structure, dependency direction, layering), acceptance moves to a **structural check** instead of a behavioural test (§4);
- where neither can decide, the process says so and routes the judgement to review, rather than manufacturing a test that would only appear to decide.

---

## 3. Acceptance is typed, so requirements are typed

The acceptance method decides the kind of requirement — not its size, not its urgency.

| Kind | Content | Acceptance object | Identifier |
| --- | --- | --- | --- |
| **Functional** | Adds or changes one observable behaviour | The behaviour becomes falsifiable once modelled: a flow, a command, a refusal class, an invariant | `REQ-F-<flow>-<n>` |
| **Architectural** | The code obeys a structural rule: boundaries, dependency directions, surface, performance budget | **The code obeys the architecture itself**, decided by an executable check — not by a behavioural test | `REQ-A-<n>` |

The distinction exists because the two were previously conflated, and the conflation produced two symmetrical failures:

- **Architecture written as behaviour.** "Behaviour unchanged after the refactor" is a *guard*, not an acceptance criterion. A migration accepted on that basis has no termination condition and nothing it can refuse; any structure passes.
- **Behaviour written as architecture.** A feature whose only evidence is "the layers are respected" ships unverified behaviour behind a green structural report.

Performance belongs to the architectural kind for a specific reason: order-of-magnitude gains come from structure, so acceptance requires both *the metric enters its budget* and *the structural change that produced it holds*. A requirement that says only "faster" can be neither accepted nor rejected.

---

## 4. Four classes of task, classified by acceptance object

Tasks are not classified by motive ("this is a cleanup", "this is a new feature") but by **what it is that has to be accepted**.

| Class | What changes | Acceptance object | Evidence required |
| --- | --- | --- | --- |
| **Construction** | A behaviour that did not exist | The new behaviour is usable from the real entry point | The entry point triggered; the affected suites and the typecheck still green |
| **Verification** | Nothing in production; a model, a baseline or a check | Behaviour becomes modelled (A), preserved (B) or structurally constrained (C) | Trace + seed + shrunk counterexample; bit-identical rerun; a deliberate red |
| **Migration** | Production code, tests and docs move; behaviour does not | Equivalence under an oracle, with a retention list | Oracle output, source→target set comparison, old path removed |
| **Removal** | Something ceases to exist | Non-existence, proven | Zero references, compile passes, no node left in the dependency graph, tests that die with it deleted |

**One task carries exactly one class.** A mixture — moving files while changing behaviour, deleting code while adding tests — splits into two, because the acceptance objects conflict: behaviour, equivalence, structure, non-existence. Written as one task, failure cannot be attributed, and the acceptance step silently degrades to "both halves were touched, so it is done".

There are exactly four classes because there are exactly four kinds of acceptance object. That is the whole derivation, and it is why the classification is stable: adding a fifth kind of task would require inventing a fifth kind of thing that can be accepted, and the process would have to define its oracle first.

What the classification buys:

1. **Attribution.** A failure names the class that owns it, and therefore the artifact to inspect.
2. **Parallel safety.** Different classes touch disjoint artifact kinds — production, model, structure, references — so parallel dispatch does not contend for the same acceptance surface.
3. **Honest accounting.** Refactors and deletions stop being disguised as construction. In the previous design every task became construction, and the two hardest kinds of change (preserve behaviour, prove absence) were never accepted at all.

---

## 5. Verification methodology

### 5.1 The unit is the business flow, not the task and not the file

A **flow** is what a person does from trigger to outcome: a command set acting on a state machine, governed by invariants. It is the unit the plan describes, the unit decomposition schedules, and the unit verification models.

The reason is arithmetic rather than taste. When the unit of verification was the task, the number of tests was a function of the number of tasks, and the number of tasks is set by scheduling constraints — parallelism, attribution, review scope. That is a formula for unbounded growth: every improvement in dispatch efficiency produced more tests. With the flow as the unit, the count is:

> *(flows touched × properties per flow) + distinct counterexamples*

which is bounded by the size of the business surface, not by the size of the schedule.

### 5.2 Three shapes of verification, each with its own logic

| Shape | Question | Used when | Evidence |
| --- | --- | --- | --- |
| **A — modelling** | Does the new behaviour satisfy its properties? | After construction is accepted | Trace, seed, shrunk minimal sequence, coverage reading |
| **B — behavioural guard** | Is behaviour preserved exactly? | Before and after a migration | Baseline frozen *before* the change; the same command rerun bit-identical |
| **C — architecture check** | Does the code obey the structural rule? | For every `REQ-A` | Green before, green after, and **one injected violation must turn it red** |

Shape C carries the epistemic weight that behavioural testing cannot: where a rule prohibits a shape rather than producing an output, no behavioural test can see it. The check is only accepted together with a demonstrated failure mode — a check that cannot go red is not a check.

### 5.3 Two gates encode the direction of dependence

- **Model gate.** A-class verification is dispatched only after every construction task it covers has been accepted. A model of code that is still in flight describes a fiction.
- **Guard gate.** Before a migration or removal: the B-class baseline has run and is frozen read-only, and the C-class check exists and is all green. After the change both rerun with the same command.

The gates are not process decoration; they are the operational form of two facts about evidence — *you cannot model what does not exist*, and *you cannot prove equivalence without a before*.

### 5.4 Negative controls are obligations, not advice

Four rules carry most of the regime's reliability:

- **Every check must have a demonstrated failure mode.** `mutate_check.py` executes this: perturb one byte at an exactly-once anchor, run the check, restore, rerun. Red under the perturbation, green after restoration, byte-identical — or the check cannot see that error.
- **Count > 0.** Green without executed volume is unfinished work. Selecting zero cases and exiting zero is not a pass.
- **A flaky red is measured, not rerun.** A property that fails once in a few dozen runs is usually drawing a rare value class. Acceptance requires *N random seeds (≥ 20) green plus the fixed seed green*, and the fix must narrow the value domain or pin the triggering value — not raise the draw count until the symptom hides.
- **The cut is audited by readers who did not write it.** A wrong scope or an undecidable acceptance criterion is invisible to the author of the cut, because the cut was made from the same understanding that produced the error, and it is expensive to the reader, because the mistake surfaces only after the work behind the task is sunk. `ceil(n/3)` read-only auditors therefore read the finished cut, three tasks each, and their findings are reproduced by the main agent before any of them is adopted.

### 5.5 What is deliberately absent

| Removed | Reason |
| --- | --- |
| A proposition per task, with a proof pair | Ties evidence volume to schedule size; produces tests ≥ tasks |
| A designated test site per task | Makes the test an artefact of the task rather than of the flow |
| Mutation testing as a per-commit gate | Cost scales with code, benefit does not; kept as a targeted control |
| Document linters | They score presence. Once presence is scored, the author optimises only the checkable half and ships a well-formed empty plan |
| Numeric task quotas (`≤ 2 files`, `≤ 5 steps`) | Played up to as targets; a split produced that way costs more than a coarse one |
| A final gate certifying the whole run | Invites "do it first, check later"; attribution belongs at the layer boundary |

---

## 6. Division of labour, and the invariant that protects it

| Role | Owns | Explicitly does not |
| --- | --- | --- |
| **plan** | The claim: business model, one behaviour section per flow, `REQ-F` / `REQ-A` | Describe anything recoverable from the code (flags, paths, schemas, test design) |
| **decompose** | Order, boundaries, classes, gates, DAG | Write tests, models or production code |
| **implement** | Execution in the given order, acceptance by class; with no tasks, the cut and dispatch of one flow's slices (no contract persisted) | Re-plan, re-cut a dispatched task, edit the contract, write tests or models, persist a breakdown |
| **review** | Independent judgement; two reviewer types selected by class | Modify code; repairs are new tasks |
| **explain** | Faithful restatement for a non-engineer | Introduce claims the plan does not contain |

The invariant underneath: **no role may silently rewrite another role's artifact.** In an agent pipeline the cheapest failure is upstream text edited until downstream passes — a relaxed clause, a widened baseline, a task re-cut to match what was built. The moment that is possible, attribution dies, and with it every measurement the process depends on. Hence dated amendments instead of in-place edits, `delta ⊆ owned`, and a stored hash of the task file compared at acceptance.

---

## 7. What the process buys

- **Cost per accepted change is linear in flows touched, not in tasks dispatched.** Verification no longer grows with the schedule.
- **Refactors and deletions become first class**: an oracle bought before the move, a retention list, an absence proof. Previously these were the two changes the process could not accept at all.
- **Parallelism is safe**: acceptance is per class and per owned file set, so concurrent work in one layer cannot corrupt another's verdict.
- **Evidence is reproducible**: command, raw output, seed, hash — a reviewer can rerun rather than trust.
- **Failures are routed, not absorbed**: a verification agent that finds a defect reports the trace; the defect becomes a construction or migration task; the gate closes again on the affected flows.

---

## 8. What it costs

| Cost | Nature |
| --- | --- |
| Upfront modelling | Properties must be written before they can be trusted; that is real design work the production side does not perform |
| Model maintenance | The model is an artifact with an owner and can rot; a stale model is worse than none because it is believed |
| Cross-flow integration | No single flow model covers interactions between flows; review carries that load |
| Discipline is load-bearing | Drop the class table or a gate and the system degrades quietly into "tests as artefacts" — the previous failure, reintroduced without a symptom |

---

## 9. Open problems

1. **Cross-flow and emergent behaviour.** Flow-level modelling bounds cost precisely because it does not model composition. Integration defects between flows are found by review and by production, not by the oracle.
2. **Subjective properties.** Naming, layering intent, and whether a seam is in the right place remain review-only. Two reviewer types narrow the variance; they do not mechanise it.
3. **Budget calibration.** Draw counts, wall-clock ceilings and shrink bounds are stated defaults, not values calibrated per repository.
4. **The residual human role.** Defining business semantics, naming the refusal classes, and deciding whether a modelled invariant is the *right* invariant. Automation removes the typing; it does not remove the judgement.

---

## 10. One sentence

> PDD is an automated code-production process in which every change must arrive with a bounded, reproducible refutation procedure; tasks are classified by the acceptance object they actually have rather than by the intent behind them; and the business flow — not the task, not the file — is the unit of modelling, because the cost of writing code has collapsed while the cost of believing it has not.

---

## Appendix: the companion skill, and why it is not a sixth stage

`pdd:study` reconstructs the business branches a repository already has and leaves them, with citations, in a
per-directory `AGENTS.md`. It is deliberately outside the pipeline: no gate, no task class, no acceptance
object of its own.

- **It answers "what is", not "what should be".** Every other skill in this bundle operates on a claim about
  intended behaviour. The inventory operates on observed behaviour and its only assertion is that the citation
  resolves — mechanically checkable, which is why it can be automated without the reviewer that §6 requires for
  judgement.
- **The unit is the directory because the reader is local.** An agent about to edit a file reads the file in
  that directory; a root document three levels up is read once, at the start, and then forgotten. Nested
  `AGENTS.md` files follow the reader down.
- **One subagent per unit is the same attribution argument as §4.** A wrong row must name a directory, so the
  repair is a re-dispatch rather than an investigation.
- **Its honest limit.** A branch table cannot tell you whether a decision is the right one, whether a seam sits
  in the place a maintainer would put it, or what the product is for. It tells you where the code changes
  behaviour and what makes each change fire — the ground truth that §3's typed acceptance, §4's class table and
  §5's flow models all assume someone already has.
- **The second run is a diff, not a study.** Once the files exist, the question changes from "what does this do"
  to "what does it do now that they do not say", and the only thing that answers it cheaply is the history the
  provenance block already names. The base is therefore per file rather than per repository — files studied at
  different times are stale by different amounts — and the classifier is one line of geometry: the deepest
  recorded unit whose directory contains the changed path owns it. The rule that keeps a refresh honest is the
  one that costs the most discipline: a row whose cited file ended the window unchanged is copied byte for
  byte, so the diff of the knowledge base reads as the diff of the code. Without it a refresh is a rebuild with
  a smaller diff, and a rebuild is how a map stops being evidence.

`pdd:archive` is the same argument applied to the *past* instead of the present. A plan records a decision once;
after two reversals the plan is worse than nothing, because it states a rule that no longer holds with an
authority no reader can see through. The archive converts that pile into a register where **one claim survives
per subject — the newest — with the rejected alternative and the quoted reason**, and then deletes the pile. The
design decision worth naming: a history that keeps both sides of a contradiction is not neutral, it is a
document that makes the reader the arbiter, and the smaller the team the more that arbitration costs. The
older claim is one `git show` away, and the deletion commit names the decisions that justified it.

---

*Applies to plugin `pdd` 1.4.0: `pdd:plan`, `pdd:decompose`, `pdd:implement`, `pdd:review`, `pdd:explain`, and the
companions `pdd:study` and `pdd:archive`.*
