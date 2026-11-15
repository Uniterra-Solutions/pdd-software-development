# Analogy Engineering

The metaphor is the instrument, not the decoration. An analogy earns its place only when a reader can
translate it back to a clause or a failure. This reference gives the domain shortlist, the role table,
and the six tests that decide whether the metaphor survives.

## 1. Choosing the domain

One domain per document. Requirements of a usable domain:

- **It belongs to the reader's week** — 海關、銀行櫃檯、物流倉庫、餐廳廚房、郵局、物業管理、自來水廠、機場安檢、
  圖書館、藥房。Choose from what the reader already operates, not from what you find vivid.
- **It has all six slots** — 守門的人、通行憑證、存放處、留下紀錄的簿子、被拒絕的人、上級規則。A domain missing
  拒絕 or 紀錄 cannot carry a plan whose design lives in its refusals.
- **It is not software in costume** — 資料流、流水線（in the pipeline sense）、檔案櫃、雲端、堆疊、信箱佇列 are
  technical terms wearing everyday clothes. They read as plain language and explain nothing.
- **It has a cost structure** — 人手、時間、租金、重工。Without cost, the 代價 line in `EXPLAIN.md` §4
  has nowhere to live.

State the domain and its limit in `EXPLAIN.md` §2 before the first metaphor sentence. A limit declared up front is
honest; one discovered after twenty paragraphs reads as a retraction.

## 2. The role table

Fill this before writing prose. One row per actor, stored thing, permission and record:

| 比喻中的角色 | 計畫裡的東西 | 編號 |

Rules:

- **One role, one referent.** Two entities sharing a role means the reader cannot tell which one a later
  sentence is about.
- **Each role carries one honest referent.** An entity with no honest counterpart goes in the prose,
  unmapped. A fabricated role is a false claim about how the system behaves, and it gets believed because
  it is concrete.
- **The role's powers must match.** If the 倉管 in the metaphor can delete a record and the system's actor
  cannot, the metaphor has granted a permission nobody approved.

## 3. The six pressure tests

Run each against every metaphor-bearing passage. A failure is either a mapping repair or a passage
rewritten in plain prose — never a passage left as it is.

1. **反向測試** — In the metaphor A holds; in the document B holds. Example: 「櫃員可以改金額」 vs the plan's
   「金額一旦寫入不能改」. Repair the role or drop the metaphor there.
2. **邊界測試** — Describe the metaphor at 空的、塞滿、殘缺. If the metaphor has no picture for empty or full,
   the reader will assume those cases do not exist — which is exactly how a boundary requirement gets
   approved without being understood.
3. **重複測試** — Say the same action twice in the metaphor. If the second time visibly does something
   more (two receipts, two扣款), the metaphor contradicts any 「同一件事做兩次，結果一樣」 clause.
4. **順序測試** — Reverse two steps. If the metaphor still works, it cannot carry an ordering requirement.
5. **中斷測試** — Stop the metaphor's process halfway (客人走了、電停了、手續辦到一半). What is left on the desk?
   If nothing, the metaphor cannot explain 部分失敗 or 補償.
6. **代價測試** — Name what the metaphor pays for the chosen path (多請一個人、慢半天、要留副本). A metaphor
   that pays nothing leaves the cost line in `EXPLAIN.md` §4 unsupported, and the decision reads as free.

**Replace rather than soften any load-bearing passage that fails tests 1–5.** 「大致上」 leaves the reader
with a metaphor the document contradicts. A passage that fails test 6 usually means the decision section
is missing its cost line.

## 4. Where the metaphor must yield

Some plan content has no honest everyday counterpart: 併發寫入的次序、雜湊、版本相容、逾時重送。These are
explained by **consequence to a person**, not by analogy:

- 併發 → 「兩個人同時按同一個位子，只能有一個坐上去，另一個會看到已經被佔了」
- 逾時重送 → 「等太久就當作沒收到，於是再送一次；所以要保證送兩次不會變兩份」
- 版本相容 → 「舊的單子用新表格也要讀得懂，否則舊客戶全部卡住」

This is prose rather than metaphor, and it belongs in `EXPLAIN.md` §6 as a declared limit wherever the
domain cannot reach it.

## 5. Worked skeleton (placeholders only)

Every placeholder here comes from the PRD; the pattern shows the shape, and the content belongs to the
document.

```
§2 比喻：<域>
 場景：<一個具體的人>在<一個具體時刻>要<做一件具體的事>。
 保證：他會拿到<具體結果>，或被告知<具體理由>；不會停在「不知道有沒有成功」。
 機制（比喻）：<守門的人>核對<憑證>，然後在<簿子>上寫一行；寫不進去就整筆不算。
 限制：這個比喻到「同時有兩個人在櫃檯」為止；之後請看 §6。
```

The pattern is: 場景 → 保證 → 機制 → 限制. Four beats. If a passage needs a fifth beat to be true,
the requirement is too vague to explain yet — return to the PRD rather than adding metaphor.
