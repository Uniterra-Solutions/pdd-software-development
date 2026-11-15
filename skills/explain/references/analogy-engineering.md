# Analogy Engineering

The metaphor is the instrument, not the decoration. An analogy earns its place only when a reader can
translate it back to a clause or a failure. This reference gives the domain shortlist, the role table,
and the six tests that decide whether the metaphor survives.

## 1. Choosing the domain

One domain per document. Requirements of a usable domain:

- **It belongs to the reader's week** — customs, bank counters, logistics warehouses, restaurant kitchens, post offices, property management, water plants, airport security,
  libraries, pharmacies. Choose from what the reader already operates, not from what you find vivid.
- **It has all six slots** — the person at the gate, the pass, the place things are kept, the ledger that keeps the record, the person who is refused, the rule from above. A domain missing
  refusal or record cannot carry a plan whose design lives in its refusals.
- **It is not software in costume** — data flow, assembly line (in the pipeline sense), filing cabinet, cloud, stack, mailbox queue are
  technical terms wearing everyday clothes. They read as plain language and explain nothing.
- **It has a cost structure** — hands, time, rent, rework. Without cost, the cost line in `EXPLAIN.md` §4
  has nowhere to live.

State the domain and its limit in `EXPLAIN.md` §2 before the first metaphor sentence. A limit declared up front is
honest; one discovered after twenty paragraphs reads as a retraction.

## 2. The role table

Fill this before writing prose. One row per actor, stored thing, permission and record:

| Role in the metaphor | The thing in the plan | Id |

Rules:

- **One role, one referent.** Two entities sharing a role means the reader cannot tell which one a later
  sentence is about.
- **Each role carries one honest referent.** An entity with no honest counterpart goes in the prose,
  unmapped. A fabricated role is a false claim about how the system behaves, and it gets believed because
  it is concrete.
- **The role's powers must match.** If the storekeeper in the metaphor can delete a record and the system's actor
  cannot, the metaphor has granted a permission nobody approved.

## 3. The six pressure tests

Run each against every metaphor-bearing passage. A failure is either a mapping repair or a passage
rewritten in plain prose — never a passage left as it is.

1. **Reverse test** — In the metaphor A holds; in the document B holds. Example: "the teller can change the
   amount" vs the plan's "once the amount is written it cannot be changed". Repair the role or drop the metaphor there.
2. **Boundary test** — Describe the metaphor at empty, full, incomplete. If the metaphor has no picture for empty or full,
   the reader will assume those cases do not exist — which is exactly how a boundary requirement gets
   approved without being understood.
3. **Repetition test** — Say the same action twice in the metaphor. If the second time visibly does something
   more (two receipts, two deductions), the metaphor contradicts any "do the same thing twice, same result" clause.
4. **Order test** — Reverse two steps. If the metaphor still works, it cannot carry an ordering requirement.
5. **Interruption test** — Stop the metaphor's process halfway (the customer left, the power went out, the paperwork half done). What is left on the desk?
   If nothing, the metaphor cannot explain partial failure or compensation.
6. **Cost test** — Name what the metaphor pays for the chosen path (hire one more person, half a day slower, keep a copy). A metaphor
   that pays nothing leaves the cost line in `EXPLAIN.md` §4 unsupported, and the decision reads as free.

**Replace rather than soften any load-bearing passage that fails tests 1–5.** "Roughly speaking" leaves the reader
with a metaphor the document contradicts. A passage that fails test 6 usually means the decision section
is missing its cost line.

## 4. Where the metaphor must yield

Some plan content has no honest everyday counterpart: the order of concurrent writes, hashing, version compatibility, resending after a timeout. These are
explained by **consequence to a person**, not by analogy:

- concurrent → "two people press the same seat at the same time; only one can sit down in it, and the other sees it is already taken"
- resend after a timeout → "wait too long and it counts as not received, so it is sent again; so you must guarantee that sending twice does not become two copies"
- version compatibility → "an old form must still be readable with the new form layout, otherwise every old client is stuck"

This is prose rather than metaphor, and it belongs in `EXPLAIN.md` §6 as a declared limit wherever the
domain cannot reach it.

## 5. Worked skeleton (placeholders only)

Every placeholder here comes from the PRD; the pattern shows the shape, and the content belongs to the
document.

```
§2 Metaphor: <domain>
  Scene: <one specific person> at <one specific moment> has to <do one specific thing>.
  Guarantee: he will get <a specific result>, or be told <a specific reason>; he will not be left at "I don't know whether it worked".
  Mechanism (metaphor): <the person at the gate> checks <the pass>, then writes a line in <the ledger>; if it cannot be written, the whole entry does not count.
  Limit: this metaphor holds only up to "two people at the counter at the same time"; beyond that see §6.
```

The pattern is: scene → guarantee → mechanism → limit. Four beats. If a passage needs a fifth beat to be true,
the requirement is too vague to explain yet — return to the PRD rather than adding metaphor.
