# PRD — <slug>

| Field | Value |
| --- | --- |
| Plan | `<slug>` — <the change in one line> |
| Date | <YYYY-MM-DD> |
| Owner | <the person who owns the business rule, or the architecture> |
| Status | Draft / In review / Handed off |
| Source | <issue / ticket / conversation of date / regulation> |
| Next | `pdd:decompose` for a multi-behaviour or architectural change; `pdd:implement` for one behaviour |

**What this document is.** Business logic, behaviour, and the architecture the code must obey. **If a
sentence can be read out of the code, it does not belong here** — flags, schema keys, file paths, module
layouts, endpoint tables, response shapes, timeouts and test designs are discovered by the later phases.
The one exception is the target architecture in §5: that structure does not exist yet, so it cannot be read
out of anything, and it is the deliverable of an architectural requirement.

Requirements come in two kinds. **Functional requirements `REQ-F-…`** are accepted by modelling their
behaviour. **Architectural requirements `REQ-A-…`** are accepted by the code obeying the architecture,
checked executably — not by a test that happens to pass.

## 1. Business and problem

<Who does what today, what breaks for them, and which outcome makes this change worth doing. One or two
paragraphs. No history, no exploration.>

## 2. Actors and objects

| Actor | Who it is | What it may do | What it is refused |
| --- | --- | --- | --- |
| <actor> | <the person or system> | <allowed operations> | <the refusals that apply to it> |

- **Objects and quantities**: <noun — unit, bounds, whether it is reversible>

## 3. Business rules

| Operation | Precondition | Result | Must hold afterwards |
| --- | --- | --- | --- |
| <operation> | <who may invoke it, in which state> | `apply` / `refuse:<class>` | <postcondition> |

- **States and transitions**: <state — legal moves — moves that must never happen>
- **Invariants**: <the law that holds in every state, with the range it quantifies over>
- **Deliberately not encoded**: <rule left out — the reason>

## 4. Behaviour

One section per flow. A flow is what a person does from trigger to outcome; it is also the unit the later
phases model and verify against. Do not organise this by endpoint, file or layer.

### F1 <flow, in the operators' words>

- **Who, and when it triggers**: <actor and the moment>
- **Happy path**: <trigger → each step → outcome, in business terms>
- **Refusal path**: <who is refused, under which condition, which class, what they see, what they can do next>
- **Boundary behaviour**: <only the boundaries that change the business outcome>
- **Must never happen**: <the outcomes that are unacceptable rather than inconvenient>
- **Where it is visible**: <the screen, report or statement where a business person sees it holding>

## 5. Architecture (only needed when there is an architectural requirement)

The target structure and the rules the code must obey afterwards. This section describes structure on
purpose: for an architectural requirement the structure is the deliverable, and nothing in the current tree
can supply it.

- **Module boundaries and responsibilities**: <module — what it owns — what it must not reach into>
- **Dependency direction**: <A may depend on B; A must not depend on C>
- **Public surface**: <the symbols other parts may use; everything else is internal>
- **Layers / partitions and cycles**: <layers, allowed edges, cycles forbidden>
- **Performance (if involved)**: <what is measured, with which instrument; current baseline; target budget; which
  structural change produces the difference>
- **Structure left alone this time**: <structure deliberately left alone, with the reason>

## 6. Requirements

### 6.1 Functional requirements

One claim per requirement, three lines each. The prefix names the flow it belongs to.

#### REQ-F-<flow>-1 <the behaviour in one falsifiable sentence>

- **From rule**: <the §3 row or §4 state transition this comes from>
- **Failure shape**: <who discovers what is wrong, and when, if this does not hold>

#### REQ-F-<flow>-2 <…>

- **From rule**: …
- **Failure shape**: …

### 6.2 Architectural requirements

`REQ-A` is the class "the code obeys the architecture". Acceptance is not a test; it is the executable check of the §5 rule.

#### REQ-A-1 <the structural rule in one falsifiable sentence>

- **Scope**: <which modules, packages or symbols the rule quantifies over>
- **Violation shape**: <what a violation looks like in the tree, concretely>
- **How it is checked**: <the executable check that returns pass or fail; naming the tool is allowed here>

#### REQ-A-2 <…>

- **Scope**: …
- **Violation shape**: …
- **How it is checked**: …

## 7. Decisions (recorded; later changes are superseded by a new decision)

Only decisions the code cannot recover: external promises, regulatory constraints, compatibility burdens,
cost ceilings, time windows, and the architecture chosen over its rival.

- **D1 <topic>**: <the chosen value>. Rejected: <alternative> — <why, one clause>.

## 8. External interface

| Surface | Who uses it | What they see | What they see on error |
| --- | --- | --- | --- |
| <screen / CLI command / report / statement / third-party API> | <actor> | <what it shows> | <what an error looks like to them> |

Route strings, flag names, payload shapes and schema keys are confirmed by `pdd:decompose` against the tree.

## 9. Non-goals

- **N1** <adjacent thing this change deliberately leaves alone, with the reason>

## 10. Open questions and risks

- **Open**: <question — the observation or command that closes it — the requirement it affects>
- **Risk**: <risk — impact — mitigation>

## 11. Handover

- Defaulted decisions: <list with `defaulted — vetoable until work starts`, or `none`>
- Chosen next skill: <pdd:decompose | pdd:implement>
- A later change enters as a new decision, dated, with the id it supersedes.
