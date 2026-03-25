# Linkora 爬蟲系統技術文件

> **版本：** 1.0.0  
> **建立日期：** 2026-03-26  
> **維護者：** Ann (AI)  
> **適用範圍：** UAT/PRD 環境

---

## 一、系統架構

### 1.1 整體流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         前端 LeadEngine.tsx                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ 黃頁模式        │  │ 製造商模式      │  │ Email 發現策略      │  │
│  │ Yellowpages     │  │ Manufacturer    │  │ free / hunter       │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘  │
└───────────┼────────────────────┼──────────────────────┼─────────────┘
            │                    │                      │
            ▼                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          後端 API 層                                 │
│  POST /api/scrape-simple (主要入口)                                  │
│  ├── miner_mode: "yellowpages"  → scrape_simple.py                  │
│  ├── miner_mode: "manufacturer" → manufacturer_miner.py             │
│  └── email_strategy: "free" / "hunter"                              │
│                                                                       │
│  POST /api/scrape (舊版，單關鍵字，已棄用)                            │
│  └── scraper.py                                                      │
└─────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          資料來源層                                  │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Yellowpages 模式                                                │ │
│  │ • ScraperAPI (http://api.scraperapi.com)                       │ │
│  │ • 直接 HTTP 爬取 (requests + BeautifulSoup)                    │ │
│  │ • 模擬降級模式 (Mock Mode，當 API 失敗時)                      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ 製造商模式                                                      │ │
│  │ • Google Custom Search API (優先)                              │ │
│  │ • Thomasnet 目錄搜尋 (美國市場備援)                            │ │
│  │ • Google Dork 搜尋 (最終備援)                                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Email 發現                                                      │ │
│  │ • 免費模式：網頁正則提取                                        │ │
│  │ • Hunter.io API (需 HUNTER_API_KEY)                            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          資料儲存層                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ ScrapeTask      │  │ Lead            │  │ EmailCampaign       │  │
│  │ (任務記錄)      │  │ (公司資料)      │  │ (郵件草稿)          │  │
│  │ • status        │  │ • company_name  │  │ • subject           │  │
│  │ • leads_found   │  │ • domain        │  │ • content           │  │
│  │ • started_at    │  │ • contact_email │  │ • status            │  │
│  │ • completed_at  │  │ • ai_tag        │  │                     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 模組對照表

| 檔案 | 用途 | 對應 miner_mode |
|------|------|-----------------|
| `scrape_simple.py` | 黃頁模式主邏輯 | `yellowpages` |
| `manufacturer_miner.py` | 製造商模式主邏輯 | `manufacturer` |
| `scraper.py` | 舊版單關鍵字爬蟲 | (已棄用) |
| `scraper_engine.py` | 底層爬蟲引擎 | (內部使用) |

---

## 二、API 規格

### 2.1 啟動爬蟲任務

```http
POST /api/scrape-simple
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "market": "US",
  "pages": 3,
  "keywords": ["cable manufacturer", "wire supplier"],
  "location": "California",
  "miner_mode": "yellowpages",
  "email_strategy": "free"
}
```

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `market` | string | ✅ | 目標市場：`US`, `EU`, `TW` |
| `pages` | int | ✅ | 爬取頁數 (1-10) |
| `keywords` | string[] | ✅ | 關鍵字列表 |
| `location` | string | ❌ | 地區過濾 |
| `miner_mode` | string | ✅ | `yellowpages` 或 `manufacturer` |
| `email_strategy` | string | ✅ | `free` 或 `hunter` |

**Response:**

```json
{
  "message": "Yellowpages Mode mining started for US with 2 keywords"
}
```

### 2.2 查詢任務歷史

```http
GET /api/search-history
Authorization: Bearer <token>
```

**Response:**

```json
[
  {
    "id": 1,
    "market": "US",
    "keywords": "cable manufacturer,wire supplier",
    "miner_mode": "yellowpages",
    "pages_requested": 3,
    "status": "Completed",
    "leads_found": 24,
    "started_at": "2026-03-26T10:00:00",
    "completed_at": "2026-03-26T10:05:30"
  }
]
```

---

## 三、爬蟲模式詳細說明

### 3.1 黃頁模式 (Yellowpages)

**資料來源：** Yellowpages.com

**處理流程：**

```python
1. 建立 ScrapeTask 記錄 (status: Running)
2. 對每個關鍵字：
   a. 呼叫 ScraperAPI 取得網頁 HTML
   b. BeautifulSoup 解析公司列表
   c. 提取：company_name, domain, phone, address
   d. 重複檢查 (by company_name)
   e. 寫入 Lead 表
3. 更新 ScrapeTask (status: Completed)
```

**降級機制：**

當 ScraperAPI 失敗或被阻擋時，自動啟動 Mock Mode：

```python
results = [
    {
        "name": "Mock Cable Corp 1-1",
        "domain": "mock-cable11.com",
        "url": "https://www.mock-cable11.com",
        "phone": "+1-555-01011",
        "address": "1001 Test Ave, Tech City, CA"
    },
    # ... 最多 10 筆模擬資料
]
```

### 3.2 製造商模式 (Manufacturer)

**資料來源：**
1. Google Custom Search API (優先)
2. Thomasnet (美國市場備援)
3. Google Dork (最終備援)

**B2B 修飾詞：**

```python
B2B_SUFFIXES = [
    "manufacturer",
    "manufacturing company",
    "OEM supplier",
    "wholesale distributor",
    "B2B supplier",
    "factory direct",
    "industrial supplier",
]
```

**企業黑名單：**

排除大型跨國企業，專注中小企業：

```python
ENTERPRISE_BLACKLIST = [
    "bosch", "siemens", "honeywell", "3m", "johnson",
    "ge ", "ford", "toyota", "samsung", "lg ",
    "apple", "amazon", "walmart",
]
```

**Email 三層策略：**

```
Layer 1: 網頁公開 Email 提取
Layer 2: Hunter.io API (如有 API Key)
Layer 3: 預設格式 (info@domain.com)
```

---

## 四、資料庫模型

### 4.1 ScrapeTask (任務記錄)

```python
class ScrapeTask(Base):
    __tablename__ = "scrape_tasks"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    market = Column(String(50))
    keywords = Column(String(255))
    miner_mode = Column(String(50))
    pages_requested = Column(Integer)
    
    status = Column(String(50), default="Running")
    # Running | Completed | Failed
    
    leads_found = Column(Integer, default=0)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
```

### 4.2 Lead (公司資料)

```python
class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    company_name = Column(String, index=True)
    website_url = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    
    contact_email = Column(String, nullable=True)
    email_candidates = Column(String, nullable=True)
    
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    ai_tag = Column(String, nullable=True)
    status = Column(String, default="Scraped")
    
    extracted_keywords = Column(String, nullable=True)
    scrape_location = Column(String, nullable=True)
    source_domain = Column(String, nullable=True)
```

---

## 五、錯誤處理與資源管理

### 5.1 例外處理結構

```python
def scrape_simple(...):
    db = SessionLocal()
    task_record = None
    
    try:
        # 建立任務記錄
        task_record = ScrapeTask(...)
        db.add(task_record)
        db.commit()
        
        # 執行爬蟲邏輯
        ...
        
        # 標記完成
        task_record.status = "Completed"
        db.commit()
        return stats
        
    except Exception as e:
        # 標記失敗
        if task_record:
            task_record.status = "Failed"
            db.commit()
        raise
        
    finally:
        # 確保資源釋放
        db.close()
```

### 5.2 重複檢查邏輯

```python
def check_company_exists(db, company_name: str, domain: str = None):
    # 1. 比對 company_name
    existing = db.query(Lead).filter(
        Lead.company_name == company_name
    ).first()
    
    if existing:
        return True, "資料庫已存在", existing
    
    # 2. 比對 domain (如有)
    if domain:
        existing_domain = db.query(Lead).filter(
            Lead.domain == domain
        ).first()
        if existing_domain:
            return True, "網域已存在", existing_domain
    
    return False, None, None
```

---

## 六、環境變數設定

### 6.1 必需變數

| 變數 | 說明 | 黃頁模式 | 製造商模式 |
|------|------|----------|------------|
| `DATABASE_URL` | PostgreSQL 連線字串 | ✅ | ✅ |
| `SCRAPER_API_KEY` | ScraperAPI 金鑰 | ✅ | ❌ |
| `GOOGLE_API_KEY` | Google CSE API Key | ❌ | ✅ |
| `GOOGLE_CSE_ID` | Google Search Engine ID | ❌ | ✅ |
| `HUNTER_API_KEY` | Hunter.io API Key | ❌ | ❌ (可選) |

### 6.2 設定範例

```bash
# .env 檔案
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# 黃頁模式
SCRAPER_API_KEY=your_scraperapi_key_here

# 製造商模式
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_cse_id_here

# Email Hunter (可選)
HUNTER_API_KEY=your_hunter_key_here
```

---

## 七、監控與日誌

### 7.1 日誌層級

```python
add_log(f"🔍 [多關鍵字爬蟲] 開始任務")           # INFO
add_log(f"✅ [匯入] {company_name}")            # INFO
add_log(f"⏭️  跳過: {name} ({reason})")        # INFO
add_log(f"⚠️  回傳內容異常短小", level="warning") # WARNING
add_log(f"❌ 爬取失敗: {error}", level="error")  # ERROR
```

### 7.2 任務狀態追蹤

| 狀態 | 說明 | 前端顯示 |
|------|------|----------|
| `Running` | 任務執行中 | 🟡 進行中 |
| `Completed` | 任務完成 | 🟢 已完成 |
| `Failed` | 任務失敗 | 🔴 失敗 |

---

## 八、效能與限制

### 8.1 速率限制

| 來源 | 限制 | 處理方式 |
|------|------|----------|
| ScraperAPI | 依套餐 | 自動等待 |
| Google CSE | 100 次/日 | 建議監控 |
| Hunter.io | 50 次/月 (免費) | 超額降級 |
| Yellowpages | 反爬蟲 | User-Agent 輪換 |

### 8.2 建議參數

```python
# 單次任務建議
MAX_KEYWORDS = 5      # 最多 5 個關鍵字
MAX_PAGES = 5         # 最多 5 頁
RATE_LIMIT = 2        # 每頁間隔 2 秒

# 製造商模式
MAX_COMPANIES = 30    # 每次最多處理 30 家公司
```

---

## 九、測試指引

### 9.1 單元測試建議

```python
# tests/test_scraper.py

def test_scrape_simple_yellowpages():
    """測試黃頁模式基本功能"""
    result = scrape_simple("US", 1, ["test"], user_id=1)
    assert result["saved"] >= 0
    assert result["skipped"] >= 0

def test_duplicate_check():
    """測試重複公司跳過"""
    # 先建立一筆
    lead = Lead(company_name="Test Corp", user_id=1)
    db.add(lead)
    db.commit()
    
    # 再次爬取應該跳過
    exists, reason, _ = check_company_exists(db, "Test Corp")
    assert exists is True

def test_scrape_task_record():
    """測試任務記錄建立"""
    # 驗證 ScrapeTask 被正確建立
    pass
```

### 9.2 整合測試指令

```bash
# 1. 黃頁模式
curl -X POST $API_URL/api/scrape-simple \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "market": "US",
    "pages": 1,
    "keywords": ["cable manufacturer"],
    "miner_mode": "yellowpages",
    "email_strategy": "free"
  }'

# 2. 檢查任務
curl $API_URL/api/search-history \
  -H "Authorization: Bearer $TOKEN"

# 3. 檢查結果
curl $API_URL/api/leads \
  -H "Authorization: Bearer $TOKEN"
```

---

## 十、已知問題與未來優化

### 10.1 已知問題

| 問題 | 影響 | 臨時解法 | 長期解法 |
|------|------|----------|----------|
| Yellowpages 反爬蟲 | 可能被封 IP | ScraperAPI + Mock Mode | Proxy Pool |
| 背景任務無進度 | 前端無法即時更新 | 輪詢 History API | WebSocket |
| 重複判斷不精確 | 僅比對 company_name | 加 domain 比對 | 模糊比對演算法 |
| Google CSE 配額 | 每日 100 次 | 監控警告 | 多 API Key 輪替 |

### 10.2 未來優化方向

1. **Proxy Pool**: 自建代理池，降低 ScraperAPI 依賴
2. **分散式爬蟲**: Celery + Redis 支援多 Worker
3. **AI 內容生成**: 自動生成公司描述、標籤分類
4. **即時進度**: WebSocket 推送任務進度
5. **重複偵測**: 模糊比對 + 相似度評分

---

## 十一、相關文件

| 文件 | 說明 |
|------|------|
| `docs/SCRAPER_TEST_PLAN.md` | 詳細測試計畫 |
| `docs/UIUX_STANDARDS.md` | UI/UX 規範 |
| `backend/scrape_simple.py` | 黃頁模式原始碼 |
| `backend/manufacturer_miner.py` | 製造商模式原始碼 |

---

*本文件由 Ann 建立，持續更新中*
