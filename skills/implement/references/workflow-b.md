# Workflow B — one flow, no tasks

The dispatcher cuts the work, dispatches it, and accepts it. Nothing is written into the plan directory:
the cut lives in the run ledger, and it dies with the run.

This file is the procedure in full. `SKILL.md` §B1–B5 is the same procedure at dispatch length.

## 1. Entry test: is this work small enough to dispatch without a contract?

Five clauses. **All five must hold**, and each is decided from the PRD by reading, not by estimating
effort — "it feels small" is not a clause.

| # | Clause | How it is decided | What fails it |
| --- | --- | --- | --- |
| 1 | **One flow, and only one** | §4 of the PRD has exactly one `F<n>` section, and every requirement in scope carries that flow's prefix | a second flow, even one that shares files; a requirement with no flow |
| 2 | **No architectural requirement** | §6.2 is absent, or empty | any `REQ-A`: its acceptance is an executable check over a scope wider than the change |
| 3 | **No prerequisite evidence** | no requirement needs a model built before another can be written, and none needs a baseline frozen before the change | any acceptance that only exists after the code does — that is what `pdd:decompose`'s model gate and guard gate are for |
| 4 | **One layer, files enumerable now** | every file the change touches can be named before dispatch, and they fall into at most three disjoint groups | files that will only be discovered by the change; a group that is not file-disjoint |
| 5 | **No migration, no removal** | no schema or data migration, no package or symbol retired, no dependency dropped | any of the three: each needs a retention list or an absence proof, i.e. a class |

**When a clause fails, the only action is to stop and hand back.** The report names the clause, the
sentence of the PRD that fails it, and the cut it would have needed. `pdd:decompose` then writes the
DAG. Two things are forbidden here, because both destroy attribution:

- **Do not write `TASKS.md` or `tasks/` yourself**, not even a minimal one. The executor writing the
  contract it is judged by is the contract editing itself, and afterwards no evidence separates the
  plan from what was convenient to build.
- **Do not run the work as "B plus a bit more".** A second flow does not become admissible because the
  first one went smoothly.

**Below one slice there is no dispatch either.** A typo, a one-line guard, a comment fix: ordinary
engineering work, done directly, outside this skill. B's overhead is a worktree, a brief, an
acceptance and a merge; paying it for an edit that fits in one diff is a worse trade than doing it.

## 2. The cut: how one flow becomes slices

A slice is **a set of owned files that serves one requirement and can be observed on its own**. That is
the same unit `pdd:decompose` calls a task; the difference is only that nothing is persisted.

Cut by seam, never by file count:

- **One requirement per slice** where the requirements are independently observable. Two requirements
  that share a file are one slice — ownership is per file, so two slices cannot both own it.
- **Supporting pieces stay with the behaviour that needs them**: a type, a config key, a registration
  entry. Splitting them out produces a slice that is green in isolation and useless alone.
- **Order only where an observation needs the earlier result.** B has no gates and no retry ladder, so
  ordering costs a whole extra batch: prefer slices that are genuinely concurrent.
- **Cap at three.** A fourth disjoint group is the first sign clause 4 was optimistic — re-read the
  entry test rather than dispatching it.

### The cut is recorded before it is dispatched

Write one row per slice into the run ledger (the same ledger that holds the working branch and the
baseline hashes), and keep it out of the repo:

| Field | Content |
| --- | --- |
| slice | `S1`, `S2` … unique within the run |
| serves | the `REQ-F-<flow>-<n>` ids this slice is accepted against — at least one, and the run covers all of them |
| owned | the exact paths it may create, modify or delete |
| observation | the command or entry point that shows the requirement holding, run from the real entry point |
| worktree | the path and the baseline hash list |

Why it is a file and not a plan: every acceptance compares the delta against `owned`, and a table that
lives only in the conversation has nothing to compare against once the conversation is summarised.
Why it is not `TASKS.md`: a persisted cut is a contract, and a contract with no gates, no classes and
no audit is worse than none — the next reader would trust it to mean what `TASKS.md` means.

## 3. The brief

Same shape as `subagent-dispatch.md` §2, with the task file replaced by a requirement reference:

```
your worktree:  <worktree path>                     ← the only writable tree
your starting point: <baseline hash list path>
build directory: <path>
read-only contract: <plan-dir>/PRD.md               ← §4 <F1>, §6.1 <REQ-F-…>
your requirement: REQ-F-<flow>-<n>                  ← execute this one, in the PRD's words
your rules:     references/subagent-charter.md      ← read only, work to it
owned:          <each path, exactly>
acceptance:     <the observation command, and what it must show>
prohibited:     editing the PRD or any other plan file; touching a sibling slice's files; weakening or
                deleting existing tests; adding dependencies; running the full suite; building the whole
                workspace; commit; push; merge; branch
stop conditions: the requirement cannot be satisfied as written / it contradicts already-merged code /
                an owned file is missing → stop, report, leave the PRD untouched
report:         opening line = the requirement id and its sentence, quoted from §6.1; then the diff
                summary, the observation command with its raw output, and the tests you ran
```

**The opening line is the proof it read the requirement**, not the brief. Without it a subagent that
misread the flow still produces a green report, and the acceptance has nothing to check against but a
diff that looks plausible.

**The PRD is read-only, and its hash is recorded.** A subagent that edited the requirement and then
satisfied its own edit is indistinguishable from one that satisfied the plan, until someone diffs the
plan — and by then the merge has landed. Compare the hash at acceptance, as in Workflow A.

**A slice may not be re-cut for the subagent's convenience.** It owns the paths in its row. When a path
outside the row turns out to be necessary, it stops and reports; the dispatcher either widens the row
explicitly, with a note in the ledger, or re-cuts and re-dispatches. A silent widening is the one thing
acceptance cannot see.

## 4. Acceptance: the requirement, observed

There is no class table here, and this is the part that cannot be improvised: **a slice is accepted by
the requirement it serves, observed from the real entry point**, plus the four rules that hold in both
workflows.

| Check | What it means in B |
| --- | --- |
| requirement observed | the acceptance command from the slice's row runs against the worktree, from the real entry point, and its output is the one the PRD's "Where it is visible" names |
| delta ⊆ owned | the diff touches only the row's paths; lockfiles and build output are byproducts, recorded and moved past |
| count > 0 | the observation executed something — a command that selects zero cases and exits 0 has not run |
| no weakened oracle | an existing assertion the change invalidates is updated or deleted **by the same slice**, and listed in its report |
| measured numbers reproduced | any "measured X" in the report is rerun by the dispatcher with the same command before it lands in code, docs or a commit message |

**An acceptance that needs a model, a frozen baseline or a checker is not B's acceptance.** It is
Workflow A's, and the moment it is needed the run stops and promotes (see §6). Substituting "the tests
pass" for a missing model is how a green run delivers a flow nobody has observed.

**Flaky reds get the same treatment as in A**: measure the trigger rate, do not rerun until green, and
require N seeds all green in addition to the fixed one.

## 5. Merge, verify, close

Identical to `SKILL.md` §5 and §7 — batch by batch, into the branch recorded before the first worktree
existed, one commit per accepted slice, delta applied as a patch when the main tree is dirty, verified in
the main tree before the worktree is removed, `git worktree list` and `git branch --list 'pdd/*'` empty
at the end. The only difference is the commit subject:

```
feat(<surface>): <what the requirement now does>

REQ-F-<flow>-<n> — <the requirement's sentence, quoted>
```

A commit that names no requirement cannot be traced back to the plan, and B has no task id to fall back
on: the requirement id is the only handle the run leaves behind.

## 6. Report, and the exit ramp

The report carries, in this order:

1. the entry test's verdict, clause by clause;
2. the cut table as dispatched, including any row widened mid-run and why;
3. per slice: accepted / retained, its commit, its worktree removed;
4. **every requirement in scope, marked covered or not covered** — the run is not complete while a
   requirement has no slice, and "it was implied" is a gap, not coverage;
5. any promotion decision, with the observation that forced it.

**The exit ramp: a run that stops being simple is promoted, not stretched.** Any of these ends
dispatching in B and hands back to `pdd:decompose`:

- a second flow, or a `REQ-A`, turns out to be in scope;
- the change needs a model, a baseline, or a checker before it can be accepted;
- a fourth disjoint slice appears, or the owned sets stop being disjoint;
- an accepted delta breaks a sibling's observation, so the slices were ordered dependencies after all;
- a migration or removal is discovered inside what looked like construction.

Work already merged stays merged and is named as the baseline for the promoted plan; worktrees are
closed before the handoff. What does not happen is a second, quieter cut made in the executor's head so
the run can keep its label.

## 7. Anti-patterns

| Shape | Why it is wrong | Instead |
| --- | --- | --- |
| "It looked simple" used as the entry test | The test is five decidable clauses, and this is none of them | Run the clauses; on failure stop and hand back |
| Writing a small `TASKS.md` so B can run like A | The executor authored the contract it is judged by; no evidence separates plan from convenience | No persisted cut in B, ever |
| Slicing by file count to get parallelism | Files that must change together are one seam; split, both slices fail acceptance and neither can merge | Slice by seam: one requirement, one observation |
| Accepting on "its tests pass" | The requirement is about an observable the tests may not touch | Trigger the PRD's "Where it is visible" from the real entry point |
| Adding "just one more" slice after a discovery | B has no gates, no classes and no audit; the fourth slice is where the plan needed decomposing | Stop, close the worktrees, promote to `pdd:decompose` |
| A commit subject naming the surface but not the requirement | B leaves no task files; the requirement id is the only trace | Name the id in the subject, quote the sentence in the body |
| Leaving the cut in the conversation only | Acceptance compares against `owned`; a summarised conversation has no rows | One row per slice in the run ledger, before dispatch |
