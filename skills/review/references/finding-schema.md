# Finding schema 與對抗案例清單

## 1. Finding schema

一條 finding 是已證實的反例，或明確標記為未證實的風險。兩種分開寫。

```
id:        R-<unit>-<n>
axis:      functional | architectural
layer:     intra-module | cross-module | integration | plan
task:      <任務 id>（`plan` 層填 none）
requirement: <REQ-F-… / REQ-A-… / missing / hollow / unformal>
severity:  critical | high | medium | low
confidence: confirmed | unproven
file:      <path:line>
clause:    <它違反的規則原文：PRD 一句、任務檔一句、或宣告的架構規則一條>（architectural 必填）
input:     <最小輸入或操作／生命週期序列>（functional 必填）
expected:  <標準要求的值或行為>
actual:    <觀察到的值或行為>
test:      <test file :: test title，靜態 finding 填 none>
command:   <審查者實際執行的命令>
evidence:  <patch 路徑、輸出檔、或行號範圍>
reproduced: yes | no
```

- **`axis` 決定證據形狀。** `functional` 要有 input／expected／actual 與能重跑的命令；`architectural` 要有 `clause` 與指認的 `file:line`，不一定有命令。
- **`severity`**：critical＝錯誤結果、資料遺失、安全洞、核心不變量從不成立；high＝必需行為在生產中不可達；medium＝邊界、錯誤路徑、非核心不變量；low＝已證實但無正確性影響。
- **沒有命令與最小輸入的行為類 finding 是 `unproven`**，不是 bug。
- **`layer: plan`** 指標準本身的缺陷，不是碼的缺陷：`REQ-A` 沒有對應的 C 檢查、一個 flow 沒有模型、一條 `REQ` 跨兩個 flow、migration 沒有 oracle、removal 沒有 absence proof、任務類別與內容不符。`file:` 指向 `PRD.md` 或 `TASKS.md` 的行，`test:` 填 `none`。
- **測試位置**：該行為的功能位置，按 repo 命名；`review_test/…`、`tests/review/…`、`adversarial.spec.ts`，或任何含任務 id 的檔名（`t3_*.spec.ts`、`guard_t3.spec.ts`）都不是合法位置——產品 gate 永遠不會收集它。
- **`evidence`**：測試構造類給 patch 與命令輸出；代碼審查類給行號範圍與引用條文。

## 2. 兩軸的證據要求

| 軸 | 誰產出 | 必須有 | 不接受 |
| --- | --- | --- | --- |
| 功能 | 測試構造型 | 最小輸入、期望 vs 實際、命令、紅腿（今天紅）、綠腿（套最小臨時修正後綠） | 只描述「看起來不對」、綠的測試、域只有一個點 |
| 架構 | 代碼審查型 | `clause`（PRD 或架構宣告的原文）、`file:line`、C 檢查在不在與會不會咬 | 「風格偏好」、沒有條文的「不夠好」、把 `REQ-A` 違反降級成 review note |

## 3. 對抗案例清單（測試構造型用）

對每個變數與狀態，逐一嘗試：

- **值的邊界** — 空、缺失、最小、最大、零、負（若合法）、重複、非 ASCII、畸形、超長、單位錯、符號錯。
- **序列邊界** — 亂序到達、重複投遞、成功後重試、重放、訊息遺失、部分批次、中途重啟、冪等被破壞。
- **狀態機邊界** — 每個合法轉移與每個非法轉移；從終態轉移；同一實體的並發轉移；操作中 teardown。
- **跨模組邊界** — 契約不符、版本偏斜、缺欄位、多欄位、快取過期、寫讀順序、部分提交、timeout、取消、背壓、錯誤被翻譯成成功。
- **並發** — 同一實體兩個 writer、重入、lost wakeup、鎖序顛倒、commit 與快取刷新之間的讀、hold 之後仍在飛的操作。
- **失敗注入** — 每個外部呼叫都失敗、提交後失敗、回畸形資料、掛住、成功兩次；每一點都要斷言定義好的安全結果。
- **資源生命週期** — init → use → teardown → restart；洩漏、重複釋放、過期 handle、孤兒任務、未釋放的 hold。

## 4. 空洞測試審計（測試構造型用，先審既有測試）

一個錯誤實作仍能通過的測試就是空洞的：

- 斷言讀的是宣告、原始碼字串、符號數量或表名；
- 斷言的值在每條路徑都被填，於是「有執行」與「沒執行」看起來一樣；
- 量測的儀器沒有括住被宣稱的行為（計數器重置太早、seam 錯了）；
- 兩個不可能互相影響的 local 被互相比對；
- 一個 fixture 被當成 `every`／`never`／`identical`；
- 期望值就是測試自己的 mock 回音、fixture 常數，或當前輸出的快照；
- generator 被縮到宣稱變成平凡真，或觀察被搬到 test-only 的孿生體。

**修法**：把斷言指到宣稱所說的生產值、還原完整域、加上天真錯誤實作的負向控制、讓最小輸入真的紅。優先就地修這一條，而不是新增第二個測試。

## 5. 跨模組清單（兩類都用）

對每一對 caller/callee 或 producer/consumer：

- 每個欄位與狀態由誰擁有、誰可以改；
- callee 返回時，caller 假設什麼已經提交；
- 跨邊界的順序與原子性；
- 生命週期與 teardown 的可見性；
- timeout、拒絕、過期資料、重試、取消、部分失敗；
- 資料格式、單位與版本相容；
- 並發交錯與重複投遞；
- 從入口到被改表面的生產呼叫鏈，附 `file:line`。

邊界上的 property 要同時量化兩側的狀態、並在 seam 上觀察。若觀察只落在其中一側內部，這條邊界就沒有被建模。

## 6. 架構審查清單（代碼審查型用）

對每一條 `REQ-A`：

- **規則在不在**：PRD §5 是否寫下了它要的結構（模組邊界、依賴方向、公開表面、分層、預算）。
- **檢查在不在**：對應的 C 檢查是否存在於 repo，且它的 owned 檔案不在生產碼裡。
- **檢查會不會咬**：有沒有注入一次違反、確認它紅的紀錄；一個從未紅過的檢查什麼都沒證明。
- **程式碼是否遵守**：依賴圖、匯入清單、公開表面、循環、模組大小、效能實測值，逐項對照宣告。
- **是否留下繞道**：`allow`／`disable` 消音、把違規藏進測試檔或生成物、用第二條路徑繞過宣告的入口。
- **是否只是重述**：C 檢查若只是把宣告抄一遍而沒有任何量測，它是文檔不是檢查。
