# Removal tasks (removal)

**Definition**: make something disappear from the repo — production code, tests, documentation, config, flag, dependency. The deliverable is an **absence**.

It serves two kinds of requirement: feature retirement (taking a `REQ-F` offline) and architecture convergence (`REQ-A` removing a module or dependency that should not exist). For the latter the acceptance is still the architecture check: that node must disappear from the dependency graph.

## When to use

- Feature retirement, path abandonment, flag expiry, dead-code cleanup, stale tests, expired documentation sections, dependencies no longer used.
- The replaced old implementation must disappear after the replacement is online.

## Prerequisites

1. **Replacement present** — the new path is online and covered by verification. Without a replacement it is not "ready to delete" but "not finished yet".
2. **Evidence of zeroed references** — run a reference query once before dispatch (grep, compiler, dependency graph), and write the result into the task. Do not rely on "I remember nobody uses it".
3. **External consumer judgement** — if someone outside the repo uses it, this is not removal but deprecation: it needs a window, an announcement, a compatibility period and an expiry condition.

## What to write in the file

1. **Disappears** — precisely list the symbols, files, sections, flags, dependencies that disappear.
2. **Absence proof** — the acceptance method: which command must report zero references, compilation passes, the dependency graph has no such node, the link check passes. This is the acceptance for this class of task.
3. **Dies with it** — the tests, fixtures, document segments, config keys that die along with it. **These deletions belong to this task**, not left for a later verification phase to rediscover.
4. **Files owned** — the deleted files, plus all files that need their references rewritten.
5. **Steps** — change the referencing code first, then delete the body, then run the absence proof.
6. **Guard** — if residue is possible (feature flag, string, migration record, environment variable), state how the zeroing is confirmed.

## Writing rules

- The acceptance is "zero references + existing oracle all green", not "the file is gone".
- Do not leave commented-out corpses, `_old` suffixes, permanent `if false`.
- Deleting tests and deleting production code belong to the same task. Evidence: about 91.4% of deleted tests are stale tests whose production code was already deleted (MSR 2025, DelTest); without synchronisation they accumulate long term.
- If the deletion changes the command set of some flow, first use one verification task to update that flow's model to the post-deletion shape, then delete.
- Documentation removal must likewise run link and cross-reference checks.

## Report on completion

- The disappearance list, checked item by item.
- The raw output of the absence proof.
- The list of tests and documentation deleted along with it.
- Whether any coexisting artifacts are left and their expiry conditions.

## Failure shapes

- **"Comment it out first"** → dead code stays forever, and no task is responsible for it any more.
- **Production code deleted but tests not deleted** → the suite starts testing something that does not exist; the tests stay green because they test a mock.
- **Deleting a public API without a deprecation window** → external consumers only find out when they upgrade, and the cost flows back as an incident.
