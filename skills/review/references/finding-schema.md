# Finding schema and adversarial case checklist

## 1. Finding schema

A finding is a proven counterexample, or a risk explicitly marked as unproven. Write the two separately.

```
id:        R-<unit>-<n>
axis:      functional | architectural
layer:     intra-module | cross-module | integration | plan
task:      <task id> (fill none at the `plan` layer)
requirement: <REQ-F-... / REQ-A-... / missing / hollow / unformal>
severity:  critical | high | medium | low
confidence: confirmed | unproven
file:      <path:line>
clause:    <the verbatim rule it violates: one sentence from the PRD, one sentence from the task file, or one declared architectural rule> (required for architectural)
input:     <minimal input or operation/lifecycle sequence> (required for functional)
expected:  <the value or behaviour the standard requires>
actual:    <the observed value or behaviour>
test:      <test file :: test title, fill none for static findings>
command:   <the command the reviewer actually ran>
evidence:  <patch path, output file, or line range>
reproduced: yes | no
```

- **`axis` determines the shape of the evidence.** `functional` needs input/expected/actual and a command that can be re-run; `architectural` needs a `clause` and a named `file:line`, and does not necessarily have a command.
- **`severity`**: critical = wrong result, data loss, security hole, core invariant that never holds; high = required behaviour unreachable in production; medium = boundary, error path, non-core invariant; low = proven but with no correctness impact.
- **A behaviour-type finding without a command and a minimal input is `unproven`**, not a bug.
- **`layer: plan`** refers to a defect in the standard itself, not a defect in the code: a `REQ-A` with no corresponding C check, a flow with no model, one `REQ` spanning two flows, a migration with no oracle, a removal with no absence proof, a task class that does not match its content. `file:` points at a line in `PRD.md` or `TASKS.md`, and `test:` is filled with `none`.
- **Test location**: the functional location of that behaviour, named per the repo; `review_test/...`, `tests/review/...`, `adversarial.spec.ts`, or any file name containing a task id (`t3_*.spec.ts`, `guard_t3.spec.ts`) are not legal locations - the product gate will never collect them.
- **`evidence`**: test-construction findings give the patch and the command output; code-review findings give the line range and the cited clause.

## 2. Evidence requirements for the two axes

| axis | who produces it | must have | not accepted |
| --- | --- | --- | --- |
| functional | test-construction type | minimal input, expected vs actual, command, red leg (red today), green leg (green after applying a minimal temporary fix) | merely describing "this looks wrong", a green test, a domain with only one point |
| architectural | code-review type | `clause` (the verbatim text of the PRD or the architectural declaration), `file:line`, whether the C check exists and whether it bites | "style preference", "not good enough" without a clause, downgrading a `REQ-A` violation to a review note |

## 3. Adversarial case checklist (for the test-construction type)

For each variable and state, try each in turn:

- **Value boundaries** - empty, missing, minimum, maximum, zero, negative (if legal), duplicate, non-ASCII, malformed, overlong, wrong unit, wrong sign.
- **Sequence boundaries** - out-of-order arrival, duplicate delivery, retry after success, replay, lost message, partial batch, restart midway, idempotence broken.
- **State-machine boundaries** - every legal transition and every illegal transition; transition out of a terminal state; concurrent transition of the same entity; teardown during an operation.
- **Cross-module boundaries** - contract mismatch, version skew, missing field, extra field, stale cache, write-read order, partial commit, timeout, cancellation, backpressure, error translated into success.
- **Concurrency** - two writers on the same entity, reentrancy, lost wakeup, reversed lock order, a read between commit and cache refresh, an operation still in flight after hold.
- **Failure injection** - every external call fails, failure after commit, malformed data returned, hanging, succeeding twice; at every point assert the defined safe result.
- **Resource lifecycle** - init -> use -> teardown -> restart; leaks, double release, stale handle, orphan task, unreleased hold.

## 4. Hollow test audit (for the test-construction type, audit the existing tests first)

A test that a wrong implementation still passes is hollow:

- the assertion reads a declaration, a source string, a symbol count, or a table name;
- the asserted value is filled on every path, so "executed" and "not executed" look the same;
- the measuring instrument does not bracket the claimed behaviour (counter reset too early, wrong seam);
- two locals that cannot possibly affect each other are compared against each other;
- one fixture is treated as `every` / `never` / `identical`;
- the expected value is the test's own mock echo, a fixture constant, or a snapshot of the current output;
- the generator is shrunk until the claim becomes trivially true, or the observation is moved to a test-only twin.

**The fix**: point the assertion at the production value the claim names, restore the full domain, add a negative control with a naive wrong implementation, and make the minimal input actually red. Prefer fixing that one in place rather than adding a second test.

## 5. Cross-module checklist (both types use it)

For every caller/callee or producer/consumer pair:

- who owns each field and state, and who may change it;
- what the caller assumes has been committed when the callee returns;
- ordering and atomicity across the boundary;
- visibility of lifecycle and teardown;
- timeout, rejection, stale data, retry, cancellation, partial failure;
- data format, unit and version compatibility;
- concurrent interleavings and duplicate delivery;
- the production call chain from entry point to the modified surface, with `file:line`.

A property on the boundary must quantify the states of both sides and be observed at the seam. If the observation falls only inside one of the sides, that boundary has not been modelled.

## 6. Architecture review checklist (for the code-review type)

For each `REQ-A`:

- **Is the rule present**: does PRD §5 write down the structure it wants (module boundaries, dependency direction, public surface, layering, budget).
- **Is the check present**: does the corresponding C check exist in the repo, and are its owned files not in production code.
- **Does the check bite**: is there a record of injecting one violation and confirming it goes red; a check that has never gone red has proven nothing.
- **Does the code comply**: dependency graph, import list, public surface, cycles, module size, measured performance values, item by item against the declaration.
- **Is a bypass left behind**: `allow` / `disable` silencing, hiding the violation in test files or generated artifacts, taking a second path around the declared entry point.
- **Is it merely a restatement**: if the C check just copies the declaration without any measurement, it is documentation, not a check.
