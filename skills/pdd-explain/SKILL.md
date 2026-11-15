---
name: pdd-explain
description: "Use when a plan must be explained to a non-engineer."
version: 1.5.0
author: Tsz Kin Lai (LaiTszKin), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [software-development, communication, explanation, metaphor, prd]
    related_skills: [pdd-plan, pdd-decompose, pdd-implement, pdd-review]
---

# Plain-Language Plan Explanation

pdd-explain turns a plan into one explanation a non-engineer can act on: what each requirement
is for, what each design decision bought and cost, and what each check catches. The plan here is the
`PRD.md` that `pdd-plan` produced together with the task list that `pdd-decompose` produced. The
explanation is a deliverable in its own right, and it works as a test instrument: a plan that resists
explanation without jargon usually rests on an assumption nobody stated.

The explanation is written in the **reader's** language. The section labels, entry labels and terminology
below are therefore the labels in their English form; `assets/EXPLAIN.md` carries the authoritative set and
they must be rendered in the reader's language when that is not English. Whatever the language, the label
set is a contract: the same five parts per requirement, in the same order, so a reader can compare entries
and find a missing one.

## When to use

- The user asks what a plan, PRD or task list actually does, or asks for a version a non-engineer,
  client, partner or investor can read ("explain it with a metaphor", "no technical terms", "for a
  non-technical reader").
- The owner wants to approve or challenge a plan before implementation money is spent.
- A change must be explained to someone who will never open the repo.
- Routing: `pdd-plan` writes and revises the plan, `pdd-decompose` splits it, `pdd-implement` implements
  it, and `pdd-review` judges code quality. This skill explains the plan and leaves the verdict to the
  owner.

## Preconditions

- Read three things in full before writing a sentence: `<plan-dir>/PRD.md`, `<plan-dir>/TASKS.md`, and
  every `<plan-dir>/tasks/T<NN>-*.md`. Reading a summary in place of those originals is the usual cause
  of an explanation that silently drops a requirement.
- The output is `<plan-dir>/EXPLAIN.md`, built from `assets/EXPLAIN.md`.
- Language: the **reader's** language, which may differ from the plan's. Identifiers used as labels
  (`REQ-…`, `D1`, `F1`, file names) stay untranslated; technical vocabulary in prose is banned outright —
  see `references/plain-language-lexicon.md`.
- The plan is read-only: `PRD.md`, `TASKS.md` and `tasks/` stay untouched. A contradiction found while
  explaining goes into `EXPLAIN.md` and into the reply to the user, and the plan itself keeps its text.

## Workflow

1. **Inventory with code rather than by eye.** Enumerate every `REQ-*` id, every `D<n>` decision, every
   flow, every state, invariant and refusal class in the domain model, and every task id.
   Write the inventory to a scratch file and print the counts. Those counts become the completeness gate
   at step 9, because a 40-requirement plan read by eye loses three and the reader cannot tell.
2. **Choose one metaphor domain for the whole document.** Criteria: the domain belongs to the reader's
   world (customs, a bank counter, a warehouse, a kitchen, a post office, property management, a water
   utility); it has room for permissions, refusals, queues, caps, duplicates, ordering and bookkeeping;
   and it is not software wearing a costume (a filing cabinet, "the cloud", an assembly line in the
   data-pipeline sense all read as plain language while explaining nothing). Write the domain down
   together with **where it stops working**, before using it.
3. **Build the role table before prose.** Each actor, each stored thing, each permission and each record
   of what happened gets one row: role in the metaphor / thing in the plan / id. An entity without an
   honest role stays unmapped and is explained in plain prose; an invented role makes the metaphor lie.
4. **Explain the requirements, one section per `REQ`, ordered by the reader's journey** (what happens
   first, in time), with the id as a label only. Two kinds take two shapes: a **functional** `REQ-F`
   carries scene / guarantee / what happens without it / boundary / evidence; an **architectural** `REQ-A`
   carries the rule / where it is violated today / what the check does / what a breach looks like. An
   architectural requirement explained through a user scene is a fiction: nobody meets a dependency
   direction. Each entry carries five parts, one sentence each:
   - **scene** — one specific person at one specific moment meets something;
   - **guarantee** — what the system then guarantees, with every stated number and its unit kept
     intact;
   - **if this guarantee were absent** — the concrete failure as an event (who discovers it,
     when, and what is lost), stated in the language of losses rather than of risk;
   - **boundary cases** — which of empty / full / the same thing sent twice / reversed order /
     malformed data / broken off halfway apply here, in plain words;
   - **visible evidence** — where a bystander confirms the guarantee held.

   The optional "in the metaphor" line makes a sixth, and it is deleted wherever it
   translates back to nothing.
5. **Explain each decision as a fork rather than as an obvious right answer:** two roads → which one was
   taken → how the other one breaks in a specific incident (not "it is worse") → **the cost of this one**
   (no choice is free) → **under what condition it should be overturned**. The cost line and the reversal
   condition are mandatory; a decision section that lists benefits alone argues for the decision rather
   than explaining it.
6. **Explain the verification, one section per flow.** Each flow's checks answer three questions:
   **which mistake it prevents** — the plausible wrong build, drawn from the flow's refusal classes and
   invariants; **where it is visible** — the surface a bystander would look at; **what it cannot catch** —
   the class of mistake this check lets through, marked "(inference)" where you derived it rather than
   read it. A flow with no model yet carries **not yet verified**: the checks are planned, so the owner
   knows which guarantees are described rather than demonstrated.
7. **Pressure-test the metaphor** (see `references/analogy-engineering.md`). Push it until it breaks, then
   either repair the mapping or write that passage in plain prose and record the limit in §6. The
   metaphor never overrides the document.
8. **Record what the document leaves unstated.** §7 lists each silence as a question the owner must
   answer, with the `REQ` it would change. §8 lists requirements that cannot both hold, quoted from both
   sides, and leaves the choice with the owner.
9. **Deliver.** Write `EXPLAIN.md`, walk the checklist below against your own text, then reply with the
   one-paragraph version, the two or three things that actually need the owner's decision, and the file
   attached.

## Decision rules

### Jargon

- **A word is jargon when an intelligent reader from outside software would have to ask about it.** The
  test is the reader, not the dictionary. `references/plain-language-lexicon.md` carries the banlist and
  the substitutions: a new term enters the ban by adding a row to §2 of that file.
- **Renaming a term in plainer words still leaves it a term.** `schema` → "schema is what a table looks
  like" still fails. Write "which columns this table has and what goes in each".
- **Numbers serve clarity rather than jargon.** Concrete figures beat vague ones — "100 ms", "5 times",
  "3 people" over "fast", "a few". Keep every number the requirement froze, with its unit;
  `` `--retries 3` `` may become "resend at most 3 times".
- **A quoted original survives once.** A file name, a command the user will type or an error line they
  will see on screen appears in backticks, immediately followed by its plain meaning, because the reader
  will meet that string and hiding it sets a trap. Everything else is translated. Backticked strings and
  appendix A are exempt; the ban applies to prose.
- **A refusal stays a refusal.** "The system handles it automatically" erases the design. Say who is
  refused, under what condition, and what they see; a refusal the owner cannot picture is a refusal he
  cannot veto.

### Metaphor

- **One domain serves the whole document.** A second domain gets its own section with its own declared
  scope, and the two never mix inside a paragraph.
- **A metaphor sentence earns its place by translating back to one contract clause or one concrete
  failure.** A sentence that translates back to nothing is decoration and gets cut.
- **The text outranks the analogy.** Where the two disagree, the text states the requirement and the
  analogy counts as a defect.
- **Vague virtues take an observable difference instead of a metaphor.** "Efficient", "robust",
  "scalable" have no counterpart in any domain; replace each with how long someone waits, how much is
  lost when it breaks, what happens with twice the people.

### Honesty

- **Mark your own inference "(inference)".** A reason the document never gave belongs to the assistant, and
  the document keeps its own reasons.
- **Explanation states what is required, what it costs and when the choice would be wrong.** A verdict,
  where the user asks for one, is given separately and labelled as the assistant's.
- **Attribute only what the user said.** Any alternative the assistant proposes is labelled as the
  assistant's own and stays outside the user's position.
- **Completeness beats elegance.** Every requirement gets an entry, including the dull ones: a missing
  entry is a defect the reader cannot detect, while a boring paragraph is a cost the reader can skip.
- **An unexplainable requirement is a plan gap rather than a writing problem.** A requirement that resists
  plain language, or that can be explained only by inventing a mechanism, goes into §7 as a question and
  into the reply — never under a fluent paragraph. A reader must know when prose stands in for a design
  nobody stated.
- **Scale does not license summary.** A 40-requirement PRD keeps 40 entries, grouped under an area-level
  scene paragraph (one paragraph saying what this batch of people is doing).
  Requirements never fold into "other": a missing `REQ` entry, or an entry with no reading of its own, is a
  defect the reader cannot detect.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Reader says "roughly got it" but cannot restate one guarantee | the section is all metaphor and no contract | add the guarantee and evidence lines with their numbers |
| The metaphor grows, the requirements shrink | the metaphor became the subject | one metaphor sentence per contract clause; cut the rest |
| A warehouse and a bank in the same paragraph | two domains | one domain per document, or a separate section with its own scope |
| The explanation reads more complete than the PRD | you supplied reasons nobody wrote | mark "(inference)" or delete |
| Every decision looks obviously right | only benefits were listed | add the cost and the reversal condition to every `D` |
| The verification section is a test list | nobody said what error it prevents | lead each flow's checks with the plausible wrong build |
| The owner asks "so will it go wrong or not" and there is no answer | blind spots unwritten | add what each check cannot catch |
| The owner approves a check that never ran | the flow is modelled after the code landed and the entry omits "not yet verified" | add that marker to the flow's section |
| Requirements explained in id order | the reader follows ids instead of events | order by the reader's journey; ids stay labels |
| §7 is empty | silences were filled by guesswork | list each silence as a question, with the `REQ` it would change |
| A requirement explained only through its file name | path used as a substitute for behaviour | say what an outsider observes; the path belongs in the appendix |

## Verification

- `EXPLAIN.md` exists at the declared path and covers every `REQ`, every `D` and every flow,
  with the section labels in place, no banlisted term in the body, and per-requirement numbers preserved.
- Every `REQ-F` entry carries scene / guarantee / what happens without it / boundary / evidence; every
  `REQ-A` entry carries the rule / where it is violated today / what the check does / what a breach looks
  like; every decision entry carries its cost and its reversal condition; every flow's
  checks carry which mistake they prevent and where they are visible.
- Every flow with no model yet carries "not yet verified", and every check the reader is asked to trust
  names what it cannot catch.
- One metaphor domain serves the document, its limit is stated up front, and §6 records every place it
  broke.
- The body holds no banlisted term, and every quoted original carries a plain gloss.
- §7 and §8 name the silences and the contradictions, and the owner's decision stays open.
- The chat reply carries the one-paragraph version, the decisions needed, and the file attached.

## References

- `assets/EXPLAIN.md` — the document template; every section exists for one item of the checklist.
- `references/analogy-engineering.md` — choosing a domain, the role table, the six pressure tests.
- `references/plain-language-lexicon.md` — banned terms with substitutions, plain translations of the
  boundary-case taxonomy, banned sentence shapes. Its §2 is the banlist.
- No document-verification script exists, and none is added: coverage and jargon are read by the writer
  against the checklist, because a script can see a missing id but not a sentence that explains nothing.
