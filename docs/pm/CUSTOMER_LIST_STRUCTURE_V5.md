# Linkora 客戶名單結構設計 — v5.0

> **日期：** 2026-03-29
> **重點：** 行業別 Tag 系統 + 完整客戶屬性

---

## 1. 行業別分類系統

### 1.1 一級行業分類（主類別）

| 代碼 | 行業名稱 | 說明 |
|------|---------|------|
| `MFG` | 製造業 | 工廠、生產、加工 |
| `TECH` | 科技業 | 軟體、硬體、電子 |
| `RETAIL` | 零售業 | 電商、實體店、批發 |
| `SERVICE` | 服務業 | 餐飲、旅遊、教育 |
| `FINANCE` | 金融業 | 銀行、保險、投資 |
| `HEALTH` | 醫療健康 | 醫院、診所、藥廠 |
| `CONSTRUCTION` | 建築營造 | 建設、工程、裝修 |
| `TRANSPORT` | 運輸物流 | 貨運、倉儲、配送 |
| `ENERGY` | 能源環保 | 電力、綠能、回收 |
| `AGRICULTURE` | 農林漁牧 | 農業、漁業、畜牧 |
| `OTHER` | 其他 | 未分類 |

### 1.2 二級行業分類（子類別）

#### MFG 製造業

| 代碼 | 子行業 |
|------|--------|
| `MFG-ELEC` | 電子製造 |
| `MFG-MECH` | 機械製造 |
| `MFG-CHEM` | 化學製造 |
| `MFG-TEXTILE` | 紡織製造 |
| `MFG-FOOD` | 食品加工 |
| `MFG-PLASTIC` | 塑膠製造 |
| `MFG-METAL` | 金屬加工 |
| `MFG-AUTO` | 汽車零件 |
| `MFG-OTHER` | 其他製造 |

#### TECH 科技業

| 代碼 | 子行業 |
|------|--------|
| `TECH-SOFTWARE` | 軟體開發 |
| `TECH-HARDWARE` | 硬體設備 |
| `TECH-SEMICON` | 半導體 |
| `TECH-IOT` | 物聯網 |
| `TECH-AI` | AI/機器學習 |
| `TECH-CLOUD` | 雲端服務 |
| `TECH-CYBER` | 資訊安全 |
| `TECH-OTHER` | 其他科技 |

#### RETAIL 零售業

| 代碼 | 子行業 |
|------|--------|
| `RETAIL-ECOMMERCE` | 電商平台 |
| `RETAIL-STORE` | 實體零售 |
| `RETAIL-WHOLESALE` | 批發貿易 |
| `RETAIL-FASHION` | 時尚服飾 |
| `RETAIL-OTHER` | 其他零售 |

#### SERVICE 服務業

| 代碼 | 子行業 |
|------|--------|
| `SERVICE-RESTAURANT` | 餐飲 |
| `SERVICE-HOTEL` | 旅遊住宿 |
| `SERVICE-EDU` | 教育培訓 |
| `SERVICE-CONSULT` | 顧問諮詢 |
| `SERVICE-MARKETING` | 行銷廣告 |
| `SERVICE-LEGAL` | 法律服務 |
| `SERVICE-ACCOUNTING` | 會計審計 |
| `SERVICE-OTHER` | 其他服務 |

#### FINANCE 金融業

| 代碼 | 子行業 |
|------|--------|
| `FINANCE-BANK` | 銀行 |
| `FINANCE-INSURANCE` | 保險 |
| `FINANCE-INVEST` | 投資理財 |
| `FINANCE-FINTECH` | 金融科技 |
| `FINANCE-OTHER` | 其他金融 |

#### HEALTH 醫療健康

| 代碼 | 子行業 |
|------|--------|
| `HEALTH-HOSPITAL` | 醫院診所 |
| `HEALTH-PHARMA` | 製藥 |
| `HEALTH-MEDICAL` | 醫療器材 |
| `HEALTH-BIOTECH` | 生物科技 |
| `HEALTH-OTHER` | 其他醫療 |

#### CONSTRUCTION 建築營造

| 代碼 | 子行業 |
|------|--------|
| `CONST-BUILD` | 建設公司 |
| `CONST-ENGINEER` | 工程承包 |
| `CONST-ARCHITECT` | 建築設計 |
| `CONST-DECOR` | 室內裝修 |
| `CONST-OTHER` | 其他營造 |

#### TRANSPORT 運輸物流

| 代碼 | 子行業 |
|------|--------|
| `TRANS-FREIGHT` | 貨運 |
| `TRANS-WAREHOUSE` | 倉儲 |
| `TRANS-SHIPPING` | 船運 |
| `TRANS-AIR` | 空運 |
| `TRANS-OTHER` | 其他運輸 |

#### ENERGY 能源環保

| 代碼 | 子行業 |
|------|--------|
| `ENERGY-ELECTRIC` | 電力 |
| `ENERGY-SOLAR` | 太陽能 |
| `ENERGY-WIND` | 風力 |
| `ENERGY-RECYCLE` | 資源回收 |
| `ENERGY-OTHER` | 其他能源 |

#### AGRICULTURE 農林漁牧

| 代碼 | 子行業 |
|------|--------|
| `AGRI-FARM` | 農業 |
| `AGRI-FISHERY` | 漁業 |
| `AGRI-LIVESTOCK` | 畜牧 |
| `AGRI-OTHER` | 其他農業 |

---

## 2. 客戶名單完整結構

### 2.1 global_leads（全域池）

```sql
CREATE TABLE global_leads (
    id SERIAL PRIMARY KEY,
    
    -- === 公司基本資訊 ===
    company_name VARCHAR(200) NOT NULL,
    company_name_en VARCHAR(200),              -- 英文名稱
    domain VARCHAR(100) UNIQUE,
    website_url VARCHAR(500),
    
    -- === 行業分類（重要！）===
    industry_code VARCHAR(20),                 -- 一級行業代碼（MFG/TECH/...）
    industry_name VARCHAR(100),                -- 一級行業名稱
    sub_industry_code VARCHAR(20),             -- 二級行業代碼（MFG-ELEC/...）
    sub_industry_name VARCHAR(100),            -- 二級行業名稱
    industry_tags TEXT,                        -- 多標籤（逗號分隔）"電子,製造,半導體"
    ai_suggested_industry VARCHAR(100),        -- AI 推薦行業
    
    -- === 公司規模 ===
    employee_count INTEGER,
    employee_range VARCHAR(20),                -- "1-10"|"10-50"|"50-200"|"200-500"|"500+"
    annual_revenue_range VARCHAR(20),          -- 營收區間
    
    -- === 公司類型 ===
    company_type VARCHAR(20),                  -- "SME"|"Enterprise"|"Startup"
    business_model VARCHAR(50),                -- "B2B"|"B2C"|"B2B2C"
    
    -- === 地理資訊 ===
    country VARCHAR(50),
    state VARCHAR(50),
    city VARCHAR(50),
    address TEXT,
    postal_code VARCHAR(20),
    
    -- === 聯繫資訊 ===
    contact_email VARCHAR(255),
    email_candidates TEXT,                     -- 所有候選 email
    phone VARCHAR(50),
    fax VARCHAR(50),
    
    -- === Email 品質 ===
    email_verified BOOLEAN DEFAULT FALSE,
    email_confidence INTEGER DEFAULT 0,
    email_source VARCHAR(50),                  -- "hunter"|"guessed"|"apify"
    last_verified_at TIMESTAMP,
    
    -- === 社群連結 ===
    linkedin_url VARCHAR(500),
    facebook_url VARCHAR(500),
    twitter_url VARCHAR(500),
    
    -- === 公司描述 ===
    description TEXT,
    products_services TEXT,                    -- 產品/服務
    keywords TEXT,                             -- 關鍵字
    
    -- === AI 分析 ===
    ai_score INTEGER DEFAULT 0,
    ai_brief TEXT,
    ai_suggestions TEXT,
    ai_tag VARCHAR(100),                       -- AI 標籤
    
    -- === 來源標記 ===
    source VARCHAR(100),                       -- "apollo"|"google_maps"|"hunter"
    source_mode VARCHAR(20),                   -- "general"|"manufacturer"|"sales"|"marketing"
    source_keyword VARCHAR(200),               -- 原始搜尋關鍵字
    source_url VARCHAR(500),                   -- 來源 URL
    
    -- === 統計 ===
    sync_count INTEGER DEFAULT 0,
    last_synced_at TIMESTAMP,
    
    -- === 資料狀態 ===
    status VARCHAR(20) DEFAULT 'active',       -- active|acquired|closed|needs_refresh
    company_group_id INTEGER,                  -- 公司群組 ID
    acquired_from VARCHAR(200),
    
    -- === 時間戳記 ===
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- === 索引 ===
    INDEX idx_domain (domain),
    INDEX idx_company_name (company_name),
    INDEX idx_industry_code (industry_code),
    INDEX idx_sub_industry_code (sub_industry_code),
    INDEX idx_country (country),
    INDEX idx_employee_count (employee_count),
    INDEX idx_source_mode (source_mode)
);
```

### 2.2 leads（私域池）

```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    global_id INTEGER REFERENCES global_leads(id),
    
    -- === 公司資訊（從全域庫同步，可覆蓋）===
    company_name VARCHAR(200) NOT NULL,
    company_name_en VARCHAR(200),
    domain VARCHAR(100),
    website_url VARCHAR(500),
    
    -- === 行業分類（同步自全域庫）===
    industry_code VARCHAR(20),
    industry_name VARCHAR(100),
    sub_industry_code VARCHAR(20),
    sub_industry_name VARCHAR(100),
    industry_tags TEXT,
    
    -- === 公司規模 ===
    employee_count INTEGER,
    employee_range VARCHAR(20),
    
    -- === 地理資訊 ===
    country VARCHAR(50),
    state VARCHAR(50),
    city VARCHAR(50),
    address TEXT,
    
    -- === 聯繫資訊 ===
    contact_email VARCHAR(255),
    email_candidates TEXT,
    phone VARCHAR(50),
    
    -- === Email 品質 ===
    email_verified BOOLEAN DEFAULT FALSE,
    email_confidence INTEGER DEFAULT 0,
    
    -- === 聯繫人（業務模式）===
    contact_person VARCHAR(100),
    contact_position VARCHAR(100),
    contact_department VARCHAR(50),
    contact_linkedin VARCHAR(500),
    
    -- === 用戶專屬 ===
    status VARCHAR(50) DEFAULT 'new',          -- new/contacted/replied/converted/lost
    lead_score INTEGER DEFAULT 0,              -- 用戶自訂評分 0-100
    priority VARCHAR(20),                      -- high|medium|low
    
    -- === 用戶自訂標籤（重要！）===
    user_tags TEXT,                            -- 用戶自訂標籤（逗號分隔）
    user_notes TEXT,                           -- 用戶筆記
    
    -- === 銷售階段 ===
    sales_stage VARCHAR(50),                   -- prospecting|qualification|proposal|negotiation|closed
    expected_deal_size DECIMAL(10,2),
    probability INTEGER,                       -- 成交機率 0-100
    
    -- === 寄信狀態 ===
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    email_opens INTEGER DEFAULT 0,             -- 開信次數
    last_opened_at TIMESTAMP,
    email_clicks INTEGER DEFAULT 0,            -- 點擊次數
    last_clicked_at TIMESTAMP,
    email_replied BOOLEAN DEFAULT FALSE,
    replied_at TIMESTAMP,
    
    -- === 來源 ===
    source VARCHAR(100),
    source_mode VARCHAR(20),
    data_source VARCHAR(20),                   -- "global_sync"|"new_scrape"|"updated"
    
    -- === 覆蓋資料（用戶可編輯）===
    override_name VARCHAR(200),
    override_email VARCHAR(255),
    personal_notes TEXT,
    custom_tags TEXT,
    
    -- === 時間戳記 ===
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_contact_at TIMESTAMP,
    last_global_sync_at TIMESTAMP,
    
    -- === 去重約束 ===
    UNIQUE (user_id, domain),
    INDEX idx_user_domain (user_id, domain),
    INDEX idx_user_industry (user_id, industry_code),
    INDEX idx_user_status (user_id, status)
);
```

### 2.3 industry_tags（行業標籤主檔）

```sql
CREATE TABLE industry_tags (
    id SERIAL PRIMARY KEY,
    
    -- === 標籤代碼 ===
    code VARCHAR(20) UNIQUE NOT NULL,          -- "MFG-ELEC"
    parent_code VARCHAR(20),                   -- "MFG"
    
    -- === 標籤名稱 ===
    name_en VARCHAR(100) NOT NULL,             -- "Electronics Manufacturing"
    name_zh VARCHAR(100) NOT NULL,             -- "電子製造"
    name_short VARCHAR(50),                    -- "電子"
    
    -- === 標籤層級 ===
    level INTEGER DEFAULT 1,                   -- 1=一級, 2=二級
    
    -- === 搜尋關鍵字 ===
    keywords TEXT,                             -- 相關關鍵字（逗號分隔）
    
    -- === 統計 ===
    company_count INTEGER DEFAULT 0,           -- 該行業公司數
    
    -- === 顯示 ===
    icon VARCHAR(50),                          -- 圖示名稱
    color VARCHAR(20),                         -- 標籤顏色
    
    -- === 排序 ===
    sort_order INTEGER DEFAULT 0,
    
    -- === 狀態 ===
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初始化行業標籤
INSERT INTO industry_tags (code, parent_code, name_en, name_zh, level, keywords, sort_order) VALUES
-- 一級行業
('MFG', NULL, 'Manufacturing', '製造業', 1, '工廠,生產,加工,製造', 1),
('TECH', NULL, 'Technology', '科技業', 1, '科技,軟體,硬體,電子', 2),
('RETAIL', NULL, 'Retail', '零售業', 1, '零售,電商,批發', 3),
('SERVICE', NULL, 'Services', '服務業', 1, '服務,餐飲,旅遊,教育', 4),
('FINANCE', NULL, 'Finance', '金融業', 1, '金融,銀行,保險', 5),
('HEALTH', NULL, 'Healthcare', '醫療健康', 1, '醫療,醫院,藥廠', 6),
('CONSTRUCTION', NULL, 'Construction', '建築營造', 1, '建築,工程,營造', 7),
('TRANSPORT', NULL, 'Transportation', '運輸物流', 1, '運輸,物流,貨運', 8),
('ENERGY', NULL, 'Energy', '能源環保', 1, '能源,電力,環保', 9),
('AGRICULTURE', NULL, 'Agriculture', '農林漁牧', 1, '農業,漁業,畜牧', 10),

-- 二級行業
('MFG-ELEC', 'MFG', 'Electronics Manufacturing', '電子製造', 2, '電子,PCB,半導體', 1),
('MFG-MECH', 'MFG', 'Mechanical Manufacturing', '機械製造', 2, '機械,車床,CNC', 2),
('MFG-CHEM', 'MFG', 'Chemical Manufacturing', '化學製造', 2, '化工,塑膠,材料', 3),
('MFG-TEXTILE', 'MFG', 'Textile Manufacturing', '紡織製造', 2, '紡織,成衣,布料', 4),
('MFG-FOOD', 'MFG', 'Food Processing', '食品加工', 2, '食品,飲料,加工', 5),
('MFG-PLASTIC', 'MFG', 'Plastic Manufacturing', '塑膠製造', 2, '塑膠,射出,模具', 6),
('MFG-METAL', 'MFG', 'Metal Processing', '金屬加工', 2, '金屬,沖壓,焊接', 7),
('MFG-AUTO', 'MFG', 'Auto Parts', '汽車零件', 2, '汽車,零件,車用', 8),

('TECH-SOFTWARE', 'TECH', 'Software Development', '軟體開發', 2, '軟體,APP,SaaS', 1),
('TECH-HARDWARE', 'TECH', 'Hardware', '硬體設備', 2, '硬體,設備,伺服器', 2),
('TECH-SEMICON', 'TECH', 'Semiconductor', '半導體', 2, '半導體,晶圓,IC', 3),
('TECH-IOT', 'TECH', 'IoT', '物聯網', 2, 'IoT,物聯網,智慧', 4),
('TECH-AI', 'TECH', 'AI/ML', 'AI/機器學習', 2, 'AI,機器學習,人工智慧', 5),

('RETAIL-ECOMMERCE', 'RETAIL', 'E-commerce', '電商平台', 2, '電商,網購,平台', 1),
('RETAIL-STORE', 'RETAIL', 'Retail Store', '實體零售', 2, '零售,門市,店面', 2),
('RETAIL-WHOLESALE', 'RETAIL', 'Wholesale', '批發貿易', 2, '批發,貿易,進出口', 3),

('SERVICE-RESTAURANT', 'SERVICE', 'Restaurant', '餐飲', 2, '餐廳,美食,外食', 1),
('SERVICE-HOTEL', 'SERVICE', 'Hotel & Tourism', '旅遊住宿', 2, '飯店,旅遊,民宿', 2),
('SERVICE-EDU', 'SERVICE', 'Education', '教育培訓', 2, '教育,培訓,課程', 3),
('SERVICE-CONSULT', 'SERVICE', 'Consulting', '顧問諮詢', 2, '顧問,諮'顧問,諮詢,顧問公司', 4),
('SERVICE-MARKETING', 'SERVICE', 'Marketing', '行銷廣告', 2, '行銷,廣告,公關', 5);
```

---

## 3. 行業標籤 UI

### 3.1 篩選器

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 客戶名單                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  篩選：                                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 行業別：[全部 ▼]                                    │    │
│  │   ├─ 製造業 (150)                                  │    │
│  │   │   ├─ 電子製造 (80)                             │    │
│  │   │   ├─ 機械製造 (40)                             │    │
│  │   │   └─ 塑膠製造 (30)                             │    │
│  │   ├─ 科技業 (120)                                  │    │
│  │   ├─ 零售業 (80)                                   │    │
│  │   └─ ...                                           │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  [已選：電子製造, 機械製造] [清除]                            │
│                                                             │
│  地區：[全部 ▼]  員工數：[全部 ▼]  狀態：[全部 ▼]           │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  客戶列表：                                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 公司        │ 行業標籤      │ 員工 │ Email    │ 狀態 │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ Tech Corp   │ 🔧 電子製造   │ 250  │ ✅       │ new  │  │
│  │ ABC Mfg     │ ⚙️ 機械製造   │ 120  │ ✅       │ cont │  │
│  │ XYZ Tech    │ 💻 軟體開發   │ 80   │ ⚠️       │ new  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 行業選擇器

```
┌─────────────────────────────────────────────────────────────┐
│  選擇行業                                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  搜尋：[輸入行業關鍵字...]                                   │
│                                                             │
│  一級行業：                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐             │
│  │🏭製造業│ │💻科技業│ │🛒零售業│ │🏥醫療  │             │
│  │  150   │ │  120   │ │   80   │ │   50   │             │
│  └────────┘ └────────┘ └────────┘ └────────┘             │
│                                                             │
│  二級行業（製造業）：                                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │🔌電子製造  │ │⚙️機械製造  │ │🧪化學製造  │            │
│  │    80      │ │    40      │ │    20      │            │
│  └────────────┘ └────────────┘ └────────────┘            │
│                                                             │
│  [取消] [確認選擇]                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. AI 自動標記行業

### 4.1 行業推斷流程

```python
def infer_industry(company_name, description, keywords):
    """
    根據公司資訊自動推斷行業
    """
    # 關鍵字匹配
    text = f"{company_name} {description} {keywords}".lower()
    
    # 規則匹配
    if any(kw in text for kw in ['electronics', 'pcb', '半導體', '電子']):
        return ('MFG-ELEC', '電子製造')
    elif any(kw in text for kw in ['machinery', 'cnc', '機械']):
        return ('MFG-MECH', '機械製造')
    elif any(kw in text for kw in ['software', 'app', '軟體', 'saas']):
        return ('TECH-SOFTWARE', '軟體開發')
    # ... 更多規則
    
    # AI 推斷（如果規則匹配失敗）
    ai_result = call_llm(f"What industry is this company? {text}")
    return map_to_industry_code(ai_result)
```

### 4.2 爬取時自動標記

```
爬取到新公司
    ↓
【Step 1】檢查來源 API 是否有行業資訊
    ├─ Apollo: 有 industry 欄位 → 直接映射
    └─ 無 → 進行推斷

【Step 2】AI 推斷
    ├─ 根據 company_name + description
    └─ 返回 industry_code

【Step 3】存入全域庫
    └─ industry_code, industry_name, industry_tags
```

---

## 5. 行業統計報表

### 5.1 行業分佈

```sql
-- 按行業統計客戶數
SELECT 
    i.industry_code,
    i.industry_name,
    COUNT(l.id) as company_count,
    AVG(l.email_confidence) as avg_email_quality
FROM leads l
JOIN global_leads g ON l.global_id = g.id
GROUP BY g.industry_code, g.industry_name
ORDER BY company_count DESC;
```

### 5.2 行業轉換率

```sql
-- 按行業統計轉換率
SELECT 
    g.industry_name,
    COUNT(l.id) as total,
    SUM(CASE WHEN l.status = 'converted' THEN 1 ELSE 0 END) as converted,
    ROUND(SUM(CASE WHEN l.status = 'converted' THEN 1 ELSE 0 END) * 100.0 / COUNT(l.id), 2) as conversion_rate
FROM leads l
JOIN global_leads g ON l.global_id = g.id
GROUP BY g.industry_name
ORDER BY conversion_rate DESC;
```

---

## 6. 實作清單

### 6.1 DB 更新

- [ ] 新增 `industry_tags` 表
- [ ] 更新 `global_leads` 表（新增行業欄位）
- [ ] 更新 `leads` 表（新增行業欄位）
- [ ] 初始化行業標籤資料

### 6.2 後端

- [ ] 行業標籤 API（`/api/industries`）
- [ ] 行業篩選 API
- [ ] AI 自動標記功能
- [ ] 行業統計報表

### 6.3 前端

- [ ] 行業篩選器 UI
- [ ] 行業選擇器 UI
- [ ] 行業標籤顯示
- [ ] 行業統計圖表

---

**行業別 Tag 系統已完整規劃！**
