# The specification for invoking review subagents

The main agent uses this document to dispatch reviewers. It governs only "how to dispatch"; the criteria for the review content are in the two type specifications.

## 1. The two paths that must be included

Every brief must paste two paths, neither may be missing:

```
Task file directory:  <plan-dir>/tasks/              <- this unit's task files are inside, read-only
Your spec:            <pdd:review>/references/reviewer-<type>.md   <- type = test-construction | code-reading
Base spec:            <pdd:implement>/references/subagent-charter.md <- compilation scope, naming, reporting
```

**Why paths rather than inline text.** Three reasons:

1. pasting inline text equals rewriting the contract at dispatch time; once the two copies drift, the subagent follows whichever one it read last;
2. specification files evolve, and a pasted-in dead copy does not change with them;
3. the brief is an order of magnitude smaller, and the saved context goes to reading code and constructing counterexamples.

**Paths must be validated.** Run `test -f` on every path before dispatching; a wrong path does not report "wrong path", the subagent merely says "the task is unclear".

## 2. The minimal content of a brief

```
Your identity:   <test-construction | code-reading> reviewer   <- determined by the Class of the tasks in scope, may not be changed by yourself
Your unit:       <unit id>
Your scope:      <task id list, at most 3>
Task file directory:  <plan-dir>/tasks/            <- read-only
Your spec:       references/reviewer-<type>.md <- follow it
Base spec:       pdd:implement/references/subagent-charter.md
Standard:        <plan-dir>/PRD.md, <plan-dir>/TASKS.md  <- read-only
Questions to answer: <3-6, each decidable>
Output:          <finding format; test-construction type additionally attaches patch and command>
Forbidden:       change production code / change PRD, TASKS, task files / add dependencies / run the full suite / create review-only directories
```

**Identity comes from a table lookup, not from choosing.** Compare against this table before dispatching; if the `Class` is not in the table it is a plan defect (stop and report, do not pick a convenient type):

| Task `Class` | Reviewer | Spec file |
| --- | --- | --- |
| **Behaviour group** | | |
| `construction` | Test construction | `reviewer-test-construction.md` |
| `verification` | Test construction | `reviewer-test-construction.md` |
| **Structure group** | | |
| `migration` | Code review | `reviewer-code-reading.md` |
| `removal` | Code review | `reviewer-code-reading.md` |

**Opening self-check (write it into the brief).** After reading the task files, the reviewer must confirm that the type given in the brief matches the `Class` of those tasks; if they do not match, stop and report, do not "do as told". This is the last line of defence, used to block the degradation of "when unsure, dispatch code review".

**Questions to answer** are written as decidable questions, not as "review this module". Example: "Does the rejection classification of `REQ-F-deposit-2` hold in the `frozen` state?" "Does the dependency rule of `REQ-A-1` have a corresponding check, and does it bite?"

**Give no hypotheses.** The brief does not write "I suspect X has a bug", nor relay the main agent's reading. The reviewer's value comes from independently re-reading the source text; once anchored, it will only confirm your guess.

## 3. The shape of the dispatch

- **One subagent per unit, and the `Class` within a unit belongs to the same group** (behaviour group = construction / verification; structure group = migration / removal). Mixing two task classes means one brief with two acceptance objects; split the unit, do not let the reviewer review both sides shallowly.
- **Scope cap of 3 tasks.** Not a quota, a cap: findings must be attributable to tasks, and the owned set of 3 tasks still fits in context. Beyond that, split the unit, do not compress the brief.
- **Serialize on the same file.** As long as the scopes of two units touch the same test file or the same module, serialize them along the DAG - one writes, one only reads, and running in parallel makes the reading side see a half-finished product.
- **Dispatch the whole batch, then end this round.** Do not poll; completion notifications are handled by batch.
- **Split into waves when the parallelism cap is insufficient.** Wave order still obeys the partial order of the DAG; do not relax the scope cap in order to fit into one round.

## 4. Collection and handover

- Each subagent reports: findings (per `references/finding-schema.md`), the commands it actually ran with their raw output, the list of test files it changed, and the scope it could not review with the reason.
- **The main agent verifies itself**, not forwards: for test-type findings it must re-run and confirm the red leg / green leg itself; for code-review-type findings it must point to line and clause.
- "I think this is wrong" in a subagent report is not a finding; a judgement without input, command or clause is returned and does not enter the report.

## 5. Failure modes

| Shape | Cost |
| --- | --- |
| Pasting only the task file path, not the type spec | The reviewer uses its own set of criteria and the two reports cannot be compared |
| Pasting inline text rather than the path | Two contracts: acceptance against one, execution against the other |
| A hypothesis written into the brief | The review becomes confirmation bias, and nobody looks for the real defect |
| 4 or more tasks in one unit | Findings cannot be attributed, and context is shredded |
| Dispatching code review when unsure | Behaviour-type tasks lose their counterexamples and are left with "looks reasonable" |
| Mixing construction and migration within a unit | One set of criteria covers two acceptance objects, and both sides are shallow |
| Two units on the same file in parallel | A test is being written while it is being read, and a half-finished product is read |
| Writing the subagent's judgement straight into the report | A finding without command and clause is opinion, not evidence |
