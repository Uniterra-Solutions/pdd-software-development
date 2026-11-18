# 一個從未渲染的 mermaid 圖通過了所有閘門 — 2026-11-16

> 後續（2026-11-18）：本 plugin 已不再隨 skill 附腳本。下文提到的 checker 與 `scripts/` 路徑均已移除，其職責改由回合內的命令與閱讀承擔 —— 事故的教訓不變，當時的修正手段已過時。


## 事件

subagent 回報「lint only — no chromium here」，主 agent 接受該說法，沒有自行渲染。該單元的 mermaid
選擇路徑圖含一個多餘括號：`check_agents_md.py`（引用解析、表格形狀）通過，`study_delta.py --verify`
（行未移動）通過，交付到 repo 的知識庫首圖在 GitHub 上渲染失敗。渲染失敗的原因是 chromium 以 root
執行時不接受預設設定，`npx @mermaid-js/mermaid-cli` 直接失敗，錯誤訊息讀起來像環境限制。

## 指引

- 缺口 — `skills/study/SKILL.md:345`（`c4e1b53`）的「## Verification」檢查表沒有任何渲染項；
  `skills/study/SKILL.md:149` 只要求主 agent「renders each mermaid block and reads the graph」，寫成
  主觀閱讀，沒有可執行的關卡。
- 當時的讀法：檢查表沒有渲染項，於是「未渲染」不構成違規；subagent 說環境沒有 chromium，主 agent 把
  這句當成環境事實接受。
- 形態：silent gap

## 反模式

### AP-003 · 「工具不可用」被當成「檢查通過」

- 觸發：一個關卡的執行環境缺一個條件，工具因此跑不起來
- 錯誤動作：接受「這裡跑不了」作為結論，讓其餘關卡的綠燈代替它
- 為何看起來合理：綠燈是既成事實，不可用是環境問題，而環境問題看起來不是產物的問題
- 正確動作：把不可用視為紅燈；提供一個能在該環境跑起來的入口（設定、包裝腳本），否則明確記錄該關卡
  未執行、產物未經此關
- 可觀察徵兆：回報裡出現「只做了 lint」「沒有 chromium」「rendering unavailable」，而交付物照樣被接受
- 來源：2026-11-16 pdd:study delta refresh 的 unit 圖

## 改進

**改進類別**：代碼改進

**未採用**：提示改進（「lint-only 不是驗證」這句在 1.3.0 已寫，但它不能讓 mermaid-cli 在 root 下跑起來；
下一次仍會得到同一個 puppeteer 錯誤，只是被寫成一行藉口）；資訊改進（agent 已經知道環境沒有可用的
chromium，缺的不是知識而是可用入口）；流程改進（步驟次序沒有產生這個失效，缺的是一支帶設定的腳本）

### 落地

- 新增 `skills/study/scripts/render_graphs.py`：逐個 mermaid block 渲染，內建 puppeteer `--no-sandbox`
  設定，exit 0 僅當全部通過，逐塊印出 parse error
- `skills/study/SKILL.md` Verification 新增「`scripts/render_graphs.py {project_root}` reports
  `failed 0`」，並在 References 補上該腳本一行；`version` 1.3.0
- `skills/report/references/gate-discipline.md` 規則 3：跑不起來的關卡必須紅（本次新增）

## 回歸判準

下一次交付含 mermaid 的知識庫時，`render_graphs.py` 以 root 在 repo root 上跑過並印出 `failed 0`；若
交付記錄只有 lint 而無渲染，判未修好。
