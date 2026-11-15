# What <plan name> Is Actually Doing

| Field | Value |
| --- | --- |
| Source of truth | `<plan-dir>/PRD.md`, `<plan-dir>/TASKS.md`, `<plan-dir>/tasks/` |
| Date | <YYYY-MM-DD> |
| Reader | <who is to read this; what his decision is> |
| Explanation language | <the reader's language> |
| Metaphor domain | <a single metaphor domain, e.g. "customs and the customs broker"> |
| Excludes | technical terms, file lists, construction steps |

> This document explains "what was required, what was decided, what is checked"; it makes no quality judgement and endorses no side.
> Anything that is my inference is marked "(inference)" in the text; whatever the documents do not say is not written up as if it were what they mean.

## 1. The one-sentence version

<One paragraph, within five sentences: for whom, what it solves, how it solves it, what the cost is, when it should be reconsidered.>

## 2. Metaphor: <metaphor domain>

<Three to five sentences, telling the shape of the whole plan as this world: who guards the gate, where things come from, whose hands they pass through, what record is left.>

### 2.1 Role mapping table

| Role in the metaphor | The thing in the plan | Id |
| --- | --- | --- |
| <role> | <thing or rule> | `<REQ-…/D…/T…>` |

### 2.2 Where this metaphor stops

- Holds up: <the part it can help you imagine>
- Does not hold up: <the part it will mislead on, and which section to read instead>

## 3. Requirements, one by one

Ordered by when the requirement happens in reality; the id is only a label.

### `REQ-<flow>-1` <plain-language title>

- **Scene**: <one specific person, at one specific moment, runs into what.>
- **Guarantee**: <what the system always does here; keep every number and unit.>
- **If this guarantee were absent**: <a specific failure event: who finds out when, and loses what.>
- **Boundary**: <empty / full / the same thing sent twice / order reversed / data incomplete / broken off halfway — which apply, and how they show up.>
- **Visible evidence**: <where a layperson confirms that it did it.>
- **In the metaphor**: <one sentence; if it cannot be translated back to the contract, delete this line.>

## 4. Decisions, one by one

### `D<n>` <plain-language title>

- **The two roads**: <A and B, one sentence each, stating system consequences not preferences.>
- **Chosen**: <A, one sentence.>
- **How the other one would break**: <the specific failure B produces in one specific situation.>
- **Cost**: <after choosing A, the extra cost, the lost capability, the places that got slower.>
- **When it should be overturned**: <one observable condition whose appearance makes this choice no longer worth it.>
- **In the metaphor**: <one sentence.>

## 5. Verification strategy: which error each flow is guarding against

Sections by business flow, not by task. Each flow's checks answer three questions: which error it guards against, where it is visible, what it fails to catch.

### `F<n>` <the flow's name in plain language>

- **Which error it guards against**: <someone could go wrong this way: translate this flow's refusal conditions or rules that must hold into plain language, while every other part looks normal.>
- **Where it is visible**: <the place looked at during a check, described in layman's words.>
- **What it fails to catch**: <the errors this check will let through; mark (inference) if it is an inference.>
- **Not yet verified**: <keep only when not yet modelled: state that the check is planned and has not been run; in all other cases delete this line.>
- **In the metaphor**: <one sentence.>

## 6. Where the metaphor fails

- <location — how the metaphor breaks — what wording to use instead — what the precise meaning of that passage is.>

## 7. Where the documents say nothing

Write each item as a question for you to answer, and point out which requirement it would affect.

- <question> — would change `<REQ-…>`.

## 8. Contradictions and things that must be decided by you

- <two requirements that cannot both hold, quote one sentence from each> — I do not choose on your behalf; the consequences on each side are: <if A holds then …; if B holds then …>.
- <the direction that needs your decision> — the options and their respective consequences; my recommendation is marked "(assistant recommendation)".

## Appendix A Original-text reference (optional)

Keep this only when the reader will see these strings with his own eyes. This section does not count towards the technical-term check.

| Original | Plain language | Where the reader will meet it |
| --- | --- | --- |
| `<string>` | <plain-language meaning> | <screen / message / command> |
