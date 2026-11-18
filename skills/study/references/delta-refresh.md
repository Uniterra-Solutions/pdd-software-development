# The delta refresh: studying a tree that moved under a knowledge base

A first study answers "what does this repository do". The second question is different and cheaper:
"what does it do **now** that the files do not say". This document is the procedure for the second
question. It assumes the tree already carries `AGENTS.md` files written by this skill.

## 1. What counts as a knowledge base

One `AGENTS.md` with a `<!-- study:begin -->` block and a resolvable `generated: {commit} @ {date}`
line. The root index alone is not a knowledge base: it names files, it does not make claims about
behaviour.

A repo with several files at different commits is the normal case, and the reason the base is per file
(§3). A repo with none is Workflow A, and the recon says so instead of producing an empty ledger.

## 2. Two diffs, because they answer two questions

```
touched   every path named by any commit in base..HEAD, plus the working tree
net       the base against the working tree: what the tree looks like now
```

Dispatch reads `touched`. Preservation reads `net`. The difference is not pedantry:

- A handler added in one commit and deleted in the next never appears in `net`. It is still a change
  the inventory was written before, and the file it lived in is still the file the inventory cites.
- A branch renamed twice inside the window ends where it started in `net`, so no row may be rewritten
  on the strength of those two commits. `touched` says who looked at what; `net` says whether the
  claim is still wrong.

Both come from git and neither is a substitute for the other. A refresh that reads only `net` misses
churn; a refresh that reads only `touched` rewrites rows whose evidence ended the window unchanged.

## 3. The base is the file's own provenance commit

```
git show HEAD:{unit}/AGENTS.md   →   generated: {commit} @ {date}   →   base
```

Not a repository-wide tag, not the commit the last study "ran" at. Files studied at different times
are stale in different amounts, and a single base produces both failure modes at once: units whose
claims are still true get re-dispatched, and units studied later than the chosen base get skipped
although they moved after their own base.

A base that does not resolve (rewritten history, shallow clone, a squashed branch) is not a diff
question any more. Record it and fall back to Workflow A for that unit only — see §8.

## 4. Classification: the deepest recorded unit owns the path

```
crates/api/src/server/handlers.rs
  recorded units: crates/api  (round 1)
                  crates/api/src/server  (round 2)
  owner: crates/api/src/server        ← deepest recorded unit whose directory contains the path
```

This is the whole classifier. Two consequences follow, and both are load-bearing:

- **A parent is not refreshed for work its child owns.** Otherwise two subagents rewrite the same
  knowledge from different angles and the parent's copy wins by proximity, which is exactly the drift
  `agents-md-format.md` §4 exists to prevent.
- **A parent is refreshed when a file it cites itself changed**, even if that file lives in the child's
  directory — the script reports those paths as `also cites, and it moved`. A handoff row
  (`delegates to src/server/`) cites a line inside the child's tree, and that line moves when the child
  is edited.

Three buckets come out of it, and every changed path lands in exactly one:

| Bucket | Test | Who acts |
| --- | --- | --- |
| `refresh` | the path is under a recorded unit, or cited by one | one subagent for that unit |
| `new` | the path is under a member with a manifest and no `AGENTS.md` | one subagent, first-study brief |
| root | the path is under no unit and under no new member | the main agent: root index or one root task |

Paths under no unit at all are the repository's own surface — workspace manifests, CI, the root
`README`. They rarely change a branch, but they always change the root index's facts, and the root file
is the main agent's artefact.

## 5. The four task kinds

| Kind | Condition | Writes |
| --- | --- | --- |
| refresh | unit has a block, its base is behind, `touched` is non-empty | the marked block of that one file, rows preserved per §6 |
| new | member with a manifest, no `AGENTS.md`, `touched` non-empty | a new file, round-1 brief (`subagent-brief.md` §1) |
| retire | an `AGENTS.md` is gone from disk | the root index only — the file is already gone; if its directory still exists, that is a `missing-file` finding, not a retirement |
| current | nothing touched, nothing cited moved | nothing, and the provenance is **not** bumped |

`retired` versus `missing-file` is the difference between "the unit was removed" and "somebody deleted
a map". The first is a bookkeeping edit in the root index; the second is a finding to report, because
the directory is still there and is now unstudied.

## 6. Row life cycle

Ids are the handle the rest of the file uses — the mermaid terminals, the nested tables, a later
review quoting a row. So:

| Event in the diff | What happens to the row |
| --- | --- |
| a cited line moved, same predicate | the id stays, the `site` is updated, the trigger is re-quoted from the new line |
| the predicate changed | the id stays, the trigger is re-quoted, the behaviour re-read |
| the branch is gone | the row is removed and **named in the report**; its id is retired, never reused |
| a new branch | a new row with the next free id; existing ids are never renumbered |
| a new entry point | a new row set plus its own mermaid graph; the old graph is kept as it was |
| no change at all under the unit | the block is not rewritten; provenance still moves to HEAD, because "true at `{commit}`" is now a later commit |

The last line is the one that surprises people: a refresh with no row change is a legitimate outcome
and its only output is a provenance line. That is still worth a commit — it is the record that someone
looked.

### 6b. A row cites more than its site, and the auxiliary citation died

A row can carry several `path:line` tokens: the `site` cell, the trigger, a `notes` cross-reference, an
example. Preservation keys on **the site cell's file**. So when the site's file ends the window unchanged
but a *secondary* citation in the same row points at a file that moved, the two checks contradict each
other: leaving the row alone fails the citation read (`cited file does not exist` / line out of range), and
repairing it breaks byte-identity with the committed row. A refresh that hits this has to guess which check
its author cared about, and both guesses are defensible — which means the rule is wrong, not the refresh.

**Preservation protects the claim, not a dead pointer.** The claim is `id`, behaviour, trigger and the
`site` cell. A `path:line` token outside the site cell is a citation, and a citation that no longer
resolves is repaired, with the row otherwise untouched:

- the site cell stays **byte-identical**, and so do the behaviour and trigger cells;
- every non-citation word stays byte-identical;
- the repair is listed in the report (`auxiliary repaired: {id}: old → new, the line that proves it`);
- the citation read tolerates a repaired auxiliary pointer while the site cell and the wording stay
  byte-identical; a row whose site cell moved while its file did not, or whose wording changed, is still a
  finding.

Verify the new line by its **text**, never by arithmetic on the old offset: `git show {base}:{file} | sed -n
'{n}p'` to get the old line, then `grep -n` for that same text in the new tree. The one case this cannot
cover is a pointer that is in range but wrong (a function pushed 49 lines down by an unrelated insertion) —
no check in this skill sees it either, so the row's own quoted predicate is the evidence, and the report
says it was re-read.

## 7. The brief

`subagent-brief.md` §5 is the delta brief: the same fields, plus `base: {sha}`, the touched-path list
for that unit, and the diff-scoped obligations.

The touched-path list is a **hint, not the record**. It is derived by a script from a log range, and it can
silently come out short — one run lost the list for two units while their `files` count was non-zero. Every
brief therefore names the authoritative command (`git log -p {base}..HEAD -- {unit}`) as step 1 of the read
order, and a child that finds the list disagreeing with the diff reports it and works from the diff. That is
the recovery path that worked; a child that trusts the list does nothing and says the unit was untouched.

It never gets the whole diff of the repository — a
subagent holding other units' diffs starts reasoning about them, and its report then describes work it
was not given.

## 8. Degenerate cases

| Situation | What the delta does |
| --- | --- |
| shallow clone / history rewritten | the recorded base may not be an ancestor. `git merge-base --is-ancestor` fails → re-study that unit as Workflow A and say so in the report |
| the working tree is dirty | `net` includes the working tree, so a dirty tree is studied as it is. The report names it; the commit happens after |
| a unit directory was renamed | `git mv {old} {new}`, then refresh — the file travels with its directory — and update the root index in the same commit — a copy loses the provenance chain and `git log --follow` stops at the copy |
| a unit was split in two | the old file is retired, both halves become `new` units. Do not try to distribute the rows by hand: two files, two studies |
| two units merged into one | the survivor's file is refreshed and the retired file is deleted; the root index loses one row |
| `AGENTS.md` was never committed | no committed version to compare against, so preservation is unverifiable — the verify step says so instead of passing silently |
| > 12 units in one delta | dispatch in waves of ~8, deepest units first, so a parent's brief can name a child that already exists |

## 9. Acceptance

```
git diff --name-only {base} HEAD -- {unit}   # moved unit → this file must differ
git diff --stat -- '*AGENTS.md'              # moved file → its unit must have moved
git ls-files '*AGENTS.md'                    # every file the root index names still exists
```

The first checks three things the second cannot: that no file is stale, that a row whose cited file
ended the window unchanged is byte-identical to the committed version, and that no knowledge-base file
disappeared without the root index noticing. Compare against the committed version, so verify runs
**before** the refresh is committed; one commit per unit after it passes.

Judgement, which no script reaches: a row that changed was changed for the reason the diff gives; a
new branch's trigger is quoted from code; a retirement names the branch it drops; the root index picked
up the new and lost the retired.

## 10. Worked example

A two-member workspace, one knowledge base commit, then one commit adding a line to `api`'s handler:

```
=== units (2)
unit          base       commits  files  status
crates/api    c44da602   1        1      refresh
crates/core   -          0        0      missing-file

=== commits and touched paths per unit
crates/api   base c44da602 → HEAD
  0b133c0  2026-11-16  api: add a module doc line
  [M] crates/api/src/handlers.rs

=== knowledge-base files gone from disk (1)
  [missing-file] crates/core/AGENTS.md

=== members with no AGENTS.md yet (1)
  crates/new	cargo

# dispatch: 1 refresh subagent(s), 1 new unit(s), 0 root path(s), 1 file(s) gone
```

Two rows cited `src/handlers.rs:20` and `:30`; the added line moved them to `:21` and `:31`. A third
row cited `src/stable.rs:7`, whose file did not move, so it had to survive verbatim — which is exactly
what `--verify` checks, and what it caught when the row was dropped in testing.

## 11. Anti-patterns

- **Re-studying the unit and rewriting the block.** The diff of the knowledge base then shows churn no
  code change explains, and the rows nobody re-read are indistinguishable from the rows that were.
- **Reading only the net diff.** A create-then-delete inside the window is invisible, and the unit looks
  untouched.
- **Refreshing everything because the ledger is cheap to produce.** The ledger is cheap; the dispatch is
  not, and a unit whose base is current needs no subagent at all.
- **One subagent for the whole delta.** Attribution dies: a wrong row no longer names a directory, and
  the fix is an investigation instead of a re-dispatch.
- **Bumping provenance without reading the diff.** `--stale` goes quiet, the file looks maintained, and
  the next reader trusts claims nobody checked.
- **Renumbering rows after removing one.** Every mermaid terminal and every quoted id downstream now
  points at the wrong branch, and nothing errors.
