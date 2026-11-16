---
name: archive
description: "Use when old plans must become one history document."
version: 1.0.1
author: Tsz Kin Lai (LaiTszKin), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [software-development, history, decisions, mermaid, cleanup]
    related_skills: [study, plan, decompose]
---

# Archive — from a pile of plans to one history

Plans decay: a `PRD.md` describes a decision that was reversed two plans later, an `AMENDMENTS.md` records the
reversal without saying why, and the reason lives in a commit message nobody reads. `pdd:archive` turns that
pile into one readable history — every decision with its reason, every phase of the project's evolution — and
then deletes the plan files, because `git` already keeps them and a superseded plan is worse than no plan.

Four phases, in the user's order:

| Phase | Who | Output |
| --- | --- | --- |
| 1. Discover and batch | main agent | the plan inventory, batched at **at most three plans per subagent** |
| 2. Summarise | one subagent per batch | decision records + evolution events, each with evidence |
| 3. Draw | main agent, after acceptance | `docs/history/` — mermaid diagrams of every evolution and every decision |
| 4. Delete | main agent, gate on coverage | the summarised plan files gone, recoverable from the commit recorded in the index |

## Definitions

| Term | Meaning |
| --- | --- |
| **plan** | One directory of plan artefacts: a `PRD.md` and/or `TASKS.md`, with `tasks/` and `AMENDMENTS.md` beside them. The unit that gets batched. A loose `notes.md` somewhere is not a plan. |
| **decision** | A choice that changed what gets built, who it is for, or how it is verified — with the alternative that was rejected. `D001`, `D002`, … Registration format in `references/decision-record.md`. |
| **evolution event** | A dated change of phase: what the project was doing before, what changed, which decisions drove it. `E1`, `E2`, … |
| **plan container** | A directory whose children are plans: `plans/`, `.plan/`, `docs/plan/`, `specs/`. The children may be directories or loose legacy documents — both are plans. |
| **format** | `current-pdd`, `legacy-pdd` (propositions, proof pairs, test sites, freeze files, numbered batches) or `ad-hoc`. **Format is never a filter**: an unfamiliar schema is exactly what the archive exists to summarise. |
| **coverage** | The property that every plan produced at least one record, and every record cites the plan it came from. Phase 4's gate is coverage, not effort. |

A comment, a task description and a code review note are not decisions. A decision has a before and an after:
*something was going to be built one way, and then it was built another way, for this reason.* If nothing was
rejected, it is a fact about the project, and facts belong in the timeline, not the register.

## When to use

- Plan directories have accumulated and the current PRD no longer explains why the system looks like this.
- A new collaborator (or a new session) needs the history rather than the archaeology.
- Old plans are about to be deleted, and their reasoning has to survive the deletion.
- Handoff: reconstructing what a live codebase does today is `pdd:study`; writing the next plan is `pdd:plan`.

## Preconditions

- The repository is a git repo and the plans are **tracked** — `git ls-files` shows them. An untracked plan that
  gets deleted is gone; it is reported, never deleted (`references/deletion.md` §3).
- `docs/` exists or can be created. The archive writes only under `docs/history/` and only deletes plan files.
- The plans are on disk, not only in history. A plan already deleted has no source to read; if `docs/history/`
  already records its decisions, they are carried forward as-is, not re-derived.

## Workflow

### 1. Discover, then batch at three

`python3 scripts/find_plans.py <project_root>` prints one row per plan: path, the artefacts it holds
(`PRD`, `TASKS`, `tasks/`, `AMENDMENTS`), first and last commit date, tracked or untracked, whether the current
workflow still references it, and whether `docs/history/index.md` already covers it.

Read that table before dispatching:

- **drop** plans a live document still points at as current work (an open `TASKS.md` with unfinished tasks is
  work in flight, not history);
- **keep untracked** plans out of the deletion set but still in the summary if their content matters — the
  summary is reversible, the deletion is not;
- **mark already-covered** plans as skip, unless their content changed since the recorded commit.

Batches hold **at most three plans**, and the number of subagents is `ceil(n / 3)`. Three is a ceiling, not a
target: a plan with a long `AMENDMENTS.md` gets a batch of one.

Batching is contiguous in chronological order — plans that superseded each other stay in the same batch, so one
reader sees the reversal and its cause. A batch boundary between a decision and its reversal produces two
records that contradict each other, and the main agent has to reconstruct what one subagent would have seen.

### 2. Summarise — one subagent per batch

Each subagent is read-only and produces records, not prose. Its brief is in `references/subagent-brief.md`; the
record shapes are in `references/decision-record.md`. Per batch it reports:

- **decision records**: statement, the alternative rejected, the reason, the evidence (`path:line`), the date,
  the plan it came from, and what superseded it if anything did;
- **evolution events**: date, phase before, what changed, the decisions that drove it;
- **conflicts**: two plans deciding the same subject differently. It emits **one** record — the newest — with the
  older claim in its `conflict:` field, and reports the collapse; the report is the only trace of what was
  overwritten;
- **plans it could not date**: a plan with no date in the file and no commit date to fall back on.

Three rules make the summary trustworthy:

1. **A decision needs its rejected alternative.** "We use a task queue" is a fact. "We use a task queue instead
   of running jobs inline, because inline jobs made the request path block for the whole job" is a decision.
2. **Quote, then cite.** The reason goes in the record as the plan wrote it, with `path:line`; a paraphrase
   without a citation cannot be checked and will be rejected in phase 3.
3. **Do not invent a period.** `E1` is a change you can date from the files or the commits. A plan with no date
   gets `undated` and an empty `E` cell, which is honest; a guessed month is not.

### 3. Draw — the main agent writes `docs/history/`

A subagent's summary is not the deliverable and its report is not acceptance. The main agent re-opens every
cited `path:line`, collapses each conflict to its newest record while reporting what was overwritten (a reversal
with no recorded reason is a finding to report, not a record to invent), then writes:

```
docs/history/index.md       what was archived, from which plans, at which commits, and how to re-run
docs/history/timeline.md    one mermaid timeline of the evolution + one era flowchart per phase change
docs/history/decisions.md   the decision register table + one mermaid decision graph
docs/history/eras/NN-<slug>.md   per-era detail, only when decisions.md would pass ~300 lines
```

Diagram shapes and the conventions they must obey are in `references/history-diagrams.md`; the copy-paste
sources are `pdd:study`'s `references/mermaid-templates.md` (§1 flowchart, §2 sequence, §3 state, §6
requirement, §12 timeline in the standalone library). Two hard rules:

- **every decision in the register appears exactly once in the decision graph**, as a node labelled `D0nn`, and
  every node in the graph has a row; the checker compares the two sets;
- **every era in the timeline names the decisions that drove it**, so a reader can walk history → decision →
  evidence without reading the plans (which by then no longer exist).

Each decision's table row carries the evidence citation and the source plan path. After phase 4 those paths are
deleted, and the row becomes the pointer of record — which is why the citation is to a `path:line` **and** a
commit hash: the commit is what still resolves after the file is gone.

### 4. Delete — gated on coverage

Only after `docs/history/` is accepted, and only what is covered. The full procedure is
`references/deletion.md`; the parts that must not be improvised:

1. **Coverage gate.** `python3 scripts/check_history.py <project_root>` must report every plan as covered, and
   zero unresolved conflicts — every disagreement already collapsed into its newest record. A plan with no record is either summarised properly or excluded from the
   deletion set, with the reason written in `index.md`.
2. **Reference sweep.** `grep -rn '<plan path>' --include='*.md'` outside `docs/history/` — a live document that
   still sends a reader to a plan about to disappear is a broken link. Fix the reference first (point it at
   `docs/history/decisions.md`), then delete.
3. **Tracked only.** `git rm -r` a plan only if `git ls-files` lists it. An untracked plan is moved nowhere and
   deleted never — it is reported to the user as unrecoverable-by-git and left alone.
4. **One commit per plan**, naming the decision ids it produced: `archive(crates/api): drop 2026-09 plan (D001
   D002 D003)`. A deletion commit that does not name what survived it is indistinguishable from an accident.
5. **Verify recoverability, not intent.** For each deleted path, `git cat-file -e <recorded-commit>:<path>`
   must succeed, and `git log --diff-filter=D --name-only -1` must list exactly the deleted paths.

The index is the audit trail: per plan, its path, its last commit, the commit that deleted it, and the decision
ids it produced. That row is what makes "we deleted it and git has it" a fact rather than a hope.

## Acceptance

Mechanical (`scripts/check_history.py <project_root>`, exit 0):

- every discovered plan is either covered by a record or listed as excluded with a reason;
- every decision row has an id, a date or `undated`, a reason, a `path:line` citation, a source plan and a status;
- every decision id appears exactly once in the decision graph, and the graph has no unregistered node;
- the timeline has one entry per era, and each era names at least one decision;
- `docs/history/index.md` lists every plan with its deletion commit, and every deletion commit exists in `git log`;
- no remaining tracked file references a deleted plan path.

Judgement (read by the main agent):

- [ ] every record has a rejected alternative, or the item was demoted to a timeline fact;
- [ ] every reason is quoted from a plan or a commit message, not reconstructed from the code;
- [ ] a conflict between two records left exactly one row — the newest — with the older claim cited inside it;
- [ ] an undated plan is marked `undated` rather than assigned a plausible date;
- [ ] the diagrams read as history — a reader can answer "why is this queue here" from `docs/history/` alone;
- [ ] nothing was deleted before its coverage row existed in the index;
- [ ] `git status --short` after the run is clean, and `git log --diff-filter=D` shows only plan paths.

## Decision rules

| Situation | Rule | Reason |
| --- | --- | --- |
| A plan is still referenced by an open task | Not history: exclude it, keep it | Deleting the plan a task cites turns the task's own contract into a dangling path |
| Two plans disagree | **Keep the newest record only.** The older claim becomes a pointer inside it, and the conflict is reported | A register that argues with itself cannot answer "why does this exist"; the newest position is the position of record, and the older one stays reachable through `supersedes` and git |
| A decision's reason is only in a commit message | Cite the commit (`<sha> — <subject>`) | Commit messages are the one place reasons survive a deleted plan |
| A plan produced no decision | Give it a timeline entry and no `D` row | Most plans confirm an approach; conflating confirmation with change inflates the register |
| The same decision appears in three plans | One record, `first seen` + `restated in` list | Three rows for one decision makes the graph unreadable and the count meaningless |
| A plan is untracked | Summarise if useful, never delete, report it | `git` cannot recover it; the deletion is irreversible |
| History is longer than the plans on disk | Cover what exists; note the earlier gap in `index.md` | An archive that claims total coverage it cannot support is worse than one that names its boundary |
| A plan is in an older or alien format | Include it, classify the format in the index, and read it for assertions | Old-format documents are the ones no current agent can read, which is precisely why they need archiving |
| `docs/history/` already exists | Extend it: append eras and decisions, never renumber | Ids are quoted by tasks, commits and reviews; renumbering breaks every one of them |

## Pitfalls

- **A summary that is a chronology of tasks.** "T01 built the parser" is a work log, not history → the register
  holds choices and their rejected alternatives; tasks are evidence for them.
- **Reasons reconstructed from the code.** Reading the implementation and inferring why it looks like that
  produces a plausible story with no author. Cite the plan or the commit, or mark the reason unknown.
- **Skipping a plan because its format is unfamiliar.** The excluded plan is usually the oldest one, which is
  the one whose reasoning exists nowhere else → classify the format and summarise by assertion.
- **A cell containing a literal `|`.** `check_history.py` splits a register row on `|` without honouring escapes, so a `\|` inside `decided` or `because` still splits the row and the row drops out of the register entirely — the conflict rule, the graph agreement and the id-for-id accounting all stop seeing it (a 528-row register parsed as 523, with only the missing ids to show for it) → strip the character when emitting cells; backslash-escaping does not work, and the checker reports the cell count and names this cause.
- **`--render` as root.** `mmdc` launches Chrome with no `--no-sandbox`, which fails when the process runs as root and reports the failure once per block — indistinguishable from a mermaid syntax error. `check_history.py` now passes `{"args":["--no-sandbox","--disable-setuid-sandbox"]}` as a puppeteer config whenever `geteuid() == 0`, so a render failure on a root box is a real syntax error; a manual `mmdc` run still needs the same config.
- **A register that keeps both sides of a conflict.** Two rows assert different rules and every reader has to
  decide which to believe → the newest record wins, the older claim survives only as a pointer inside it, and the
  replacement is cited so the change is auditable.
- **Batches split across a supersession.** The decision in batch 1, its reversal in batch 2, and neither
  subagent can see it → contiguous chronological batching.
- **Deleting before the coverage gate.** The plans are the only evidence; deleting first and summarising second
  means the summary is written from whatever the subagent still remembers.
- **Deleting an untracked plan.** Git cannot recover it, and the acceptance criterion the skill promised
  ("git has it") is false.
- **A deletion commit with no ids.** Later nobody can tell which decisions depended on the deleted plan, so no
  one dares remove a surviving artefact that only that plan justified.
- **Renumbering on a re-run.** `D007` becomes `D004`, and every task, commit message and review that cited
  `D007` now points at a different decision.
- **The archive becomes the new plan pile.** `docs/history/` grows per-era files with no index → the index is
  the entry point and the only file a re-run updates first.

## Verification

- [ ] `scripts/find_plans.py` was run, and its inventory matches what was batched (`ceil(n/3)` batches, ≤3 each);
- [ ] every subagent report was checked against the plans by the main agent, citation by citation;
- [ ] `scripts/check_history.py` exits 0 after phase 3 and again after phase 4;
- [ ] every mermaid block renders (`check_agents_md.py --render` from `pdd:study`, or `mermaid-cli` directly);
- [ ] every deleted path is recoverable at the commit named in the index;
- [ ] `git log --diff-filter=D --name-only` lists only plan paths, and `git status --short` is clean.

> Cross-skill references name the sibling skill and the file separately:
> `skill_view("pdd:study", "references/mermaid-templates.md")`. Every sibling is registered under this
> plugin's namespace, so the skill argument always carries the `pdd:` prefix.

## References

- `references/plan-discovery.md` — what counts as a plan, how the inventory is built, what to exclude.
- `references/decision-record.md` — the record schema, what qualifies as a decision, dating, status.
- `references/history-diagrams.md` — timeline, era flowchart and decision graph: shapes and conventions.
- `references/subagent-brief.md` — the brief the main agent sends, and the report it demands back.
- `references/deletion.md` — the delete step: coverage gate, reference sweep, tracked-only rule, verification.
- `assets/HISTORY.md` — the `docs/history/index.md` template.
- `scripts/find_plans.py` — inventory and batching input.
- `scripts/check_history.py` — acceptance: coverage, graph/register agreement, deletion audit.
