<!-- Template for docs/history/index.md. Keep the table columns exactly: check_history.py
     reads them. One row per discovered plan, written before its deletion, with the commit
     filled in afterwards. -->

# Project history — index

This directory holds the project's history: the decisions that still govern it
(`decisions.md`), the phases it passed through (`timeline.md`), and the plan documents those were derived
from — which no longer exist on disk.

**Plan paths below are historical.** Each resolves at the commit in its `commit` column, not in the working
tree: `git show <commit>:<path>`. That is the archive's whole deal — the reasoning survives, the pile does not.

## Boundary

- **covers**: every plan artefact that existed on disk at `<YYYY-MM-DD>`, from `<first plan date>`.
- **does not cover**: decisions recorded only in chat, review threads or meetings; anything before the first
  commit; plans already deleted before this archive ran, except where a record was carried forward.
- **format eras present**: `current-pdd`, `legacy-pdd`, `ad-hoc` — see the `format` column. Older plans predate
  the current schema and were summarised from whatever they actually said, not from what the schema expects.

## Coverage

| plan | format | first_commit | last_commit | decisions | status | deleted_in | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `plans/2026-09-auth` | current-pdd | `a1b2c3d` | `d4e5f6a` | D001 D002 D003 | deleted | `3c1f0ab` | superseded by the jobs plan |
| `.plan/2026-05-propositions.md` | legacy-pdd | `0918abc` | `0918abc` | D010 | deleted | `4d2e1f0` | proposition/proof-pair format |
| `plans/2026-11-pdd-rebuild` | current-pdd | `e1eff4b` | `4cf2220` | D020–D031 | in_flight | — | the current plan; not history yet |

`status` is one of:

| status | Meaning | Required |
| --- | --- | --- |
| `deleted` | summarised and removed | `deleted_in` names the commit, and the path is recoverable there |
| `archived` | summarised, still on disk | `note` says why it survived |
| `excluded` | deliberately not summarised | `note` gives the reason (template, vendored, generated, empty) |
| `in_flight` | current work, not history | `note` names the open task or branch |

`format`: `current-pdd` (a `PRD.md` and/or `TASKS.md`), `legacy-pdd` (an older PDD schema — propositions, proof
pairs, test sites, freeze files), or `ad-hoc` (a plan in all but name). The format never decides whether a plan
is in scope; it only decides what the reader should expect inside it.

## Eras

| era | date | one clause | decisions |
| --- | --- | --- | --- |
| E1 | 2026-09-14 | tasks carried their own propositions | D001 D002 D003 |
| E4 | 2026-11-14 | task classes derived from the requirement kind | D020 D022 D024 |

## Re-running

```bash
python3 <plugin>/skills/archive/scripts/find_plans.py .        # inventory; new plans appear here
python3 <plugin>/skills/archive/scripts/check_history.py .     # acceptance, coverage and deletion audit
```

A re-run **appends**: new `D`/`E` ids continue the sequence, existing rows are edited only when a newer plan
supersedes them (`references/decision-record.md` §4). Renumbering is never allowed — every task, commit message
and review that cites `D007` would silently start pointing at something else.
