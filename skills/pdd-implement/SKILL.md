---
name: pdd-implement
description: "Use when a TASKS.md exists and its DAG must be executed."
version: 2.3.0
author: Tsz Kin Lai (LaiTszKin), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [software-development, implementation, subagents, dispatch]
    related_skills: [pdd-plan, pdd-decompose, pdd-review, pdd-explain]
---

# Executing a scheduled task DAG

One goal: **in the order `pdd-decompose` set, dispatch every task in `TASKS.md`, accept each against the
acceptance object of its own class, integrate, then dispatch the next one.**

It does not set the order, does not edit tasks, does not write tests or models, does not judge whether a
requirement is right, and does not do a quality review. It is the executor, not a second planner.

## When to use

- `TASKS.md` and its `tasks/` directory exist, and the work is to execute the DAG they describe.
- A layer of ready tasks must be dispatched in parallel and each result accepted before the next layer.
- Routing: order, gates and task boundaries belong to `pdd-decompose`; requirement correctness belongs to
  `pdd-plan` or the user; quality judgement belongs to `pdd-review`, and only when the user asks.

**Without `TASKS.md` this skill has no input.** Report that, and ask the user to run `pdd-plan` and
`pdd-decompose` first. A one-off small change is ordinary engineering work: it is not part of the PDD
process and must not borrow this skill's name to be improvised on the spot.

### What this skill does not do

| Thing | Belongs to |
| --- | --- |
| Deciding order, gates, task boundaries, owned files | `pdd-decompose` |
| Splitting tasks, merging tasks, changing dependency direction | `pdd-decompose` (via amendment) |
| Writing tests, models, baselines, constraint scripts | the verification task (A/B/C) |
| Judging whether a requirement is right or worth doing | `pdd-plan`, or the user |
| Quality judgement, adversarial review | `pdd-review`, and only when the user asks |
| commit, push, tag, deploy, version numbers | the user's explicit instruction |

## Preconditions

- `TASKS.md`: the DAG (with classes and gates), the register, requirement traces, the wave table.
- `tasks/<id>-<slug>.md`: each task self-sufficient.
- `PRD.md`: the standard for behaviour and architecture.
- The repo.

The contract it executes is read-only except through dated amendments; a contradiction found here stops the
run and returns to `pdd-decompose`, it is never patched in place.

## Workflow

### 1. Load the contract and check only executability

This is not a re-review of the plan, only a check that it can run:

- the DAG has no cycles, every node has a task file, and the register and the task files agree on `Class`,
  `Depends on` and `Owned files`;
- every gate's condition is decidable on the graph (who feeds it, whom it releases);
- the ready set is computed from the set **accepted by the dispatcher**, not from what subagents
  self-reported as successful.

If any of these fails: stop, report with evidence, hand back to `pdd-decompose`. Do not fill the gap
yourself, do not guess, do not edit the contract in place.

### 2. Shared work before dispatch (the dispatcher does it, not a subagent)

Worktrees, baselines and shared prerequisites are detailed in `references/subagent-dispatch.md` §1.

- One worktree per subagent, each with its own build output directory (Rust's `CARGO_TARGET_DIR`): a shared
  target lets one person's build pollute everyone's.
- An explicit dispatch baseline (hash list) per worktree. A dirty main tree is expressed as an overlay: no
  commits, no stashing of the user's work, and every unaccepted sibling delta excluded.
- manifest, lockfile, shared enum/type modules, the migration chain, registry/route table/plugin list,
  shared fixtures, entry aliases: no single subagent can own these, so the dispatcher finishes them first
  and declares them read-only.

### 3. Dispatch a whole layer

One `delegate_task` per ready layer. The brief's shape and its rationale are in
`references/subagent-dispatch.md` §2; the point is to give paths, never pasted text:

- the worktree root, the baseline hash list, the isolated build output directory, the read-only integration
  tree;
- `PRD.md`, `TASKS.md`, **the `tasks/` directory and the path of its own task file** — paths, not pasted
  bodies. Pasting full text rewrites the contract at dispatch time, and once two copies drift the subagent
  follows whichever it read last;
- **the path of `references/subagent-charter.md`**, with the brief saying "work to it": compile only what
  you changed, run only the tests related to your change plus your own acceptance tests, write only owned
  files, follow the repo's naming conventions;
- an opening report of one line from its task file (the purpose, for instance) as evidence that it opened
  the right file; `test -f` every path before dispatch; record the task file's hash and compare it at
  acceptance to prove it was not edited;
- the exact list of files it may create, modify or delete, and nothing else;
- prohibitions: editing the PRD or `TASKS.md`, touching a sibling task's files, weakening or deleting
  existing tests, adding dependencies, running the full suite, building the whole workspace, commit, push;
- stop conditions: the task cannot be satisfied, it contradicts already-merged code, an owned file is
  missing → stop and report, leaving the contract untouched;
- report format: the one its task file specifies.

Do not poll during the same period. End the turn after dispatch and handle completion notices in batch.
When the parallelism ceiling is below the ready set, dispatch in waves and say so.

**Measurement tasks (wall-clock baselines, `--record`, performance budgets) run in a round of their own.**
Their product is a median; sharing CPU with any other task measures the other task's load, and that number
later becomes the before. Re-recording a baseline has one more precondition: the suite must be green — run
the full suite once to confirm, then `--record`; if the script warns that the baseline records a red suite,
delete that baseline, fix the reds and record again, and never keep the red numbers as a reference point.

### 4. Accept by class

A subagent's report is not evidence. Acceptance reads its own class, and never applies another class's
criteria.

| Class | Acceptance | What the dispatcher looks at |
| --- | --- | --- |
| **construction** | the purpose is observable from the real entry point; delta ⊆ owned; the affected existing suites and the typecheck still green | trigger the real entry point itself; the suite summary and the typecheck count |
| **verification A** | the model exists; the property ran within budget; counterexamples are shrunk and pinned | trace, seed, minimal sequence, coverage reading |
| **verification B** | the baseline was frozen **before** the change; after the change the same command reruns and the output is bit-identical | both outputs and the comparison |
| **verification C** | the check is all green before the change and still green after; injecting one violation must turn it red | two passes plus one record of a deliberate red |
| **migration** | every retention-list item has evidence; source set → target set matches; the old path is removed or has an expiry condition | oracle output plus the structural comparison |
| **removal** | the raw output of the absence proof (zero references, compile passes, no node left in the dependency graph); the tests that die with it are deleted | the command output |

Common principles:

- **delta ⊆ owned.** Touching another file breaks the contract: send it back to the same owner. lockfile,
  build products and caches are byproducts — record them and move on.
- **count > 0.** Any "green" needs real executed volume; selecting zero cases and exiting 0 is not having
  run, it is not green.
- **Existing oracles may not be weakened.** If a task invalidates an existing assertion, it must update or
  delete that assertion in the same task and list it; not listing it is a defect.
- **For a flaky red, measure the trigger rate first, do not just rerun.** A property that goes red once every
  few dozen runs is usually drawing a rare value class, not an environment problem. Sample 20k runs to
  compute P(hitting the trigger set) × draws per case: a measured 0.055% per sample means about 1.4% per
  25-draw run, and ten all-green runs at 1.4% have an 87% chance of merely not having drawn it — so "it
  passed on the rerun" is not acceptance. Send it back to the same owner with the mechanism, the
  counterexample and the command; acceptance requires **N random seeds (≥20) all green plus the fixed seed
  green**, and the fix must narrow the value domain or pin the triggering value, not raise `numRuns`.
- **Rerun any "measured X" in a report yourself.** A subagent will write a wrong measurement into a
  deliverable's file header or comment — for instance, claiming `fc.string({unit:'binary'})` produced 168 of
  200 lone surrogate pairs when the true value is 0 (it counted valid pairs), with its tests all green.
  Whenever a number from a report lands in code, docs or a baseline, the dispatcher reproduces it with the
  same command; a mismatch goes back to the same owner (and the dispatcher does not edit that file itself).
- **A mutation experiment hands over byte-level restoration evidence.** When a subagent temporarily edits a
  sibling task's file to prove "the property goes red", require a `sha256` before and after; at acceptance,
  confirm once more with a behavioural probe (the family samples still satisfy the predicate, the entry
  signature is unchanged). A temporary crossing of the boundary is acceptable; a silent one is not.
- **Naming and formatting follow the repo, not the agent.** New code's naming must show the shadow of a
  same-style module; the repo's formatter/linter runs only on the files that task changed, with no new
  `allow`/`disable` suppressions. A task id, `V2`, `tmp` or `new*` in a name is a defect.
- **Execution scope stays inside the brief.** A report showing the full suite, a whole-workspace build or
  another flow's tests is out of bounds: reject that round's conclusions and have it rerun per
  `references/subagent-charter.md`.

### 5. Integrate

Integrate the accepted delta back into the main tree: verify the destination baseline hashes first, resolve
conflicts explicitly, and never overwrite newer work in the main tree. After integrating, rerun that task's
observation **in the main tree**, plus the existing modules and suites it affects. A worktree is removed
only after integration verification passes and the report and patch are saved; a failed, unintegrated
worktree stays with its blocker attached.

### 6. Next layer, until the DAG is exhausted

The DAG being exhausted ends the run. `TASKS.md` sets the order; the dispatcher does not reorder — when the
parallelism ceiling forces waves, wave order still obeys the DAG's partial order.

**Before every dispatch, reconcile the register's ids against the set "accepted ∪ in flight".** In a graph
of a dozen or so tasks, a skipped mid-graph node raises no error: it may have no downstream, or its
downstream was released by another edge, so it surfaces only in the final wave. The reconciliation is one
set difference costing a second; the price of a miss is that the task's second-phase verdict is never
executed (the list is never emptied, the check is never created) while every report looks green.

**The closing task's brief (the joint rerun of B/C) lists every check by name.** That is the only mechanism
that catches "one C task was never dispatched": a missing script returns `MODULE_NOT_FOUND` rather than a
failing verdict, and it surfaces in the step where you ask for "all six checks green". A brief that says
"run all the checks" without the names has no such probe — the subagent runs only the ones it finds.

### 7. Report

Per layer: which tasks were dispatched, which were accepted, the gate states, any stops.

At the end: DAG completion, task counts and acceptance counts per class, unresolved items (each with its
command and raw output). Do not enter `pdd-review` on your own initiative, and do not commit, push, tag or
deploy.

## Decision rules

### Gate enforcement

The dispatcher only **enforces** gates; it does not re-judge whether a gate should exist:

- **model gate** unmet (the construction tasks it covers are not all accepted) → do not dispatch A-class
  verification.
- **guard gate** unmet (the B-class baseline is not frozen, or the C-class check is not all green) → do not
  dispatch migration or removal.
- A migration task that wants to edit the check judging it → refuse, report, require a dated amendment.
- **A C check that is already violated on the day it lands starts in two phases.** Phase one accepts "the
  hit set equals the frozen violation list", not an empty set; the script must print "this is the violation
  set failing to grow, not the rule being satisfied" in its verdict, or phase one will be read as green.
  Emptying the baseline counts as **editing a rule that judges you**: the dispatcher does it after the
  corresponding removal is accepted, item by item and reviewable, and neither the script nor the task may
  do it.
- **A C check is a standing gate and turns red because of sibling tasks.** It quantifies structure: any new
  barrel export, new seam declaration or new spec file may push a check that was green yesterday into red.
  That is not a regression, it is the rule being enforced — ask "who added what", and route the removal or
  narrowing back to **that owner**; widening the baseline to fit the hit set is exactly the self-exemption
  this rule forbids.

When a gate condition cannot be met, the only action is to stop and report. Do not "do it first and add the
check afterwards" — that is cancelling the gate.

### When to stop (rather than adjust the plan)

- the task file contradicts itself (two purposes, an owned file that is missing, a `Class` that does not
  match its contents);
- the acceptance the task declares is impossible on the real tree;
- a gate condition cannot be met (no oracle, for instance, and no way to get one before building);
- a red gate cannot be attributed (not a regression, not an overtake, not the baseline, not the
  environment).

Stopping carries three things: the command and its raw output, the minimal counterexample, and which clause
of the contract it contradicts. Hand back to `pdd-decompose` to fix the contract, and let the user decide
whether to re-dispatch.

**No plan edits mid-run**: no re-cutting, no merging, no relaxing acceptance, no rewriting a clause because
"that is how it really is", no numeric exceptions. That is this skill's discipline and what separates it
from the previous version.

### Repo gates

- Layer boundaries run the agreed integration checks; subagents run only their own checks, never the full
  suite.
- **typecheck is a separate leg.** Test runners usually do not typecheck, so a green suite proves nothing
  about types. Record the starting baseline (for instance `npx tsc --noEmit 2>&1 | grep -c 'error TS'`) and
  rerun it after every layer; the count may only fail to rise.
- **Attribute a red before rerunning.** Reproduce the failure in isolation first, then decide whether it is a
  regression, an overtake, the baseline, or an environment limit. When a subagent blames the environment,
  the dispatcher reruns that command itself; a single command's difference decides which kind the amendment
  records.
- **When an evidence artifact asserts equality with the live run, it is a constructive red.** Regenerate it
  with the repo's own script (for instance `npm run evidence`); never hand-edit the numbers. When the
  generated value disagrees with the task's expectation, report and block — that is a discovery, not a
  number to update.
- **Product tests do not read generated artifacts.** The generator empties its output first, so tests run
  before the artifact exists; the product test asserts the cause and the pack owns the result.

## Pitfalls

The full catalogue is in `references/pitfalls.md`. The five most recurrent:

- **Treating a subagent's self-report as acceptance.** "Done" is neither an observable purpose nor proof
  that the delta is inside owned.
- **Dispatching downstream with a gate unmet.** "Do it first and add the check later" turns the gate into
  decoration; an A-class model then describes code that is not settled, and a B-class baseline compares new
  code with itself.
- **Editing the contract mid-run.** Re-cutting a task, relaxing acceptance, adding a numeric exception —
  each one means the later evidence no longer corresponds to the original plan.
- **Mistaking a byproduct for a contract breach, or a contract breach for a byproduct.** A lockfile is the
  former; touching a sibling's file is the latter.
- **Calling zero selected cases green.** Green without executed volume is unfinished work, and dispatching
  past it lets the defect surface two layers later.

## Verification

- [ ] every layer was dispatched in the DAG's partial order; no task started before its dependencies were
      accepted;
- [ ] every register entry appears in "accepted or dispatched" (the dispatch ledger reconciles, no wave was
      skipped);
- [ ] every gate was checked before dispatch, and no A-class task or migration/removal bypassed one;
- [ ] every task's delta stayed inside its own owned set, with byproducts recorded;
- [ ] every task was accepted by its own class (construction triggered the real entry point, A has a trace,
      B has a bit-for-bit comparison, C has a deliberate red, migration has a retention list, removal has an
      absence proof);
- [ ] existing tests were not weakened, skipped or deleted unless the task listed them in its own report;
- [ ] after integration the affected modules and suites were rerun in the main tree;
- [ ] the typecheck error count did not rise above the baseline;
- [ ] no commit, push, tag, deploy or version change happened;
- [ ] every stop carries its command, raw output and the contract clause it contradicts.

> Cross-skill references are written `<skill>/<path>`, relative to the skills category directory
> (`software-development/`); read them with `skill_view`, not resolved against this skill's own directory.

## References

- `pdd-decompose/assets/TASK.md` — the task file's shape; the brief is taken from it verbatim.
- `pdd-decompose/references/task-construction.md`, `task-verification.md`, `task-migration.md`,
  `task-removal.md` — each class's fields and acceptance objects.
- `pdd-decompose/references/testing-methodology.md` — A/B budgets, seeds, shrinking and failure reading.
- `pdd-decompose/references/ownership-rules.md` — one writer per file and the class boundaries; consult it
  when judging whether a delta is out of bounds.
- `scripts/mutate_check.py` — negative control: change one byte at an exactly-once anchor, run the check,
  restore, rerun. Exit 0 means red after the perturbation, green after restoration and byte-identical;
  1 means the check cannot see that error; 2 means the anchor is missing or ambiguous. Both C's "an injected
  violation must go red" and B's "the baseline really bites" are executed with it, not described in prose.
- `references/subagent-charter.md` — the subagent charter: the brief must carry its path; compile only what
  you changed, run only related tests plus your own acceptance tests, follow the repo's naming conventions
  (three levels of authority: configuration → neighbouring modules → language idiom), the action scope, the
  report, the failure shape.
- `references/subagent-dispatch.md` — the dispatch paradigm: worktree and baseline, a brief giving the
  `tasks/` directory instead of pasted text, acceptance by class, the full sequence of a layer,
  anti-patterns.
- `references/pitfalls.md` — the full catalogue.
- `references/browser-harness.md` — when the observation is a screenshot, a computed style, font readiness
  or an accessible name: configuration binding, parallel-build risk, font loading.
- `references/behaviour-preserving-refactor.md` — the depth of a migration: baseline freezing, extraction
  order, cross-module `instanceof`, runner contention, reaction to a frozen artifact.
