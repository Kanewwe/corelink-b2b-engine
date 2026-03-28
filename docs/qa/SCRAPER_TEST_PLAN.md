# Linkora 探勘引擎完整測試計面 (Scraper Test Plan)

本文件定義了 Linkora v3.1.8 探勘引擎（Manufacturer & Yellowpages）的測試標準、測試指標與失敗還原流程。

---

## 1. 測試核心流程：四階段發現法 (v3.2.0)

| 階段 | 測試重點 (Validation) | 預期結果 |
| :--- | :--- | :--- |
| **P1: Reservoir** | 重複查詢 `apple.com` | 確認 `Leads` 表會從 `GlobalLeads` 克隆而非重新採集。 |
| **P2: Live Scrape** | 在 Apify 中啟動製造商 Actor | 確認 `leads_found` > 0 且傳回 raw 選項。 |
| **P3: Enrichment** | 檢查 Email 取得邏輯 | 確認 `email_candidates` 有資料且 `contact_email` 是有效信箱。 |
| **P4: Persistence** | 檢查資料庫寫入 | 查看 `Leads` 與 `GlobalLeads` 是否同步新增資料。 |

---

## 2. 製造商模式 (Manufacturer) 測試案例

### 負壓測試 (Stress Test)
- **條件**: 輸入 10 個不同的產業關鍵字同時併發。
- **指標**: 
    - 任務超時比率 < 10%。
    - 資料庫並行連線數不應超出 50。
    - **Fallback**: 若 Thomasnet 失效，需在 10s 內切換至 Google CSE。

### 準確度驗證
- 驗證 `ai_tag` 是否正確識別。如查詢 `PCB assembly` 應標記為 `NA-EMS` 或 `NA-PCB`。

---

## 3. 黃頁模式 (Yellowpages) 測試案例

- **區域測試 (US/TW)**: 確認 US 區域時是否正確掛載了 `ScraperAPI` 的自定義 Proxy。
- **翻頁邏輯**: `pages=3` 時，驗證資料庫是否累積了 60+ 筆 leads。

---

## 4. 故障復原測試 (Recovery)

| 異常情境 | 模擬動作 | 復原預期 |
| :--- | :--- | :--- |
| **API Key 失效** | 手動刪除 `OPENAI_API_KEY` | 任務狀態應顯示 `Failed` 且日誌紀錄 `AI Error`。 |
| **資料庫斷線** | 停止 Postgres Service | 爬蟲應在本地暫存數據，待連線後重新嘗試 Sink。 |
| **強制終止** | 任務執行 181s | 背景 Thread 應被強行殺死，避免累積殭屍行程。 |

---
*Created by Antigravity AI - Scraper QA Principles v3.1.8*
