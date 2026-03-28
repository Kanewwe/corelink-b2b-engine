# 爬蟲 Debug 手冊 — Linkora v3.2

> 最後更新：2026-03-28
> 版本：v3.2.1 (commit `1692017`)

---

## 1. 問題分類矩陣

| 層次 | 問題 | 嚴重性 | 狀態 |
|------|------|--------|------|
| Apify Actor | Junipr YellowPages 返回餐廳/無效公司 | 🔴 高 | 待替換 Actor |
| Apify Actor | `searchTerms` 需為**字串**，非陣列 | 🔴 高 | ✅ 已修復 |
| Email 補強 | `find_emails_free()` 每 domain 需 210 秒 | 🔴 高 | ✅ 已修復（free 模式跳過） |
| 去重邏輯 | 全域/私域池去重太 aggressive | 🟡 中 | 需觀察 |
| 任務超時 | 製造商模式超時 | 🟡 中 | 需優化 |
| Leads 入庫 | 所有舊 Leads 無 email_candidates | 🟡 中 | 需重新爬取 |
| API 路由 | SystemSettings 前端呼叫錯誤接口 | 🟡 中 | ✅ 需修復 |

---

## 2. 爬蟲四模式架構

```
前端 LeadEngine.tsx
  └─ POST /api/scrape-simple
       └─ miner_mode: "yellowpages" | "manufacturer"
          └─ email_strategy: "free" | "hunter"

┌─ 黃頁模式 (yellowpages) ──────────────────────────────┐
│  backend/scrape_simple.py                             │
│                                                      │
│  Apify Junipr YellowPages Scraper                   │
│    actor: "junipr/yellow-pages-scraper"              │
│    input: {"searchTerms": "關鍵字", "location": "US"}│
│    ⚠️ searchTerms 必須是字串，不是陣列！             │
│    ⚠️ Junipr 對製造商關鍵字返回餐廳（資料品質差）     │
│    → raw items (含 name, website, phone, address)    │
│                                                      │
│  資料過濾                                            │
│    排除關鍵字: restaurant, cafe, bar, pizza, hotel,   │
│                motel, inn, grill, bistro, pub, deli  │
│    排除關鍵字: auto glass, auto repair, muffler,     │
│                tire, brake, car wash, dealership (！│
│    ⚠️ 太多 auto 相關被排除，導致真的 auto parts 工廠  │
│        也被濾掉                                      │
│                                                      │
│  Email 補強（三層）                                  │
│    Layer 1: Apify 回傳的 email 欄位（email/         │
│             emails/contactEmail）                    │
│    Layer 2: (free) → 跳過（太慢）                   │
│             (hunter) → Hunter.io API                │
│    Layer 3: Guessing（info/sales/contact前綴）      │
│                                                      │
│  去重                                                │
│    sync_from_global_pool(domain, name)               │
│    ⚠️ 太 aggressive，相似名稱也視為重複              │
└──────────────────────────────────────────────────────┘

┌─ 製造商模式 (manufacturer) ──────────────────────────┐
│  backend/manufacturer_miner.py                       │
│                                                      │
│  Apify ThomasNet Scraper                             │
│    actor: "zen-studio/thomasnet-suppliers-scraper"  │
│    ⚠️ 從未成功完成（超時 10 分鐘）                  │
│                                                      │
│  若無 Apify → Fallback 全域池同步                    │
│    sync_from_global_pool(domain, name)              │
│    ⚠️ 從未成功跑完過                                 │
└──────────────────────────────────────────────────────┘
```

---

## 3. Email 三層策略（v3.2.1）

```
Apify Actor 回傳
  ├─ email / emails / contactEmail 欄位
  │   └─ Layer 1: 直接使用（source="apify"）
  │
  └─ 無 email 欄位時
       ├─ email_strategy == "hunter"
       │    └─ Layer 2: Hunter.io API（source="hunter"）
       │         └─ Layer 3: Guessing
       └─ email_strategy == "free"
            └─ Layer 3: Guessing（跳過 Layer 2，太慢）
                 前綴優先順序: info > sales > contact

Layer 3 Guessing 前綴: ["info", "sales", "contact"]
→ info@example.com, sales@example.com, contact@example.com
→ 存於 email_candidates（不當 primary contact_email）
```

---

## 4. 已觀測的 Leads 資料（2026-03-27 深夜）

### Task #34-#39 全部無 email_candidates

```
ID 1-81:   全部 email_candidates=null, contact_email=null
           - 大量餐廳（Olive Garden, P.F. Chang's, Jun Japanese...）
           - 大量 auto shops（Firestone, Auto Truck Services...）
           → Junipr YellowPages 資料品質問題

ID 65-81:  email_candidates="" (空字串), contact_email=null
           - 仍是餐廳/auto shops
           - scrape_simple.py 的 extract_best_email() 舊版本行為
```

### 全域池同步問題

```
全域池有 0 筆資料時，黃頁任務仍跳過所有結果。
原因：sync_from_global_pool() 的 company_name 比對太寬鬆
"Rocky Roads Auto" 匹配 "Rocky Roads Auto Glass" → 視為重複
```

---

## 5. Debug 工具

### 5.1 直接測試 Apify Actor

```python
import requests, time, json

APIFY_TOKEN = "your_token"
ACTOR_ID = "junipr/yellow-pages-scraper"

def test_actor(search_term, location="United States", max_results=5):
    # Step 1: 啟動任務
    run = requests.post(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs",
        json={"input": {
            "searchTerm": search_term,       # ⚠️ 單數字串
            "searchTerms": search_term,      # ⚠️ Junipr 用 searchTerms
            "location": location,
            "maxResults": max_results
        }},
        headers={"Authorization": f"Bearer {APIFY_TOKEN}"}
    ).json()
    run_id = run["data"]["id"]
    
    # Step 2: 等待完成
    for i in range(20):
        status = requests.get(
            f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}",
            headers={"Authorization": f"Bearer {APIFY_TOKEN}"}
        ).json()["data"]["status"]
        print(f"  [{i*5}s] {status}")
        if status in ("SUCCEEDED", "FAILED"): break
        time.sleep(5)
    
    # Step 3: 取結果
    if status == "SUCCEEDED":
        items = requests.get(
            f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}/dataset/items",
            headers={"Authorization": f"Bearer {APIFY_TOKEN}"}
        ).json()
        print(f"  結果筆數: {len(items)}")
        for item in items[:3]:
            print(f"    {item.get('businessName','?')} | {item.get('email')} | {item.get('website')}")
```

### 5.2 任務日誌查詢

```python
import urllib.request, json

BASE = "https://linkora-backend-uat.onrender.com"
TOKEN = "admin_token_here"

def get_task_logs(task_id):
    req = urllib.request.Request(
        f"{BASE}/api/admin/scrape-tasks/{task_id}/logs",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    logs = json.loads(urllib.request.urlopen(req, timeout=15).read())
    for l in logs:
        print(f"  [{l['level'].upper():5}] {l['message'][:80]}")

# 用法
get_task_logs(39)
```

### 5.3 Email Enrichment 獨立測試

```python
# 本地端測試（不經過 API）
import asyncio, sys
sys.path.insert(0, "backend")
from free_email_hunter import find_emails_free

async def test():
    result = await find_emails_free("example.com", "Example Corp", timeout=5)
    print(result)

asyncio.run(test())
# ⚠️ 正常需 200+ 秒，timeout=5 實際也會卡住（底層未支援超時中斷）
```

---

## 6. 已知 Bug 與對應修復

### BUG-1: Junipr YellowPages Actor 返回餐廳 ✅ 已記錄
- **現象**：搜尋「auto parts」「steel fabrication」返回餐廳
- **原因**：Junipr actor 的關鍵字匹配演算法有問題
- **Workaround**：更換為 backup actor `automation-lab/yellowpages-scraper` 或 `thecrazymikey/yellowpages-scraper`

### BUG-2: find_emails_free() 210 秒 blocking ✅ 已修復
- **現象**：free 模式 worker timeout
- **原因**：`free_email_hunter.py` 的底層 HTTP 呼叫未支援 asyncio 超時
- **修復**：`scrape_simple.py` 的 free 模式跳過 `find_emails_free()`，改用 Guessing

### BUG-3: 全域池去重太 aggressive
- **現象**：新爬到的公司全部被視為重複
- **原因**：`sync_from_global_pool()` 的 name 比對使用 `ilike`
- **修復**：需要調整比對邏輯，domain 精確匹配 > name 模糊匹配

### BUG-4: SystemSettings 前端 API 路由錯誤
- **現象**：SystemSettings 頁面空白，無法載入設定
- **原因**：前端 GET `/admin/settings`，後端為 `/system/settings`
- **修復**：見下方維修清單

---

## 7. 維修清單（TODO）

- [ ] **更換 Junipr Actor** → 測試 `automation-lab/yellowpages-scraper`
- [ ] **修復 SystemSettings.tsx** → GET path 從 `/admin/settings` 改為 `/system/settings`
- [ ] **修復 SystemSettings.tsx 版本號** → `V3.1.9` → `V3.2 (AI Intelligence)`
- [ ] **製造商模式超時** → Thomasnet actor 無法完成，需要替換或加大 worker timeout
- [ ] **重建 find_emails_free()** → 支援 asyncio 超時中斷
- [ ] **調整去重邏輯** → domain 精確匹配優先於 name 模糊匹配
- [ ] **重新爬取無 email 的 Leads** → 清理舊資料，用正確關鍵字重新爬取

---

## 8. 測試流程（v3.2.1）

### 前置條件
```bash
# 確認新版已部署
curl https://linkora-backend-uat.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@linkora.com","password":"admin123"}' | python3 -c "import sys,json; print('✅ online' if json.load(sys.stdin).get('access_token') else '❌')"
```

### 模式一：免費黃頁（free）
```bash
# 1. 清空全域池（避免去重跳過）
POST /api/admin/global-pool/clear

# 2. 發起爬蟲
POST /api/scrape-simple
{
  "market": "US",
  "pages": 1,
  "keyword": "lighting fixtures manufacturer",
  "miner_mode": "yellowpages",
  "email_strategy": "free"
}

# 3. 等 30 秒，檢查任務日誌
GET /api/admin/scrape-tasks/{id}/logs

# 4. 預期日誌
#   [INFO] 🌐 呼叫 Apify: junipr/yellow-pages-scraper
#   [INFO] 📦 Apify 回傳 N 筆原始資料
#   [INFO] ✅ 過濾後有效資料: M 筆
#   [INFO] 💡 Email Guessing: info@domain.com  (for each)
#   [SUCCESS] 完成

# 5. 檢查 Leads
GET /api/leads
# 預期：有 email_candidates，無 contact_email
```

### 模式二：Hunter.io 黃頁
```bash
POST /api/scrape-simple
{
  "market": "US",
  "pages": 1,
  "keyword": "electronics components manufacturer",
  "miner_mode": "yellowpages",
  "email_strategy": "hunter"
}

# 預期：[INFO] 📧 Hunter.io: xxx@company.com
```

### 模式三：免費製造商（⚠️ 從未成功）
```bash
POST /api/scrape-simple
{
  "market": "US",
  "pages": 1,
  "keyword": "auto parts",
  "miner_mode": "manufacturer",
  "email_strategy": "free"
}
# 預期：任務超時，需更換 Thomasnet actor
```

### 模式四：Hunter.io 製造商（⚠️ 從未成功）
同上，改 `email_strategy: "hunter"`

---

## 9. 關鍵檔案索引

| 檔案 | 行號 | 內容 |
|------|------|------|
| `backend/scrape_simple.py` | ~279 | `scrape_keyword_page_apify()` — Apify 呼叫 |
| `backend/scrape_simple.py` | ~160-200 | Email 補強三層邏輯 |
| `backend/scrape_simple.py` | ~95 | `sync_from_global_pool()` 去重呼叫 |
| `backend/manufacturer_miner.py` | ~150 | `sync_from_global_pool()` |
| `backend/manufacturer_miner.py` | ~50 | Thomasnet Actor 呼叫 |
| `backend/free_email_hunter.py` | 全域 | `find_emails_free()` — 需重寫 |
| `backend/email_hunter.py` | 全域 | Hunter.io API |
| `frontend/src/services/api.ts` | 126 | GET 設定路徑（錯誤）→ 需修復 |
| `frontend/src/pages/SystemSettings.tsx` | ~210 | 版本號顯示（錯誤）→ 需修復 |
