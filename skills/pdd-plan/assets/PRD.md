# PRD — <slug>

| Field | Value |
| --- | --- |
| Plan | `<slug>` — <the change in one line> |
| Date | <YYYY-MM-DD> |
| Owner | <the person who owns the business rule, or the architecture> |
| Status | Draft / In review / Handed off |
| Source | <issue / ticket / conversation of date / regulation> |
| Next | `pdd-decompose` for a multi-behaviour or architectural change; `pdd-implement` for one behaviour |

**What this document is.** Business logic, behaviour, and the architecture the code must obey. **If a
sentence can be read out of the code, it does not belong here** — flags, schema keys, file paths, module
layouts, endpoint tables, response shapes, timeouts and test designs are discovered by the later phases.
The one exception is the target architecture in §5: that structure does not exist yet, so it cannot be read
out of anything, and it is the deliverable of an architectural requirement.

Requirements come in two kinds. **功能需求 `REQ-F-…`** are accepted by modelling their behaviour.
**架構需求 `REQ-A-…`** are accepted by the code obeying the architecture, checked executably — not by a
test that happens to pass.

## 1. 業務與問題

<Who does what today, what breaks for them, and which outcome makes this change worth doing. One or two
paragraphs. No history, no exploration.>

## 2. 角色與物件

| 角色 | 它是誰 | 可以做什麼 | 會被拒什麼 |
| --- | --- | --- | --- |
| <actor> | <the person or system> | <allowed operations> | <the refusals that apply to it> |

- **物件與數量**: <noun — unit, bounds, whether it is reversible>

## 3. 業務規則

| 操作 | 前置條件 | 結果 | 之後必須成立 |
| --- | --- | --- | --- |
| <operation> | <who may invoke it, in which state> | `apply` / `refuse:<class>` | <postcondition> |

- **狀態與轉移**: <state — legal moves — moves that must never happen>
- **不變量**: <the law that holds in every state, with the range it quantifies over>
- **刻意不編碼**: <rule left out — the reason>

## 4. 行為

One section per flow. A flow is what a person does from trigger to outcome; it is also the unit the later
phases model and verify against. Do not organise this by endpoint, file or layer.

### F1 <flow, in the operators' words>

- **誰、何時觸發**: <actor and the moment>
- **正常路徑**: <trigger → each step → outcome, in business terms>
- **拒絕路徑**: <who is refused, under which condition, which class, what they see, what they can do next>
- **邊界行為**: <only the boundaries that change the business outcome>
- **絕不可發生**: <the outcomes that are unacceptable rather than inconvenient>
- **在何處可見**: <the screen, report or statement where a business person sees it holding>

## 5. 架構（只有架構需求時才需要）

The target structure and the rules the code must obey afterwards. This section describes structure on
purpose: for an architectural requirement the structure is the deliverable, and nothing in the current tree
can supply it.

- **模組邊界與職責**: <module — what it owns — what it must not reach into>
- **依賴方向**: <A may depend on B; A must not depend on C>
- **對外表面**: <the symbols other parts may use; everything else is internal>
- **分層／分區與循環**: <layers, allowed edges, cycles forbidden>
- **效能（如涉及）**: <what is measured, with which instrument; current baseline; target budget; which
  structural change produces the difference>
- **這次不動的結構**: <structure deliberately left alone, with the reason>

## 6. 需求

### 6.1 功能需求

One claim per requirement, three lines each. The prefix names the flow it belongs to.

#### REQ-F-<flow>-1 <the behaviour in one falsifiable sentence>

- **由規則**: <the §3 row or §4 state transition this comes from>
- **失敗樣貌**: <who discovers what is wrong, and when, if this does not hold>

#### REQ-F-<flow>-2 <…>

- **由規則**: …
- **失敗樣貌**: …

### 6.2 架構需求

`REQ-A` 是「程式碼遵守架構」這一類。驗收不是測試，是 §5 規則的可執行檢查。

#### REQ-A-1 <the structural rule in one falsifiable sentence>

- **範圍**: <which modules, packages or symbols the rule quantifies over>
- **違反樣貌**: <what a violation looks like in the tree, concretely>
- **如何檢查**: <the executable check that returns pass or fail; naming the tool is allowed here>

#### REQ-A-2 <…>

- **範圍**: …
- **違反樣貌**: …
- **如何檢查**: …

## 7. 決策（記錄；後續變更以新決策取代）

Only decisions the code cannot recover: external promises, regulatory constraints, compatibility burdens,
cost ceilings, time windows, and the architecture chosen over its rival.

- **D1 <topic>**: <the chosen value>. Rejected: <alternative> — <why, one clause>.

## 8. 對外介面

| 表面 | 誰用 | 看到什麼 | 出錯時看到什麼 |
| --- | --- | --- | --- |
| <screen / CLI command / report / statement / third-party API> | <actor> | <what it shows> | <what an error looks like to them> |

Route strings, flag names, payload shapes and schema keys are confirmed by `pdd-decompose` against the tree.

## 9. 非目標

- **N1** <adjacent thing this change deliberately leaves alone, with the reason>

## 10. 未定與風險

- **未定**: <question — the observation or command that closes it — the requirement it affects>
- **風險**: <risk — impact — mitigation>

## 11. 交接

- Defaulted decisions: <list with `defaulted — vetoable until work starts`, or `none`>
- Chosen next skill: <pdd-decompose | pdd-implement>
- A later change enters as a new decision, dated, with the id it supersedes.
