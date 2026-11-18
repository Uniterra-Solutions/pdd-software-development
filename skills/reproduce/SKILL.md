---
name: reproduce
description: "Use when a known bug needs a machine-found trigger."
version: 1.0.0
author: Tsz Kin Lai (LaiTszKin), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [software-development, debugging, reproduction, search]
    related_skills: [plan, implement, review, study]
---

# Reproduction — a machine-found trigger for a known failure

A failure whose trigger is unknown is a search problem wearing the costume of a reading problem. Reading the
code until the cause appears is an open-ended dig: no termination condition, no artefact, nothing the next
reader inherits. The eight steps below convert the dig into a bounded search whose success and whose failure
are both observable.

**The direction is the opposite of property-based testing, and the whole design follows from that.**
`property-based-testing` starts from a proposition and looks for an input that falsifies it — deduction. Here
the failure is given and the trigger is sought — abduction. There is therefore no proposition to falsify, so
there is no oracle, and a search with no oracle runs until it is switched off. Steps 0 to 3 exist to
manufacture that oracle, step 6 exists to prove it discriminates, and the remaining steps exist to make the
result durable.

Three names cover this activity and they are not interchangeable:

| The object | Its name |
| --- | --- |
| The whole activity | search-based crash reproduction / automated failure reproduction, under search-based software testing |
| Directed at a chosen location or a reported stack frame | directed greybox fuzzing; the objective is seed distance to the target |
| The found input, minimised and kept | a reproducer; when what is violated is an invariant, the path that violates it is an error trace |

## When to use

- A failure is reported or observed, the trigger is unknown, and reading toward it would be open-ended.
- A defect must be pinned before its fix, and no minimal input is known.
- A suite reddens intermittently and the failing shape has no name.
- An incident recurs and nobody can describe the path that reaches it.
- The same failure has been "fixed" twice without a reproduction. The third attempt starts here.

## When not to use

- **The trigger is recoverable by reading in minutes.** Then read it. Search replaces inference; it does not
  replace reading, and a search harness for a one-line trigger is a cost with no counterpart.
- **The space cannot be declared bounded** — real production traffic, a live adversary, a multi-day window.
  Instrument the system and replay production traces instead; a space that must be guessed is not a space.
- **The failure is non-deterministic** — race, timing, GC, network reordering. Establish deterministic replay
  first (record/replay, fixed scheduler, single-threaded harness). A fingerprint that moves is not a target,
  and a search will happily find a run that reproduces once.
- **The failure is not machine-observable** — "it feels slow", a judgement about a screen, a customer's
  discomfort. Observability first; step 0 cannot start.

## Preconditions

- A commit where the failure is red, and a commit where it is green (usually the tag before the change).
  Step 6 needs both, and the green commit is easy to lose once the search begins.
- The ability to run the system locally under a frozen environment.
- The report itself: exception type and message, stack frames, error code, revert selector, assertion id, or a
  screenshot of the failing screen. Enough to write a fingerprint, never enough to write the input.

## The eight steps

Each step names its artefact, its gate, and what the gate's failure means. The order is fixed because each
gate is the only place where that step's failure is detectable at all.

### 0. Freeze the failure into a red

Write the fingerprint: the exact observable that defines "reproduced" — the exception type with its message,
the set of stack frames, the error code, the revert selector with its arguments, the assertion id. Then build
one input by hand that reddens it locally. That input may be large, ugly and half-random; it will not be kept.
It exists to prove the failure is red on this commit and to calibrate steps 3 and 4.

- **Artefact**: the fingerprint, plus the hand-built input and the commit it reddens.
- **Gate**: the hand-built input reddens locally, repeatedly, on a named commit.
- **Failure means**: observability, not search. Add the probe, then come back — a search whose target cannot be
  detected returns "not found" for every query and looks like a hard bug.

### 1. Write the discriminating oracle

The fingerprint as an executable predicate. Not "an error occurred" but these frames; not "it reverted" but
this selector with these arguments. The oracle must be narrow enough that a **different** defect cannot
satisfy it.

- **Artefact**: one predicate over an execution, and the negative control it was proved against.
- **Gate**: a nearby but different failure returns false — a second bug's stack trace, another revert path,
  the same symptom on another code path, a refusal from a different branch. This control is built now, not
  later; built later, it confirms what is already believed.
- **Failure means**: every product of the following steps is contaminated, and step 6 cannot run. The workflow
  usually dies here, and dies silently: a wide oracle reports "reproduced" on the first run and nobody argues
  with a green.

### 2. Declare the space

Three declarations, in writing, before any search begins:

- **Initial state** — machine-rebuildable and deterministic: empty account, fixed fixture, seeded database,
  pinned slot values, starting balance, clock at a literal instant.
- **Action alphabet** — which operations are permitted, each one's parameter domain, each bound with its
  reason. The alphabet is the part that is routinely written too narrow.
- **Frozen environment** — clock, timezone, randomness source, and every external dependency either mocked or
  pinned to a version.

The space must be small enough to search and wide enough to contain the trigger, and only the step-0 input
proves the second half.

- **Artefact**: the three declarations, in the bug record or the plan.
- **Gate**: the step-0 input lies inside the declared space. If it does not, the declarations are wrong —
  widen them until they contain it.
- **Failure means**: every "not found" from here on is unattributable. A narrow space fails silently and
  always: the search returns nothing, the suite stays green, and the defect is recorded as irreproducible.

### 3. Build the graded objective

A boolean oracle in a large space is hit by luck rather than by search. Replace "is it reproduced" with "how
far from reproduction", as a ladder whose rungs are separately observable:

starts → reaches the target function → covers the target frame or basic block → reaches the failure site →
raises the target observable → fingerprint matches exactly.

Each rung needs a measurement that exists today: coverage, execution trace, a log line, a counter. This is the
trade the whole workflow makes — an open-ended reading exchanged for a declared space, a ladder and a budget —
and the ladder is where that trade is priced.

- **Artefact**: the ladder, with the instrument that reads each rung.
- **Gate**: the step-0 input scores the maximum. That is the ladder's positive control; without it the search
  may be climbing a hill that does not contain the bug.
- **Failure means**: a flat ladder. The search degenerates into a random walk with extra steps, and a larger
  budget only makes it a longer random walk.

### 4. Run the search, cheapest strategy first

- **Enumeration** — when the space is small (a few actions, a ten-member alphabet, finite value domains).
  Take the cartesian product. Completeness is free here, and an evolutionary algorithm at this size buys
  randomness that was not needed.
- **Constrained sampling** — space large, trigger shallow. Fixed seed, fixed budget, bounded generator; the
  generator rules in `property-based-testing` apply verbatim (sample primaries, compute derived fields, declare
  every bound).
- **Directed or evolutionary** — the trigger needs a long path: several steps, a cross-contract sequence, a
  rare branch. The ladder then becomes a fitness function, in one of the two published shapes: stack-trace
  similarity (EvoCrash) or seed distance to a target location (AFLGo).

Budget discipline: recorded seed, recorded budget, three different seeds. Three empty runs do not justify a
larger budget; they justify returning to step 2 or step 3, because both ways of failing here — a narrow space
and a flat ladder — present as "needs more runs".

- **Artefact**: the run record — strategy, seed, budget, and the outcome.
- **Gate**: either a trigger, or three-times-not-found with the space and the ladder named.
- **Failure means**: a local optimum, or an initial state that cannot reach the trigger. Both are reported in
  the reproduction literature as search failures rather than as irreproducible defects, which is the
  distinction this gate exists to preserve.

### 5. Shrink

The first reproducer is always too large to read. Remove in order: actions (delta debugging over the action
sequence), then parameters (a thousand down to the smallest failing value), then state (preconditions that
turn out not to be needed).

- **Artefact**: the minimal reproducer, and the pre-shrink version kept as the audit trail.
- **Gate**: still red; each removed part, restored alone, either does not restore the failure or is not
  required by the fingerprint.
- **Failure means**: the pin is unreadable, so the next person re-derives it by hand and the saving is given
  back in full.

### 6. Prove it is that defect

A reproducer of *a* failure is not a reproducer of *the* failure. Run it both ways: green on the fixed commit,
red on the unfixed one. Where the fix is partial, reverting the missing part must restore the red.

- **Artefact**: both observations, with commit ids, stored beside the case.
- **Gate**: both directions observed on named commits.
- **Failure means**: still red after the fix, and the symptom is a different defect. File it, keep both, return
  to step 4 for the original. A pin that outlives its fix is worse than no pin, because it certifies a defect
  as covered.

### 7. Pin

The case is committed with literal values, not a seed, whenever a literal exists: a seed resolves to different
samples across generator versions and says nothing to a reader. A seed is kept only when a draw is the sole
handle on the shape, and then beside the version that produced it. The record carries the input, the
expected-wrong observation, the fingerprint, the space declaration, the ladder and the fix's commit.

- **Artefact**: the committed case and its record.
- **Gate**: from a clean clone, red on the unfixed commit, green on the fixed one.
- **Failure means**: the pin exists only on the machine that made it.

### 8. Feed the answer back

The only step that makes the workflow a net gain. Answer the question the search was standing in for: **why
did this need a search?** Which invariant was missing, which assertion was never written, which boundary was
undeclared, which state transition was legal and should not have been. Add the declarative guard at that point
so the class reddens at step 0 next time.

- **Artefact**: one landed guard, and the answer recorded in the same commit.
- **Gate**: the guard is in the tree and the reason sits beside it.
- **Failure means**: the cost of the dig has been converted into the cost of a search harness, and the next
  defect of the same shape pays again. The reproducer is not the product; the answer to "why was this not
  obvious" is.

## Failure-mode router

| Where it stops | The disease | The move |
| --- | --- | --- |
| 0 | not machine-observable | add the probe; no search yet |
| 1 | oracle too wide | narrow to frames and selectors; build the negative control |
| 2 | space too narrow | widen until the step-0 input fits |
| 3 | ladder flat | add the intermediate rung that is measurable |
| 4 | local optimum or plateau | split the objective, or re-declare the initial state |
| 5 | no shrink | delta debugging, and keep the pre-shrink record |
| 6 | still red after the fix | a different defect — file it, do not pin |
| 7 | does not reproduce from a clean clone | the environment is not frozen; return to step 2 |
| 8 | skipped | the dig was paid for and nothing was bought |

## What the gates buy

Every failure in this workflow is silent. A narrow space returns "irreproducible", a wide oracle returns
"reproduced", a flat ladder returns "not found", a partial fix returns "green, done", an unshrunk pin returns
"committed". None of them raises an error and none of them appears in a diff. The eight gates are the only
places where each is caught, which is why the sequence has a fixed order rather than a menu of techniques.

**No script accompanies this skill, deliberately.** Whether a space contains the trigger, whether a ladder has
a plateau, whether an oracle discriminates and whether a fix is complete are judgements over evidence the
search has already produced. A checker that scans a reproduction record for the word "gate" would pass on an
empty record, and anything it scored would be optimised against instead of the defect.

## Verification

- [ ] the fingerprint names frames, selectors or codes, and a hand-built input reddens it on a named commit;
- [ ] the oracle returns false for a different failure, and that negative control is recorded;
- [ ] the space declaration contains the step-0 input, and each alphabet bound carries its reason;
- [ ] the step-0 input attains the ladder's maximum;
- [ ] every run records strategy, seed and budget, and three seeds were tried before any budget increase;
- [ ] the reproducer is minimal in all three dimensions, with the pre-shrink version kept;
- [ ] both directions of step 6 are recorded on named commits, or the case was filed as a different defect;
- [ ] the pin carries literal values where a literal exists, and reproduces from a clean clone;
- [ ] one guard landed with its reason beside it, or the omission is recorded as accepted;
- [ ] if no trigger was found, the failing step is named and the next decision is written down.

## Handoff

- `pdd:plan` takes step 0's fingerprint as a requirement's failure appearance, and step 1's oracle as a flow's
  refusal path.
- `pdd:implement` implements the fix against a pinned reproducer, and treats the pin as the acceptance.
- `pdd:review` checks the double-sided proof in step 6 rather than the mere existence of a reproducer.
- `pdd:study` is what replaces step 2 when the space spans a codebase whose business branches are unread.

## References

- Soltani, Panichella, van Deursen, *Search-Based Crash Reproduction and Its Impact on Debugging*, IEEE TSE
  2018 — EvoCrash; fitness is code coverage, crash coverage and stack-trace similarity, and its failures are
  local optima rather than irreproducible defects.
- Derakhshanfar et al., *Botsing, a Search-Based Crash Reproduction Framework for Java*, ASE 2019 — the
  extensible form of the same idea.
- Böhme, Pham, Nguyen, Roychoudhury, *Directed Greybox Fuzzing*, CCS 2017 — AFLGo; seed distance to a target
  location, with crash reproduction named as an application.
- Zeller and Hildebrandt, *Simplifying and Isolating Failure-Inducing Input* (delta debugging), IEEE TSE 2002
  — the shrink in step 5.
- `property-based-testing` — the other direction of the same machinery: its generator, non-vacuity and
  regression-guard rules govern step 4's sampling leg and step 7's record.
