# Choosing the diagram

You are the cartographer for one directory. This file decides **whether** to draw, and **which** shape to
draw. The selection-path conventions are in `references/mermaid-selection-path.md`; the sources to copy are in
`references/mermaid-templates.md`.

The default is always the same: **one selection-path flowchart per entry point.** Anything else has to earn its
place by answering a question the flowchart cannot.

## 1. Ask what question the picture answers

| The question a reader will ask | Draw | Template |
| --- | --- | --- |
| "Which branch runs for this input, and what makes it run?" | selection path (`flowchart TD`) | `mermaid-templates.md` §1 |
| "Who decides this, and where is the handoff?" | swimlanes | §7 |
| "In what order do the calls happen, and what is skipped?" | sequence | §2 |
| "Which states are legal, and what moves between them?" | state | §3 |
| "Which variants of this type exist?" | class (enums, traits, implementations) | §4 |
| "What does the stored data look like, and which row wins?" | ER | §5 |
| "Which requirement does this branch serve, and what checks it?" | requirement | §6 |
| "Which service does this unit talk to?" | architecture | §8 |
| "Which layer may import which?" | block | §9 |
| "What is this unit made of, before going deeper?" | mindmap | §10 |

Two diagrams per entry point is the practical ceiling: the selection path, plus at most one structural diagram
when the unit's branches are mostly *type* branches. A third diagram usually means two entry points were merged
into one picture.

## 2. When not to draw at all

A diagram that restates a table one-for-one, without adding a traversal, is noise — it doubles the maintenance
and halves the trust when the two drift. Do not draw when:

- **there is one branch.** A single `if` is a table row; a flowchart of it is a picture of a sentence.
- **the content is a list.** More than about seven sibling items with no ordering is a table, not a graph.
- **the reader's question is "what is the value?"** Numbers, counts and proportions belong in a table unless
  there is exactly one dimension.
- **you would need a second diagram for the same fact.** Pick the shape that answers the more expensive
  question and link the rest.
- **the only difference between two nodes is colour.** Colour is decoration; the id and the label carry meaning.

## 3. What each shape cannot do

Mind the mismatch, because a wrong shape silently drops information:

| Shape | Cannot show | Use instead |
| --- | --- | --- |
| flowchart | data shape, cardinality, storage | ER or class |
| sequence | which predicate *decided* the branch — only that a message happened | flowchart (or note the predicate on the arrow label) |
| state | concurrency or two owners of one state | swimlanes, plus an invariant in the table |
| class | runtime order or config defaults | flowchart / sequence |
| ER | control flow or which branch reads the row | flowchart, with the row named in the trigger |
| mindmap | predicates, ordering, or anything with a direction | flowchart |

## 4. Rules that apply to every shape

1. **Ids come from the branch table.** A node labelled `B07` is a claim that row `B07` exists; the checker
   compares the two sets.
2. **Every edge says why it was taken.** `yes` / `no` / the value. An unlabelled edge loses the conjunction.
3. **Predicate nodes carry `file:line`.** The diagram is navigated by opening files.
4. **No code in nodes, no function names as nodes.** Nodes are the things a caller observes, or the predicate
   that selects them.
5. **Declare the direction once** (`TD` for a pipeline, `LR` for a chain of peers) and keep it for the file.
6. **Prefer the stable tier** (`flowchart`, `sequence`, `class`, `state-v2`, `ER`, `requirement`) when the file
   is committed next to code; the beta types are for local documents or a known renderer version.
7. **A block that does not render is not evidence.** Run the renderer, or say in the report that only the lint
   ran.

## 5. Two worked choices

**A handler module with a mode enum, a size limit and an auth guard.** The reader's question is "which branch
runs" → one selection-path flowchart per entry point, three predicates, four terminals including the default.
The enum is visible in the predicate labels; it does not need a class diagram, and drawing one would create a
second place where the variant list can go stale.

**A worker package whose behaviour is a job state machine, driven by a queue.** The reader's question is "is
this transition legal" → one state diagram, with the guard on each edge. A selection-path flowchart would
repeat the same edges as predicates and tell the reader nothing about the states, so it is drawn only for the
one entry point that is not state-driven (the cancel handler).

## 6. Report what you chose, and why

The report line is `graph: {n} mermaid blocks ({types}); render run: yes|no (lint only)`, and if you drew a
shape other than the selection path, one clause saying which question it answers. That clause is how the main
agent tells a considered choice from an accident.
