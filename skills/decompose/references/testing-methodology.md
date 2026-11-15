# Testing methodology — one business unit, falsified over the whole flow

**Status: adopted direction, parameters still open.** This file is the only place in `pdd:decompose` where
a test is specified. `SKILL.md`, `assets/TASK.md` and `assets/TASKS.md` carry no propositions, commands,
test paths or proof pairs. §1–§3 record what was removed and why; §4 is the adopted method; §5 lists the
numbers that still need a ruling.

## 1. What was removed

A per-task contract: one or two formal propositions per task (`forall / pre / obs / post / witness`), each
with a test site, a single verification command, and a `before:`/`after:` proof pair pasted into the task
file — enforced by scripts that checked presence (a proposition exists, a pair is pasted). Deleted in
v3.0.0. What replaced it is §4.

No field in this file is something a task file must carry. §2 keeps only the diagnosis — why that contract
grew without bound — because the failure is what has to be avoided, not the machinery that produced it.

## 2. Why the per-task regime produced unbounded test growth

Four mechanisms, and they compound:

1. **The unit of proof was the unit of construction.** Verification was owed per task, so the suite grew
   with the number of tasks — and task count is set by parallelism and attribution, not by risk.
2. **Obtaining a red run was cheapest by writing a new assertion.** Every task paid a new-file tax, and no
   task ever paid a deletion.
3. **The gates scored presence, not value.** "A check exists here" is machine-checkable; "this assertion is
   worth keeping" is not. Only the checkable half was optimised.
4. **Nothing removed anything.** No step merged or deleted a test, no budget capped the total, no clause
   priced the suite's runtime. Growth had no counter-force.

Net: the suite became the bottleneck, and a regression signal diluted across hundreds of tool-named
assertions reports failure less usefully than a small set with one owner per invariant. §4 is the
replacement; §4.9 says what it still does not cover.

**Confidence.** This is a mechanism argument read from the withdrawn text, not a measurement of one plan's
test count.

## 3. Judgements that survived the deletion

- Name the counterexample before writing anything: one concrete input that makes the claim false.
- Observe the production seam, never a mock's internal calls.
- Prove an absence last, or it passes vacuously.
- Name tests after behaviour, never after a task or issue id.
- One seam, both outcomes observable — a reason to keep the seam coupled, not to double the test count.

## 4. Adopted: the flow is the unit, and property-based testing falsifies it

### 4.1 A flow is command set × state machine × invariants

The unit of verification is a business flow a user can drive end to end — not an endpoint, a module or a
task.

```
FLOW deposit
  states      idle, active, suspended, closed
  commands    open(amount), deposit(amount), withdraw(amount), close()
  invariants  balance ≥ 0
              closed ⇒ no further command applies
              Σ deposits − Σ withdrawals = balance
```

Task count is deliberately not an input. A plan of thirty tasks may own three flows, and test volume is a
function of the three flows.

### 4.2 The PRD already carries the generator's source

`pdd:plan` §3 already requires entities with numeric domains, one decision table per operation (inputs,
precondition, outcome `apply` or `refuse` with a named class, postcondition), states with legal and
forbidden moves, and the invariants that hold in every state. That is the specification a model-based
property test consumes:

| PRD element | Becomes |
| --- | --- |
| Entities with numeric domains | the generators' value space (u64 slot, native units, bps, timestamps) |
| Decision table rows | command applicability, the `refuse` class set, and the postcondition |
| States and legal moves | the command mask per state; illegal moves must be refused, not crashed |
| Invariants | the properties asserted over every trace |
| Refusals with a named class | the oracle for the negative branch: the exact class, not "an error" |

No new PRD field is needed. A flow whose decision table cannot be written is under-specified, and the
correct move is to return to `pdd:plan` rather than write a test that guesses.

### 4.3 Three layers, and a count formula without `tasks` in it

| Layer | Owned by | Grows with | Contents |
| --- | --- | --- | --- |
| Property layer | the flow | flows × 3–7 properties | invariants, refusal classes, idempotency, monotonicity, conservation |
| Model / oracle layer | the flow | one per flow | the decision table transcribed as an executable reference, or the invariant set when it is strong enough |
| Pin layer | the counterexample | distinct findings | one example test per shrunk counterexample, permanent |

```
test count ≈ flows × properties + distinct counterexamples found
```

A pin enters when the flow is falsified and leaves when the invariant it pins is retired — the deletion
path the old regime lacked.

### 4.4 Finite-step falsification: the budget is part of the contract

Property-based testing proves nothing; it falsifies inside a stated budget. These are contract fields, not
runner defaults:

- **Samples.** Per flow per run, stated in the flow's harness file (proposal: 200 on commit, 5 000 nightly).
- **Seed.** Every failure prints its seed and trace; the seed replays verbatim in CI until the fix lands,
  then the shrunk trace becomes a pin.
- **Shrinking minimises command-sequence length.** The reported counterexample is the shortest trace that
  still violates the property. A shrinker that only reduces numeric arguments hands the reader a five-step
  trace where one step suffices, and the attribution is gone.
- **Reachability, not coverage.** The domain claim is "every reachable (command, precondition partition,
  state) triple runs at least once per run", measured from the generator's transition log. Line coverage
  says nothing about which business branch ran.
- **Runtime ceiling.** A median wall time per flow (proposal: 10 s on commit). Without it, bloat relocates
  from file count to minutes.
- **Determinism.** No wall clock, no network, no unseeded randomness inside the flow; time and identifiers
  are injected. A flaky property run is worse than none, because it trains the reader to re-run until green.

### 4.5 Attribution comes from the shrink

A failing property reports a trace: the command sequence, the state before each command, the outcome
(`apply` or `refuse:<class>`), and the invariant that broke. The first transition in the shrunk trace where
the observed outcome differs from the decision table is the seam, and that seam belongs to one task in the
DAG. Attribution therefore survives without one test file per task — which is why shrinking to the shortest
trace is a contract requirement, not a convenience.

A failure reported as `assert false` with no trace is not a test result; it is a bug report with the
evidence removed.

### 4.6 The four cases that still earn a hand-written test

1. **A found counterexample** — pinned, permanent (§4.3).
2. **A refusal whose class is a security or accounting boundary** — the exact class and message are the
   contract, and a generator rarely reaches those argument combinations on its own.
3. **A cross-flow contract** — two flows sharing a table or a lock, meaningful only when both are driven in
   one trace.
4. **A surface with no model** — a generated artefact, a template, a migration that cannot run twice.

### 4.7 Which task class builds the model, and when

Modelling is a **task of its own class** (`verification`), never a clause inside a construction task, and
its timing depends on what it protects:

| Situation | Shape | Must run |
| --- | --- | --- |
| construction added commands to a flow | A — build the model | after those construction tasks are accepted |
| migration or removal will touch a modelled flow | B — oracle bracket | baseline **before** the change, verbatim re-run after |
| a flow exists but nothing models it, and no change is planned | A — build the model, as its own piece of work | whenever it earns its cost |

Rules that follow:

- **Construction tasks own no model and no property.** They land behaviour; where they falsify an existing
  assertion they update or delete it in the same task (the deletion path).
- **A verification task owns one flow**: its model file, its harness entry point, its pin file.
- **A production defect found by a run becomes a construction or migration task.** The verification agent
  reports the trace and the seed; the main agent opens the task; the affected flow's model and pins are
  updated after the fix lands. An agent that patches production code from inside a verification task has
  destroyed the boundary that makes its report believable.
- **A behaviour-preserving change with no new command** names the invariant that keeps it so, and states
  whether any existing property reads that surface.

Why the order is fixed for new behaviour: a model written before the code exists describes an imagined
implementation, and properties written against that imagination pin the design fiction. Why it inverts for
preservation work: an oracle created after the change compares the new code with itself.

### 4.8 Where this method does not hold

Three limits belong in the record, because each one is where the method silently degrades into the regime
it replaced.

- **"Every business branch" is unbounded unless it is defined as the reachable transition set.** The
  enumerable claim is `(command × precondition partition × state)` reachable under the generator; the
  unbounded claim includes amount boundaries and interleavings, which no sample count covers. Someone will
  eventually write generators "for coverage" — that is the new bloat, arriving as generator code rather
  than assertion code. The counter-force is to name unreachable partitions as out of scope in the flow
  model, in writing.
- **The oracle moves cost rather than removing it.** At flow level there is no per-seam expected value, so
  the property set must be backed by an executable model or by invariants strong enough to pin the answer.
  Without one of those, "properties" collapse into no-crash, no-negative-balance assertions that pass while
  the flow computes the wrong number. A flow with no model and no conservation-type invariant should not
  claim property coverage at all.
- **Concurrency is not covered by sampling.** Interleavings that violate an invariant are exponentially
  sparse in random schedules; PBT at any practical sample count misses them. Concurrent flows need
  deterministic enumeration of linearization points, which is a different harness, and claiming otherwise
  is the strongest form of false assurance in this document.

### 4.9 What this method does not cover: architectural requirements

A `REQ-A` is not verified here. Its acceptance is that the code obeys a declared structure — dependency
direction, module boundaries, public surface, cycles, complexity, a performance budget — and that is decided
by an executable constraint check, not by sampling behaviour. Two reasons the methods differ:

- **A property test samples inputs; a structural rule quantifies over the tree.** No sample count makes a
  layering violation visible if the generator never produces the import that causes it.
- **Performance is an architectural claim.** Order-of-magnitude gains come from structure (an index, a
  cache boundary, batching, removing a hop), so the acceptance is the measured metric *plus* the structural
  rule that produces it. A latency property over random inputs is neither necessary nor sufficient.

The constraint layer's own quality test is a negative control: introduce the violation on purpose and the
check must fail. A check that cannot fail proves nothing, exactly as with a property that has no witness.

## 5. Still open

| # | Question | Candidates |
| --- | --- | --- |
| D2 | Concrete sample and runtime numbers | per-commit 200 / nightly 5 000 / 10 s per flow — or one tier |
| D3 | Pin retention | permanent per finding, or periodic merge of pins that pin the same invariant |
| D4 | Does a flow with no invariant earn PBT | invariants only, or a reference model is mandatory |
| D5 | Concurrency | PBT sampling (weak, see §4.8), or bounded enumeration of linearization points |
| D6 | What the review checklist checks | flow-model completeness (every command and refusal class present), reachability report, runtime ceiling, pin count reported but not gated |
| D7 | Who may delete a pin | main agent on invariant retirement, or reviewer with a stated reason |

## 6. Consequences for the other files

- No document-verification script exists in this skill: they scored presence, and presence is the half that
  can be scored.
- `references/task-verification.md` carries the three shapes (A model, B behaviour bracket, C architecture
  check) and is the file a verification task is written from.
- `references/pitfalls.md`, `references/atomic-task.md` and `references/ownership-rules.md` describe the
  current rules only.
