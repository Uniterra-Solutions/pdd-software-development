# The `AGENTS.md` format

One file per studied directory. Its reader is an agent that is about to change code in that directory and has
thirty seconds; its second reader is a human onboarding. Everything in it is either a claim about present
behaviour with a citation, or a pointer to a child file.

## 1. Required shape

```markdown
# {member name}

<!-- study:begin -->
## Scope

What this directory is responsible for, in one paragraph, in terms of what callers get. Not a feature list.

## Entry points

| Entry point | Invocation | Site |
| --- | --- | --- |
| HTTP `POST /v1/jobs` | `POST /v1/jobs` | `src/handlers.rs:41` |
| CLI `serve` | `myapp serve --mode {mode}` | `src/main.rs:77` |

## Branches

| id | branch | behaviour (observable) | trigger (quoted) | site | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `B01` | … | … | … | `src/handlers.rs:88` | … | … |

## Selection paths

```mermaid
flowchart TD
  …
```

## Invariants and traps

Rules that hold today and would not survive an innocent-looking edit: ordering, atomicity, a lock's scope, a
cache that must be invalidated before the write, a field that must stay optional for old clients. Each with the
line that enforces it.

## Verify

The commands that exercise this directory, cheapest first: build, one suite, one CLI invocation.

## Nested package roots

| Path | Why it is a separate unit | Round |
| --- | --- | --- |
| `src/server/` | own router and own handler set | 2 |

Or `None — this directory is a leaf; no deeper unit owns an entry point.`

## Provenance

- generated: `<40-char commit>` @ `<YYYY-MM-DD>`
- by: `pdd:study` round `{n}`
- re-check: `git log -1 --format=%h` against `generated:`, then `git diff --name-only {base} HEAD -- {unit}`
<!-- study:end -->
```

Everything between the two markers is generated and may be replaced wholesale on a re-run. Everything outside
them is human-owned and is never touched.

## 2. The marked-block rule

`AGENTS.md` is a file humans also write — onboarding notes, dos and don'ts, contacts. A tool that overwrites it
destroys the only part with a maintainer. So:

- **no file → create it** with the block, in the shape above;
- **file exists without markers → append** the block at the end, after one blank line, leaving every existing
  byte untouched;
- **file exists with markers → replace only** what lies between them (markers included), leaving everything
  outside intact;
- **a human rule conflicts with a reconstructed branch** → do not edit the human rule. Record it in the
  `Branches` table's `notes` as `contradicts: {quoted human rule}` and report it. The file the humans maintain
  is the authority on what they meant; the inventory is the authority on what the code does, and a disagreement
  between them is the most valuable thing this skill can surface.

Regeneration also replaces the provenance block, which is why the commit is inside the markers: the claim "this
was true at `{commit}`" is a property of the generated block, not of the file.

## 3. Provenance and staleness

- `generated: {commit} @ {date}` — the tree the study read. Without it a file cannot be distinguished from one
  written against code that no longer exists.
- `by: pdd:study round {n}` — which round produced it, so a later reader knows whether a nested directory was
  ever studied.
- `re-check: …` — the exact command that re-verifies citations, so "is this file still true?" is one paste.

Re-running after the code moved is a diff question, not a rebuild question:

```
git diff --name-only <recorded-commit>..HEAD -- {member}/   # a member only re-runs if this is non-empty
```

A full re-run rewrites files whose claims are still true, buries the real drift in noise, and replaces citations
that were correct with citations that are also correct.

## 4. Nesting: parent points, child owns

| Level | Carries | Does not carry |
| --- | --- | --- |
| root `AGENTS.md` | the index of every file, repository-level rules, how to run one member's tests, where shared fixtures live | any member's branch table |
| member `AGENTS.md` | entry points, branches, selection paths, invariants of that member | the detail of a nested package root's branches |
| package-root `AGENTS.md` | the same, for its own entry points | restatements of the parent's rules |

The parent names each child with one clause ("own router and handler set") and links the path; the child owns
the rows. A sentence in two files will drift, and the deeper file wins by proximity — which is how an agent ends
up following a rule the parent already retired.

Where a branch belongs to a boundary rather than to one directory (a dispatch that hands off downward), the
parent keeps the row with `delegates to {child}`, and the child keeps the rows for what happens inside. Both are
true, and neither is a copy of the other.

## 5. Language and verbatim identifiers

Write in the language the repository's existing documentation uses — an English repo gets English, a Chinese
repo gets Chinese — because a file an agent reads is also a file a human reviewer reads. Identifiers, paths,
config keys, enum variants and predicates stay verbatim, in backticks, in whatever the surrounding language is.
Translating `Mode::Stream` into prose is how a citation stops being resolvable.

## 6. What does not belong in the file

- **Prescriptions.** "This module should be split" is a plan; `pdd:plan` writes plans. The inventory records
  what is, and the closest it comes to advice is a `traps` entry naming a consequence.
- **Feature history.** "Added in 2023 for the partner integration" cannot be verified from the tree and ages
  badly; a commit reference in `notes` is the checkable version.
- **Architecture claims nobody checks.** If a rule matters, cite the line that enforces it. If no line enforces
  it, it is an aspiration; say so in `Invariants` with `not enforced`, and let the reader decide.
- **The whole branch table of a child.** That is what the child file is for.

## 7. The delta write

A refresh edits a block that already exists. The branch table is where the rules bite, in this order:

| What the diff shows | What happens to the row |
| --- | --- |
| a cited line moved, predicate unchanged | same id, new `site`, trigger re-quoted from the new line |
| the predicate changed | same id, new trigger, behaviour re-read against the new arm |
| the branch is gone | the row is deleted, its id retired and named in the report; ids are never renumbered |
| a new branch | the next free id; nothing else renumbered |
| a new entry point | a new row set and its own graph; the existing graphs are left as they are |
| nothing under the unit moved | the block is not touched; only the provenance line changes |

Two write rules follow from that:

- **Preservation.** A row whose cited file ended the window unchanged is copied byte for byte — id, cells,
  spelling, notes. Rewording it is a claim that the code changed, and the diff says it did not.
  `git diff -- {file}`, read before the refresh is committed, shows whether such a row moved or vanished.
- **Provenance.** `generated:` keeps its shape, because that is what the recon greps for; the refresh records
  where it came from on the next line:

```markdown
- generated: `{head sha}` @ `<YYYY-MM-DD>`
- by: `pdd:study delta <base8>..<head8>`
- re-check: `git log -1 --format=%h` against `generated:`, then `git diff --name-only {base} HEAD -- {unit}`
```

`round {n}` belongs to a first study. A file refreshed twice carries the latest base, and the chain of earlier
bases lives in `git log -p -- {unit}/AGENTS.md`, which is where a reader looking for history should end up.

The block is still generated, so replacing it wholesale is not a violation in itself — the content is what
must not move. The distinction matters because a human merges this file: a diff of six rows is reviewable, a
regenerated block is not, and the second one hides the sentence that actually changed.
