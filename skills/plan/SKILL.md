---
name: plan
description: "Use when planning a change: writes a behaviour-first PRD."
version: 2.1.0
author: Tsz Kin Lai (LaiTszKin), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [software-development, planning, prd, requirements]
    related_skills: [decompose, implement, review, explain]
---

# PRD Planning — business logic and behaviour

A PRD states what the business does: who acts, what is guaranteed, when the system refuses, and what must
never happen. It is written at the level a business owner can argue with, because that owner is the reader
who can still change it cheaply.

**The one rule that keeps the document small: if a sentence can be read out of the code, it does not belong
in the PRD.** Flags, schema keys, file paths, module layouts, endpoint tables, response shapes, error-code
internals, timeout values, buffer sizes and test designs are all discoverable from the tree. Written into a
PRD they become micro-decisions that `pdd:decompose` inherits as if they were requirements, and the plan
then decomposes into micro-tasks with micro-verification — the failure this document exists to prevent.

What survives the rule is short: the business intent, the behaviour, the refusals, the invariants, the
external promises, and the trade-offs nobody can recover from the code.

**Every requirement is one of two kinds, and the kind decides how it is accepted.**

| Kind | Content | Acceptance object | Prefix |
| --- | --- | --- | --- |
| **Functional requirement** | Adds or changes one observable behaviour | The behaviour becomes falsifiable once modelled (flow, command, refusal, invariant) | `REQ-F-<flow>-<n>` |
| **Architectural requirement** | Code obeys a structural rule; refactoring, module boundaries, performance | **The code obeys the architecture itself**, decided by an executable architecture check, not by a test | `REQ-A-<n>` |

Performance work is normally architectural: only a structural change produces an order-of-magnitude gain,
so its acceptance is "the metric enters its budget" **plus** "the structural rule that produced the
improvement holds". A requirement that asks for both a new behaviour and a new structure splits into two —
their acceptance objects differ, and merged together neither side gets verified.

## When to use

- The user names the PDD workflow, PDD planning, or asks to plan a feature, refactor, migration or bug
  batch, or asks for a PRD / requirements document.
- The request is vague enough that implementation would start with guesses about the business.
- A change spans several behaviours, and later agents need one statement of what the business now does.
- Handoff: `pdd:decompose` cuts the work into four classes of task, `pdd:implement` implements one seam,
  `pdd:review` judges the code, `pdd:explain` re-tells this document to a non-engineer.

## Preconditions

- The request, the repo, existing issues/ADRs/docs and any stated constraints are in hand.
- The output is `<plan-dir>/PRD.md`, built from `assets/PRD.md`, where `<plan-dir>` defaults to
  `.plan/<DD-MM-YYYY>/<slug>/` and follows the repo's convention when the repo has one.
- The document is written in the project's working language. Business nouns (`order`, `settlement`,
  `refund`) stay in the language the operators use; an identifier enters only where the business itself
  names it (`USDC`, a regulatory form number, a tariff code).
- Before writing, list the plan dir's siblings (`find .plan -maxdepth 2 -type d`): an earlier plan may
  already own this territory, and its recorded decisions constrain the new one. A PRD that contradicts a
  live decision without naming it has re-decided it silently.

## Workflow

### 1. Learn the business before the code

Ask and answer, from the user and from documents, not from the tree:

- **who acts** — the actors, their permissions, who is refused and by whom;
- **what moves** — money, goods, entitlement, state, and which of those is irreversible;
- **when it refuses** — the conditions, and what the refused party sees;
- **what must never happen** — the failures that are unacceptable rather than merely inconvenient;
- **what the numbers are** — rates, caps, windows, deadlines, with the authority that sets each.

A sentence that survives only because "the code does it that way" is a bug report, not a business rule.

### 2. Take from the repo only the facts that change a business judgement

Read the surfaces the request touches for three things: an external promise the change would break, a
compatibility burden with real cost, and an existing refusal whose meaning must survive. Settle those with
`search_files` / `read_file`. Everything else the tree offers — naming, structure, defaults — is
recoverable by the later phases and stays out.

### 3. Clarify in rounds, in business vocabulary

Ask until the next answer would leave the document unchanged. Questions that earn their round:

- who is allowed, and who is refused in the same situation;
- what the refused party sees, and what they can do next;
- which state change is irreversible, and whether that is intended;
- the caps, windows and deadlines, and who may change them;
- what happens to work already in flight when the new rule lands;
- which existing promise this change weakens, and who agreed to that.

Do not spend a round on stack, schema, flags or file layout. Those are implementation choices that the
tree and `pdd:decompose` settle; asking the business owner about them produces decisions nobody owns.

### 4. Write the business model

- **Actors and objects** — each with its unit and bounds (money in minor units, quantity, timestamp,
  identifier space) and whether it is reversible.
- **Decision table** — one row per operation: inputs, precondition, outcome (`apply`, or
  `refuse:<class>` with a class name the business uses), and what must hold afterwards. Refusals included.
- **States** — the legal moves between them, and the moves that must never happen.
- **Invariants** — each with the range it quantifies over.
- **Deliberately not encoded** — the rules left out, each with its reason.

### 5. Write the behaviour, one section per flow

A flow is what a person does from trigger to outcome: a sequence of commands against the state machine. It
is the unit the later phases schedule and verify against, so it is the unit of the document too.

Each flow section carries: who triggers it and when; the normal path, step by step, in business terms; the
refusal path, naming the refused actor and what they see; the edge behaviour (nothing to act on, the
maximum, the same request twice, out of order, malformed input, interruption halfway) stated as business
consequences; the things that must never happen; and where a business person sees the outcome holding —
which screen, report or statement.

Do not organise this section by endpoint, file or layer. An endpoint table describes an interface; a flow
describes what the business does, and only the second one survives a refactor.

### 6. Declare the architecture, then separate the two kinds of requirement

Write §5's architecture — the target structure and its constraints — first, and derive `REQ-A` from it.
An architectural requirement with no target structure is only a wish.

**What the architecture contains** (this section is the one place in the document allowed to describe
structure, because the structure is the deliverable):

- module boundaries and each module's responsibility;
- the allowed dependency directions, and the forbidden dependencies;
- the external surface (which symbols may be used from outside);
- layering or partitioning rules, and the cycles they forbid;
- if this change touches performance: the measurement method, the current baseline, the target budget,
  and which structural change produces the improvement;
- **every shared facility this change adds, test-side ones included.** A change that needs both a generator
  and a test bench will be caught at decompose if only the generator is written: each verification task
  then declares its own `sink()` / `fakeTransport()` / config double, and that duplication usually trips no
  existing gate (marker lists are finite enumerations; they recognise only the names listed in them), so
  the duplication ships silently — while "one facility" is the entire value of this kind of change. Write
  down each shared component, what it owns, and which check answers the rule "spec files must not build
  their own"; the one you leave out becomes a new `REQ-A` plus a construction task, and the cost is
  reopening the contract.

**What a functional requirement contains**: which flow it belongs to, which commands it adds, which state
or refusal class it changes.

The test for the kind is the acceptance method, not the size of the change: a result that can be written as
"some behaviour of some flow" is a functional requirement; a result that can only be written as "some code
must not do X" or "some metric must land at some value" is an architectural requirement.

### 7. Derive the requirements from the behaviour

**Functional requirements**: `REQ-F-<flow>-<n>`, one claim each, three lines.

```
#### REQ-F-<flow>-1 <the behaviour in one falsifiable sentence>

- **From rule**: <the decision-table row or state transition this comes from>
- **Failure appearance**: <who discovers what is wrong, and when, if this does not hold>
```

**Architectural requirements**: `REQ-A-<n>`, one claim each, four lines. The last two lines are what
separates this from a functional requirement — with no executable check, an architectural requirement is
not acceptable.

```
#### REQ-A-1 <the structural rule in one falsifiable sentence>

- **Scope**: <which modules, packages or symbols the rule quantifies over>
- **Violation appearance**: <what a violation looks like in the tree, concretely>
- **How it is checked**: <the executable check that returns pass or fail; naming the tool is allowed here, because the check is the acceptance mechanism, not an implementation detail>
```

One claim per requirement. Anything that needs two sentences is two requirements. A requirement every
implementation would satisfy is not worth writing — delete it instead of padding the count with it.

### 8. Record only the decisions the code cannot recover

A `D-n` carries the chosen value and the alternative it beat (`Rejected: <alternative> — <one clause>`).
This section exists for external promises, regulatory constraints, compatibility burdens, cost ceilings and
time windows — the things that, if lost, would be re-decided wrongly by whoever reads the code next. A
decision that merely restates the implementation belongs in the commit message.

### 9. List the surfaces the business sees, without their wiring

One row per surface (screen, CLI command, report, statement, API a third party integrates): who uses it,
what they see in it, and what an error looks like to them. The route string, flag name, payload shape and
schema keys are confirmed by `pdd:decompose` against the tree; they are not this document's business.

### 10. Self-check and hand off

Walk the checklist below, then tell the user where the PRD sits and which decisions were defaulted. The
complex change goes to `pdd:decompose`; the single-behaviour change goes to `pdd:implement`.

**Sweep the finished draft for what your own hand wrote in.** The author writes flag names, schema keys and
paths while thinking about the surface, so they arrive by default and no amount of rereading removes them.
Sweep with a grep over the file, not with your eyes: `--[a-z][a-z-]+`, `[A-Z]{2,}_[A-Z_]+` (env vars),
backticked lowercase terms (`message`, `numRuns`), and `[a-z]+/[a-z*/]+` (paths). Each hit is either
replaced by the noun the operator would use — "machine-readable mode" for a flag that selects JSON output,
"flag > env > profile > default" for the resolution chain — or kept deliberately. Paths and module names
survive ONLY in the architecture section and in a `REQ-A`'s scope, where the structure is the deliverable,
plus a measurement command inside "how it is checked" and the error shape inside §8.

## Decision rules

### What belongs in the document

- **Business quantities stay; implementation constants go.** A fee rate, a cap, a settlement window and a
  statutory deadline are business facts and carry their source. A retry count, a buffer size, a cache TTL
  and a timeout in milliseconds are implementation choices: they are discovered, not specified.
- **Name the actor, the moment and what they see.** "The system rejects invalid input" is unfalsifiable;
  "a merchant whose settlement exceeds the daily cap is refused at submission and sees the remaining
  headroom" can be argued with.
- **One flow per section, one claim per requirement.** The count of requirements should follow the count of
  business behaviours, not the count of endpoints or database tables.
- **Write the refusal as a first-class outcome.** Who is refused, under which condition, with which class,
  and what they can do next. A refusal that only appears as an error code in the code is undesigned.
- **State an invariant with its domain.** "No balance goes negative" fails as written the moment a fee
  correction exists; "no balance goes negative, in settlement or in withdrawal" survives review.
- **Record the trade-off, not the preference.** A decision names what it gave up. A decision with no cost
  is a description.

### The two kinds of requirement

- **The acceptance method decides the kind, not the size of the change.** A one-line structural fix is
  still an architectural requirement; a new refusal class is still a functional requirement.
- **A functional requirement may not argue "the architecture would be better", and an architectural
  requirement may not accept "behaviour unchanged".** The latter is an equivalence check (a refactoring
  guard), not an acceptance criterion; mixing them yields a requirement that can be neither falsified nor
  rejected.
- **An architectural requirement must be checkable.** Rule, scope, violation appearance and check — with
  any one of the four missing it is an opinion, not a requirement.
- **A performance requirement needs all three parts**: measurement method and baseline, target budget, and
  the structural change that produces the gain. A requirement that says only "faster" can be neither
  accepted nor rejected. The baseline is taken with the same instrument and the same command, as a median.
- **A change that needs both a new behaviour and a new structure** splits into one `REQ-F` plus one
  `REQ-A`. Written as one, acceptance degrades to "both are done, so we are finished".
- **Measure the rule in the tree before writing a `REQ-A`.** The architectural check is one of decompose's
  guard-gate conditions — "all green before the change". A rule that is already violated today (duplicated
  logic scattered over four files, dozens of zero-reference exports, a duration long past its budget)
  written as "must be zero" or "must be empty" makes that gate impossible to pass on day one, and
  decompose can only choose between "pretend it is green" and "stop". The measurement decides the form of
  the check: compliant today means an absolute form (zero hits); already violated means a **relative
  baseline** — freeze today's named violation list, and the check is "must not be longer than that" (or
  "must reach zero after the change") — and the document says which half is in this plan's scope. Measure
  the rule's **boundary** at the same time: a rule of "no module anywhere in the repo may build its own X"
  often catches a legal second layer (a field value-domain model is not a general-purpose generator), so
  read the hits before fixing the scan domain.

### Measured values

- **A number the business commits to is measured before it is written.** Rates, caps and windows come from
  the user, a contract or a regulation, with the authority named beside the figure.
- **A number that describes current performance is measured, not estimated.** Read the built artifact, run
  the exporter, time the query with the command that produced the number, and publish the median of three
  with that command. State a speed claim as a ratio against a measured baseline when the measurement runs
  under shared load, because an absolute duration encodes worker count and contention.
- **Trace a value to the form the business actually receives.** The layer that persists a value routinely
  re-prefixes, rounds or hashes what the caller assigned, so a rule written against the assigned string
  describes something nobody sees.
- **Enumerate the family before writing a rule that spans N members.** Two list surfaces served by
  different modules may return different envelopes; read each one's actual shape and write the rule against
  the families that exist.
- **Diff every table of names against the tree with code.** The §5 module list and the §8 surface list are
  sets a command can compare; a long table read by eye hides one wrong row, and the implementer inherits
  that row as a decision.
- **A scan-based count carries its method.** "27 zero-reference exports" and "35" can describe the same
  tree: the first counts a mention inside a comment as a reference, the second strips comments before
  comparing. Write the exclusion rules beside the number (whether comments are stripped, whether string
  literals count, whether type-only exports count, which file extensions are scanned); otherwise, when the
  next, stricter scan contradicts it, nobody can tell method drift from a real change — and once a baseline
  is written down, "which number is authoritative" becomes something other people must obey. When an
  executable check exists, that check is authoritative; a quick grep is only for sizing the work and
  finding the shape.
- **Give a behavioural-equivalence rule a negative control.** Name the change that must make the result
  visibly wrong; a rule with no control passes forever.
- **Probe the behaviour a requirement will assert, before writing the requirement.** Read the seam, then
  run it once with the hostile input. A requirement written against an inferred behaviour fails on day one
  or, worse, states a promise the code never made; a one-line probe settles in seconds what a paragraph of
  inference gets wrong, and the observed output belongs in that requirement's failure appearance as the
  measurement. This is how a plan discovers that the change it calls a test rewrite actually carries one new
  behaviour.

### Consistency

- **Test the conjunction after every round.** Compare each new answer against every recorded decision and
  existing ADR: individually reasonable answers routinely contradict each other — a mandate to act whose
  only authorised actor another answer excludes. When two answers do collide, do not silently pick one:
  write the reconciliation as a `D-n` carrying the boundary ("this one behaviour changes; every other
  finding is pinned to today's behaviour and filed as its own issue"), so the implementer cannot read the
  plan as licence for either extreme.
- **Give a state-specific behaviour the hook it needs, or record the reduction.** "The lockout notice is a
  warning" has only violations as honest options if every error renders through one element with no
  variant; name the hook here, or write the scope reduction down.
- **Verify a claim that the existing path already does this, using `search_files` over the call sites.** An
  ADR mandating one write path describes intent, and implementations bypass it with an inline copy.
- **Write a parity rule as two enumerated sets.** "Everything a merchant can do, an agent can do too" is
  prose until both sides are sets with a fixed allowlist — see `references/parity-requirements.md`.

### Document hygiene

- **Map every requirement onto something the document already declares** — a flow in §4, a rule in §5, or a
  non-goal. A requirement that maps to nothing is scope nobody agreed to, and a flow with no requirement is
  behaviour nobody will be held to.
- **Keep the prose out.** Current-state essays, history and exploration stay in the repo; the PRD states
  what the business will do.
- **Keep one id space.** A requirement keeps its id for the life of the plan.

## Pitfalls

- **The PRD is a spec of the implementation.** Flags, schema keys, endpoint tables, file paths, timeouts
  and test plans make the document long and make `pdd:decompose` micro-manage: it inherits each constant as
  a requirement and splits along them. If a sentence would survive deletion of the codebase, keep it.
- **One section per endpoint.** An endpoint list is an interface inventory; it says nothing about what goes
  wrong for the actor, and it changes shape every time the transport does.
- **Boundary cases as a checklist.** `empty / max / duplicate / out-of-order / malformed` filled
  mechanically produces rows nobody reasons about. Write only the boundaries that change the business
  outcome, in business words.
- **Unfalsifiable vocabulary.** "Correctly", "properly", "robust", "supports", "as expected" hide the
  predicate the reader must be able to attack.
- **A requirement per table or per file.** That is a diff partition. The count of requirements follows
  behaviours.
- **The refusal left implicit.** Every refusal names its actor, its condition and its class, or the design
  has a hole where a user will meet it.
- **An item another requirement depends on, left optional.** Omitting it fails the dependent requirement;
  adding it breaks the optionality. Make it required or state the fallback.
- **Two businesses in one PRD.** Different actors, different refusal rules, different readers: two
  documents, or the sections will contradict each other by paragraph forty.
- **Every item carrying an observation API.** That is the withdrawn test contract speaking. Observation is
  derived when the flow is modelled, after the code exists.
- **An architectural requirement written as a behavioural test.** "Behaviour unchanged after the refactor"
  is a guard, not an acceptance. An architectural requirement is accepted when the code obeys the
  architecture — dependency directions, boundaries, surface, budget — and an executable check answers that.
- **A performance requirement with no baseline and no structure.** With no baseline there is no before, and
  with no structure nothing can be attributed to the after; what is left is "some optimisation was done".
- **A refactor with no declared target.** With the target structure unwritten, the refactor has no
  termination condition and nothing to check.
- **A test-infrastructure change that names only the generator.** §5 names "the arbitrary-string module"
  but not "the test bench the spec files share", so each verification task writes its own seam by
  responsibility, and the repo's existing duplication scanners do not recognise those names (markers are a
  finite enumeration). Derive the shared-facility list from "what every spec file will use", not from "what
  modules I am adding": generator, test bench, fixture factory and the shared scratch directory all sit on
  the same table.

## Verification

- [ ] every flow has a trigger, a normal path, a refusal path with class and what the actor sees, edge
      behaviour in business terms, what must never happen, and where the outcome is visible;
- [ ] every requirement carries its kind: `REQ-F` traces to a decision-table row or state transition, or
      `REQ-A` carries rule, scope, violation appearance and check;
- [ ] every functional requirement names the flow whose behaviour it changes;
- [ ] every architectural requirement is decidable by an executable check, and no architectural
      requirement rests on "behaviour unchanged" as its acceptance;
- [ ] every performance requirement carries a baseline measured with a named instrument, a budget, and the
      structural change that produces the difference;
- [ ] the architecture section exists whenever any `REQ-A` exists, and every `REQ-A` traces to a rule in it;
- [ ] the document carries no flag name, schema key, file path, module layout, endpoint table, timeout
      or test design;
- [ ] every number carries its authority or its measurement, with unit and source;
- [ ] every `D-n` names the alternative it beat and the cost it accepted;
- [ ] every invariant states its domain, and every exception takes a form that domain permits;
- [ ] the requirements and the decisions form one consistent conjunction when read together;
- [ ] every open question names the observation that would close it, and defaults are marked;
- [ ] a business owner could read each flow and disagree with something specific;
- [ ] the document names its source and date, and names the next skill (`pdd:decompose` or
      `pdd:implement`).

> Cross-skill references name the sibling skill and the file separately:
> `skill_view("pdd:decompose", "references/task-construction.md")`. Every sibling is registered under
> this plugin's namespace, so the skill argument always carries the `pdd:` prefix and the path is
> relative to that skill's own directory.

## References

- `de-ai-writing` carries the prose rules for the body: every paragraph opens with its claim, every
  reference names its noun, and every negation anchors a state a reader could meet.
- `assets/PRD.md` is the template: fill every section, delete the instructional comments, drop any flow
  section the change does not touch.
- `references/parity-requirements.md` explains how to write "any operation available in A must be available
  in B" as a falsifiable set relation, including how to enumerate the authoritative side by booting the
  app, where grepping route files misses decorated prefixes and placeholder routes.
- No document-verification script exists, and none is added. A linter can check that every id has a field;
  it cannot check that the sentence describes a business behaviour, and presence is the dimension an author
  optimises once it is scored. The checklist above is the handoff gate.
