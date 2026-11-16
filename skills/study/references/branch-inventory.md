# The branch inventory

The inventory is the part of `AGENTS.md` that is worth reading a year later. It answers one question per row:
*for this entry point, which decisions change what the caller gets, and what makes each one fire?*

## 1. What counts as a business branch

A decision earns a row when **the caller can tell which way it went**. The test, applied per conditional:

1. Name the two (or n) outcomes.
2. Ask what the caller observes differently: the response body or status, a field, a side effect (write, emit,
   send, delete), a file on disk, a metric, or the failure mode.
3. If nothing differs that the caller can observe, it is not a business branch. Logging level, an internal
   cache hit, a defensive `assert`, a loop's exit check, a null-guard that cannot fire on the public surface —
   these are implementation, and a row for them costs the reader attention and returns nothing.

The test is deliberate about "the caller": a library's caller is its importer, a service's caller is the
client, a CLI's caller is the terminal. An internal refactor that changes neither is invisible, and a branch
that only changes which internal helper runs is not in the inventory either.

## 2. Branch kinds and what each trigger looks like

| Kind | What selects it | Trigger evidence to quote |
| --- | --- | --- |
| **dispatch** | the request's shape routes to different handlers (`match req.kind`, a router table, a protocol line) | the match arm or route entry, plus the type or schema that makes the arm reachable |
| **mode / config** | a flag, env var or config key, with a default when unset | the read of the key, its default, and where it is validated |
| **data shape** | payload size, presence of an optional field, empty vs non-empty, cardinality | the predicate and the type invariant that permits the case |
| **policy / limit** | quota, rate limit, max depth, timeout, retry count | the constant, its unit, and the branch taken at the boundary |
| **error / retry** | failure class of a dependency call, backoff, circuit state | the error type matched, not the message string |
| **state machine** | current state before the transition (idle → running → failed) | the state enum variant and the guard predicate |
| **environment** | platform, feature build, target, store backend | the `cfg`/`sys.platform`/build-tag predicate, and what the other side does |
| **protocol / version** | wire format version, API version, capability negotiation | the version comparison and the compatibility behaviour |

A conditional that matches none of these is usually the one to exclude.

## 3. The row schema

| id | branch | behaviour (observable) | trigger (quoted) | site | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `B01` | streaming response | body arrives incrementally, `Transfer-Encoding: chunked` | `req.mode == Mode::Stream`, default `Mode::Batch` (`config.toml:12`) | `src/handlers.rs:88` | `POST /v1/jobs {"mode":"stream"}` | cross: `pdd-core` owns the mode parser |
| `B02` | batch response | one JSON body, `200` after completion | `req.mode != Mode::Stream` | `src/handlers.rs:104` | `POST /v1/jobs {}` | the default path |
| `B03` | rejected payload | `400` + `{"error":"too_large"}` | `body.len() > MAX_BODY` (`limits.rs:9`, 8 MiB) | `src/handlers.rs:61` | `POST /v1/jobs` with a 9 MiB body | the boundary is the branch |

Column rules:

- **id** — `B01`, `B02`, … stable within the file; the graph uses the same ids, so a reader can go table →
  graph → table. Never renumber on a re-run: a branch that disappeared keeps its id and is struck as
  `removed`, so a diff shows what changed.
- **behaviour** — what the caller observes, in one clause. Not "calls `stream_response()`".
- **trigger** — the predicate quoted verbatim, plus every config key and default it depends on. Two
  predicates that both must hold are joined with `and`; the graph draws them as two nodes.
- **site** — `file:line` of the predicate itself, not of the function. It is what the checker resolves and what
  the next agent opens first.
- **example** — one concrete input or state that takes this branch. If you cannot name one, you have not
  understood the branch, and the row is a guess.
- **notes** — `cross:` when the predicate reads state owned by another member, `unreachable` when no input can
  take it, `unknown` when the trigger could not be resolved (with the searches performed).

## 4. Making the trigger decidable

A trigger is decidable when another agent can predict the branch without running the code. Three parts:

1. **the predicate, quoted**, with `file:line` — the code is the authority, the prose is the index;
2. **the configuration that participates**, with its default and where it is read — most "why did it do that"
   incidents are a default nobody knew about;
3. **the precedence**, when two branches overlap — "stream wins over batch even when `batch=true`" is the kind
   of sentence that saves an hour, and it is only visible if you read both predicates together.

The default path is the most important row in the table. Every entry point has one — the arm reached when
nothing matches — and it is the branch nobody documents and everybody depends on. If the default is "reject
with 400", write it; if it is "silently treat the input as the first enum variant", write that too.

## 5. Boundaries with other directories

- **Cross-member**: a branch whose predicate reads a value produced or configured elsewhere is recorded with
  `cross: {member}` and *not* duplicated. The member that owns the value owns the row; the other file links to
  it. Two copies drift and then contradict each other inside one review.
- **Nested package root**: if a branch's behaviour is implemented below the directory you are studying, record
  the branch at the boundary (`delegates to {package_root}`, with the call site) and report the package root
  as a round-N candidate. You are mapping *this* directory's decisions; the child maps its own.
- **Unreachable**: two flavours, and both are findings rather than prose. *Cannot* be reached (a feature flag
  the build never sets, an arm shadowed by an earlier one) → `unreachable`, routed to `pdd:decompose` as a
  removal candidate. *Not* reached today (a legitimate mode nobody configures) → a row like any other, with
  the example stating what would reach it.
- **Library boundaries**: an exported function that documents "returns `None` if the key is absent" has a
  branch even if no local caller takes it. Public surfaces are branches because external callers take them.

## 6. Exhaustiveness check before accepting a table

- every entry point in the file's entry-point section has at least one row, and its default row;
- every `match`/`switch`/`elif` chain on the public path is accounted for — either as rows or in an explicit
  "excluded, because …" list, so the reader knows the difference between "no branch here" and "nobody looked";
- every row's `site` resolves (the checker does this mechanically);
- every row has one example;
- branches that share a config key are adjacent in the table, so their precedence reads as a block.
