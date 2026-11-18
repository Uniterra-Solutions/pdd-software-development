# pdd-software-development

A Hermes plugin that ships **Proposition-Driven Development (PDD)** as five bundled skills, plus four
companions: one maps what the code does today, one retires the plans that no longer do, one turns a known
failure with an unknown trigger into a machine-found one, and one repairs the skills themselves when the
process misfires.

PDD is a business-first spec workflow: the PRD describes business logic and observable behaviour,
decomposition yields four classes of task, and verification exhausts each operation's decision table to a
declared interaction strength rather than sampling a flow or accumulating a test per task. `pdd:study` reconstructs the branches a codebase already has, with citations, before
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
| `pdd:implement` | Dispatch the batch, accept each unit against the plan's own standard, merge it back into the recorded working branch and close its worktree before the next opens. Two entries: the `TASKS.md` DAG batch by batch, accepted by class; or — with no tasks — one PRD flow the dispatcher cuts into slices itself, accepted against the `REQ-F` each serves, promoted back to `pdd:decompose` the moment the work stops being small |
| `pdd:reproduce` | Companion: a known failure with an unknown trigger becomes a bounded search — fingerprint, discriminating oracle, declared space, graded objective, cheapest-first search, shrink, double-sided proof, pin, and the answer to why the defect needed a search at all |
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
rather than matters of preference. Step 0 below is not a skill call but a precondition, and it pays for
itself whenever the change binds to an external framework.

| # | Step | What it settles | Required |
| --- | --- | --- | --- |
| 1 | `pdd:plan` | The behaviour the change must have — one section per flow, `REQ-F` / `REQ-A` — before a single task exists | yes |
| 2 | `pdd:decompose` | The four task classes, one dependency graph, the two gates, and an audit of the cut's scope and acceptance criteria | **conditional** — a multi-behaviour or architectural change needs it; a PRD naming one flow goes straight to `pdd:implement`, which cuts the slices for that one dispatch and persists none |
| 3 | `pdd:explain` | Whether the plan as a whole can be followed by someone who will never read the code | **optional** — the comprehension check |
| 4 | `pdd:implement` | The build: batch by batch, every task accepted by its class — or, with no tasks, one flow cut into slices and accepted against the requirement each serves — each batch merged back into the recorded branch | yes |
| 5 | `pdd:review` | An independent reading of the PRD and the tasks, against the delivered diff | **optional** — see below |

The companions sit outside the chain: `pdd:study` runs before step 1 when the codebase has no map,
`pdd:archive` runs after step 5 when the plan is retired, and `pdd:report` runs whenever a step misfires.

### Step 0 — vendor the frameworks you bind to, then study them

Before the first line of code goes against an external framework — an SDK, a state-machine library, an ORM,
a protocol client — pin the **latest stable release** into the repository and vendor the part of it the work
will actually read. Then run `pdd:study` over the vendored tree, so the framework's real surface enters the
knowledge index with citations.

Three things follow, and each is measurable:

- **The version the agent reads is the version it compiles against.** An API recalled from training data and
  an API in the pinned release are different objects; the gap surfaces as "it compiles in my head", which is
  the most expensive class of defect to debug because the code is plausible at every line.
- **Token cost falls, because retrieval becomes a local read.** A cited `file:line` inside the vendored tree
  replaces fetching documentation, pulling a release, or reconstructing an interface from memory, and the
  AGENTS.md branch table keeps the map small so the reads stay targeted.
- **Plans stop inventing adapters.** With the framework's entry points and branch tables recorded,
  `pdd:plan` names the seam that exists instead of an abstraction the framework never had.

Pin what is stable rather than what is newest: a pre-release API is a moving target, and stopping the
movement is the entire point. Vendor only the surface you bind to — the modules whose API the plan calls —
and record the tag and commit in the AGENTS.md provenance block.

Two rules keep this from becoming the drift problem it is meant to prevent. An upgrade is a **migration
task** with a B-class baseline, not an in-place bump. A refresh of the vendored copy is a `pdd:study` delta
run, not a rebuild. A vendored copy nobody refreshes is worse than no copy, because it is believed.

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
knowing whether a green run means anything — and every skill here points at it from its verification
section.

Its last step publishes: the tracker is searched for the mechanism first, and a match receives a comment on
the existing issue rather than a twin; the body is scrubbed of every project and person before it leaves the
machine, and a scrub read holds that boundary — absolute paths, emails, IPs, non-GitHub URLs, bare
revisions, deny words, and the redaction line that says what was removed.

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

## How verification works

A decision table is an enumerable object, so the process enumerates it. For each operation, `pdd:decompose`
requires the rows as implications plus a default, checks that they are mutually exclusive, and converts each
antecedent to DNF; the longest conjunct gives `k`, and the table is in `k`-DNF. Two arrays follow:

- **PTEST** — one row per term, that term's literals positive and every other term of the same rule negated.
  The negations are the point: with `ab + cd → R1`, an input that satisfies both terms passes even when the
  implementation ignores `a` and `b`, so masking hides the defect.
- **NTEST** — a covering array of strength `k` over the table's whole variable universe, constrained by the
  negation of the rule's antecedent, every row expecting the named default or refusal class.

Numeric inputs are cut into equivalence classes with boundary representatives, never drawn from a range. The
`(operation × state)` matrix is enumerated, so a forbidden move is a row expecting `refuse:<class>` rather
than a comment. Because every row of one array carries the same expectation, the oracle is free — which is
why a large array is not a maintenance burden, and why the reference model must be right.

The claim on a green run is bounded, and it is stated: *no defect outside a term of `k` literals*. Beyond
`k`, detection is partial, and the report says so. Nothing here is sampled, so nothing shrinks, no seed is
pinned, and no regression corpus accumulates; the arrays are derived from the table and regenerate with it.
The one cost the method adds is honest: the transcribed table is a second copy of the rules and can drift,
so the mutated-table control — change one literal, the suite must redden — is a gate rather than advice.

`skills/decompose/references/testing-methodology.md` is the only place a test is specified.

## Design philosophy

The process is built on one asymmetry: the cost of writing a change has collapsed, while the cost of
verifying one has not. Every design decision follows from choosing evidence, not throughput, as the binding
constraint — acceptance is typed, tasks are classified by acceptance object, and the unit of testing is a
decision table, with its completeness claim bounded by a declared strength.

Read [DESIGN.md](DESIGN.md) for the full argument: the enumeration thesis and why a bounded completeness
claim beats a statistical one, the four task classes and where they come from, the three shapes of
verification (decision-table coverage / behavioural guard / architecture check), the two gates, and the costs
the process accepts.

## Requirements

- Hermes Agent with plugin support (`hermes plugins doctor .` should pass).
- Python 3.10+ (the plugin itself has no third-party dependencies).
- No script ships with the skills. Every gate is a command run in the turn (`git`, `grep`, `find`, `sed`)
  or a reading recorded in the report, so the loader runs nothing and there is nothing to keep executable.
- Rendering a study graph optionally shells out to `mmdc` or `npx @mermaid-js/mermaid-cli`; without one, the
  graph is lint-read by eye and recorded as unrendered.

## Layout

```
plugin.yaml            manifest (name: pdd)
__init__.py            register(ctx) -> ctx.register_skill() per skill directory
skills/plan/           SKILL.md + assets/
skills/decompose/      SKILL.md + assets/ + references/
skills/implement/      SKILL.md + references/
skills/review/         SKILL.md + references/
skills/explain/        SKILL.md + assets/ + references/
skills/study/          SKILL.md + assets/ + references/
skills/archive/        SKILL.md + assets/ + references/
skills/reproduce/      SKILL.md
```

## Versioning

`plugin.yaml` version tracks the skill set as a whole. Each `SKILL.md` carries its own version in
frontmatter; they move independently when a single skill changes.

## Licence

MIT — see [LICENSE](LICENSE). © 2026 Uniterra Solutions Ltd.
