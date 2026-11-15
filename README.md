# pdd-software-development

A Hermes plugin that ships **Proposition-Driven Development (PDD)** as five bundled skills.
PDD is a business-first spec workflow: the PRD describes business logic and observable behaviour,
decomposition yields four classes of task, and verification is modelled per business flow rather
than per task.

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
| `pdd:decompose` | Turn the PRD into four classes of task (construction / verification / migration / removal), one DAG, two gates |
| `pdd:implement` | Dispatch the DAG layer by layer, accept each task by its class, stop on contradiction |
| `pdd:review` | Read PRD + tasks, write a review DAG, dispatch two reviewer types, synthesise findings |
| `pdd:explain` | Explain a plan to a non-engineer without inventing claims |

```
skill_view("pdd:decompose")
skill_view("pdd:decompose", "references/task-verification.md")
```

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
- `pdd:implement/scripts/mutate_check.py` needs a working Python interpreter and is invoked by the
  skill, not by the plugin loader.

## Layout

```
plugin.yaml            manifest (name: pdd)
__init__.py            register(ctx) -> ctx.register_skill() per skill directory
skills/pdd:plan/       SKILL.md + assets/
skills/pdd:decompose/  SKILL.md + assets/ + references/
skills/pdd:implement/  SKILL.md + references/ + scripts/mutate_check.py
skills/pdd:review/     SKILL.md + references/
skills/pdd:explain/    SKILL.md + assets/ + references/
```

## Versioning

`plugin.yaml` version tracks the skill set as a whole. Each `SKILL.md` carries its own version in
frontmatter; they move independently when a single skill changes.

## Licence

MIT — see [LICENSE](LICENSE). © 2026 Uniterra Solutions Ltd.
