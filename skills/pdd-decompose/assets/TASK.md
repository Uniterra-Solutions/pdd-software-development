# <ID> — <任務標題>

| Field | Value |
| --- | --- |
| Task | `<ID>` |
| Class | `construction` \| `verification` \| `migration` \| `removal` |
| 需求 | `REQ-F-…`（功能）或 `REQ-A-…`（架構） |
| Depends on | <任務 id；驗證類還需 gate> |
| Seam | `<file:function \| route \| command>` — 建設、重構、刪減 |
| Flow | `<flow 名>` — 驗證類 |
| Owned files | <清單，一行一個> |
| REQs | `<REQ-...>` |
| Plan | `<plan-dir>/` |
| PRD | [`../PRD.md`](../PRD.md) — 目前陳述 |
| DAG 與其他任務 | [`../TASKS.md`](../TASKS.md) |
| Status | 工作契約 |

**自足性**：只讀本檔與它引用的 PRD 章節就能動工。DAG、register、trace 在 `../TASKS.md`；兩者不一致時以 PRD 為準，直到 main agent 裁決。

**邊界**：只寫 `Owned files` 列的檔案。不改 `../PRD.md`、`../TASKS.md`、同批任務的檔、別件任務的檔。規格自相矛盾或範圍錯誤時停下並上報，由 main agent 以 dated amendment 處理；不要弱化需求，也不要靜默改契約。

**類別邊界**：建設不寫檢查、模型或 pin；驗證不改生產檔；重構不順便改行為；刪減不留並存物。四類的詳細規範見 `references/` 下對應的 `task-*.md`。

**路徑基準**：以下路徑相對 repo 根，不是相對本檔。

---

## 建設（construction）

- **Purpose**：<一個新出現的可觀察結果；兩個可獨立上線的結果是兩件任務>
- **Seam**：`<file:function | route | command>` — 這件任務**創造**的入口
- **Flow it feeds**：`<flow>` — 它為哪個 flow 加命令
- **Files owned**：
  - `<path>` — 這裡改什麼
- **Steps**（有序；逐步不寫程式碼）：
  1. <定位入口，寫下可觀察契約>
  2. <改行為，含邊界、拒絕、migration 與相容>
  3. <明確不動什麼>
- **Refusal**：`<refuse class>` — 對應行為
- **Untouched**：<不會變的東西；若令既有斷言失效，在報告列出>

## 驗證（verification）

- **Flow**：<命令集 × 狀態 × 拒絕分類 × 不變量>
- **Covers**：`<生產任務 id 清單>`
- **Shape**：`A 建模`（服務 `REQ-F`）| `B 行為護欄`（基線／重跑）| `C 架構檢查`（服務 `REQ-A`）
- **Files owned**：
  - `<model path>` — 模型（A）
  - `<harness path>` — 入口、樣本、seed（A／B）
  - `<pin path>` — 反例固化（A）
  - `<constraint path>` — 約束腳本與門檻（C）
- **Steps**：
  1. <A：讀已落地的 seam，轉錄決策表｜B：跑基線並記 seed 與輸出摘要>
  2. <A：為新命令加 property，每條附預算｜B：不動基線 artifact>
  3. <A：跑、shrink、pin｜B：同一命令重跑，逐位比較｜C：改動前跑到全綠，改動後重跑仍須 pass>
- **Budget**：寫在 harness 檔（樣本數、seed、shrink 界、每 flow 執行時間上限）

## 重構（migration）

- **Source**：<要被搬走的集合：檔案、符號、章節>
- **Target**：<搬到哪裡；目標結構就是交付物>
- **Preserved**：<必須保住的 flow id、約束名、API 表面>
- **Oracle**：<哪個既有套件／模型／基線判定等價；沒有就不得派遣>
- **Files owned**：<來源側與目的側都列出>
- **Steps**：
  1. <一個結構動作>
  2. <下一個結構動作>
  3. <最後：移除舊路徑，跑 oracle>
- **Reversible**：<回滾點>
- **效能**（僅效能導向的重構）：<量測儀器與命令、目前基線、目標預算>

## 刪減（removal）

- **Disappears**：<符號、檔案、章節、flag、依賴，逐項>
- **Replaced by**：<已在場且被驗證覆蓋的替代品>
- **Absence proof**：<哪個命令必須回報零引用；編譯；依賴圖；鏈接檢查>
- **Dies with it**：<隨之而死的測試、fixture、文件段、設定鍵>
- **Files owned**：<被刪的檔，加上所有要改寫引用的檔>
- **Steps**：
  1. <改引用者>
  2. <刪本體與其測試>
  3. <跑 absence proof>
- **Guard**：<如何確認殘留清零>

---

## 報告格式

做完回報四件；缺一件即未完成：

1. 結果——建設：呼叫者現在看到什麼；驗證：走到哪些分支、抓到什麼（trace、seed、最短序列）；重構：保留清單逐條的證據；刪減：absence proof 的原始輸出。
2. 實際建立或修改的檔案，逐項對 `Owned files`。
3. 偏離本檔之處與理由——沒有就寫 `none`。
4. 在 owned 檔案內無法交付的事，以及它需要什麼決定；驗證類另附所有發現的生產缺陷與它指名的 seam。
