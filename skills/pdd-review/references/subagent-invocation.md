# 調用審查 subagent 的規範

main agent 用這份文件派遣審查者。它只管「怎麼派」，審查內容的判準在兩份類型規範裡。

## 1. 必附的兩個路徑

每一份 brief 都要貼兩個路徑，缺一不可：

```
任務檔目錄：  <plan-dir>/tasks/              ← 本 unit 的任務檔在裡面，只讀
你的規範：    <pdd-review>/references/reviewer-<type>.md   ← type = test-construction | code-reading
基礎規範：    <pdd-implement>/references/subagent-charter.md ← 編譯範圍、命名、報告
```

**為什麼是路徑而不是內文。** 三個理由：

1. 貼內文等於在派遣時重寫一次契約，兩份副本一旦漂移，子代理跟隨它最後讀到的那份；
2. 規範檔會演化，貼死的副本不會跟著改；
3. brief 小一個數量級，省下的上下文留給讀碼與構造反例。

**路徑要驗。** 派遣前對每個路徑 `test -f`；寫錯的路徑不會回報「路徑錯」，子代理只會說「任務不明確」。

## 2. brief 的最小內容

```
你的身分：   <測試構造型 | 代碼審查型> 審查者   ← 由 scope 內任務的 Class 決定，不得自行更改
你的 unit：   <unit id>
你的 scope：  <任務 id 清單，最多 3 件>
任務檔目錄：  <plan-dir>/tasks/            ← 只讀
你的規範：    references/reviewer-<type>.md ← 照它執行
基礎規範：    pdd-implement/references/subagent-charter.md
標準：        <plan-dir>/PRD.md、<plan-dir>/TASKS.md  ← 只讀
要回答的問題：<3–6 條，逐條可判定>
輸出：        <finding 格式；測試構造型另附 patch 與命令>
禁止：        改生產碼／改 PRD、TASKS、任務檔／新增依賴／跑全套／建立審查專用目錄
```

**身分是查表得來的，不是挑的。** 派遣前對照這張表，`Class` 不在表裡就是計劃缺陷（停下回報，不要選一個順手的類型）：

| 任務 `Class` | 審查者 | 規範檔 |
| --- | --- | --- |
| **行為組** | | |
| `construction` | 測試構造 | `reviewer-test-construction.md` |
| `verification` | 測試構造 | `reviewer-test-construction.md` |
| **結構組** | | |
| `migration` | 代碼審查 | `reviewer-code-reading.md` |
| `removal` | 代碼審查 | `reviewer-code-reading.md` |

**開場自檢（寫進 brief）。** 審查者讀完任務檔後，要確認 brief 給的類型與那些任務的 `Class` 一致；不一致就停下回報，不要「照做」。這是最後一道防線，用來擋住「不確定就派代碼審查」的退化。

**要回答的問題**寫成可判定的問句，不要寫成「審查這個模組」。例：「`REQ-F-deposit-2` 的拒絕分類在 `frozen` 狀態下是否成立？」「`REQ-A-1` 的依賴規則有沒有對應檢查，它會不會咬？」

**不給假設。** brief 不寫「我懷疑 X 有 bug」，也不轉述 main agent 的讀法。審查者的價值來自獨立重讀原文；一旦被錨定，它只會確認你的猜測。

## 3. 派遣的形狀

- **一個 unit 一個 subagent，且 unit 內的 `Class` 同屬一組**（行為組＝construction／verification；結構組＝migration／removal）。 混了兩類任務，就等於一份 brief 兩種驗收物件；拆 unit，不要讓審查者兩邊都審不深。
- **scope 上限 3 件任務。** 不是配額，是上限：findings 要能歸因到任務，且 3 件的 owned 集合還放得進 context。超出就拆 unit，不要壓縮 brief。
- **同檔序列化。** 兩個 unit 的 scope 只要碰到同一個測試檔或同一個模組，就依 DAG 序列化——一個會寫、一個只讀，並行會讓讀的一方看到半成品。
- **整批派遣，然後結束這一輪。** 不要 poll；完成通知按批次處理。
- **平行上限不足時分波。** 波序仍守 DAG 的偏序；不要為了塞進一輪而放寬 scope 上限。

## 4. 回收與轉交

- 每個子代理回報：findings（依 `references/finding-schema.md`）、它實際執行的命令與原始輸出、它改過的測試檔清單、它未能審的範圍與原因。
- **main agent 自己覆核**，不是轉發：測試類 finding 要自己重跑並確認紅腿／綠腿；代碼審查類 finding 要指到行與條文。
- 子代理報告裡的「我認為這不對」不是 finding；沒有輸入、命令或條文的判斷退回，不進報告。

## 5. 失敗樣貌

| 樣貌 | 代價 |
| --- | --- |
| 只貼任務檔路徑，沒貼類型規範 | 審查者用自己的一套判準，兩份報告無法比較 |
| 貼了內文而不是路徑 | 契約兩份，驗收對著一份、執行對著另一份 |
| brief 裡寫了假設 | 審查變成確認偏誤，真正的缺陷沒人找 |
| 一個 unit 4 件以上任務 | findings 無法歸因，context 被切碎 |
| 不確定就派代碼審查 | 行為類任務失去反例，只剩「看起來合理」 |
| unit 內混了 construction 與 migration | 一套判準涵蓋兩種驗收物件，兩邊都淺 |
| 同檔兩個 unit 並行 | 一邊寫測試一邊被讀，讀到半成品 |
| 把子代理的判斷直接寫進報告 | 沒有命令與條文的 finding 是意見，不是證據 |
