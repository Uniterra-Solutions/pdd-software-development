# Decomposition pitfalls

Every row is a real failure mode, with its mechanism and its fix. Read this file before dispatch, and again
when a reviewer disagrees with the cut.

| Symptom | Cause | Fix |
| --- | --- | --- |
| The purpose is written as internal structure ("add XxxService") | The direction of a construction task is inverted | Write the purpose as the outcome a caller can observe |
| One task both moves structure and changes behaviour | Two classes mixed; the acceptance objects conflict | Split into migration and construction; let the migration go green first, then change behaviour |
| A migration with no oracle | Saving one verification task | Dispatch verification B/C first to establish the behavioural baseline and the architecture check |
| A removal with no replacement | Reading "not finished yet" as "ready to delete" | Build the replacement first, and have it covered by verification |
| Production code deleted but its tests remain | The tests assert against a mock, so they stay green | The removal task owns the tests that die with the code it deletes |
| One flow with two model files | Two verification tasks in parallel overwrite each other | One model per flow; make the second a shared prerequisite |
| A verification agent edits production files along the way | Class boundary unclear | Report the trace, the seed and the minimal sequence; the main agent opens the task |
| A migration loosens the check that judges it | Self-exemption | Editing a constraint, a baseline or a pin requires a dated amendment first |
| An architectural requirement written as a behavioural test | Confusing a guard with an acceptance criterion | Rule, scope, violation shape and check — all four, or it is not a C task |
| A performance requirement with no baseline | "It got faster" said afterwards | Same-instrument baseline, target budget, the structural change that produced the gain |
| Tasks cut by file or by symbol | A diff split disguised as a decomposition | Cut by seam and flow; every owned file serves one behaviour |
| The task id enters a path, a test title or a filter | Ids change, and the name starts lying | Name it after the function it performs |
| The implementer is stuck between two contradictory instructions | A file it needs is not in `Owned files` | Add it to owned, or give that file to an earlier task |
| The plan claims a surface nobody builds | The PRD's surface list grew and the task set did not | Before dispatch, sweep every surface against every construction purpose |
| No step can say what it leaves untouched | Scope not delimited | Write `Untouched`, and check it in the report |
| The slice is too coarse for any step to go green alone | Two things changed at once | Re-cut until every step can go green on its own |
| Two tasks edit one registry or barrel | Missing shared prerequisite | Give that file its own unit; the others depend on it |
| The plan has a cycle, or a verification node bypasses a gate | Ordering kept in memory instead of in the graph | Draw the gate into the DAG; derive the waves from depth |
| The cut is audited by its author | The author reads the split back as confirmation — same understanding, same blind spot | One fresh auditor per three tasks, reading the PRD first and the task file second, with the class's acceptance criterion in hand |
| The auditor is handed write access | It re-cuts the plan to its own taste, and every id that the register, DAG and trace matrix are indexed by moves with it | The auditor reports; the main agent amends |
| Audit findings adopted without reproduction | "The criterion looks vague" arrives ten times a run, and half of them are wrong | Reproduce each one, or reject it in writing with the reason |
| `floor(n/3)` auditors for `n` tasks | The remainder is a task nobody read, while the report says the audit is complete | `ceil`, and check the covered ids against the register |
