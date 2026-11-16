# The decision record

A record is worth writing when it would let a reader predict what the project would have done differently. The
test is the **rejected alternative**: if nothing was rejected, nothing was decided.

## 1. What qualifies

| Qualifies | Does not qualify |
| --- | --- |
| a technology, library or protocol chosen over a named alternative | "we use TypeScript" (no alternative was considered, or none is recorded) |
| a boundary moved: what the system owns vs delegates | a refactor that preserved every boundary |
| a task class changed: a migration reclassified as construction | "T03 was implemented" (that is a work log) |
| an acceptance criterion replaced, or a gate added/removed | a test added under an existing criterion |
| a scope deleted from the plan, with its replacement | scope deferred to "later" with no successor |
| a pricing, governance or policy position reversed | a position restated unchanged in a new document |
| an architecture rule declared (`REQ-A`) with a check that enforces it | an aspiration nobody checks — a timeline fact |

Two consequences worth stating, because they are where the register bloats:

- **A restatement is not a decision.** The same choice appearing in plan A, plan B and a design doc is one
  record with `restated in` listing all three. Three rows for one decision make the graph unreadable and the
  count meaningless.
- **A confirmation is not a decision.** Most plans confirm an approach and change nothing. Those get a timeline
  entry and no `D` row.

## 1b. Pasting a subagent's paste-ready blocks — stop at the section, not at the next id

A summary pass returns blocks as `### D557 — …` followed by one report layout: the records, then the register rows,
then the era, then the conflicts. A parser that splits on `\n### (D\d+) — ` and reads fields to the next match
**swallows every section after the LAST record into that record**, because the last block has no next `### ` to stop
at. The damage is silent and survives a field-shape check: the fields are all legal, they are just the wrong ones —
a decision gains a `before`/`after`/`driven by`, inherits the era's `cost accepted`, and can take a *date* from the
era header. It cannot be seen by reading the row; it shows up only when a block is read whole.

Two rules:

- cut each block at `\n### ` **or** at `\n## ` — whichever comes first — before parsing fields;
- after writing the era files, assert that no `###` block contains `before`, `after` or `driven by`, and that exactly
  one `date` appears per block. That check is three lines and it catches the whole class.

## 2. The record

```markdown
### D004 — task classes derived from the requirement kind, not from the action

- **date**: 2026-11-14
- **subject**: task-classification  # short slug naming the thing decided; two accepted rows may never share one
- **status**: accepted            # accepted | superseded | unknown
- **decided**: each task's class is derived from its requirement's kind (`REQ-F` → construction + verification A;
  `REQ-A` → migration/removal + verification C), not from the verb in the task title.
- **rejected**: classifying by action verb ("refactor" → migration). Rejected because the same verb covers both
  a behaviour change and a pure move, so the acceptance object — the thing the class exists to type — stays
  undecided.
- **because**: "The parenthesis in the third column is the real boundary of the classification: `REQ-A` decides
  the acceptance object (the code obeys the architecture), not the action." — `plans/2026-11-pdd-rebuild/PRD.md:118`
- **supersedes**: D002 (task classes by file count)
- **source**: `plans/2026-11-pdd-rebuild/AMENDMENTS.md:7`
- **commit**: `e1eff4b`            # the commit that still holds the evidence after the plan is deleted
- **eras**: E5
```

Field rules:

| Field | Rule |
| --- | --- |
| `id` | `D001`, stable forever. Re-runs append; they never renumber. |
| `subject` | a short slug naming *what* was decided (`retry-cap`, `task-classification`). Two **accepted** rows may never share a subject — that is exactly the conflict rule in §4, and the checker enforces it. |
| `date` | from the file if it states one, else the plan's `last_commit` date, else `undated`. Never a guess. |
| `status` | `accepted` (still governs) or `superseded` (a later record replaces it; name it in `superseded by`) or `unknown` (the plan asserts a choice, the current code disagrees, and nothing records the reversal). There is no `contested` status: a conflict is resolved, not preserved — §4. |
| `decided` | one sentence, present tense, about the project — not about the document |
| `rejected` | the alternative, with the reason it lost. This field is what makes the record history rather than documentation. |
| `because` | **quoted**, with `path:line`. A paraphrase is not evidence. |
| `supersedes` / `superseded by` | ids, both directions filled in once known |
| `source` | the plan file and line the record came from |
| `commit` | the commit that will still hold the evidence after deletion — the citation of record |
| `eras` | which evolution events this decision caused or belongs to |

### 2.1 The register table in `decisions.md`

The per-record blocks are the evidence; the register is the index a reader scans. Eleven columns, in this order:

| id | subject | date | status | decided | rejected | because (quoted) | evidence | source | commit | eras |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `D004` | `task-classification` | 2026-11-14 | accepted | class from requirement kind | class by action verb | "`REQ-A` decides the acceptance object, not the action" | `PRD.md:118` | `plans/2026-11-pdd-rebuild` | `e1eff4b` | E4 E5 |

- **one row per subject**, and the row is the newest claim (§4). A superseded claim is `supersedes:` text inside
  the newest row's `rejected`/`because` field, not a second row.
- **`because (quoted)` must contain quotation marks** and a `path:line` (or a commit sha). The checker accepts
  neither a paraphrase nor an empty cell.
- **`evidence`** is the `path:line` inside the plan; **`source`** is the plan path; **`commit`** is what still
  resolves after the plan is deleted. All three are required, because they fail in different ways: a wrong line,
  a moved plan, a rewritten history.
- **`date`** is `YYYY-MM-DD` or `undated`. `undated` rows sort last and lose every conflict (§4).
- The detailed block for each id lives below the table, or in `eras/NN-<slug>.md` when the table grows past a
  screen. The table is what `check_history.py` parses; the blocks are what a human reads.

## 3. Dating

Three sources, in order of authority:

1. **a date in the file** — an amendment line, a "Decided on" heading, a changelog entry;
2. **the commit that added the passage** — `git log -S '<quoted phrase>' --format='%h %ad %s' --date=short --
   <path>` finds when a sentence appeared, which is usually when the decision was made;
3. **the plan's `last_commit`** — a lower bound on when the decision existed, never the decision's date.

If none applies, `undated`. An archive with twelve `undated` records and honest citations is more useful than
one with plausible months and no source, because the first can be improved and the second cannot be trusted.

## 4. Supersession and conflict — the newest record wins

When two sources decide the same thing differently, **only the newest record survives as a row.** The archive
states the latest position; it does not host a debate.

- **Superseded** (the normal case): a later plan changes the earlier decision. One row per subject — the newest.
  The replaced claim lives inside it:

  ```
  - **supersedes**: D004 (2026-11-14) "classes by file count" — `plans/2026-09-auth/PRD.md:31`
  ```

  `D004` keeps its id and its row only if it decided something *else* as well; if it decided only this subject,
  it collapses into the pointer and the graph carries a single node. Nothing is lost: `git` holds the old text,
  and the pointer names the commit.

- **Conflict** (no plan records which won): the newest claim is the record of record, the older claim is cited
  inside it with the phrase `conflict:`, and the main agent **reports** the disagreement. The report is what
  makes the collapse auditable — a reader can check whether the newer plan had the authority to change it, which
  is the one question the archive cannot answer for them.

  ```
  - **conflict**: plans/2026-10-billing/AMENDMENTS.md:12 caps retries at 3 (2026-10-22) while
    plans/2026-10-jobs-v2/PRD.md:71 leaves them unbounded (2026-10-09); newest kept, nothing recorded a reversal
  ```

- **Ordering is by date, and `undated` loses.** An undated claim never displaces a dated one; it is kept only if
  no dated claim covers the subject, and it is marked `undated` so a later pass can replace it. Two undated
  claims on one subject: keep the one whose plan has the later `last_commit`, and say which rule was applied.

- **Unknown**: the plan states a decision and the current code does the opposite, with no later plan in
  between. `status: unknown` plus both citations, and it is reported — it means a decision was made somewhere
  the archive cannot see.

Why collapse rather than keep both: a reader arriving at `decisions.md` wants the rule that holds today and the
reason for it. Two rows that contradict each other either make the register unusable or make the reader the
arbiter, and the older claim is never more than a `git show` away.

## 5. The evolution event

An `E` record is a phase change, not a release. It needs a date, a before, an after, and at least one decision:

```markdown
### E3 — verification moved from per-task tests to per-flow modelling

- **date**: 2026-10-30
- **before**: every task carried its own assertion file; the suite grew with the task count
- **after**: one model per business flow, falsified once; tasks are accepted against the flow's model
- **driven by**: D007 (flow as the unit of modelling), D009 (property-based generation over example tables)
- **evidence**: `plans/2026-10-jobs-v2/PRD.md:44`, `plans/2026-10-jobs-v2/AMENDMENTS.md:19`
- **cost accepted**: composition between flows is no longer modelled (recorded in D007's `because`)
```

`before`/`after` are one clause each. An era with three paragraphs of `before` is a summary of a plan, not a
phase change, and the timeline diagram cannot render it.

## 6. Report format

Per batch, the subagent reports in this order, and the main agent reads it against the plans:

```
batch:           1 (plans/2026-09-auth, plans/2026-09-jobs)
decisions:       5 records (D001..D005), 1 demoted to a timeline fact
eras:            2 (E1, E2)
undated:         1 (plans/2026-09-auth has no date in file and one commit)
conflicts:       1 — retry cap: unbounded (jobs/PRD.md:71, 2026-10-09) vs capped at 3
                 (jobs-v2/AMENDMENTS.md:12, 2026-10-22); newest kept, older cited in `conflict:`
commits:         every record carries the commit that will still resolve after deletion
plans without decisions: none
```

The `conflicts` line is the most valuable output of the whole phase. Everything else reconstructs what the
project believed; that line says where the record was overwritten, and by what, so a reader can judge whether the
newer plan had the standing to overwrite it. Report every conflict even though the register keeps only the newest
claim — the collapse is silent by design, and the report is the only place it becomes visible.
