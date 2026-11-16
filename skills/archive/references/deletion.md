# Deleting the plans

The deletion is the part that cannot be undone by re-reading. It is gated on coverage, restricted to tracked
files, committed one plan at a time, and verified by reading git back.

## 1. The gate, in order

Nothing is deleted until all five hold. Each one is cheap; skipping any of them is how an archive destroys the
only evidence for its own claims.

1. **Coverage.** `python3 scripts/check_history.py <root>` reports every plan as `covered` or `excluded` with a
   reason, with zero errors. A plan with no record is summarised first, or excluded and named.
2. **Conflicts collapsed.** No subject has two `accepted` rows. The newest claim is the row; the older one is a
   pointer inside it (`references/decision-record.md` §4).
3. **Reference sweep.** No live file outside `docs/history/` still points at the plan -- sweep **every tracked
   file type**, not only `*.md`:

   ```
   git grep -n --fixed-strings '<plan path>' -- . ':!docs/history/*'
   ```

   Then classify every hit, because three classes need different handling:

   | hit | what it is | what to do |
   | --- | --- | --- |
   | a document pointing a reader at the plan | a broken link waiting to happen | rewrite it to `docs/history/decisions.md` (or the era file) in the same commit as the deletion |
   | **a script or config that READS a file inside the plan** | not a link -- a dependency: the tool breaks the moment the plan is gone | move the file out of the plan to a stable home beside its consumer, repoint the reader, commit that move **before** the deletion, then re-run the consumer and record its output |
   | a captured command output inside another plan | a transcript, not a pointer | rewrite the path token to where the file lives today and add an editorial note naming which words were rewritten; never silently falsify a transcript |

   The second class is the one that bites: a roster, a census or a `pins/` file that a gate script parses looks
   like a plan artefact and reads like history, but deleting it turns a green check into a crash. A file a checker
   reads on every run is a production input, and production inputs do not live inside plans.
4. **Tracked.** `git ls-files --error-unmatch <plan path>` succeeds. An untracked plan is **never** deleted —
   git cannot recover it, and the promise "git has it" would be false. Report it and leave it on disk.
5. **Index row written.** The plan's row in `docs/history/index.md` already carries the decisions it produced.
   The deletion commit then only fills in the commit hash — the row exists before the file does not.

## 2. One plan, one commit

```
git rm -r plans/2026-09-auth
git commit -m "archive: drop plans/2026-09-auth (D001 D002 D003)

Summarised in docs/history/decisions.md; evidence recoverable at 3c1f0ab."
```

- **one plan per commit** — a single commit deleting six plans cannot be reverted for one of them;
- **the ids in the subject line** — this is the only place that links a deleted path to the decisions it produced
  without reading the index;
- **the archive commit in the body** — the commit that holds the summary, so `git show` has a starting point;
- **deletion message verb is `archive:`**, not `chore:` or `cleanup:`, so `git log --grep '^archive:'` lists the
  whole history disposal.

Batch deletions commit per plan even when the round deleted eight of them. Eight commits is the cost of being
able to say, later, which plan's removal broke a link.

## 3. What is never deleted

| Thing | Why |
| --- | --- |
| The in-flight plan (`TASKS.md` with unfinished tasks, or a task id in the branch name) | it is current work; its task contracts cite it |
| Anything untracked | git cannot recover it; the archive's own premise fails |
| `docs/history/` itself | it is the record of record |
| `README.md`, `DESIGN.md`, `AGENTS.md`, `CONTRIBUTING.md` | living documents, read by humans and agents, not history |
| A plan with an unresolved conflict | the conflict report needs both citations until it is resolved |
| A plan whose decisions are only in code | the citation would not survive; record it first |
| Vendored or generated trees | not the project's history |

## 4. Verification — read it back, do not assume

After the deletion commits:

```bash
git status --short                                   # clean: nothing staged, nothing modified
git log --diff-filter=D --name-only --oneline -20     # only plan paths, no source files
git ls-files <plan path>                             # empty
git cat-file -e <recorded-commit>:<plan path>         # succeeds → still recoverable
git show --stat <deletion commit>                     # one plan's files, nothing else
```

`git cat-file -e` with a directory path is not enough on its own — git stores blobs, not directories. Use
`git ls-tree -r <recorded-commit> -- <plan path> | head` and require output: a non-empty tree is the proof that
the content is still there.

Then repair the one thing the deletion invalidates: **relative links**. `docs/history/decisions.md` cites plan
paths, which no longer resolve. That is intended — the citation now means "this path at `<commit>`". Check the
index states that convention once, at the top, so no reader mistakes a dead path for a mistake:

> Plan paths below are historical: each resolves at the commit in its `commit` column, not on disk.

## 5. Recovering a deleted plan

`git show <recorded-commit>:<plan path>/PRD.md`. If the goal is to bring a plan back into the working tree:

```bash
git checkout <recorded-commit> -- <plan path>
```

and then decide whether the archive's records are wrong — a restored plan that contradicts the newest record is
a finding, not a rollback: fix the record in the same commit as the restore, or the register and the tree
disagree.

## 6. When the deletion is wrong

If a deletion turns out to have removed something still in use, the recovery is `git checkout <sha> -- <path>`
plus a record: which plan, why it was needed, and which record was wrong about it being history. Do not silently
restore — the archive's claim was that these files were superseded, and a silent restore leaves that claim
standing while its evidence is back on disk.
