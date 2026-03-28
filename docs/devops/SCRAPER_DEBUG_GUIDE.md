# Linkora 探勘引擎：深度除錯指南 (Scraper Debug Guide)

本指南旨在幫助開發者排查 Linkora v3.1.8 探勘引擎在執行背景任務時可能遇到的連線、權限、以及資料入庫問題。

---

## 一、探勘失敗常見場景與排查路徑

### 1.1 Apify Actor 狀態檢查
- **現象**: 任務狀態顯示為 `Failed` 且 `leads_found` 為 0。
- **排查**:
  1. 登入 Apify 控制台，檢查 `zen-studio/thomasnet-suppliers-scraper` 的執行日誌。
  2. 確認 `APIFY_TOKEN` 是否過期或點擊數已達上限。
  3. 檢查傳入 Actor 的 `queries` 是否為空。

### 1.2 403 Forbidden (網域封鎖)
- **現象**: 黃頁模式下 `junipr/yellow-pages-scraper` 正常回傳，但 `find_emails_free` 抓取官網時失敗。
- **對策**: Ensure `SCRAPER_API_KEY` 已正確設定於 `System Settings`。

---

## 二、多層 Fallback 策略驗證

| 順序 | 模式 (Mode) | 預設途徑 | 備援途徑 |
| :--- | :--- | :--- | :--- |
| **L1** | 製造商 (Manufacturer) | Thomasnet (Apify) | Google CSE / Bing |
| **L2** | 黃頁 (Yellowpages) | Yellowpages (Apify) | ScraperAPI Proxy |

### 如何驗證備援？
1. 手動將 `APIFY_TOKEN` 設為無效。
2. 啟動一個製造商任務。
3. 觀察日誌，確認系統是否出現 `[FALLBACK] Thomasnet failed, trying Google CSE...` 訊息。

---

## 三、資料庫與補全腳本 (SQL Debug)

若發現 `leads` 資料表中的 `vendor_id` 或 `global_id` 缺失，請使用以下 SQL 進行修正：

```sql
-- 補全 Member 與 Vendor 的關連 (範例)
UPDATE users 
SET vendor_id = (SELECT id FROM users WHERE email = 'admin@linkora.com')
WHERE role = 'member' AND vendor_id IS NULL;

-- 檢查全域情報池同步狀態
SELECT domain, company_name, contact_email 
FROM global_leads 
ORDER BY last_scraped_at DESC 
LIMIT 10;
```

---

## 四、超時與 Watchdog 機制

系統對異步任務設有 **180s 強制超時**。
- **核心代碼**: `backend/manufacturer_miner.py`
- **除錯**: 若任務頻繁超時，請檢查目標網域的 DNS 回應速度，或調降 `pages` 數量至 1-2 頁以提升成功率。

---
*Created by Antigravity AI - Scraper Engineering Support v3.1.8*
