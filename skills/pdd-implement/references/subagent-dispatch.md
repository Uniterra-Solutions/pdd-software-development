# 調用 subagent 的高效範式

三件事決定一次派遣的成敗：**工作區隔離、契約的單一真相、按類別驗收。** 其餘都是細節。

## 1. 建立 worktrees

一子一 worktree，各自的 build 目錄，一個明確的起點。這三件事分開做就會出現「兩人各自綠、合併後紅」。

- **從 baseline 開，不從 dirty 主樹開。** baseline 是一份 hash 清單：base commit ＋ 已接受任務的 overlay。dirty 主樹以 overlay 表達，不 commit、不 stash 使用者的工作。
- **overlay 要排除未接受的東西**：兄弟任務的 delta、失敗的實驗、未還原的 mutation、被打斷的子代理留下的突變。一個漏進去的 pending mutation 會讓每個 worktree 的驗證假綠。
- **獨立 build 目錄。** 共享 `target/`（或 `dist/`、`node_modules/.cache`）時，一個人的 clean 會刪掉另一個人的產物，而兩邊的命令都 exit 0。Rust 用 `CARGO_TARGET_DIR`，Node 用各自的 cache 與 out-dir，Python 用各自的 venv 或 `PYTHONPYCACHEPREFIX`。
- **埠與 socket 也要隔離。** 並行 harness 綁同一個埠時，第二個連上的是第一個的伺服器，斷言描述的是別的應用。固定一個不常見的埠、用 strict-port 旗標、關閉 server reuse。
- **一個 layer 一個 baseline。** amendment 之後，每個 worktree 的 PRD／TASKS／task 快照都要刷新再派；一份留在舊依賴上的 worktree 與它的兄弟產出兩份無法合併的結果，而且都回報成功。
- **子代理不碰 worktree 的生命週期**：不建立、不刪除、不 merge、不 cherry-pick、不 commit、不 push、不清理共享產物。
- **中斷就從證據恢復**：比對當前碼與最後已知良好 checkpoint，檢查 mutation 腳本與備份；把突變保留為證據，只還原那一個 hunk，然後才接受任何東西。

## 2. 把 task file 的 dir 貼給 subagent

brief 給**路徑**，不貼內文。

```
你的 worktree：<worktree 路徑>        ← 唯一可寫
你的起點：   <baseline hash 清單路徑>
build 目錄： <路徑>
唯讀契約：   <plan-dir>/PRD.md、<plan-dir>/TASKS.md
你的任務：   <plan-dir>/tasks/T03-<slug>.md   ← 只讀，照它執行
你的規範：   references/subagent-charter.md   ← 只讀，照它執行
owned：      <逐項，照任務檔>
禁止：       改 PRD／TASKS／兄弟任務檔；弱化或刪除既有測試；新增依賴；跑全套 suite；整 workspace 編譯；commit；push
停止條件：   任務不可滿足／與已合併的碼矛盾／owned 缺檔 → 停下，回報，契約不動
報告：       依任務檔指定的報告格式，貼原始輸出
```

**為什麼是 dir 而不是貼內文。** 三個理由，每一個都曾造成真實損失：

1. **兩份副本會漂移。** 貼進 brief 的內文與檔案正文一旦不同，子代理跟隨它最後讀到的那份；`pdd-decompose` 明文規定一件任務的正文只存在一處，brief 貼全文就是第二處。
2. **貼全文等於在派遣時重寫契約。** 任何省略、改寫、翻譯成步驟清單，都是靜默的修改，而驗收仍對著檔案原文進行，於是兩邊對不上時無法判斷是誰改了什麼。
3. **brief 小一個數量級，證據鏈不變。** 一個 200 字的 brief 指向 8 KB 的契約，子代理自己讀；上下文省下來給實作，而不是給重複。

**為什麼給整個 `tasks/` 目錄而不是只給檔名。** 同一層的兄弟任務檔就在旁邊，子代理會讀到自己的依賴以理解邊界（它讀得到，但無權寫）。owned 清單仍是唯一的寫入授權；dir 只是讓它不必猜。

三條實務要求：

- 派遣前 `test -f` 每個路徑。一個寫錯的路徑讓子代理開場就卡住，而它不會告訴你路徑錯了，只會說「任務不明確」。
- 任務檔是**唯讀**：派遣前記下它的 hash，驗收時比對。子代理改了契約再實作，是最難查的一種失敗。
- brief 不再附 header 的逐字副本。子代理開場第一件事是讀自己的檔並回報檔案裡的一行（例如 purpose），這是「打開了正確的檔」的證據，成本一個 token。

## 3. 依類別驗收

驗收讀任務自己所屬的類別，不套用別類的判準。dispatcher 自己執行、自己看原始輸出；報告只是索引。

| 類別 | acceptance | dispatcher 實際做的事 |
| --- | --- | --- |
| **construction** | purpose 從真實入口可觀察 | 自己觸發一次入口（建物件、注入一個請求、跑一次 CLI）；`git diff --stat` 對 owned；跑受影響的既有 suite 與 typecheck |
| **verification A** | 模型在、property 跑過、反例已 pin | 讀 harness 的執行紀錄：seed、樣本數、shrink 後最短序列；確認每條 property 有對應的預算 |
| **verification B** | 基線在改動前凍結，改動後同命令重跑逐位相同 | 比對兩次輸出的 hash；確認基線 artifact 的 mtime 早於改動 |
| **verification C** | 改動前全綠、改動後仍綠，且注入違反必須紅 | 自己跑一次檢查；用 `mutate_check.py` 注入一個違反，確認它紅，再還原確認位元組相同 |
| **migration** | 保留清單逐條有證據；來源→目的對得上；舊路徑已移除或有到期條件 | 讀 oracle 輸出；`git diff --name-status` 對來源與目的集合；`grep` 舊符號應為零 |
| **removal** | absence proof；零引用；隨它而死的測試已刪 | 自己跑一次引用查詢與編譯；確認測試檔與 fixture 一起消失 |

三條跨類別的共同線：

- **delta ⊆ owned。** 碰到別的檔案就是契約破裂，退回同一 owner。lockfile、build 產物、快取是 byproduct，記錄即可。
- **count > 0。** 任何「綠」都要有實際執行量。選擇到零個案子而 exit 0 是未完成，不是綠。
- **既有 oracle 不得被弱化。** 令既有斷言失效的任務，必須在同件更新或刪除並列出。

**類別錯配的症狀**（用來檢查自己有沒有用錯尺）：

| 錯配 | 症狀 |
| --- | --- |
| 用 A 的判準驗 construction | 你開始要求子代理交測試，於是每件建設都新增一份斷言 |
| 用 construction 的判準驗 C | 你只確認「檢查通過」，沒有確認它會紅——一個不會紅的檢查什麼都沒證明 |
| 用 B 的判準驗 migration | 你只比對行為，沒有檢查架構規則，於是重構可以朝錯的方向走 |
| 用 removal 的判準驗 migration | 你只確認舊路徑消失，沒有確認保留清單 |

## 4. 一層的完整序列

1. 算 ready set（已接受的依賴，不是自報成功）。
2. 建 worktree 與 baseline，記 hash。
3. 做共享前置：manifest、lockfile、registry／route table、共享 fixture、入口 alias；宣告唯讀。
4. 寫 brief（路徑形，見 §2），一次 `delegate_task` 派整層。
5. dispatch 後結束這一輪，不 poll；完成通知按批次處理。
6. 驗 delta：changed paths 等於 owned，byproduct 另記。
7. 依類別驗收（§3），失敗退回同一 owner。
8. 整合：核對目的端 baseline hash，明示解決衝突，在主樹重跑該任務的觀察與受影響的模組。
9. 報告與 patch 保存後才移除 worktree；未整合的失敗 worktree 連同阻礙保留。
10. 下一層。

## 5. 反模式

- **貼全文 brief。** 契約變成兩份，驗收對著一份、實作對著另一份。
- **共用 build 目標。** 兩人各自 exit 0，合併後才發現產物是半成品。
- **從 dirty 主樹開 worktree。** 一個未還原的 mutation 被複製到每個子代理，全部假綠。
- **沿用上一層的 worktree。** baseline 已過期，且上一個任務的 delta 混進了這一個。
- **子代理自己 commit 之後才整合。** dispatcher 失去核對 baseline 的機會，衝突變成不可解。
- **用「報告說 done」驗收。** 報告是索引，不是證據。
- **一個 worktree 跑兩件任務。** owned 交集無人負責，失敗無法歸因。
