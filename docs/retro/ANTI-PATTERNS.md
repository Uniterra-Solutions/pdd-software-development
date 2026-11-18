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

## AP-006 – AP-011（2026-11-17 這一輪）

形狀是 `pdd:report` Step 1 的三選一：**誤導性規則**（句子本身導致錯誤動作）、**沉默缺口**（沒有句子覆蓋那個時刻）、**規則衝突**（兩條都適用且互斥，選了錯的一條）。形狀決定修正點在哪：誤導性規則改句子、沉默缺口指出規則該住哪、規則衝突說明哪一條勝出。

| id | title | shape | class of fix | date | report | state |
| --- | --- | --- | --- | --- | --- | --- |
| AP-006 | 把工具誤判寫成流程繞道 | 誤導性規則 | 代碼改進 | 2026-11-17 | `2026-11-17-checker-misjudgement.md` | active |
| AP-007 | 只寫不比的檢查器 | 沉默缺口 | 代碼改進 | 2026-11-17 | `2026-11-17-write-only-gate.md` | active |
| AP-008 | 失敗即整批回退 | 誤導性規則 | 提示改進 | 2026-11-17 | `2026-11-17-all-or-nothing-revert.md` | active |
| AP-009 | 反模式 issue 開在產品 repo | 沉默缺口 | 提示改進 | 2026-11-17 | `#4`（issue） | active |
| AP-010 | 把產出物當成證據 | 誤導性規則 | 提示改進 | 2026-11-17 | `2026-11-17-artefact-as-evidence.md` | active |
| AP-011 | 把互斥的切片排成序列 | 規則衝突 | 提示改進 | 2026-11-17 | `2026-11-17-slices-run-in-sequence.md` | active |

AP-009 的紀錄是本 repo 的 issue `#4`（連同 `tidy-up-your-thoughts#1` 與兩處 commit），不另立報告檔：那條的修正點是一句目的地綁定，報告只是同一件事的第二次敘述。
