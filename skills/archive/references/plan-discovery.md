# Finding the plans

The inventory decides everything downstream: which batches exist, what may be deleted, and how honest the
archive's coverage claim is. The commands in `SKILL.md` §1 build the first draft; the main agent corrects it.

## 1. What counts as a plan

A **plan** is a directory of plan artefacts, usually produced by `pdd:plan` and `pdd:decompose`:

| Artefact | What it contributes to the archive |
| --- | --- |
| `PRD.md` | the requirement as stated at the time: the behaviour, the boundaries, the `REQ-F`/`REQ-A` split |
| `TASKS.md` | the dispatch order and the gates: what the plan believed had to happen first |
| `tasks/*.md` | evidence for what each task actually owned — rarely a decision, often the citation for one |
| `AMENDMENTS.md` | **the richest file in the archive**: dated amendments are decisions with a reason attached |
| `DESIGN.md`, `NOTES.md`, `*-proposal.md` | a plan in all but name when they sit in a plan directory |

### 1.1 Formats are not a filter

Plan artefacts in a real repository come in every shape, and the older ones are exactly what an archive is for.
A `.plan/` directory holding loose documents, a single `docs/plan/2025-q3.md`, a `PROPOSITIONS.md` with proof
pairs, a `FREEZE.md`, a directory whose `TASKS.md` predates the current schema — all of it is **in scope**. The
inventory classifies the format, it never excludes on format:

| `format` | What it looks like | How to read it |
| --- | --- | --- |
| `current-pdd` | `PRD.md` + `TASKS.md` + `tasks/` + `AMENDMENTS.md` | as the current workflow defines them |
| `legacy-pdd` | propositions, proof pairs, test sites, freeze lists, numbered batches, `SPEC*.md` | by what each document asserts, not by the schema it half-follows |
| `ad-hoc` | a plan in all but name: `notes.md`, a proposal, a decision memo | quote the sentence that states the choice |
| `unknown` | unreadable, truncated, binary, or an empty directory | report it; a coverage gap blocks its deletion |

Three rules follow, and they are what keeps the archive honest when the old schema is unfamiliar:

1. **Read for assertions, not for structure.** An old-format document may have no "Decision" heading; the
   decision is the sentence that says what will be done and what will not.
2. **Map its concepts; do not import its vocabulary.** A proposition is a claim about behaviour (usually a
   `D` record when it replaced another, a timeline fact when it did not). A proof pair or a test site is an
   acceptance decision. A freeze list is a scope decision. The register speaks the current taxonomy either way.
3. **Say which format it was.** `index.md` has a `format` column; a reader who knows `legacy-pdd` will not expect
   the citations to look like today's.

Signals that a directory is *not* a plan, even when it holds a `PRD.md`:

- it is the current, in-flight plan: `TASKS.md` lists unfinished work, or the working branch names one of its
  task ids;
- it is a template or an example: `assets/PRD.md`, `templates/`, a fixture tree under `tests/`;
- it is a vendored copy: `node_modules/`, `vendor/`, `third_party/`.

The script reports `in_flight` and `template` candidates so the main agent can exclude them deliberately rather
than by accident.

## 2. The inventory columns

One row per candidate, from the four commands in `SKILL.md` §1:

| Column | Meaning | Why it matters |
| --- | --- | --- |
| `path` | plan directory | the batching unit and the deletion unit |
| `artefacts` | `PRD;TASKS;tasks/;AMENDMENTS` | tells the subagent what to read first |
| `prd_lines`, `amendments` | size and how many dated amendments | an `AMENDMENTS.md` with nine entries is usually its own batch |
| `first_commit`, `last_commit` | the date range git knows | dating evidence when no file states a date |
| `tracked` | `yes` / `no` | untracked plans are never deleted |
| `covered` | `yes` when `docs/history/` already cites the path | re-runs skip covered plans |
| `flags` | `in_flight`, `template`, `no-date`, `empty` | exclusions and report lines |

Two of those columns decide the work: `amendments` (how much there is to read) and `tracked` (whether phase 4
may touch it at all).

## 3. Batching

- **At most three plans per subagent**, contiguous in `first_commit` order. `ceil(n / 3)` batches.
- Three is a ceiling, not a target. A plan with eight amendments gets a batch of one, because a reader that
  skims the amendments produces a summary of the PRD it already understood.
- **Never split a supersession.** If plan B's `AMENDMENTS.md` cites plan A, they belong in one batch; the reader
  who sees only the reversal writes a record with no cause.
- **Order the batches earliest first.** Later batches then inherit the record ids they need to say
  "supersedes D004" instead of inventing a new id for a decision that already exists.
- **Covered plans are not re-summarised** unless `git diff <covered-commit>..HEAD -- <path>` shows they changed.

The batch plan goes into the run ledger, because the coverage claim in `docs/history/index.md` is a comparison
against it, not an impression:

```
batch 1: plans/2026-09-auth/ plans/2026-09-jobs/            → subagent A
batch 2: plans/2026-10-jobs-v2/ plans/2026-10-billing/      → subagent B
batch 3: plans/2026-11-pdd-rebuild/                          → subagent C  (8 amendments: alone)
```

## 4. Reading order inside one plan

Give the subagent an order, or it reads the PRD, decides it understands the project, and skims the rest:

1. `AMENDMENTS.md` — dated, and each entry is a decision with a cause.
2. `PRD.md` — the requirement as last stated.
3. `TASKS.md` — what the plan thought had to happen first, and which gates it declared.
4. `tasks/*.md` — only to resolve a citation, never to derive a decision.

Plan order matters more than file order: read the earliest plan's PRD before the latest plan's amendments, or
the reader evaluates the old decision against today's understanding and records a reversal that never happened.

## 5. What the inventory cannot tell you

- **Plans that were never committed.** No dates, no history, and deletion is irreversible — the script flags
  them, and `references/deletion.md` §3 forbids deleting them.
- **Plans that predate the repository.** "Since the records begin" starts at the first commit; a boundary that begins later
  belongs in `index.md` as a stated limit, not as total coverage.
- **Decisions made in chat, in a review, or in a meeting.** No artefact, no evidence — they are out of scope,
  and mentioning them in the archive requires a citation the archive does not have.
- **Whether a plan was superseded.** A later plan that neither cites the earlier one nor amends it may be a
  parallel branch, not a successor. The record says `relationship unknown` and the main agent reports it.
