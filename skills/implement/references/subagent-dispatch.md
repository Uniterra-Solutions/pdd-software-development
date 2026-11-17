# The efficient subagent dispatch paradigm

Three things decide whether a dispatch succeeds: **isolated workspace, one copy of the contract, acceptance
by class.** Everything else is detail.

## 1. Build the worktrees

One worktree per child, its own build directory, one explicit starting point. Do these three things apart and
you get "each of them green, red after the merge".

- **Record the working branch first.** `git rev-parse --abbrev-ref HEAD` before the first worktree exists,
  written into the run ledger. It is the merge target for every batch, and it is not re-read later: after the
  user switches branches, `HEAD` is a different branch that looks equally plausible.
- **Start from the baseline, not from the dirty main tree.** The baseline is a hash list: the base commit plus
  an overlay of accepted tasks. A dirty main tree is expressed as an overlay — no commits, no stashing of the
  user's work.
- **The overlay must exclude what is not accepted**: siblings' deltas, failed experiments, unrestored
  mutations, a mutation an interrupted child left behind. One leaked pending mutation makes every worktree's
  verification falsely green.
- **A separate build directory.** With a shared `target/` (or `dist/`, `node_modules/.cache`), one person's
  clean deletes another's artefacts and both commands exit 0. Rust uses `CARGO_TARGET_DIR`, Node its own
  caches and out-dir, Python its own venv or `PYTHONPYCACHEPREFIX`.
- **Ports and sockets too.** Two parallel harnesses bound to one port: the second connects to the first's
  server and asserts about someone else's app. Pin an unusual port, use a strict-port flag, disable server
  reuse.
- **One baseline per layer.** After an amendment, refresh every worktree's PRD/TASKS/task snapshot before
  dispatching. A worktree left on the old dependency produces a result that cannot be merged with its sibling,
  and both report success.
- **Subagents never touch the worktree's lifecycle**: no create, no remove, no merge, no cherry-pick, no
  commit, no push, no cleaning of shared artefacts. Building a tree, merging a tree and deleting a tree are
  the dispatcher's actions alone.
- **After an interruption, recover from evidence**: diff the current tree against the last known good
  checkpoint, check the mutation script and its backups, keep the mutation as evidence, restore only that one
  hunk, and accept nothing until that is done.

## 2. Give the subagent the task file's directory

The brief gives **paths**, never pasted bodies.

```
your worktree:  <worktree path>          ← the only writable tree
your starting point: <baseline hash list path>
build directory: <path>
read-only contract: <plan-dir>/PRD.md, <plan-dir>/TASKS.md
your task:      <plan-dir>/tasks/T03-<slug>.md   ← read only, execute it
your rules:     references/subagent-charter.md   ← read only, work to it
owned:          <each item, per the task file>
prohibited:     editing PRD/TASKS/sibling task files; weakening or deleting existing tests; adding
                dependencies; running the full suite; building the whole workspace; commit; push;
                merge; branch
stop conditions: the task cannot be satisfied / it contradicts already-merged code / an owned file is
                missing → stop, report, leave the contract untouched
report:         the format its task file specifies, raw output pasted
```

**Why the directory and not the text.** Three reasons, each of which has cost real money:

1. **Two copies drift.** Once the pasted text and the file differ, the subagent follows whichever it read
   last; `pdd:decompose` says a task's body exists in exactly one place, and a brief that pastes it creates
   the second place.
2. **Pasting is rewriting the contract at dispatch time.** Any omission, paraphrase or translation into a
   checklist is a silent edit, while acceptance still runs against the file's original text — and when the two
   disagree, nobody can say who changed what.
3. **The brief is an order of magnitude smaller and the evidence chain is unchanged.** A 200-word brief
   pointing at an 8 KB contract lets the subagent read it; the saved context goes into the work, not into
   repetition.

**Why the whole `tasks/` directory rather than one filename.** Sibling task files sit next to it, and the
subagent reads them to understand its boundaries (it can read them; it may not write them). The owned list is
still the only write authorisation; the directory only saves it from guessing.

Three practical requirements:

- `test -f` every path before dispatch. One wrong path blocks the subagent at its opening move, and it will
  not tell you the path is wrong — it will say the task is unclear.
- The task file is **read only**: record its hash before dispatch and compare it at acceptance. A subagent
  that edited the contract and then implemented it is the hardest failure to diagnose.
- The brief carries no verbatim copy of the header. The subagent's first action is to read its own file and
  report one line from it (the purpose, for instance) — evidence that it opened the right file, at a cost of
  one token.

## 3. Accept by class

Acceptance reads the task's own class and never applies another class's criteria. The dispatcher runs the
commands and reads the raw output itself; the report is only an index.

| Class | Acceptance | What the dispatcher actually does |
| --- | --- | --- |
| **construction** | the purpose is observable from the real entry point | triggers the entry point itself (constructs the object, injects a request, runs the CLI once); `git diff --stat` against owned; runs the affected existing suites and the typecheck |
| **verification A** | the model exists, the property ran, the counterexample is pinned | reads the harness record: seed, sample count, shrunken minimal sequence; confirms every property has a budget |
| **verification B** | the baseline was frozen before the change, the same command reruns bit-identical afterwards | compares the hashes of both outputs; confirms the baseline artefact's mtime precedes the change |
| **verification C** | green before the change, still green after, and an injected violation must go red | runs the check itself; uses `mutate_check.py` to inject a violation, confirms red, restores and confirms byte-identical |
| **migration** | every retention-list item has evidence; source set → target set matches; the old path is removed or has an expiry condition | reads the oracle output; `git diff --name-status` against the source and target sets; `grep` for the old symbol, expecting zero |
| **removal** | absence proof; zero references; the tests that died with it are deleted | runs the reference query and the compile itself; confirms the test files and fixtures disappeared with it |

Three lines across every class:

- **delta ⊆ owned.** Touching another file is a contract breach; send it back to the same owner. Lockfile,
  build products and caches are byproducts — record them and move on.
- **count > 0.** Every "green" needs real executed volume. Selecting zero cases and exiting 0 is unfinished,
  not green.
- **Existing oracles may not be weakened.** A task that invalidates an existing assertion must update or
  delete that assertion in the same task and list it.

**Symptoms of a class mismatch** (use them to check which ruler you are holding):

| Mismatch | Symptom |
| --- | --- |
| A's criteria applied to construction | you start asking the subagent for tests, so every construction task gains one more assertion file |
| construction's criteria applied to C | you only confirm "the check passes", never that it can go red — a check that cannot go red proves nothing |
| B's criteria applied to migration | you compare behaviour only, never the architecture rule, so the refactor can move in the wrong direction |
| removal's criteria applied to migration | you confirm the old path is gone, never the retention list |

## 4. The full sequence of one layer

1. Compute the ready set (dependencies **accepted**, not self-reported as successful).
2. Record the working branch (`git rev-parse --abbrev-ref HEAD`) into the ledger.
3. Create the worktrees and baselines, record the hashes.
4. Do the shared prerequisites: manifest, lockfile, registry / route table, shared fixtures, entry aliases;
   declare them read-only.
5. Write the briefs (path-shaped, §2) and dispatch the whole layer in one `delegate_task`.
6. End the turn after dispatch; do not poll. Handle the completion notices in batch.
7. Verify the delta: the changed paths equal owned, byproducts recorded separately.
8. Accept by class (§3); a failure goes back to the same owner.
9. **Merge into the working branch recorded in step 2.** Re-verify the destination hashes; pick the mechanism
   by the state of the main tree — clean: commit in the worktree on `pdd/<task-id>` and `git merge --no-ff`;
   dirty: apply the delta as a patch and stage only its own paths. One commit per accepted task, naming the
   task id and class. A conflict is resolved explicitly and recorded; an unresolvable one stops the run.
10. **Verify again in the main tree**: the task's observation, the affected modules and suites, the typecheck
    leg. The worktree's green says nothing about the main tree.
11. **Close the worktree, in this order**: `git worktree remove <path>` → `git worktree prune` →
    `git branch -D pdd/<task-id>` → `git worktree list` shows the path is gone. The report and the patch are
    saved before removal. A failed or unmerged worktree stays, with its blocker attached, and is named in the
    layer report.
12. Next layer. Only after the last layer: the closing check (`git worktree list` has nothing beyond the
    pre-existing trees plus the retained ones; `git branch --list 'pdd/*'` is empty).

## 5. Anti-patterns

- **Pasting the whole brief.** The contract becomes two copies; implementation follows one, acceptance the
  other.
- **A shared build target.** Both exit 0, and the artefact turns out to be half-finished only after the merge.
- **Opening a worktree from the dirty main tree.** One unrestored mutation is copied into every child, and
  everything goes falsely green.
- **Reusing last layer's worktree.** The baseline is stale and the previous task's delta is mixed into this
  one.
- **Letting the subagent commit before integration.** The dispatcher loses the chance to check the baseline,
  and the conflict becomes unsolvable.
- **Accepting "the report says done".** The report is an index, not evidence.
- **Two tasks in one worktree.** The intersection of their owned sets belongs to nobody and a failure cannot
  be attributed.
- **Merging at the end of the run.** Between the first batch and the merge, the second batch was built on a
  baseline the first one has already moved; the two deltas cannot both land, and neither report shows it.
- **Merging into `HEAD` instead of the recorded branch.** The user switched branches mid-run, the merge
  succeeds, and the work is now on a branch nobody will run.
- **Leaving the worktree and its branch behind.** A stale worktree keeps an old baseline alive, and the next
  layer picks it up as if it were current — the run is closed by `git worktree list` and
  `git branch --list 'pdd/*'`, not by the DAG being exhausted.
- **Rolling a worktree back to the baseline after one failed step.** The steps that passed die with the step
  that failed, and the next attempt re-derives them at the same cost. Commit them as a `wip(<task-id>)`
  checkpoint and re-dispatch from there; a partial delta that is green on its own step check is progress, not
  contamination. And for every acceptance criterion in the brief, state the observation that would make it
  fail: a criterion that cannot go red is not a criterion.
- **Serialising a task's file-disjoint slices.** Five slices run one after another because "one task, one
  commit" was read as "one workspace". Slices are same-layer dispatches: one worktree each, one commit each at
  merge, and each slice's failure costs only its own wall-clock time.
- **Compensating inside the steps for a gate that is wrong.** A save/copy/restore dance around a checker, a
  hand-computed value pasted next to the script's output. The instrument is the deliverable; report it, do not
  route around it.
