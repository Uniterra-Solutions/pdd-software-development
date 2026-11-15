# Behaviour-preserving refactor — extracting shared libraries

Depth for any task whose acceptance is "the same behaviour, from fewer declarations": a dedup extraction, a
route-to-service move, a type program that gains a new source of truth. The obligation is inverted from a
feature: a wrong feature fails one test, a wrong refactor passes all of them and changes a payload.

## 1. Freeze the gate before touching code

Record four baselines, each with the command that produced it, and put them in the PRD or task file:

- suite: `npm test` → exact `Test Files` and `Tests` counts (not "all green");
- visual: the screenshot suite's passed count and its diff-pixel threshold ("74 passed, maxDiffPixels 0");
- types: `npx tsc --noEmit 2>&1 | grep -c 'error TS'` — a nonzero baseline is normal, the invariant is
  *not rising*, so write the pre-existing count down and where it lives (usually the test tree);
- sizes: the recorded budgets and the measured values from the built artefact.

Run each once *before* the first edit. A gate you first run after the change cannot distinguish your
regression from the tree's. When a leg of the gate has never observed your artefact class (a unit suite
never sees computed style), add its command rather than claiming coverage.

## 2. Order the work units by dependency, one commit each

A work order that has survived several extractions:

1. **declaration** — the value-domain constants (zero imports, so schemas and types cannot form an import
   cycle), then the DTOs derived from the runtime schema (`z.infer`), then the row types derived from the
   DTOs. Everything downstream now compiles or fails together.
2. **error type** — one error carrying `code`/`statusCode`/extra fields, one handler at the app boundary,
   and the per-module classes deleted. Delete the route-level `catch` blocks in the same commit or the
   old and new producers coexist and only one of them is exercised.
3. **projection** — one row-to-view mapper for the entity read by several services.
4. **parsing** — one query/pagination reader for every list endpoint.
5. **transactional actions** — one function per write idiom (revoke sessions, append event, bump version).
6. **context** — one actor extraction for every protected route.
7. **route → service** — move the business body into a service module, leave the file holding HTTP binding
   only. A route plugin that needs the framework (`FastifyRequest`) cannot live in the service layer;
   keep the factory where it is and move the logic.
8. **frontend** — shared types by `import type` from the server DTOs, one formatter, one request hook.

Suite after every unit. Each commit's message states the duplicate count it removes ("one HttpError
replaces nine per-module error classes"), because that is the claim review audits.

## 3. Identity across a module boundary

**`instanceof` on your own class fails across the framework's dynamic `import()`.** A router or plugin
autoloader loads handlers through its own loader; under the test runner those modules can land in a second
module graph, so `error instanceof HttpError` is `false` at the boundary. The failure is quiet: the app's
error handler falls through to the generic branch, and the response keeps `code`/`message` while dropping
its optional payload (`current_version`, the conflicting row, the reference list). Every test asserting the
envelope alone stays green, so the defect surfaces as four red tests that assert the extras, against code
that reads correctly. The short form of this entry is in `pitfalls.md`.

Dispatch on structure instead — an `isHttpError(value)` guard checking a string `code`, a numeric
`statusCode` and a callable `body()`, and type it as a predicate so the handler narrows. Prove the seam
with one probe that constructs the error through the route path, not by reasoning about it.

## 4. Runner discipline

- **One invocation at a time, from the shell.** Two overlapping runner processes (a full suite plus a
  single-file rerun, or a suite started from inside a script) produce mass phantom failures whose message
  is a native-loader error on a production file you never touched — `ERR_UNKNOWN_FILE_EXTENSION` on
  `.ts`, tens of files failing with no root cause. Kill the strays, run one isolated file, and only then
  believe a red. A red that names a file outside your diff is contention until one isolated run says
  otherwise.
- **A spec belongs to the runner that can transform its imports.** A node-project test that imports a
  module owned by the browser bundle can pull the whole web graph into the wrong transform pipeline and
  take unrelated `inject`-based tests down with it. Put the assertions in the project that owns the
  module's runtime (the jsdom project for a formatter consumed by React), and keep the node project for
  server seams.
- Long suites and the tool layer: a runner invocation that exceeds the foreground limit becomes a
  background process; poll it and read the final counts. Do not launch a second copy "to see if it is
  stuck".

## 5. Frozen artefacts react to every edit

- **An evidence pack that records counts is red by construction** the moment the suite grows. Regenerate
  through the repo's script; never edit a recorded number. If the regenerated number disagrees with a
task-file expectation, that disagreement is a finding to report, not a number to smooth.
- **Commit new spec files before running the pack's verifier.** A verifier that asserts the tree is clean
  treats an untracked new test as a violation, so the pack fails on files that are correct.
- **A source-wide codepoint gate counts your comments.** A glyph/coverage test that scans every character
  in the source tree turns a new CJK comment into a failure; regenerate the subset through its script,
  then re-measure the asset against its budget and re-run the visual baselines, because the font bytes
  changed even though no markup did.
- **Every byte budget is a measured post-condition**, so record the new value beside the limit. A size
  that grew because a server-only module leaked into the client bundle is the finding; the growth of an
  intentionally shared module is not.

## 6. Widening a type program finds the fixtures that lied

Turning on type checking for a directory that was never checked (a browser tree excluded from `tsconfig`)
produces a bounded burst of errors, and most are real: fixtures written against the *declared* shape
(`id: 1`) rather than the *served* shape (a UUID string). Fix the value, not the type — and record it in
the amendment ledger, because a fixture edit looks exactly like a weakened test to a reviewer who only
sees a diff. State the evidence: no `expect` referenced the literal, and the new value matches what the
server sends.

Expect a small number of genuine shape errors in the newly checked tree; each one is a real defect the
program was hiding (a client field typed `number` for an identifier the API sends as a string).

## 7. Negative controls for equivalence requirements

"Behaviour is unchanged" is satisfied by any check that cannot fail. For each frozen artefact, execute a
mutation and record the red:

- add a key to the schema DTO → the row-type assertion, the projection assertion, the mapper's
exhaustiveness and the browser fixture must all fail (one tree: 8 errors across 5 files);
- rename a response field → the contract test must fail by name, not by snapshot drift;
- restore, then confirm the type-check count and the file hash return to their pre-mutation values.

A named wrong implementation is a hypothesis; a recorded red run is the evidence. Mutation on a frozen
artefact costs seconds.

## 8. Amendment ledger

Every deviation gets a section `A<n>` with four parts: **conflict** (the requirement and the code that
contradict it), **measurement** (the command and the number that proves it), **ruling** (what you did and
the principle — value correction vs assertion change; added test vs edited test), **affected REQ**.

The recurring rulings:

- a test that referenced a deleted class by name → assert the surviving contract (status code and code),
  which is usually stricter than the old check; never relax the assertion to keep the import;
- a check the PRD wanted inside an existing test while another requirement freezes that file → write it
  as an added spec file, so the frozen aggregate keeps its floor and the new check has a home;
- a service module that would need the framework type → leave the factory in the route file and move only
  the body; record that the PRD's file list was optimistic;
- two constants with the same value and the same meaning → one definition, one re-export alias.

## 9. Probe the seam no test covers

Assembly is never quantified by a property: an app factory, a CLI entry, a migration runner. Start the
real server against a throwaway database once (bootstrap env supplied), and hit one 2xx, one unknown API
path and one authenticated call. On one extraction this was the only evidence that migrations still apply
and the identifier reached the client as a string. Record the observed status codes in the run notes.

## 10. Report shape

The final message is a table of commits with line deltas, a gate table where every row carries its exact
command and result, a duplicate table (`concept | before | after`) measured with `rg`, the amendment list,
and a **residual findings** section naming what is still duplicated or still has two producers. Closing a
deliverable with "all done" when a known second producer survives is how the next audit re-finds it.
