# Dispatch pitfalls

Every entry is a failure mode that actually occurred during dispatch and acceptance, with its mechanism and
its fix. Read it before dispatching a layer, and again when a gate goes red. `SKILL.md` indexes it by the same
groups.

## 1. Dispatch discipline

- **Treating a subagent's self-report as evidence.** "Done" does not mean the purpose is observable from the
  real entry point, nor that the delta stayed inside owned. Acceptance is always done by the dispatcher, which
  reads the raw output rather than the report's conclusion.
- **Dispatching off the DAG.** "It looks like it can start now" — once one task jumps ahead, every later
  attribution is void. The ready set is computed only from accepted dependencies.
- **One subagent carrying several tasks.** Two tasks in one brief means a failure cannot be attributed to
  either seam, and the intersection of their owned sets belongs to nobody.
- **Parallel subagents running `git`.** Concurrent `git add` / `checkout` / `stash` trample the user's work;
  only the dispatcher touches git.
- **Breaking the partial order while splitting into waves.** When the parallelism ceiling is below the ready
  set, the edges still hold between waves; pulling a second-wave task into the first wave is a reordering,
  not a schedule.
- **Opening the next batch before closing the last one.** Worktrees from the previous batch, still holding the
  older baseline, are read as current; the second batch's green is measured against a tree that is missing the
  first batch's merged deltas.

## 2. False green

- **Exit 0 while running zero cases.** A wrong selector, a directory outside the include glob, a missing mount
  — the command succeeds and nothing executes. Green without executed volume is pending.
- **Tests derived from the implementation.** Writing assertions while looking at the code you just wrote
  measures that implementation, not the requirement; A-class tests are written from the decision table and the
  report.
- **Editing the test afterwards to make it pass.** The only legitimate fix is the production code; if the
  contract does not fit, stop.
- **Blaming the environment without rerunning.** Font version and toolchain differences can be the real cause,
  or an excuse; the dispatcher runs the same command once, and one command tells them apart.
- **Rerunning until green.** Rerunning is not fixing. One isolated rerun is allowed to exclude a flake; the
  result is recorded as a waiver, and no further gate budget is spent on it.
- **A green check that never bit.** A check that always passes proves nothing; C-class injects a violation with
  `mutate_check.py` and must go red, and B-class confirms its baseline bites the same way.

## 3. Gates and ordering

- **Dispatching downstream with the gate unmet.** "Do it first, add the check later" cancels the gate: an
  A-class model describes code that is not settled, and a B-class baseline compares new code with itself.
- **Modelling before the construction lands.** The model describes an imagined implementation, the properties
  pin down a design fantasy, and the first real behavioural change is reported as a model defect.
- **A migration task editing the check that judges it.** Once the check is loosened the migration is compliant
  by construction. Any change to a constraint, a baseline or a pin requires a dated amendment first.
- **Reading a gate condition as advice.** The gate means "unmet, so do not dispatch"; reading it as "meet it if
  possible" makes the whole ordering meaningless.

## 4. Shared state

- **Two writers on one file.** Whoever integrates second silently swallows the earlier delta, and both report
  success.
- **A shared registry / barrel / route table with no owner.** The router table, the plugin list, the app
  factory's `register`, the static mounts — no single subagent can own them; the dispatcher builds them before
  dispatch and declares them read-only.
- **A shared build target.** Two subagents sharing `target/` (or its equivalent): one's clean deletes the
  other's artefacts while both commands still exit 0.
- **A subagent reaching across worktrees.** Creating or removing a worktree, merging, cherry-picking, cleaning
  shared artefacts — all of it belongs to the dispatcher.
- **An interrupted subagent leaves a stable mutation.** An unrestored mutation can be stable, and is then
  copied into every worktree and into the main baseline; recover from evidence (last known good checkpoint, the
  mutation script and its backups), keep the mutation as evidence, and restore only that one hunk.
- **The batch ends with the merge deferred.** The next batch opens on a baseline that predates the previous
  batch's deltas; when the merge finally happens, the conflict is real and unattributable. Merge at the end of
  the batch, not at the end of the run.
- **Merging into whatever `HEAD` is now.** The user switched branches mid-run and the merge succeeds onto the
  wrong one; the merge target is the branch recorded before the first worktree existed.
- **'Removed' means the directory only.** The `pdd/<task-id>` branch survives, the next run treats it as
  current work, and `git worktree list` still shows a prunable entry. Removal is the four commands, ending with
  reading `git worktree list`.

## 5. Class overreach

- **A construction task writing tests along the way.** This is the old model's new-file tax: every task adds one
  more assertion file and the suite only grows. Construction delivers behaviour.
- **A verification task editing production code.** The defect disappears into an unreviewed diff and the
  report loses its credibility. Verification reports the trace, the seed and the minimal sequence.
- **A migration changing behaviour along the way.** The difference is unattributable and there is no rollback
  point. Behaviour changes go into their own construction task, after the migration is green.
- **A removal leaving comment corpses.** `_old` suffixes, `if false`, permanent coexistence: dead code stays
  and no task is responsible for it any more.
- **Production code deleted, its tests kept.** The suite starts testing something that no longer exists and
  stays green, because it asserts against a mock. The tests that die with it belong to the removal task.
- **A removal with no replacement.** The user loses the old thing before having the new one; the replacement
  ships and is covered by verification first.

## 6. Attribution

- **Red pointing at a file outside the diff.** Assume contention first: one isolated rerun; still red is a
  real regression.
- **Waiting on the agent instead of on the observation.** Under load the assertion runs before the state
  commits, so "green alone, red in the suite" looks like a flake but is a race. Wait on the artefact being
  observed, not on a longer timeout.
- **`instanceof` across a dynamic loader.** The same code is two constructors in two loaders; use structure or
  a marker, not identity.
- **A forward reference inside a build artefact.** The artefact refers to something that does not exist yet,
  and only a cold start exposes it; verify with a cold start, not with incremental output.

## 7. Contract and reality

- **Rewriting a clause because "this is how it really is".** That turns the contract into a documentary. When
  reality conflicts with the contract, stop and report; `pdd:decompose` changes the contract and the user
  decides whether to re-dispatch.
- **Cramming two behaviours into one task.** To avoid stopping, two things are done in one task, and the price
  is a failure nobody can attribute.
- **Treating "unsatisfiable" as something to route around.** A subagent reporting unsatisfiability is doing its
  job; routing around it (narrowing the domain, renaming, adding an exception) silently gives up that
  requirement.
- **Stopping without recording.** The value of a stop is the three things it leaves: the command and its raw
  output, the minimal counterexample, and the contract clause it contradicts. Miss one and the next person
  starts from scratch.
