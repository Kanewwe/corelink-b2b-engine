# Linkora 爬蟲測試矩陣（v3.2）

> 建立：2026-03-27 | 更新：2026-03-28  
> 測試環境：UAT (uat 分支) | 網址：linkora-frontend-uat.onrender.com

---

## 一、爬蟲四種模式矩陣

| 模式 | 後端檔案 | 爬蟲來源 | Email 策略 | API 端點 |
|------|---------|---------|-----------|---------|
| **免費黃頁** | `scrape_simple.py` | Junipr YellowPages Scraper | `find_emails_free()` 官網爬取 | `/api/scrape-simple` |
| **免費製造商** | `manufacturer_miner.py` | Thomasnet + Google CSE | `find_emails_free()` 官網爬取 | `/api/scrape-simple` |
| **Hunter黃頁** | `scrape_simple.py` | Junipr YellowPages Scraper | Hunter.io API | `/api/scrape-simple` |
| **Hunter製造商** | `manufacturer_miner.py` | Thomasnet + Google CSE | Hunter.io API | `/api/scrape-simple` |

---

## 二、API 呼叫格式

### `/api/scrape-simple`（主端點）

```json
POST /api/scrape-simple
{
  "market": "US",           // US / UK / CA / AU
  "pages": 1,                // 爬取頁數
  "keyword": "cable manufacturer",  // 關鍵字（單一，字串）
  "miner_mode": "yellowpages",      // yellowpages / manufacturer
  "email_strategy": "free"          // free（官網爬取）/ hunter（付費API）
}
```

---

## 三、每種模式的完整流程圖

### 免費黃頁模式 (`scrape_simple.py`, `email_strategy=free`)
```
1. 配額檢查 (check_user_quota)
       ↓
2. sync_from_global_pool() 去重檢查
   - 先查私域 (user_id + domain)
   - 再查全域池 (domain → company_name)
       ↓
3. Junipr YellowPages Actor
   - searchTerms = keyword (字串，非陣列)
   - location = "United States" 等
   - extractEmails = true
   - maxResults = 20
   → 備援: automation-lab/yellowpages-scraper
       ↓
4. 過濾垃圾資料（餐廳/咖啡廳等非目標）
       ↓
5. Email 三層補強（免費模式）:
   Layer 1: extract_best_email() → Apify 回傳的 email
   Layer 2: find_emails_free(domain) → 從官網爬取
   Layer 3: Domain Prefix Guessing → info@/sales@/contact@
       ↓
6. 入庫 → increment_usage() → save_to_global_pool()
```

### Hunter.io 黃頁模式 (`scrape_simple.py`, `email_strategy=hunter`)
```
步驟 1-4: 同上
       ↓
5. Email 補強:
   Layer 1: extract_best_email() → Apify 回傳
   Layer 2: Hunter.io API (domain-search) → 付費 email 查找
   Layer 3: Domain Prefix Guessing (email_candidates only)
       ↓
6. 入庫 → increment_usage() → save_to_global_pool()
```

### 免費製造商模式 (`manufacturer_miner.py`, `email_strategy=free`)
```
1. 配額檢查 (check_user_quota)
       ↓
2. sync_from_global_pool() 去重檢查
       ↓
3. Thomasnet Actor (zen-studio/thomasnet-suppliers-scraper)
   - searchKeywords = keyword
   - maxItems = 20
   → 備援: jeeves_is_my_copilot/thomasnet-supplier-directory-scraper
       ↓
4. 備援: Google Custom Search API
   - 關鍵字: "{keyword} manufacturer"
   - 每日配額: 100 次
       ↓
5. auto_discover_domain(domain) → 找官網
       ↓
6. Email 補強（免費）:
   Layer 1: extract_best_email()
   Layer 2: find_emails_free(domain, company_name) → 官網爬取
   Layer 3: Domain Prefix Guessing
       ↓
7. 入庫 → increment_usage() → save_to_global_pool()
```

### Hunter.io 製造商模式 (`manufacturer_miner.py`, `email_strategy=hunter`)
```
步驟 1-6: 同上（但 Layer 2 使用 Hunter.io API）
       ↓
6. Email 補強（Hunter付費）:
   Layer 1: extract_best_email()
   Layer 2: Hunter.io API (domain-search)
   Layer 3: Domain Prefix Guessing
       ↓
7. 入庫 → increment_usage() → save_to_global_pool()
```

---

## 四、測試資料表

### 黃頁模式測試

| 執行日期 | 市場 | 關鍵字 | Email策略 | 任務ID | 任務狀態 | 爬取筆數 | 有email | 有candidates | 全為空 |
|---------|------|--------|---------|--------|---------|---------|--------|-------------|-------|
| 2026-03-28 | US | cable manufacturer | free | #34 | Completed | 0 | 0 | 0 | 0 |
| 2026-03-28 | US | steel fabrication | free | ? | ? | ? | ? | ? | ? |
| 2026-03-28 | US | plastic molding | free | ? | ? | ? | ? | ? | ? |
| 2026-03-28 | US | restaurant equipment | free | ? | ? | ? | ? | ? | ? |

### 製造商模式測試

| 執行日期 | 市場 | 關鍵字 | Email策略 | 任務ID | 任務狀態 | 爬取筆數 | 有email | 有candidates | 全為空 |
|---------|------|--------|---------|--------|---------|---------|--------|-------------|-------|
| 2026-03-28 | US | auto parts | free | #33 | Running | ? | ? | ? | ? |
| 2026-03-28 | US | car parts | free | #30 | Running | ? | ? | ? | ? |
| 2026-03-28 | US | electronics | free | ? | ? | ? | ? | ? | ? |
| 2026-03-28 | US | cable manufacturer | free | ? | ? | ? | ? | ? | ? |

### 測試結果計算
```
Email 成功率 = 有 contact_email 的筆數 / 總爬取筆數 × 100%
Candidates 率 = 有 email_candidates 的筆數 / 總爬取筆數 × 100%
```

---

## 五、Debug 排查清單

| 問題 | 原因 | 解法 |
|------|------|------|
| 爬取筆數 = 0 | Junipr searchTerms 用錯格式 | 確認是字串非陣列 |
| 結果是餐廳 | YellowPages 關鍵字太廣 | 過濾餐廳關鍵字 |
| email 全為 null | YellowPages 隱私政策不顯示 | 靠 Layer 2/3 補強 |
| 製造商模式卡住 | Thomasnet API 慢 / Google CSE 配額用完 | 等 10min 或檢查 Render 日誌 |
| Hunter 模式失敗 | API Key 未設定 | 確認 SystemSettings 有填入 |

---

## 六、驗收標準

| 等級 | 項目 | 標準 |
|------|------|------|
| 🔴 | 免費黃頁：API 有回傳 | 筆數 > 0 |
| 🔴 | 免費黃頁：email_candidates 有值 | ≥ 30% |
| 🟡 | 免費黃頁：contact_email 有值 | ≥ 10% |
| 🔴 | 製造商模式：API 有回傳 | 筆數 > 0 |
| 🔴 | 製造商模式：email_candidates 有值 | ≥ 30% |
| 🟡 | 任務狀態正確 | Completed / Failed，無卡住 |
| 🟡 | 日誌完整 | 每步驟有 INFO/WARNING/ERROR |

---

*文件由 Ann 建立，2026-03-28 更新至 v3.2*
