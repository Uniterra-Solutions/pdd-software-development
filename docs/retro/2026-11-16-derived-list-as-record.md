# 一份被算短的清單，讓兩個 unit 什麼都沒做 — 2026-11-16

> 後續（2026-11-18）：本 plugin 已不再隨 skill 附腳本。下文提到的 checker 與 `scripts/` 路徑均已移除，其職責改由回合內的命令與閱讀承擔 —— 事故的教訓不變，當時的修正手段已過時。


## 事件

`study_delta.py` 產出的 touched-path 清單對兩個 unit 缺少路徑，而兩者的 `files` 計數非零。subagent 以
清單為閱讀範圍，判定該 unit 在此窗口沒有變更，回報「untouched」，兩份 `AGENTS.md` 未刷新、也沒有任何
錯誤。

## 指引

- 當時遵守的原文（`c4e1b53`）：`skills/study/references/delta-refresh.md:113` —「`subagent-brief.md` §5
  is the delta brief: the same fields, plus `base: <sha>`, the touched-path list for that unit, and the
  diff-scoped obligations.」
- 當時的讀法：brief 把清單列為該 unit 的輸入之一，於是清單被當成窗口內變更的完整紀錄，清單裡沒有的
  路徑就是沒變的路徑。
- 形態：misleading rule

## 反模式

### AP-004 · 衍生清單被當成權威紀錄

- 觸發：派工時要把一大段事實（diff、日誌、審計輸出）摘要成一份小清單交給下一個執行者
- 錯誤動作：把清單當成完整輸入，不提供取得原始事實的命令，也不要求兩者不一致時回報
- 為何看起來合理：清單由工具產出，工具在別處都可靠；而且清單短，讀起來快，看起來就是為了被讀而存在
- 正確動作：清單標明為提示；brief 第一個閱讀步驟給出取得原始事實的權威命令；兩者不一致時子代理回報並
  依原始事實工作
- 可觀察徵兆：下一個執行者回報「無變更」，而同一次輸出裡的計數非零
- 來源：2026-11-16 pdd:study 在 uniterra-dev 的 delta refresh

## 改進

**改進類別**：提示改進

**未採用**：代碼改進（產生清單的腳本沒有算錯：它按 log range 取路徑，range 本身短就清單短；修腳本
不能保證每個 repo 的 range 都完整）；資訊改進（清單存在、長度也被看到，缺的是它在 brief 裡的地位）；
流程改進（派工步驟沒有錯，錯的是輸入的權重）

### 落地

- `skills/study/references/delta-refresh.md` §7 改寫：清單是 hint，`git log -p {base}..HEAD -- {unit}`
  是紀錄；不一致時子代理回報並依 diff 工作
- `skills/study/SKILL.md` Pitfalls 新增對應條目；`version` 1.3.0

## 回歸判準

下一次 delta 派工時，brief 的第一個閱讀步驟是一條 `git log -p` 命令，清單以「提示」字樣出現；若子代理
仍以清單長度判斷 unit 是否變更，判未修好。
