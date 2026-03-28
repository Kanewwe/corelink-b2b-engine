# Linkora 爬蟲系統技術規格書 — v4.2

> **角色：** SA（系統架構師）
> **日期：** 2026-03-29
> **目標：** 優化費用、避免重複、善用全域庫

---

## 1. 核心問題：重複性與費用浪費

### 1.1 問題描述

**情境：** 用戶 A 爬取「electronics manufacturer」，花費 Hunter.io quota
**情境：** 用戶 B 也爬取「electronics manufacturer」，再次花費 quota
**情境：** 同一家公司被重複查詢 email

**費用浪費：**
```
 Hunter.io: $49/月 = 1,000 queries
 重複率假設 30% → 浪費 300 queries = $14.7
```

### 1.2 解決方案

**核心策略：優先查全域庫，命中則免費同步**

```
用戶發起爬取請求
    ↓
檢查全域庫是否有相符資料
    ├─ 命中 → 直接同步到私域池（$0）
    │         └─ 扣除用戶配額
    │
    └─ 未命中 → 呼叫外部 API 爬取
               ├─ 存入全域庫
               └─ 同步到私域池
                   └─ 扣除 API quota + 用戶配額
```

---

## 2. 資料庫設計

### 2.1 global_leads（全域池）

**用途：** 所有用戶共享的公司資料，避免重複爬取

```sql
CREATE TABLE global_leads (
    id SERIAL PRIMARY KEY,
    
    -- 公司基本資訊
    company_name VARCHAR(200) NOT NULL,
    domain VARCHAR(100) UNIQUE,              -- 主要去重鍵
    website_url VARCHAR(500),
    
    -- 聯繫資訊
    contact_email VARCHAR(255),              -- 最佳 email
    email_candidates TEXT,                   -- 所有候選 email（逗號分隔）
    phone VARCHAR(50),
    address TEXT,
    
    -- Email 品質
    email_verified BOOLEAN DEFAULT FALSE,    -- 是否驗證過
    email_confidence INTEGER DEFAULT 0,      -- Hunter 信心度 0-100
    email_source VARCHAR(50),                -- "hunter"|"guessed"|"apify"
    
    -- 公司分類
    ai_tag VARCHAR(100),
    industry VARCHAR(100),
    employee_count INTEGER,                  -- 員工數
    company_type VARCHAR(20),                -- "SME"|"Enterprise"
    
    -- 來源標記
    source VARCHAR(100),                     -- "apollo"|"google_maps"|"hunter"
    source_mode VARCHAR(20),                 -- "general"|"manufacturer"|"sales"|"marketing"
    source_keyword VARCHAR(200),             -- 原始搜尋關鍵字
    
    -- 統計
    sync_count INTEGER DEFAULT 0,            -- 被同步次數
    last_synced_at TIMESTAMP,
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_domain (domain),
    INDEX idx_company_name (company_name),
    INDEX idx_source_mode (source_mode),
    INDEX idx_employee_count (employee_count)
);
```

### 2.2 leads（私域池）

**用途：** 用戶專屬的潛在客戶名單

```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    global_id INTEGER REFERENCES global_leads(id),  -- FK 到全域池
    
    -- 公司資訊（從全域池同步，但可覆蓋）
    company_name VARCHAR(200) NOT NULL,
    domain VARCHAR(100),
    website_url VARCHAR(500),
    
    -- 聯繫資訊
    contact_email VARCHAR(255),
    email_candidates TEXT,
    phone VARCHAR(50),
    address TEXT,
    
    -- Email 品質
    email_verified BOOLEAN DEFAULT FALSE,
    email_confidence INTEGER DEFAULT 0,
    
    -- 用戶專屬
    status VARCHAR(50) DEFAULT 'new',        -- new/contacted/replied/converted
    tags TEXT,                               -- 用戶自訂標籤
    notes TEXT,                              -- 用戶筆記
    lead_score INTEGER DEFAULT 0,            -- 用戶自訂評分
    
    -- 業務模式專用
    contact_person VARCHAR(100),             -- 聯繫人姓名
    contact_position VARCHAR(100),           -- 聯繫人職位
    
    -- 寄信狀態
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    
    -- 來源
    source VARCHAR(100),
    source_mode VARCHAR(20),
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 去重約束
    UNIQUE (user_id, domain),
    INDEX idx_user_domain (user_id, domain)
);
```

### 2.3 scrape_logs（爬取日誌）

**用途：** 追蹤每次爬取，計算費用

```sql
CREATE TABLE scrape_logs (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES scrape_tasks(id),
    
    -- 爬取結果
    companies_found INTEGER DEFAULT 0,       -- 找到的公司數
    from_global_pool INTEGER DEFAULT 0,      -- 從全域庫同步（免費）
    from_external_api INTEGER DEFAULT 0,     -- 從外部 API 爬取（花費）
    
    -- API 費用
    apollo_credits_used INTEGER DEFAULT 0,
    hunter_queries_used INTEGER DEFAULT 0,
    estimated_cost_twd DECIMAL(10,2) DEFAULT 0,
    
    -- 時間
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. 後端 API 設計

### 3.1 爬取 API

#### POST /api/scrape

**請求：**
```json
{
  "mode": "manufacturer",           // general|manufacturer|sales|marketing
  "keyword": "electronics manufacturer",
  "location": "United States",
  "filters": {
    "employee_count_min": 10,
    "employee_count_max": 500,
    "only_verified_email": true
  }
}
```

**回應：**
```json
{
  "success": true,
  "task_id": 123,
  "stats": {
    "total_found": 50,
    "from_global_pool": 30,         // 免費同步
    "from_external_api": 20,        // 需付費
    "estimated_cost_twd": 98.0
  },
  "message": "找到 50 家公司，其中 30 家從全域庫同步（免費）"
}
```

### 3.2 全域庫查詢 API

#### GET /api/global-pool/search

**用途：** 爬取前先查全域庫，顯示有多少可免費同步

**請求：**
```json
{
  "keyword": "electronics",
  "mode": "manufacturer",
  "limit": 10
}
```

**回應：**
```json
{
  "total": 150,
  "available": 150,                 // 可免費同步的數量
  "companies": [
    {
      "company_name": "Tech Corp",
      "domain": "techcorp.com",
      "email_verified": true,
      "email_confidence": 95,
      "employee_count": 250
    }
  ]
}
```

### 3.3 同步 API

#### POST /api/global-pool/sync

**用途：** 從全域庫同步到私域池

**請求：**
```json
{
  "global_ids": [1, 2, 3, 4, 5]
}
```

**回應：**
```json
{
  "success": true,
  "synced": 5,
  "skipped": 0,                      // 已存在私域池
  "quota_used": 5                    // 扣除配額
}
```

---

## 4. 後端流程設計

### 4.1 爬取流程（含重複檢查）

```python
def scrape_manufacturers(keyword, location, user_id, filters):
    """
    製造商模式爬取流程
    優先查全域庫，避免重複花費
    """
    stats = {
        "total_found": 0,
        "from_global_pool": 0,
        "from_external_api": 0,
        "cost_twd": 0
    }
    
    # Step 1: 查全域庫
    global_leads = query_global_pool(
        keyword=keyword,
        mode="manufacturer",
        filters=filters,
        limit=100
    )
    
    stats["total_found"] = len(global_leads)
    stats["from_global_pool"] = len(global_leads)
    
    # 同步到私域池
    for lead in global_leads:
        sync_to_private_pool(user_id, lead)
    
    # Step 2: 如果全域庫不夠，才呼叫外部 API
    if len(global_leads) < filters.get("min_results", 50):
        remaining = filters["min_results"] - len(global_leads)
        
        # 呼叫 Apollo.io
        apollo_results = apollo_search(
            keyword=keyword,
            location=location,
            employee_count_range=(filters.get("employee_count_min"), 
                                   filters.get("employee_count_max"))
        )
        
        # 過濾已在全域庫的
        new_companies = filter_existing(apollo_results, global_leads)
        
        # 呼叫 Hunter.io 取得 email
        for company in new_companies[:remaining]:
            if company.get("domain"):
                hunter_result = hunter_domain_search(company["domain"])
                company.update(hunter_result)
                
                # 存入全域庫
                global_lead = save_to_global_pool(company, source="apollo")
                
                # 同步到私域池
                sync_to_private_pool(user_id, global_lead)
                
                stats["from_external_api"] += 1
        
        # 計算費用
        stats["cost_twd"] = calculate_cost(
            apollo_calls=1,
            hunter_queries=len(new_companies[:remaining])
        )
    
    # 記錄日誌
    log_scrape_stats(user_id, stats)
    
    return stats
```

### 4.2 全域庫查詢邏輯

```python
def query_global_pool(keyword, mode, filters, limit):
    """
    查詢全域庫，支援模糊匹配
    """
    query = db.query(GlobalLead).filter(
        GlobalLead.source_mode == mode
    )
    
    # 關鍵字匹配（公司名稱或產業）
    query = query.filter(
        or_(
            GlobalLead.company_name.ilike(f"%{keyword}%"),
            GlobalLead.industry.ilike(f"%{keyword}%")
        )
    )
    
    # 員工數過濾
    if filters.get("employee_count_min"):
        query = query.filter(
            GlobalLead.employee_count >= filters["employee_count_min"]
        )
    if filters.get("employee_count_max"):
        query = query.filter(
            GlobalLead.employee_count <= filters["employee_count_max"]
        )
    
    # Email 驗證過濾
    if filters.get("only_verified_email"):
        query = query.filter(GlobalLead.email_verified == True)
    
    # 按信心度排序
    query = query.order_by(GlobalLead.email_confidence.desc())
    
    return query.limit(limit).all()
```

### 4.3 同步到私域池

```python
def sync_to_private_pool(user_id, global_lead):
    """
    從全域庫同步到用戶私域池
    """
    # 檢查是否已存在
    existing = db.query(Lead).filter(
        Lead.user_id == user_id,
        Lead.domain == global_lead.domain
    ).first()
    
    if existing:
        return None  # 已存在，跳過
    
    # 建立新 Lead
    lead = Lead(
        user_id=user_id,
        global_id=global_lead.id,
        company_name=global_lead.company_name,
        domain=global_lead.domain,
        website_url=global_lead.website_url,
        contact_email=global_lead.contact_email,
        email_candidates=global_lead.email_candidates,
        email_verified=global_lead.email_verified,
        email_confidence=global_lead.email_confidence,
        phone=global_lead.phone,
        address=global_lead.address,
        source=global_lead.source,
        source_mode=global_lead.source_mode,
        status="new"
    )
    
    db.add(lead)
    
    # 更新全域庫統計
    global_lead.sync_count += 1
    global_lead.last_synced_at = datetime.utcnow()
    
    # 扣除用戶配額
    decrement_user_quota(user_id, "leads", 1)
    
    db.commit()
    
    return lead
```

---

## 5. UI/UX 設計

### 5.1 爬取頁面（LeadEngine.tsx）

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 探勘引擎                                    [V3.2.1]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  模式選擇：                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 一般模式 │ │製造商模式│ │ 業務模式 │ │ 行銷模式 │       │
│  │  免費    │ │  專業版  │ │  企業版  │ │  專業版  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                             │
│  關鍵字：[electronics manufacturer        ] [搜尋]         │
│                                                             │
│  地區：[United States ▼]  員工數：[10] - [500]              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 💡 智慧提示：全域庫已有 150 筆相關公司                │   │
│  │    可免費同步，節省 Hunter 額度                      │   │
│  │                                                      │   │
│  │    [查看全域庫資料] [直接同步] [繼續爬取新資料]      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  結果預覽：                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 公司名稱          │ Domain    │ Email     │ 來源   │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Tech Corp         │ tech.com  │ ✅ 已驗證 │ 全域庫 │   │
│  │ ABC Manufacturing │ abc.com   │ ✅ 已驗證 │ 全域庫 │   │
│  │ XYZ Electronics   │ xyz.com   │ ⚠️ 猜測  │ 新爬取 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [同步選取] [全部同步]                                       │
│                                                             │
│  配額狀態：已使用 50/100 leads                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 全域庫預覽 Modal

```
┌─────────────────────────────────────────────────────────────┐
│  📚 全域庫預覽                                    [關閉]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  篩選：[已驗證 Email ☑] [員工數 10-500 ☑]                   │
│                                                             │
│  找到 150 筆相關公司                                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ │ Tech Corp       │ 250員工 │ ✅ info@tech.com   │   │
│  │ ☑ │ ABC Mfg         │ 120員工 │ ✅ sales@abc.com   │   │
│  │ ☑ │ XYZ Electronics │ 80員工  │ ✅ contact@xyz.com │   │
│  │   │ ...              │ ...     │ ...                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  已選取 30 筆，將扣除 30 配額                                │
│                                                             │
│  [全選] [取消] [確認同步]                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 爬取進度頁面

```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ 爬取進度                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  任務 #123 - 製造商模式                                      │
│  關鍵字：electronics manufacturer                            │
│  狀態：進行中 (45%)                                          │
│                                                             │
│  進度：[████████████░░░░░░░░░░] 45/100                      │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  即時日誌：                                                  │
│  [INFO] 🔍 檢查全域庫...                                     │
│  [INFO] ✅ 全域庫命中 30 筆（免費）                          │
│  [INFO] 🌐 呼叫 Apollo API...                                │
│  [INFO] 📦 Apollo 返回 50 筆公司                             │
│  [INFO] 🔍 過濾重複... 剩餘 20 筆                            │
│  [INFO] 📧 呼叫 Hunter.io 查詢 email...                      │
│  [INFO] ✅ Tech Corp → info@tech.com (verified)              │
│  [INFO] ⚠️ XYZ Inc → 無有效 email                            │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  預估費用：$98 TWD                                           │
│  節省費用：$147 TWD（從全域庫同步 30 筆）                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 費用優化策略

### 6.1 費用計算

```python
def calculate_cost(apollo_calls, hunter_queries):
    """
    計算 API 費用（台幣）
    """
    # Apollo: $49/月 = 10,000 credits
    # 每次搜尋約 100 credits
    apollo_cost_usd = apollo_calls * 100 * (49 / 10000)
    
    # Hunter: $49/月 = 1,000 queries
    hunter_cost_usd = hunter_queries * (49 / 1000)
    
    # 轉台幣（匯率 32）
    total_twd = (apollo_cost_usd + hunter_cost_usd) * 32
    
    return round(total_twd, 2)

# 範例：
# 1 次 Apollo + 20 次 Hunter
# = $0.49 + $0.98 = $1.47 USD = $47 TWD
```

### 6.2 節省費用範例

**情境：** 100 家公司，全域庫已有 60 家

```
不使用全域庫：
  - Apollo: 1 次 = $0.49
  - Hunter: 100 次 = $4.90
  - 總計：$5.39 USD = $172 TWD

使用全域庫：
  - 全域庫同步：60 家 = $0
  - Apollo: 1 次 = $0.49
  - Hunter: 40 次 = $1.96
  - 總計：$2.45 USD = $78 TWD

節省：$94 TWD (55%)
```

---

## 7. 實作清單

### 7.1 後端（Backend）

- [ ] 更新 `global_leads` 表結構（新增欄位）
- [ ] 更新 `leads` 表結構（新增欄位）
- [ ] 新增 `scrape_logs` 表
- [ ] 實作 `query_global_pool()` 函數
- [ ] 實作 `sync_to_private_pool()` 函數
- [ ] 更新爬取流程（優先查全域庫）
- [ ] 新增 `/api/global-pool/search` endpoint
- [ ] 新增 `/api/global-pool/sync` endpoint
- [ ] 更新 `/api/scrape` endpoint（返回費用資訊）

### 7.2 前端（Frontend）

- [ ] 更新 `LeadEngine.tsx` 模式切換 UI
- [ ] 新增全域庫預覽功能
- [ ] 新增智慧提示（全域庫命中數）
- [ ] 新增爬取進度頁面
- [ ] 顯示費用資訊和節省金額

### 7.3 測試

- [ ] 測試全域庫查詢
- [ ] 測試同步邏輯（避免重複）
- [ ] 測試費用計算
- [ ] 測試配額扣除

---

## 8. 下一步

**確認後開始實作：**
1. 先更新 DB 結構
2. 實作全域庫查詢邏輯
3. 更新爬取流程
4. 前端 UI 更新

**預估時程：** 1 週完成一般模式 + 全域庫優化
