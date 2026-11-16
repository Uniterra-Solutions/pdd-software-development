# pdd-software-development

A Hermes plugin that ships **Proposition-Driven Development (PDD)** as five bundled skills, plus three
companions: one maps what the code does today, one retires the plans that no longer do, and one repairs
the skills themselves when the process misfires.

PDD is a business-first spec workflow: the PRD describes business logic and observable behaviour,
decomposition yields four classes of task, and verification is modelled per business flow rather
than per task. `pdd:study` reconstructs the branches a codebase already has, with citations, before
anything is planned against them; `pdd:archive` turns a pile of superseded plans into one history of
decisions and eras, then deletes the pile — the reasoning survives, the archaeology does not.

A third companion closes the loop on the process. `pdd:report` is used when a skill misfired — a step
was followed and the result was wrong, a gate passed something it should have caught, a script reported
success it did not achieve. The incident is not the deliverable: one abstract anti-pattern and one
class of change to the process are.

## Install

```bash
hermes plugins install Uniterra-Solutions/pdd-software-development --enable
```

Or from a local checkout:

```bash
hermes plugins install <path>/pdd-software-development --enable
```

## Skills

Registered with the plugin namespace, so a bare `skill_view("pdd:plan")` still resolves to any
same-named skill on disk — call the qualified name:

| Qualified name | What it does |
| --- | --- |
| `pdd:plan` | Write the PRD: business model, one behaviour section per flow, `REQ-F` / `REQ-A` |
| `pdd:decompose` | Turn the PRD into four classes of task (construction / verification / migration / removal), one DAG, two gates, then audit the cut's scope and acceptance criteria with one read-only auditor per three tasks |
| `pdd:implement` | Dispatch the DAG batch by batch, accept each task by its class, merge the batch back into the recorded working branch, close its worktrees, stop on contradiction |
| `pdd:review` | Read PRD + tasks, write a review DAG, dispatch two reviewer types, synthesise findings |
| `pdd:explain` | Explain a plan to a non-engineer without inventing claims |
| `pdd:study` | Companion: one read-only subagent per workspace member or package root reconstructs every business branch, its trigger and its selection path, and writes the result as a per-directory `AGENTS.md`; the main agent re-resolves every citation and indexes them all in the root `AGENTS.md`. When the knowledge base already exists it runs as a delta: every commit since each file's recorded commit is diffed, the changed paths are sorted by the unit that owns them, and one subagent per affected unit rewrites only the rows whose evidence moved |
| `pdd:report` | Companion: when the process itself misfired — a skill was followed and the result was wrong, a step was skipped, a script reported success it did not achieve. Traces the incident to the guideline that produced it (quoted, with file and line), extracts one abstract anti-pattern with six fields, then picks exactly one class of change (prompt / information / code / process, with the process change carrying the argument against the cheaper fix), applies it in the same session, and writes the report to `docs/retro/` with a regression criterion |
| `pdd:archive` | Companion: subagents read at most three plans each (any era, any format) and return decision records with the rejected alternative and the quoted reason; the main agent draws every era and every decision in `docs/history/`, then deletes the summarised plans — recoverable from the commits the index names |

```
skill_view("pdd:decompose")
skill_view("pdd:decompose", "references/task-verification.md")
```

## The recommended flow

Five steps, in this order. Two of them are conditional, and the conditions are properties of the work
rather than matters of preference.

| # | Step | What it settles | Required |
| --- | --- | --- | --- |
| 1 | `pdd:plan` | The behaviour the change must have — one section per flow, `REQ-F` / `REQ-A` — before a single task exists | yes |
| 2 | `pdd:decompose` | The four task classes, one dependency graph, the two gates, and an audit of the cut's scope and acceptance criteria | yes |
| 3 | `pdd:explain` | Whether the plan as a whole can be followed by someone who will never read the code | **optional** — the comprehension check |
| 4 | `pdd:implement` | The build: batch by batch, every task accepted by its class, each batch merged back into the recorded branch | yes |
| 5 | `pdd:review` | An independent reading of the PRD and the tasks, against the delivered diff | **optional** — see below |

The companions sit outside the chain: `pdd:study` runs before step 1 when the codebase has no map,
`pdd:archive` runs after step 5 when the plan is retired, and `pdd:report` runs whenever a step misfires.

### Step 3 — why `explain` sits before `implement`

`explain` is written for readers who are not software engineers. It converts the plan into pure logical
inference — what follows from what, and what would have to be true for each step to hold — so that
knowledge from another field can be applied to this one without first acquiring the implementation
vocabulary.

Run it when the plan is large enough that you are not certain you understand the whole of it. If the
explanation cannot be followed without a claim that is not already in the plan, the plan has a gap, and
finding it here costs nothing next to finding it in the diff.

Its output is not a summary for a stakeholder; it is a test of the plan's internal sufficiency, addressed
to a reader who reasons logically and takes nothing on trust.

### Step 5 — when `review` is worth its cost

Review is a second, independent reading of the same plan by an agent that did not write it. That is worth
paying for when the change is complex: several flows interacting, an architecture constraint to honour, a
migration, or a deletion whose blast radius is not obvious.

It is usually not worth paying for a refactor whose behaviour is meant to be unchanged and whose test
safety net is adequate. The suite already states what must stay true; a reviewer would add a second opinion
on a question the tests answer mechanically. The same holds for a change small enough to read in one
screen.

The judgement is the complexity of the change, not the length of the task list: ten mechanical renames
carry less reviewable risk than one altered state machine.

## Why `pdd:report` exists

A method that edits itself needs the same evidence discipline it demands of code. Every change to a
skill therefore carries three things a reviewer can check without re-running the session:

- **the guideline it answers**, quoted with file and line, so the fix lands where the mistake was
  caused rather than where it was noticed;
- **one abstract anti-pattern** with the reason the wrong action looked right, so the reviewer can tell
  whether the class of failure was understood or only this instance;
- **a regression criterion** naming what observable thing will differ next time, so "fixed" is a claim
  someone else can falsify.

Reports live in `docs/retro/` beside an `ANTI-PATTERNS.md` index; ids are never reused. What the first
round of reports taught is generalised into `skills/report/references/gate-discipline.md` — five rules for
knowing whether a green run means anything — and every skill here whose verification section runs a
checker points at it.

Its last step publishes: the tracker is searched for the mechanism first, and a match receives a comment on
the existing issue rather than a twin; the body is scrubbed of every project and person before it leaves the
machine, and `scripts/check_issue.py` holds that boundary mechanically — absolute paths, emails, IPs,
non-GitHub URLs, bare revisions, deny words, and the redaction line that says what was removed.

The same skill ships in `tidy-up-your-thoughts` as `tidy-up-your-thoughts:report`, writing to the thought
topic instead. Its purpose in both places is the same: an agent that can repair its own process is only safe
while the repair is reviewable, and reviewable means the reasoning, the change and the test are all on
disk before the next session starts.

## What "bundled" buys you

- These skills live in the plugin registry, **not** in `~/.hermes/skills/`. They are read-only and
  cannot be edited by `skill_manage`, by the curator, or by a background review pass.
- They still appear in `skills_list` and in the system prompt's `<available_skills>` index while
  the plugin is enabled, under their qualified names.
- Disabling the plugin removes them from the index without deleting anything.

## Design philosophy

The process is built on one asymmetry: the cost of writing a change has collapsed, while the cost of
verifying one has not. Every design decision follows from choosing evidence, not throughput, as the binding
constraint — acceptance is typed, tasks are classified by acceptance object, and the unit of modelling is the
business flow.

Read [DESIGN.md](DESIGN.md) for the full argument: the bounded-step falsification thesis, the four task
classes and where they come from, the three shapes of verification (modelling / behavioural guard /
architecture check), the two gates, and the costs the process accepts.

## Requirements

- Hermes Agent with plugin support (`hermes plugins doctor .` should pass).
- Python 3.10+ (the plugin itself has no third-party dependencies).
- `pdd:implement/scripts/mutate_check.py` and the three `pdd:study` scripts need a working Python
  interpreter and are invoked by the skills, not by the plugin loader.
- `pdd:study --render` optionally shells out to `mmdc` or `npx @mermaid-js/mermaid-cli`; without one,
  the mermaid check falls back to a lint and says so.

## Layout

```
plugin.yaml            manifest (name: pdd)
__init__.py            register(ctx) -> ctx.register_skill() per skill directory
skills/plan/           SKILL.md + assets/
skills/decompose/      SKILL.md + assets/ + references/
skills/implement/      SKILL.md + references/ + scripts/mutate_check.py
skills/review/         SKILL.md + references/
skills/explain/        SKILL.md + assets/ + references/
skills/study/          SKILL.md + assets/ + references/ + scripts/  (list_members, check_agents_md, study_delta)
skills/archive/        SKILL.md + assets/ + references/ + scripts/  (find_plans, check_history)
```

## Versioning

`plugin.yaml` version tracks the skill set as a whole. Each `SKILL.md` carries its own version in
frontmatter; they move independently when a single skill changes.

## Licence

MIT — see [LICENSE](LICENSE). © 2026 Uniterra Solutions Ltd.
