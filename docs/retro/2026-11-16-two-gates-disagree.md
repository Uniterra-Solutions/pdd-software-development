# 兩個閘門對立時，改產物去迎合其中一個 — 2026-11-16

## 事件

刷新後某一行 `AGENTS.md` 的 `site` 引用的檔案在窗口內未變，但同一行 `notes` 欄裡的次要引用
（`path:line`）指向的檔案已移動。保留該行 → `check_agents_md.py` 報 `cited file does not exist`；
修補該行 → `study_delta.py --verify` 報 `rewritten although their cited file ended unchanged`。兩種做法
各紅一個閘門，而兩者都是專案自己的工具。

## 指引

- 當時遵守的原文（`c4e1b53`）：`skills/study/references/delta-refresh.md:105` —「| no change at all
  under the unit | the block is not rewritten; provenance still moves to HEAD …」
- 當時的讀法：保留規則以「這一行有沒有被改寫」為判準，於是任何修補都是違規；同時 `check_agents_md.py`
  要求每個 `path:line` 都能解析，兩條規則同時生效時沒有出路。
- 形態：conflicting rules

## 反模式

### AP-002 · 兩個閘門對立時，改資料去迎合其中一個

- 觸發：兩個檢查器對同一份產物的不同部分給出互斥要求
- 錯誤動作：挑一個比較好解釋的閘門，改產物讓它過，把另一個的紅燈當成已知問題記下
- 為何看起來合理：閘門被當成事實、產物被當成可改的東西，而事實不會錯，所以錯的一定是產物
- 正確動作：先寫出每個閘門擁有產物的哪個欄位；對立代表擁有權沒定義，改規則與擁有權，再讓兩個閘門
  同時過
- 可觀察徵兆：為了讓某個檢查器閉嘴而出現的例外條款，數量隨刷新次數增加，每一條都附一句「已知」
- 來源：2026-11-16 pdd:study delta refresh 的保留閘門

## 改進

**改進類別**：提示改進

**未採用**：代碼改進（`--verify` 在舊規則下判斷正確；改腳本只是讓它接受新規則，若規則不改，腳本改完
兩個閘門仍然對立）；資訊改進（不是工具語義不明，而是「保留保護什麼」從未被寫下）；流程改進（步驟次序
沒有製造這個對立，缺的是欄位擁有權的一句話）

### 落地

- `skills/study/references/delta-refresh.md` 新增 §6b「A row cites more than its site, and the
  auxiliary citation died」：保留保護 claim（`id`、行為、觸發、`site` 格），site 格以外的引用壞了則修，
  修補記入報告
- `skills/study/scripts/study_delta.py`：`--verify` 比較前先正規化非 site 引用，仍會抓「site 移動但檔案
  未改」與「措辭改變」
- `skills/study/SKILL.md` Pitfalls 新增對應條目；`version` 1.3.0

## 回歸判準

下一次出現「保留 vs 修補」的對立時，先產出一個欄位擁有權的句子，再動任何一份 `AGENTS.md`；若刷新過程
仍需要一條例外條款才能通過兩個閘門，判未修好。
