# Ownership rules for a task plan

Every rule below exists to keep **one writer per file**. A second writer on one file is two tasks editing
the same bytes in parallel worktrees: the later integration loses the earlier delta silently, and both
children report success.

## Hot files and shared artefacts

- **Give each hot file one owner.** Two tasks that need the same hot file: the earlier task owns it and
  the later task depends on it.
- **Assign shared hot files to the root task.** The manifest, the lockfile, the shared enum or type module,
  the migration chain and the harness entry point belong to the root task, and later tasks import them. A
  dependency discovered missing is an escalation; a local edit reopens the collision the assignment
  prevents.
- **Declare every command entry point the plan invokes in the root task** — a script alias for the
  migration, the backup, the CLI, the SPA build and each runner — even where the file behind the alias does
  not exist yet. A manifest missing one alias forces the integrator to reopen it mid-plan.
- **Split a migration family into its own file.** When one table family belongs to a different task than
  the rest of the schema (audit, event/outbox), each family gets its own migration file and its own writer.
- **Give a shared guard or predicate its own task.** Two or more endpoint tasks that need the same guard
  depend on that task: the rule is implemented once, and each endpoint only has to make its surface
  reachable.

## Class boundaries

- **Construction and migration own production paths.** Neither lists a flow model, a harness entry point
  or a pin file.
- **Verification owns model paths only.** It may not list a production file, and it does not fix what it
  falsifies — the finding goes to the main agent as a construction or migration task.
- **Migration owns both sides of the move** — source set and target set — because a single writer must hold
  the old and the new at the same time. It may not also change behaviour; that is a separate construction
  task.
- **Removal owns the deletions and every file that referenced them**, including the tests, fixtures and
  documentation sections that die with the thing. Tests are deleted by the task that deletes their subject,
  not left for a later verification pass to rediscover.
- **Architecture checks belong to a verification task, never to the task they judge.** A migration that
  edits the constraint deciding whether it passed has exempted itself; the edit needs a dated amendment and
  the main agent's ruling. Same rule for a baseline, a pin, or a frozen expectation.
- **One flow, one model file, one verification task.** Two tasks editing one model is the same collision as
  two tasks editing one source file, with a slower failure mode: the second run overwrites the first
  task's properties.
- **An oracle is read-only while the migration or removal it guards is in flight.** Any task that wants to
  change a pin, a baseline or a frozen expectation raises a dated amendment first; editing the oracle
  mid-flight destroys the equivalence proof and leaves a set of new tests that merely agree with
  themselves.
- **Existing test files are production surface.** When a behaviour change falsifies an existing assertion,
  the task that changes the behaviour updates or deletes it in the same task and names each path in its
  report. New model apparatus is never written here.

## The object that carries a helper needs an owner

A plan calls a helper `h.x`, so the object that carries `x` needs an owner: where the flow model reads a
property of a shared fixture (`h.inspect`, `h.ledger`, `ctx.db`), the file that constructs that object
appears in some unit's *Files owned*, usually the support module nobody listed. The alternatives are
giving that file to the unit which adds the property, or expressing the helper as a free function over the
seam the caller already holds (`inspect(h.db)`).

## Declaration sites, barrels and registries

- **Name the declaration site rather than the barrel.** A module that only `export * from './enums.ts'`
  accepts an "add two error codes" edit and changes nothing at runtime. Grep the symbol first
  (`git grep -n "export const ERROR_CODES\|export type ErrorCode" -- src`), name the declaring file, and
  list a barrel only where the task changes the barrel.
- **Check the repo's own gates before naming an import path.** A meta-check that permits only the barrel
  entry (`from '../support/index.ts'`) makes every direct module import red at the layer gate, and that
  gate is behaviour the plan may not change, so the step gives way to the gate. Grep the harness for such
  a scan before the steps say "import from `path/to/module.ts`", give the barrel to the root task, and let
  each module task register itself in the commit that creates it. Route tables, plugin lists and
  `register()` calls follow the same rule: an enforced single file is a registry with one owner.
- **Where a registry, a policy table and a count-pinning check are all shared**, every endpoint task edits
  the same three files, so the one-writer rule collapses a per-endpoint split into **one task per route
  family**.
- **Give every exported hook a caller with an owner.** A registrar, plugin, route table, component or CLI
  takes effect only when another file invokes it, so it becomes a deliverable once the invoking line has an
  owner. Where the invoking file belongs to the root task or to another unit, nothing names that line: give
  the call site an owner, either as a wiring step in the task that owns the caller or as an explicit
  integration task, and observe the effect through the real entry point (`server.ts`, the app's route
  table) rather than a fixture that constructs the registrar by hand.

## Oracles that pin the set a task grows

- **Grep the harness for every oracle that pins the set this task grows.** A hard-coded route, table or
  migration count sits in more than one place — the same total appears in a contract check and in a
  support helper — and an exhaustive `{ readonly [T in InspectTable]: … }` map turns one new table into
  TS2741 in a file no task owns. Run `git grep -n "<the literal>" -- tests` and `git grep -n "\[T in " --
  tests` before dispatch, and give every hit an owner or record that the main agent repairs it.
- **A baseline about baselines carries the same hazard with no literal to grep.** A group baseline that
  pins another spec's assertion count, its collected-case count, its titles and a suite-wide total goes red
  as soon as any change adds an assertion. Search for `GROUP_BASELINE`, `assertions:` and `collected:`,
  and assign both the entry and the totals to the unit whose additions move them.
- **A behaviour change that makes a pinned total wrong owns the pinned total.** Correcting the number is
  part of the change, not a follow-up; leaving it red hands the next agent a false failure.

## Harness collection

- **Keep a new package inside the main runner's include globs.** A project including `tests/**` collects no
  spec under a new top-level package: the run exits 0 with zero files and the reachability claim is void.
  Keep the specs in the main tree and the source plus packaging in the new package, or add a project that
  includes the new package. The verification unit's harness entry point states which.

## Task size and integration

- **Keep a task within one subagent session.** A task that needs a long chase through unrelated modules
  gets reconnaissance first, then a smaller task.
- **Treat reconnaissance unit lists as candidates.** Check the owned paths, the caller, the line budget and
  the domain before assigning ids, and accept a larger coupled unit only after checking its concrete
  reason and owned paths. Forcing them, or excluding a necessary third file to meet a size target, costs
  the attribution instead.
- **Give integration its own operation.** Registrations, generated artifacts and compile-coupled retirement
  catalogues get an exact integrator-owned operation with its prerequisite set and file list. A behavioural
  cutover stays behavioural: renaming it mechanical evades the limits, and a structural task invented for a
  deletion has no observable outcome. Every retained behaviour needs its own executable successor, and a
  pure mechanism retirement needs an explicit inspected disposition.
