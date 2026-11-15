# Parity requirements — writing "everything A can do, B must be able to do"

A coverage mandate needs both of its sides enumerated as sets, because the prose form ("all operations
are available") is unfalsifiable and drifts on the first new endpoint. Write the requirement as a set
relation between two enumerated sets: the authoritative side and the consumer side.

## 1. Enumerate the authoritative side at run time

The authoritative set comes from the running application, because a grep over route files misses
decorated prefixes, autoload directory names, `autoPrefix` overrides, multi-method registrations and
placeholder routes. Boot the real application and read the surface that the application publishes about
itself.

Route table, Fastify + tsx (a throwaway probe at the repo root, deleted before the session ends — a
leftover probe enters the type gate's scope and can break an unrelated commit):

```ts
import { buildApp } from './src/app.ts';
import { openDatabase } from './src/db/connection.ts';
import { runMigrations } from './src/db/migrate.ts';

const db = openDatabase(':memory:');
runMigrations(db);
const app = await buildApp({ db });
await app.ready();
console.log(JSON.stringify(app.routeTable, null, 0));
await app.close();
```

The probe shape generalises to any system that reports on itself: `app.router`/`app.routes`, a plugin
registry, a command registry, a `--help --json` dump. A runtime probe reveals two facts that no file
listing shows:

- **Placeholder routes** exist only to return 405 or 404, and each one belongs on the allowlist rather
  than in the consumer.
- **Response shapes** split into bodyless (204) responses and envelope responses, and that split decides
  the consumer's `--json` contract for those operations; the route name cannot decide the contract.

## 2. Fix the three sets

Parity rests on three fixed sets. `A` is the enumerated authoritative set of `(method, route)` pairs,
written exactly as the framework prints them (`/api/accounts/:id`, rather than the resolver's internal
pattern). `R` is the consumer registry, holding one entry per command with its `method`, `route` and
required permission. `E` is the allowlist of authoritative members that carry no consumer operation.

The requirement holds when both differences are empty: `A \ E \ R = ∅` and `R \ A = ∅`. One direction
alone lets a command survive a route that no longer exists.

The allowlist carries a fixed cardinality ("`|E|` is exactly 2"). The allowlist is otherwise the
cheapest place to hide drift, and the test meant to expose growth absorbs the drift instead.

## 3. Name the mutations that must turn the gate red

A set-equality gate accepts two empty sets forever, so acceptance includes showing the red for each of
these mutations:

- a new authoritative member with no consumer entry;
- a consumer entry with no authoritative member;
- a third allowlist entry.

## 4. Count the allowlist, and leave `A` and `R` uncounted

Only the allowlist carries a number. `A` and `R` both grow as part of the very change being planned,
because the new endpoints are half the work, so an absolute count ("the CLI covers 23 endpoints")
becomes a second truth the moment the plan is implemented, and that count contradicts the plan's own
requirements. Fix the relation and the allowlist's cardinality; the two sides stay uncounted.

## 5. State the assumption that makes one side imply the other

The mandate usually reads "everything the *page* can do", which names a different set from the API set.
The two sets coincide under one condition: the page has no privileged channel. Verify that condition by
finding the single client module that every page call goes through; where several such modules exist, or
one page talks to the server directly, the parity requirement holds by construction only for the page's
observed requests, and the requirement must be stated against those requests.

Runtime enumeration beats a source-shape test that scans call sites, because a test over string
literals measures source shape and breaks on refactors that change nothing observable.

## 6. Register operations, one entry per command

Consumer entries describe operations. Three status transitions may share one permission and one route
family while remaining three distinct commands with three distinct routes, and one endpoint may carry
both a read and a write and need two commands. Registry uniqueness therefore rests on the command path,
and every entry names exactly one `(method, route)` pair.
