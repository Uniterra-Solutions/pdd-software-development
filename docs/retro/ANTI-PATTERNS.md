# Anti-patterns — pdd

One line per anti-pattern extracted from an incident report in this directory. Ids are never reused or
renumbered; a retired id stays in the table with `retired` in the state column.

Read this before starting a round that reproduces a trigger below. The report behind each id carries the
guideline it answered, the rejected fix classes and the regression criterion; this table is the index,
not the record.

| id | title | trigger (short) | class of fix | date | report | state |
| --- | --- | --- | --- | --- | --- | --- |
| AP-001 | 閘門在比它要驗的引用更窄的 root 上跑 | 檢查工具同時決定掃描範圍與相對路徑解析基準 | 資訊改進 | 2026-11-16 | `2026-11-16-gate-root.md` | active |
| AP-002 | 兩個閘門對立時，改資料去迎合其中一個 | 兩個檢查器對同一產物的不同部分給出互斥要求 | 提示改進 | 2026-11-16 | `2026-11-16-two-gates-disagree.md` | active |
| AP-003 | 「工具不可用」被當成「檢查通過」 | 關卡的執行環境缺一個條件，工具跑不起來 | 代碼改進 | 2026-11-16 | `2026-11-16-unavailable-read-as-pass.md` | active |
| AP-004 | 衍生清單被當成權威紀錄 | 把一大段事實摘要成小清單交給下一個執行者 | 提示改進 | 2026-11-16 | `2026-11-16-derived-list-as-record.md` | active |
| AP-005 | 刪除前的掃描只覆蓋一種檔案類型 | 刪除一個目錄前先檢查誰引用它 | 提示改進 | 2026-11-16 | `2026-11-16-sweep-one-file-type.md` | active |

## The five, as one rule set

AP-001 to AP-005 came out of one `pdd:study` run and its archive cleanup on `uniterra-dev`. Read
together they are one property: **a gate is only a gate while it can fail for the right reason.**

`skills/report/references/gate-discipline.md` states the five rules that follow from them, and every
skill whose verification section runs a checker points at it.
