# Plain-Language Lexicon

§2 of this file is the banlist, so a new term enters the ban the moment its row lands here, and adding a
row is the whole fix. §3 and §4 guide the rewrite and are read by the writer, not by any tool. Backticked
strings and appendix A stay exempt, because a quoted original is text the reader will meet verbatim.

## 1. The test

A word is jargon if an intelligent reader from outside software would have to ask about it — not if a
dictionary contains it. 「表格」 is fine; 「schema」 is not. 「複本」 is fine; 「cache」 is not.

## 2. Banned terms and their replacements

| 技術詞 | 白話 |
| --- | --- |
| API / endpoint / route | 對外開放的窗口：誰可以從哪裡送什麼進來、拿什麼回去 |
| schema / model / DTO | 這張表有哪幾欄、每欄放什麼、哪幾欄不能空 |
| database / table / row | 帳本 / 一張帳 / 一行紀錄 |
| migration | 搬家：舊資料改成新格式，搬的途中不能掉 |
| cache | 隨手放的複本，過期就要重拿 |
| index | 目錄 |
| queue / worker / job | 排隊的單子 / 誰去處理 / 定時或按需做的一件事 |
| idempotent | 同一件事做兩次，結果跟做一次一樣 |
| race condition / lock / mutex | 兩件事同時發生時互相踩到；同一時間只准一個進來 |
| transaction / atomic | 要嘛整筆成功，要嘛整筆不算 |
| timeout / retry / backoff | 等太久就當作沒收到 / 再送一次 / 越等越久再送 |
| token / session / auth | 通行證 / 這次進來的憑證 / 驗明身分 |
| permission / role / RBAC | 誰准做什麼 / 職位 / 按職位給權限 |
| hash / signature / encrypt | 指紋 / 簽章 / 上鎖 |
| regex / parse / serialize | 比對字串的樣式 / 讀懂一段文字 / 轉成可存放的寫法 |
| refactor | 外表不變，換掉裡面 |
| deploy / rollback / release | 上線 / 退回上一版 / 發布 |
| CI / pipeline / test runner | 每次改動都自動重跑的一整套檢查 |
| unit test / mock / fixture / stub | 小段演練 / 假裝的對手 / 預先擺好的場地 |
| coverage | 演練蓋到多少種情況 |
| DAG / dependency / wave | 誰必須先做完的順序圖 / 前後關係 / 同時可做的批次 |
| invariant | 任何時候都不會變的規矩 |
| requirement / spec / contract | 要求 / 標準 / 雙方的約定 |
| latency / p99 / throughput | 最慢的那批要等多久 / 一定時間內能處理多少 |
| flag / config key / env var | 開關 / 設定項 |
| log / metric / alert | 紀錄 / 數字指標 / 通知 |
| error variant / exception | 出錯時系統回報的哪一種錯 |
| feature branch / PR / merge | 另開一條路試做 / 送審 / 合併 |
| feature flag / canary | 只給一部分人先用的開關 |
| cron / scheduler | 定時自動做 |
| dry run | 空跑一次，不真的改東西 |
| sandbox / staging | 練習場 / 試辦場地 |
| 落地 / 賦能 / 打通 / 對齊 / 閉環 | 刪掉，改成「誰在哪裡多做或少做一件事」 |

## 3. Boundary cases in plain words

The plan's boundary taxonomy is precise and unreadable. Translate, do not drop:

| 原文 | 白話 |
| --- | --- |
| empty / absent | 一個都沒有 / 東西不在 |
| min / single | 只有一筆 |
| max / at limit | 塞到上限，再來一筆就進不來 |
| duplicate | 同一件事送兩次 |
| out-of-order | 順序顛倒，後發的先到 |
| malformed | 資料殘缺、格式不對 |
| partial failure | 做到一半斷掉，前面做了、後面沒做 |
| concurrent | 兩個人同時做同一件事 |
| stale / version skew | 拿的是舊版本的資料 |
| unauthorized | 沒有通行證的人來敲門 |

## 4. Banned sentence shapes

| 不要寫 | 因為 | 改寫 |
| --- | --- | --- |
| 系統會自動處理 | 沒有人知道拒絕長什麼樣 | 誰在什麼情況下被拒、他看到什麼 |
| 正常情況下 | 把邊界掃到地毯下 | 講出那個不正常的條件 |
| 理論上 / 應該 / 基本上 | 讀者無法驗收 | 給一個數字或一個可觀察事件 |
| 具體來說（後面接空話） | 假裝具體 | 換成一個場景 |
| 大幅提升 / 更穩定 | 無對應物 | 等多久、多久壞一次、多一倍人會怎樣 |
| 為之後擴展留空間 | 用未來換現在的批准 | 現在多付多少、什麼條件下才用得上 |

## 5. What may stay in the original

Only strings the reader will personally meet: a file name, a command he will type, an error line on
screen, a field label on a form. Each appears once, in backticks, followed immediately by its plain
meaning. Ids (`REQ-…`, `D1`, `P1`, `T1`) are labels, not jargon, and stay unglossed.
