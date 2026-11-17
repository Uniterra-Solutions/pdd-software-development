---
name: implement
description: "Use when a plan must be built: a TASKS.md DAG, or one PRD flow with no tasks."
version: 2.5.0
author: Tsz Kin Lai (LaiTszKin), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [software-development, implementation, subagents, dispatch]
    related_skills: [plan, decompose, review, explain]
---

# Building a plan

One goal: **dispatch the work the plan describes, accept each unit against the plan's own standard, and
merge it into the working branch and close its worktree before the next unit opens.**

Two entries, one discipline:

| Workflow | Input | The unit of dispatch | What accepts it |
| --- | --- | --- | --- |
| **A — scheduled DAG** | `TASKS.md` and `tasks/` | one task file, in the order `pdd:decompose` set, gated | the acceptance object of its own class |
| **B — one flow, no tasks** | `PRD.md` with one flow and no `TASKS.md` | a slice the dispatcher cuts itself, dispatched in one layer | the `REQ-F` it serves, observed from the real entry point |

**Workflow B is not a shortcut around the process, it is the process for a smaller input.** The PRD's
"Next: `pdd:implement` for one behaviour" is B's invitation; its simpleness test (§B1) is the admission
price, and a run that stops being simple is promoted back to `pdd:decompose` rather than stretched. Both
workflows share A's shared work, its brief, its per-batch merge and its closing check — B replaces the
contract with a cut it does not persist, nothing else.

In A it does not set the order, does not edit tasks, does not write tests or models, does not judge
whether a requirement is right, and does not do a quality review. In B it does not write the plan either.
It is the executor, not a second planner.

## When to use

- `TASKS.md` and its `tasks/` directory exist, and the work is to execute the DAG they describe → **Workflow A**.
- A layer of ready tasks must be dispatched in parallel and each result accepted before the next layer.
- Routing: order, gates and task boundaries belong to `pdd:decompose`; requirement correctness belongs to
  `pdd:plan` or the user; quality judgement belongs to `pdd:review`, and only when the user asks.

**No `TASKS.md` and no `tasks/`, but a `PRD.md` exists** → **Workflow B**: the dispatcher cuts one flow into
slices, dispatches them in one layer, and accepts each against the requirement it serves. It runs only if
§B1's five clauses pass; when one fails, the answer is `pdd:decompose`, not a narrower reading of the clause.

**No `TASKS.md` and no `PRD.md`** → there is no contract to build against. Report that, and ask for
`pdd:plan` first (then `pdd:decompose`, or `pdd:implement` when the plan names one behaviour). Working from
a chat message with neither is ordinary engineering work; it must not borrow this skill's name to be
improvised on the spot — and a change smaller than one slice is that same ordinary work even when a PRD
exists.

### What this skill does not do

| Thing | Belongs to |
| --- | --- |
| Deciding order, gates, task boundaries, owned files | `pdd:decompose` |
| Splitting tasks, merging tasks, changing dependency direction | `pdd:decompose` (via amendment) |
| Writing tests, models, baselines, constraint scripts | the verification task (A/B/C) |
| Judging whether a requirement is right or worth doing | `pdd:plan`, or the user |
| Quality judgement, adversarial review | `pdd:review`, and only when the user asks |
| merging accepted work into the working branch, with one commit per accepted task | this skill, §5 |
| cutting one flow into slices **for one dispatch**, when no `TASKS.md` exists | this skill, Workflow B |
| persisting that cut as `TASKS.md`, a task file, or anything the next run could read as a contract | `pdd:decompose` — the executor authoring its own contract is the contract editing itself |
| push, tag, deploy, version numbers | the user's explicit instruction |

## Preconditions

**Workflow A**

- `TASKS.md`: the DAG (with classes and gates), the register, requirement traces, the wave table.
- `tasks/<id>-<slug>.md`: each task self-sufficient.
- `PRD.md`: the standard for behaviour and architecture.
- The repo.

The contract it executes is read-only except through dated amendments; a contradiction found here stops the
run and returns to `pdd:decompose`, it is never patched in place.

**Workflow B**

- `PRD.md` whose §4 has one flow, no §6.2 requirements, and no migration or removal in scope — the five
  clauses of §B1, decided by reading.
- The repo, and the real entry point the requirement's observation runs through.
- No `TASKS.md`. If one appears mid-run it wins: stop and execute it as Workflow A.

The PRD is read-only, its hash recorded before the first dispatch: a requirement edited by the subagent
that then satisfies it is indistinguishable from a satisfied plan until someone diffs the plan.

## Workflow A — the scheduled DAG (`TASKS.md` exists)

### 1. Load the contract and check only executability

This is not a re-review of the plan, only a check that it can run:

- the DAG has no cycles, every node has a task file, and the register and the task files agree on `Class`,
  `Depends on` and `Owned files`;
- every gate's condition is decidable on the graph (who feeds it, whom it releases);
- the ready set is computed from the set **accepted by the dispatcher**, not from what subagents
  self-reported as successful.

If any of these fails: stop, report with evidence, hand back to `pdd:decompose`. Do not fill the gap
yourself, do not guess, do not edit the contract in place.

### 2. Shared work before dispatch (the dispatcher does it, not a subagent)

Worktrees, baselines and shared prerequisites are detailed in `references/subagent-dispatch.md` §1.

- One worktree per subagent, each with its own build output directory (Rust's `CARGO_TARGET_DIR`): a shared
  target lets one person's build pollute everyone's.
- **Record the working branch before the first worktree exists**: `git rev-parse --abbrev-ref HEAD`, written
  into the run ledger. Every merge targets that name (§5). A detached HEAD, or a checked-out branch that
  changed mid-run, stops the run — merging into whatever `HEAD` happens to be at the time is how a batch
  lands in the wrong branch, and afterwards no evidence distinguishes it from the right one.
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

**A failed step does not undo the steps that passed.** A multi-step task that fails at step *k* keeps the
worktree as it stands: commit steps 1..*k*−1 as `wip(<task-id>): steps 1..k−1, blocked at <step>` and report
the failing step with its command and output. The re-dispatch starts from that checkpoint and its failure
list is expected to be shorter. Returning the worktree to the baseline discards work that was already green
on its own step check, and the next attempt pays for all of it again.

**A slice is a dispatch, not a step.** When one task's steps fall into groups whose owned files are disjoint,
each group is its own subagent in its own worktree, dispatched in the same layer — only the merge, the frozen
contract files and each worktree's build output directory are sequential. The mapping that settles the doubt:
**one worktree's delta becomes one commit, produced by the dispatcher at merge time**, because subagents
never commit. So the number of worktrees follows the number of disjoint file sets and nothing else; "one
commit" constrains what a commit may contain, never how many worktrees may run at once.

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

### 5. Merge back and close the worktree, per batch

A batch ends when every task in it is accepted or retained. Then, **before the next batch opens**, each
accepted delta is merged into the current working branch and its worktree is removed. Deferring the merge to
the end of the run is what produces two worktrees whose deltas can no longer both land: the later one was
built on a baseline the earlier one has already changed.

**The target branch is the one recorded in §2, never re-read from `HEAD`.** Merging into "whatever is
checked out now" lands a batch in the wrong place after the user switches branches, and the log looks
innocent. A branch change detected mid-run stops the run.

**The dispatcher merges; subagents never do** — no commit, no merge, no cherry-pick, no branch
(`references/subagent-dispatch.md` §1). Two mechanisms, chosen by the state of the main tree:

- **clean main tree** → commit inside the worktree on `pdd/<task-id>`, then `git merge --no-ff
  pdd/<task-id>` into the working branch, so the ancestry and the attribution are real;
- **main tree carrying the user's uncommitted work** (the usual case) → apply the delta as a patch, stage
  only the delta's own paths (`git add <path>` per owned file) and commit on the working branch. No
  stashing, no committing the user's files, no `git add -A`.

Before applying, re-verify the destination hashes. A path whose content changed since the baseline is newer
work: stop and report, never overwrite it. One commit per accepted task, the message naming the task id and
its class, so a later revert is attributable — a batch of three accepted tasks gives three commits in DAG
order. A task run as several disjoint slices gives one commit per slice, merged in the order the task file
names; it is squashed into one commit only when the task file asks for one. Conflicts are resolved explicitly
by the dispatcher and recorded in the layer report; an unresolvable
conflict stops the run with the clause it contradicts.

**Then verify in the main tree**: that task's observation rerun there, plus the existing modules and suites
it affects, plus the typecheck leg. A green worktree proves nothing about the main tree, where a sibling's
accepted delta is now also present.

**Then remove the worktree, in this order**: `git worktree remove <path>` → `git worktree prune` →
`git branch -D pdd/<task-id>` → read `git worktree list` and confirm the path is gone. Removing before
verifying leaves nowhere to run the failing command; verifying without removing leaves a directory that
keeps a stale baseline alive and the next layer may reuse it by accident.

**Exactly one case keeps a worktree**: acceptance failed, or the merge could not be resolved. It stays with
its blocker attached, is named in the layer report, and is counted in §7. There is no third case, and "I
might still need it" is not one.

### 6. Next layer, until the DAG is exhausted

The DAG being exhausted ends the dispatching, not the run: §5's cleanup of the last batch and §7's closing
check come after it. `TASKS.md` sets the order; the dispatcher does not reorder — when the parallelism ceiling
forces waves, wave order still obeys the DAG's partial order.

**A batch does not open while the previous batch's worktrees exist.** The exception is a retained worktree
named in the layer report; its blocker is worked or escalated first, because a second batch built on a
baseline that excludes the first batch's merged deltas produces reports that are green and wrong.

**Before every dispatch, reconcile the register's ids against the set "accepted ∪ in flight".** In a graph
of a dozen or so tasks, a skipped mid-graph node raises no error: it may have no downstream, or its
downstream was released by another edge, so it surfaces only in the final wave. The reconciliation is one
set difference costing a second; the price of a miss is that the task's second-phase verdict is never
executed (the list is never emptied, the check is never created) while every report looks green.

**The closing task's brief (the joint rerun of B/C) lists every check by name.** That is the only mechanism
that catches "one C task was never dispatched": a missing script returns `MODULE_NOT_FOUND` rather than a
failing verdict, and it surfaces in the step where you ask for "all six checks green". A brief that says
"run all the checks" without the names has no such probe — the subagent runs only the ones it finds.

### 7. Close the run: no worktree left behind

The DAG being exhausted is not the end of the run; the worktree ledger being empty is.

- `git worktree list` shows exactly the worktrees that existed **before** the run — normally one, the main
  tree — plus any retained worktree named in a layer report, and nothing else. Paste the raw output.
- `git branch --list 'pdd/*'` is empty. A leftover branch is a leftover worktree in another form, and it will
  be picked up by the next run as if it were current.
- `git worktree prune` has run, so no administrative entry survives a directory that was deleted by hand.
- The count matches the ledger: one worktree created per dispatched task, one removed per accepted task, one
  retained per blocked task. Two numbers that disagree mean a merge or a removal was skipped, and the task
  it belonged to is now unmerged.

A run whose DAG is exhausted while `git worktree list` still lists three paths has not finished: its last
batch is unmerged, and every measurement taken in the main tree since is missing those deltas. Report the
paths and their tasks; do not clean up silently and do not call the run complete.

### 8. Report

Per layer: which tasks were dispatched, which were accepted, which commits landed on which branch, which
worktrees were removed, the gate states, any stops.

At the end: DAG completion, task counts and acceptance counts per class, unresolved items (each with its
command and raw output). Do not enter `pdd:review` on your own initiative, and do not commit, push, tag or
deploy.

## Workflow B — one flow, no tasks (`PRD.md`, no `TASKS.md`)

`references/workflow-b.md` is the procedure in full. The steps below are the dispatch. Read that file
before the first brief: the entry test and the cut are where B fails, and neither is improvised well.

### B1. Gate the entry: five clauses, all of them

Decided by reading the PRD, not by estimating effort. All five must hold:

| # | Clause | What fails it |
| --- | --- | --- |
| 1 | one flow — §4 has exactly one `F<n>`, and every requirement in scope carries its prefix | a second flow, even one sharing files; a requirement with no flow |
| 2 | no architectural requirement — §6.2 absent or empty | any `REQ-A`, whose acceptance is a check over a wider scope |
| 3 | no prerequisite evidence — nothing needs a model or a frozen baseline before the change | an acceptance that exists only after the code does |
| 4 | one layer, files enumerable now, at most three disjoint groups | paths discovered only by making the change; groups that are not file-disjoint |
| 5 | no migration, no removal | a schema or data migration, a retired symbol, a dropped dependency |

**A failed clause ends the workflow there.** Report the clause, quote the PRD sentence that fails it, and
hand back to `pdd:decompose`. Two things are forbidden, because both destroy attribution: **writing a
minimal `TASKS.md`** so B can run like A (the executor authoring the contract it is judged by), and
**running "B plus a bit more"** (a second flow does not become admissible because the first went smoothly).

**Below one slice, dispatch nothing.** A typo, a one-line guard, a comment fix is ordinary engineering
work: B costs a worktree, a brief, an acceptance and a merge, and paying that for one diff is a worse trade
than doing it.

### B2. Cut the flow into slices, and record the cut before dispatching

A slice is **a set of owned files that serves one requirement and is observable on its own** — the same
unit as a task, minus the file. One requirement per slice; requirements sharing a file are one slice,
because two slices cannot both own a path; a type, config key or registration entry travels with the
behaviour that needs it; order only where an observation needs the earlier result, since B has no gates to
hold a slice back and an ordering costs a whole batch.

Cap at three. A fourth disjoint group is the first sign clause 4 was optimistic: re-read the entry test
rather than dispatching it.

One row per slice, written into the run ledger before dispatch and kept out of the repo: slice id, the
`REQ-F` ids it serves, the exact owned paths, the observation command, the worktree and its baseline
hashes. Acceptance compares every delta against `owned`, and a cut that lives only in the conversation has
no rows left to compare against once the conversation is summarised.

### B3. Shared work before dispatch

Workflow A §2 applies unchanged: the working branch recorded before the first worktree exists, one worktree per
slice, a separate build output directory each, an explicit baseline per worktree, and the shared
prerequisites frozen by the dispatcher rather than owned by any slice. B's frozen set is often
proportionally larger — one flow tends to mean one registry entry or one shared type — and it is still the
dispatcher that writes it.

### B4. Dispatch the whole layer

One `delegate_task` per slice, all in the same layer. The brief's shape is `references/workflow-b.md` §3:
the PRD's path and the requirement id it executes, the charter's path, its owned paths, its acceptance
command, the prohibitions and stop conditions that apply in A, and an opening line quoting the requirement
from §6.1 — the proof it read the requirement, not the brief.

**A slice may not widen its own owned set.** A path outside its row is a stop and a report; the dispatcher
widens the row explicitly in the ledger, or re-cuts and re-dispatches. A silent widening is the one thing
acceptance cannot see.

**A slice that fails part-way keeps its work**: commit what passed as `wip(<slice>)`, report the failing
step with its command, and re-dispatch from that checkpoint — Workflow A §3's rule, unchanged. Do not poll during the
layer; end the turn and handle the completion notices in batch.

### B5. Accept by the requirement, then merge per batch

| Check | What it means here |
| --- | --- |
| requirement observed | the row's command, run from the real entry point, produces what the PRD's "Where it is visible" names |
| delta ⊆ owned | the diff touches only the row's paths; lockfiles and build output are byproducts, recorded |
| count > 0 | the observation executed something; selecting zero cases and exiting 0 has not run |
| no weakened oracle | an assertion the change invalidates is updated or deleted by the same slice, and listed |
| measurements reproduced | any "measured X" is rerun by the dispatcher before it lands in code, docs or a commit |

**An acceptance that needs a model, a frozen baseline or a checker is not B's**, it is A's: stop and
promote rather than substituting "the tests pass" for an observation nobody made.

Then Workflow A §5 verbatim — merge into the recorded branch, verify in the main tree, remove the worktree — with one
difference: the commit names the requirement, since B leaves no task id behind.

```
feat(<surface>): <what the requirement now does>

REQ-F-<flow>-<n> — <the requirement's sentence, quoted>
```

### B6. Report, and the exit ramp

The report carries: the entry test clause by clause; the cut table as dispatched, with every mid-run
widening and why; per slice accepted or retained, its commit and its removed worktree; **every requirement
in scope marked covered or not covered** (a requirement with no slice is a gap, and "it was implied" is not
coverage); and any promotion, with the observation that forced it.

**A run that stops being simple is promoted, not stretched.** Any of these ends dispatching and hands back
to `pdd:decompose`: a second flow or a `REQ-A` turns out to be in scope; the change needs a model, a
baseline or a checker before it can be accepted; a fourth disjoint slice appears or the owned sets stop
being disjoint; an accepted delta breaks a sibling's observation, so the slices were ordered dependencies;
a migration or removal is discovered inside what looked like construction.

Work already merged stays merged and is named as the baseline of the promoted plan; the worktrees are
closed before the handoff. What does not happen is a second, quieter cut made in the executor's head so the
run can keep its label.

## Decision rules

### Gate enforcement

**These are Workflow A's gates; Workflow B has none.** That absence is why §B1's five clauses are
admission criteria rather than preferences: with no gate, no class and no retry ladder, a clause that is
"nearly true" has no mechanism left to hold the run back, and the defect surfaces after the merge as an
observed behaviour that does not match the plan.

In A, the dispatcher only **enforces** gates; it does not re-judge whether a gate should exist:

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
of the contract it contradicts. Hand back to `pdd:decompose` to fix the contract, and let the user decide
whether to re-dispatch.

**No plan edits mid-run**: no re-cutting, no merging, no relaxing acceptance, no rewriting a clause because
"that is how it really is", no numeric exceptions. That is this skill's discipline and what separates it
from the previous version.

In B the cut plays the contract's part, so the same rule binds it: a slice re-cut after dispatch, an owned
row widened without a ledger note, a requirement quietly dropped from the covered list — each one means the
later acceptance no longer corresponds to what was dispatched. A cut that has to change that much is a
promotion (§B6), and promotion is not a failure of the run.

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

The full catalogue is in `references/pitfalls.md`. The most recurrent:

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
- **Merging at the end of the run instead of at the end of the batch.** The second worktree was opened on a
  baseline the first one has since changed, so the two deltas cannot both land and the conflict is
  unattributable — merge and remove per batch, in §5's order.
- **Leaving worktrees and `pdd/*` branches behind.** A stale worktree keeps an old baseline alive, and the
  next layer picks it up thinking it is current — the run is closed by `git worktree list` and
  `git branch --list 'pdd/*'`, not by the DAG being exhausted.
- **Entering Workflow B because the change "looked simple".** §B1 is five decidable clauses read off the
  PRD; an estimate of effort is none of them. The cost of a wrong entry is a flow nobody modelled, merged
  green.
- **Accepting a slice because its tests pass.** B has no class table, so there is no weaker standard to
  fall back on either: the requirement is observed from the real entry point, or the slice is retained.
- **Persisting the cut as a small `TASKS.md`.** It resumes like a contract while carrying no gates, no
  classes and no audit, and the next reader trusts it to mean what `TASKS.md` means.

## Verification

> A gate is only a gate while it can fail for the right reason. Before trusting a green run:
> `skill_view("pdd:report", "references/gate-discipline.md")`.

**Workflow A**

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
- [ ] after each merge the affected modules and suites were rerun in the main tree;
- [ ] the typecheck error count did not rise above the baseline;
- [ ] every accepted task's delta was merged into the working branch recorded in §2, one commit per task
      naming its id and class (one per slice for a sliced task), and no merge landed after the next batch had
      opened;
- [ ] a task's file-disjoint slices ran concurrently — `git worktree list` showed more than one at a time —
      and the run cost the slowest slice, not the sum;
- [ ] a multi-step task that stopped left a `wip(<task-id>)` checkpoint whose delta is exactly the steps that
      passed; no worktree was returned to the baseline;
- [ ] every merge was verified in the main tree before its worktree was removed, and every removed worktree's
      directory and `pdd/<task-id>` branch are gone;
- [ ] the closing check ran: `git worktree list` lists only the pre-existing worktrees plus retained ones
      named in a layer report, `git branch --list 'pdd/*'` is empty, `git worktree prune` has run;
- [ ] no push, tag, deploy or version change happened;
- [ ] every stop carries its command, raw output and the contract clause it contradicts.

**Workflow B**

- [ ] all five clauses of §B1 were decided from the PRD, and the verdict is in the report clause by clause;
- [ ] no `TASKS.md` or `tasks/` was written, and nothing in the plan directory changed except the PRD's
      recorded hash being compared;
- [ ] the cut existed in the run ledger before the first brief: every slice names its requirement, its owned
      paths, its observation command and its worktree;
- [ ] every requirement in scope is marked covered — none was dropped between the PRD and the slices;
- [ ] every slice was dispatched in one layer (or the ordering was named, with the observation that forced it),
      and no slice widened its owned set without a ledger note;
- [ ] each acceptance is the requirement observed from the real entry point, not a suite that passes;
- [ ] each commit names its `REQ-F` id and quotes the requirement, and each was verified in the main tree
      before its worktree was removed;
- [ ] a run that stopped being simple was promoted to `pdd:decompose` with its merged work named as the
      baseline — not re-cut inside the executor.

> Cross-skill references name the sibling skill and the file separately:
> `skill_view("pdd:decompose", "references/task-construction.md")`. Every sibling is registered under
> this plugin's namespace, so the skill argument always carries the `pdd:` prefix and the path is
> relative to that skill's own directory.

## References

- `pdd:decompose/assets/TASK.md` — the task file's shape; the brief is taken from it verbatim.
- `pdd:decompose/references/task-construction.md`, `task-verification.md`, `task-migration.md`,
  `task-removal.md` — each class's fields and acceptance objects.
- `pdd:decompose/references/testing-methodology.md` — A/B budgets, seeds, shrinking and failure reading.
- `pdd:decompose/references/ownership-rules.md` — one writer per file and the class boundaries; consult it
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
- `references/workflow-b.md` — Workflow B in full: the five-clause entry test, how one flow becomes slices,
  the brief with a requirement instead of a task file, acceptance by observation, the report and the exit
  ramp, anti-patterns.
- `references/pitfalls.md` — the full catalogue.
- `references/browser-harness.md` — when the observation is a screenshot, a computed style, font readiness
  or an accessible name: configuration binding, parallel-build risk, font loading.
- `references/behaviour-preserving-refactor.md` — the depth of a migration: baseline freezing, extraction
  order, cross-module `instanceof`, runner contention, reaction to a frozen artifact.
