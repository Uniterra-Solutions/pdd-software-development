# The subagent brief

One subagent, at most three plans, contiguous in time. Paths only, no pasted bodies — the contract drifts the
moment there are two copies of it.

## 1. The brief

```
role:        historian. Read-only. You write no file and you delete nothing.
project:     <project root>                       ← read-only
your batch:  <plan path 1>, <plan path 2>, <plan path 3>   ← at most three, contiguous in time
already known: <path to docs/history/decisions.md, batch ≥ 2 only>  ← read-only; never re-number its ids
record rules: <plugin>/skills/archive/references/decision-record.md
diagram rules (context only, main agent draws): <plugin>/skills/archive/references/history-diagrams.md
date source:  files first, then `git log -S '<phrase>' --format='%h %ad %s' --date=short -- <path>`

deliverables, in your report:
  1. decision records — D-ids continuing the register, with rejected alternative, quoted reason, path:line,
     date, source plan, commit, status
  2. evolution events — E-ids: date, before (one clause), after (one clause), the decisions that drove it
  3. conflicts — two plans deciding the same subject differently: emit ONE record (the newest) with the older
     claim in its `conflict:` field, and report the collapse
  4. undated plans, plans with no decision, and anything the format makes unreadable

prohibited:  editing any file; deleting anything; inventing a date; inferring a reason from the code;
             renumbering an existing D-id; summarising a plan you did not open; writing mermaid
stop when:   a plan is unreadable (encoding, binary, truncated) → report the path and read the rest;
             two records would need the same id → report the collision, do not renumber;
             a decision's reason exists only in code → record `because: unknown`, cite the code path:line
report:      §2 of this file, decisions first, conflicts at the end
```

`test -f` every path before dispatch. The `already known` file matters from batch 2 onward: without it, the
second subagent invents `D001` again and the register has two founders.

## 2. The report

```
batch:            2 of 3
plans read:       plans/2026-10-jobs-v2 (4 files), plans/2026-10-billing (2 files)
decisions:        6 records, ids D006..D011
eras:             E3, E4
undated:          none
no-decision plans: plans/2026-10-billing — confirms the existing billing split, changes nothing
conflicts:        1 — retry cap: D008 unbounded (jobs-v2/PRD.md:71, 2026-10-09) vs capped at 3
                  (billing/AMENDMENTS.md:12, 2026-10-22). Emitted D010 only; D008 collapses into its
                  `conflict:` field, nothing recorded a reversal
unreadable:       none
unresolved:       D009's reason is only in code (src/retry.rs:44) — recorded as `because: unknown`
ids used:         D006 D007 D008 D009 D010 D011
```

Four parts of that report are load-bearing:

- **`ids used`** — the next batch needs it to continue the register rather than restart it, and the main agent
  checks it against the files it actually opens.
- **`conflicts`** — the only output that cannot be reconstructed later; everything else can be re-read from the
  plans while they still exist. The register keeps the newest claim, so this line is the only trace of what was
  overwritten.
- **`no-decision plans`** — an explicit zero is a finding. Silence is indistinguishable from a skipped plan.
- **`unreadable`** — a plan the subagent could not parse is a coverage gap, and a coverage gap blocks its
  deletion in phase 4.

## 3. What "summarise" excludes

The subagent produces records and events, not a narrative. Specifically it does not:

- **retell the plan.** "The plan describes a jobs service with streaming and batch modes" is the plan's abstract,
  and the abstract is in git forever.
- **list the tasks.** Task ids and their status are evidence for a decision (`source:`), never a record.
- **describe the current code.** That is `pdd:study`'s job and it will be wrong the moment the code changes.
- **evaluate.** "This was a good decision" is not history; the `cost accepted` line in an era record is the
  closest thing allowed, and it must be quoted from the plan.

## 4. Batch boundaries and supersession

If your batch's earliest plan is cited by a plan in a later batch, say so in the report (`cited by:
plans/2026-11-x at AMENDMENTS.md:9`). The main agent uses that to decide whether the boundary split a
supersession, and can merge or re-dispatch the batches. A reversal whose cause is in another batch produces two
records that contradict each other in the register — which is checkable, but it reads as two mistakes.
