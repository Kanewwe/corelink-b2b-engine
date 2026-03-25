# Linkora 爬蟲功能測試計畫

> 建立日期：2026-03-26  
> 目標：驗證所有爬蟲功能在 UAT 環境正常運作

---

## 一、爬蟲架構總覽

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 LeadEngine.tsx                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ 黃頁模式    │  │ 製造商模式  │  │ Email 發現策略      │  │
│  │ yellowpages │  │ manufacturer│  │ free / hunter       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                        後端 API                              │
│  POST /api/scrape-simple (主要入口)                          │
│  ├── miner_mode: "yellowpages" → scrape_simple.py            │
│  ├── miner_mode: "manufacturer" → manufacturer_miner.py      │
│  └── email_strategy: "free" / "hunter"                       │
│                                                               │
│  POST /api/scrape (舊版，單關鍵字)                            │
│  └── scraper.py                                              │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      資料來源                                │
│  Yellowpages: 直接 HTTP 爬取 (requests + BeautifulSoup)      │
│  Manufacturer: Google CSE API + Thomasnet + Dork 備援         │
│  Email Discovery: Hunter.io API (可選)                       │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      資料儲存                                │
│  ScrapeTask (任務記錄) → History 頁面顯示                    │
│  Lead (公司資料) → LeadEngine 客戶列表                       │
│  EmailCampaign (草稿) → 後續寄信使用                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、測試項目清單

### ✅ T1 — API 端點健康檢查

| 測試 | 方法 | 端點 | 預期結果 |
|------|------|------|---------|
| T1.1 | POST | `/api/scrape-simple` | 202 Accepted，任務啟動 |
| T1.2 | GET | `/api/search-history` | 200 OK，回傳任務列表 |
| T1.3 | GET | `/api/leads` | 200 OK，回傳爬取的公司 |

### ✅ T2 — 黃頁模式 (yellowpages)

| 測試 | 場景 | 輸入 | 預期結果 |
|------|------|------|---------|
| T2.1 | 單一關鍵字 | `keyword: "cable manufacturer"` | 成功爬取，Leads 入庫 |
| T2.2 | 多關鍵字 | `keywords: ["cable", "wire"]` | 依序處理，任務記錄正確 |
| T2.3 | 不同市場 | `market: "US" / "EU" / "TW"` | 對應黃頁網站 |
| T2.4 | 頁數控制 | `pages: 1 / 3 / 5` | 正確限制爬取深度 |
| T2.5 | 重複檢查 | 同公司再次爬取 | 跳過已存在，記錄原因 |

### ✅ T3 — 製造商模式 (manufacturer)

| 測試 | 場景 | 輸入 | 預期結果 |
|------|------|------|---------|
| T3.1 | 基本搜尋 | `keyword: "auto parts"` | Google CSE 回傳結果 |
| T3.2 | B2B 過濾 | 大型企業名稱 | 黑名單排除 (bosch, siemens 等) |
| T3.3 | 公司規模 | 中小企業網站 | 成功識別並入庫 |
| T3.4 | 備援機制 | Google CSE 失敗 | 自動切換 Thomasnet / Dork |
| T3.5 | 多關鍵字批次 | 3+ 關鍵字 | 依序執行，不阻塞 |

### ✅ T4 — Email 發現策略

| 測試 | 場景 | 策略 | 預期結果 |
|------|------|------|---------|
| T4.1 | 免費模式 | `email_strategy: "free"` | 從網頁提取公開 Email |
| T4.2 | Hunter.io | `email_strategy: "hunter"` | 呼叫 Hunter API |
| T4.3 | API Key 缺失 | Hunter 未設定 | 優雅降級為 free 模式 |

### ✅ T5 — 背景任務與記錄

| 測試 | 場景 | 檢查點 | 預期結果 |
|------|------|--------|---------|
| T5.1 | 任務狀態 | History 頁面 | Running → Completed |
| T5.2 | 進度追蹤 | `leads_found` 欄位 | 數字正確累加 |
| T5.3 | 錯誤處理 | 無效關鍵字 | Failed 狀態 + 錯誤記錄 |
| T5.4 | 時間記錄 | `started_at` / `completed_at` | 時間戳正確 |

### ✅ T6 — 資料完整性

| 測試 | 欄位 | 來源 | 驗證 |
|------|------|------|------|
| T6.1 | company_name | 網頁標題 | 清理後正確 |
| T6.2 | domain | 網址解析 | 正確提取 |
| T6.3 | email_candidates | 網頁/Hunter | 格式正確 |
| T6.4 | description | AI 生成 | 有內容 |
| T6.5 | ai_tag | AI 分類 | 自動標籤 |

---

## 三、環境變數檢查清單

```bash
# 必需（黃頁模式）
- 無特殊需求，requests + BeautifulSoup 即可

# 製造商模式建議
GOOGLE_API_KEY=xxx      # Google Custom Search API
GOOGLE_CSE_ID=xxx       # Search Engine ID

# Email Hunter（可選）
HUNTER_API_KEY=xxx      # Hunter.io API
```

---

## 四、手動測試步驟

### Step 1: 黃頁模式測試
```bash
curl -X POST https://linkora-backend-uat.onrender.com/api/scrape-simple \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "market": "US",
    "pages": 1,
    "keywords": ["cable manufacturer"],
    "miner_mode": "yellowpages",
    "email_strategy": "free"
  }'
```

### Step 2: 檢查任務記錄
```bash
curl https://linkora-backend-uat.onrender.com/api/search-history \
  -H "Authorization: Bearer <token>"
```

### Step 3: 檢查 Leads
```bash
curl https://linkora-backend-uat.onrender.com/api/leads \
  -H "Authorization: Bearer <token>"
```

### Step 4: 製造商模式測試
```bash
curl -X POST https://linkora-backend-uat.onrender.com/api/scrape-simple \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "market": "US",
    "pages": 1,
    "keywords": ["auto parts"],
    "miner_mode": "manufacturer",
    "email_strategy": "free"
  }'
```

---

## 五、已知問題與風險

| 問題 | 影響 | 狀態 | 備註 |
|------|------|------|------|
| Yellowpages 反爬蟲 | 可能被封 IP | 🟡 監控中 | 有 User-Agent 輪換 |
| Google CSE 配額 | 每日 100 次 | 🟡 監控中 | 建議加配額檢查 |
| Hunter.io 免費版 | 每月 50 次 | 🟢 可接受 | 超額自動降級 |
| 背景任務無進度 | 前端無法即時更新 | 🟡 已知 | 需輪詢或 WebSocket |
| 重複公司判斷 | 僅比對 company_name | 🟡 可優化 | 建議加 domain 比對 |

---

## 六、自動化測試建議

```python
# tests/test_scraper.py（建議新增）
def test_scrape_simple_yellowpages():
    """測試黃頁模式基本功能"""
    pass

def test_scrape_simple_manufacturer():
    """測試製造商模式基本功能"""
    pass

def test_scrape_task_record():
    """測試任務記錄建立"""
    pass

def test_duplicate_check():
    """測試重複公司跳過"""
    pass
```

---

## 七、驗收標準

- [ ] T1: 所有 API 端點回傳 200/202
- [ ] T2: 黃頁模式成功爬取 ≥5 家公司
- [ ] T3: 製造商模式成功爬取 ≥3 家公司（有 GOOGLE_API_KEY）
- [ ] T4: Email 發現策略切換正常
- [ ] T5: History 頁面正確顯示任務狀態
- [ ] T6: Leads 資料完整無缺欄位

---

*測試計畫由 Ann 建立，待 Kane 確認後執行*
