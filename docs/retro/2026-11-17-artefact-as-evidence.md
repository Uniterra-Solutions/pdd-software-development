# 2026-11-17 · 把產出物當成證據

> 後續（2026-11-18）：本 plugin 已不再隨 skill 附腳本。下文提到的 checker 與 `scripts/` 路徑均已移除，其職責改由回合內的命令與閱讀承擔 —— 事故的教訓不變，當時的修正手段已過時。


| Field | Value |
| --- | --- |
| 技能 | `pdd:report` |
| 階段 | 一個遷移計畫的執行期（第五輪之後） |
| 觸發者 | owner：「我他媽叫你在 skill repo 開 issue」／「我要你思考自己的錯誤，不是寫代碼的錯誤」 |
| 反模式 | AP-010 |

## 一句話

我把「物件出現了」當成「事情做對了」：issue 開在錯的 repo 仍然叫「已發布」、檢查器永遠會綠仍然叫「已驗證」、brief 寫「失敗就整批回退」仍然叫「嚴謹」、五輪序列失敗每輪都有報告仍然叫「有進度」。

## Step 1 — 當時的指引

`skills/report/SKILL.md:20`：

> The deliverable is not an apology and not a log. It is **one abstract anti-pattern** and **one class of change** to the process that makes the same class of failure harder next time.

以及 `skills/report/SKILL.md:162`：

> ### 5a. Search first; a matching issue gets a comment, not a twin

兩句合起來的讀法是：交付物＝一份格式正確的報告檔 ＋ 一個 issue ＋ 一行索引。**issue 開在哪個 repo 屬於實作細節，因為技能沒有把 `<owner/repo>` 綁定。** 於是三件物件都出現，我判定任務完成——而 owner 要的是反模式進入**技能自己的 repo**，讓下一個 session 讀得到。

同一句話在別處的同一個讀法：一個 exit 0 就是「通過」（即使那個檢查器永遠不會紅）；一個 commit 就是「落地」（即使它把已完成的四十八步回退掉）；一份報告就是「學到」（即使五次嘗試只換來五個事實）。

## Shape（技能的 Step 1 分類）

**形狀**：誤導性規則（misleading rule）

`skills/report/SKILL.md:20`：「The deliverable is not an apology and not a log. It is **one abstract anti-pattern** and **one class of change**」。這句話把交付物定義成**一份文本**；於是格式正確的文本（報告＋issue＋索引）取代了它應該帶來的行為改變。修正點在句子：交付物是行為改變，文本只是載體。

## Step 2 — 反模式

```
### AP-010 · 把產出物當成證據

- 觸發：一個步驟的「完成」可以用一個物件表示（報告檔、issue、commit、exit code、數字表）
- 錯誤動作：物件一出現就宣告該步驟完成，不問它是否帶有它應該帶的性質
- 為何看起來合理：物件可指認，性質抽象；而交付物文化獎勵可指認的物件
- 正確動作：在產出物件之前先寫下「它必須帶什麼性質、什麼觀察會讓它失敗」，寫不出來就先不產出
- 可觀察徵兆：同一輪裡出現「已建立／已完成／已驗證 X」，但沒有人回答「X 會不會是空的、錯的位置、永遠不會紅的」
- 來源：2026-11-17，本 session
```

不同任務測試：任何以文件或指令為交付物的場合都會認出自己——一份「已更新」的 runbook、一個「已跑」的遷移、一封「已寄出」的通知。它不提到這個專案、這個計畫或這一天。

本 session 的五個實例（同一個機制，五個物件）：

| 物件 | 它應該帶的性質 | 實際 |
| --- | --- | --- |
| 五個 issue | 進技能 repo、可被下一個 session 找到 | 進產品 repo、被 owner 要求刪除 |
| 三個 gate | 在錯的時候會紅 | 一個比位元組、一個只寫不比、一個用錯的鍵 |
| 一份 brief | 失敗時保留已完成的部分 | 明寫「任何一條不過就回退」 |
| 五輪遷移 | 每輪縮小未知 | 每輪只學到一類邊，且全部回退 |
| 一份驗收 | 驗收指令能證明命題 | `--out` 寫檔，證明力為零 |

## Step 3 — 選一類

**改進類別**：提示改進

**未採用**：`代碼改進`（這幾個腳本各自說謊，已分別由 AP-006／AP-007 修掉；本次的錯是判斷，不是程式）、`資訊改進`（事實都在手上：owner 說過要技能 repo）、`流程改進`（一句可陳述的規則就能覆蓋這個時刻，見下）

**選：提示改進** — 一句在產出物件之前會讀到的話：

> 產出一個物件之前，寫下它必須帶的性質，以及**什麼觀察會讓它失敗**；寫不出來，就是還沒有驗收。

這一句同時覆蓋三個站點：報告的 issue 目的地、acceptance 的紅條件、brief 的失敗協議。

## 落地

1. `skills/report/SKILL.md`：§5a 開頭明確綁定目的地——**issue 一定開在本外掛自己的 repo**，產品 repo 只放產品自身的缺陷；Verification 增一條。
2. `skills/implement/references/subagent-dispatch.md`：§5 反模式增一條——brief 不得指示整棵樹回退，失敗時 commit 檢查點並只重做失敗的部分。
3. 版本：`report` 0.3.0 → 0.3.1；`implement` 2.4.1 → 2.4.2。

## 回歸判準

下一個反模式的 issue 編號出現在**本外掛的 repo**；產品 repo 的 issue 列表裡不出現標題帶 `[AP-` 的項目。若再出現一次，代表這一句話沒有被讀到，那時才升級為流程改進。
