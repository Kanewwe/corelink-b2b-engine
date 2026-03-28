# Linkora 爬蟲方案執行計畫 — v4.1

> **日期：** 2026-03-29
> **幣別：** 台幣（TWD）
> **目標：** 1000-3000 筆有效 Email/月

---

## 1. 商業模式確認

### 1.1 Vendor 抽成（台幣）

| 項目 | 價格 | 說明 |
|------|------|------|
| **寄送** | $20/封 | 每封郵件寄出 |
| **觸及（開信）** | $200/次 | 收件者打開郵件 |
| **回覆** | $1,000/次 | 收件者回覆 |
| **訂單** | 5% 抽成 | 成交金額 5% |

**範例計算：**
```
Vendor A 本月表現：
  - 寄出：5,000 封 → $100,000
  - 開信：2,000 次 → $400,000
  - 回覆：50 次 → $50,000
  - 訂單：10 筆，總額 $5,000,000 → $250,000

本月收入：$800,000
```

### 1.2 會員方案（台幣）

| 方案 | 月費 | 爬取配額 | 寄信配額 | 可用模式 |
|------|------|---------|---------|---------|
| **免費版** | $0 | 10 leads | 10 封 | 一般模式 |
| **入門版** | $899 | 100 leads | 100 封 | 一般+製造商 |
| **專業版** | $2,999 | 500 leads | 500 封 | 全部模式 |
| **企業版** | $9,999 | 2,000 leads | 2,000 封 | 全部+API |

---

## 2. 全域庫/私域庫架構整合

### 2.1 現有架構

```
┌─────────────────────────────────────────────────────┐
│                  Global Pool（全域池）               │
│                                                     │
│  - 所有會員共享的公司資料                            │
│  - company_name, domain, contact_email              │
│  - email_candidates, phone, address                 │
│  - ai_tag, industry                                 │
│  - source: "apify_yellowpages", "hunter", etc.      │
│                                                     │
│  去重邏輯：domain UNIQUE                            │
│                                                     │
└─────────────────────────────────────────────────────┘
                        ↓ sync_from_global_pool()
┌─────────────────────────────────────────────────────┐
│               Private Pool（私域池）                 │
│                                                     │
│  - 每個用戶自己的 Leads                              │
│  - user_id, company_name, domain                    │
│  - contact_email, email_candidates                  │
│  - status, assigned_bd                              │
│  - email_sent, email_sent_at                        │
│                                                     │
│  去重邏輯：user_id + domain UNIQUE                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2.2 新版架構（整合爬蟲四模式）

```
┌─────────────────────────────────────────────────────┐
│                  爬蟲來源層                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  一般模式        製造商模式       業務模式      行銷模式 │
│  Google Maps    Apollo+Hunter   LinkedIn     Google  │
│      ↓              ↓             ↓            ↓    │
│                                                     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│              Global Pool（全域池）v4.1               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  新增欄位：                                          │
│  - source_mode: "general"|"manufacturer"|"sales"   │
│  - email_verified: BOOLEAN（Hunter驗證結果）        │
│  - email_confidence: INTEGER（0-100）              │
│  - employee_count: INTEGER                          │
│  - company_type: "SME"|"Enterprise"               │
│                                                     │
│  去重邏輯：                                          │
│  - domain UNIQUE（主要）                            │
│  - company_name ILIKE（輔助，避免拼寫差異）          │
│                                                     │
│  資料來源標記：                                      │
│  - source: "google_maps"|"apollo"|"hunter"         │
│  - source_mode: 對應四種模式                         │
│                                                     │
└─────────────────────────────────────────────────────┘
                        ↓
                sync_from_global_pool()
                        ↓
┌─────────────────────────────────────────────────────┐
│            Private Pool（私域池）v4.1                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  新增欄位：                                          │
│  - global_id: FK → global_leads.id                 │
│  - email_verified: BOOLEAN                         │
│  - email_confidence: INTEGER                       │
│  - lead_score: INTEGER（Vendor 可自訂評分）          │
│  - contact_person: VARCHAR（業務模式用）             │
│  - contact_position: VARCHAR（職位）                │
│                                                     │
│  用戶專屬資料：                                      │
│  - status: 用戶自訂狀態                             │
│  - tags: 用戶自訂標籤                               │
│  - notes: 用戶筆記                                  │
│  - email_sent: 是否已寄信                           │
│  - last_contact_at: 最後聯繫時間                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2.3 資料流向

```
爬蟲執行（四模式之一）
  ↓
  ├─→ Global Pool 去重檢查
  │     ├─ 已存在 → 更新 email_candidates（如果有新的）
  │     └─ 不存在 → 新增記錄
  │
  └─→ Private Pool 同步
        ├─ 檢查用戶是否已有此公司
        ├─ 無 → 從 Global Pool 同步
        │      └─ 扣除用戶配額
        └─ 有 → 跳過

配額扣除時機：
  - 新增到 Private Pool 時扣除
  - sync_from_global_pool 成功時扣除
```

---

## 3. 四模式難度評估

### 3.1 評估維度

| 維度 | 權重 | 說明 |
|------|------|------|
| **技術難度** | 30% | API 整合、爬蟲開發 |
| **資料品質** | 30% | Email 獲取率、驗證率 |
| **維護成本** | 20% | API 穩定性、變更頻率 |
| **成本效益** | 20% | 每筆成本、ROI |

### 3.2 評估結果

---

#### 模式一：一般模式（Google Maps）

**技術難度：** ⭐⭐ (20%)

| 項目 | 評估 |
|------|------|
| API 整合 | 簡單，Google Maps API 文件完整 |
| 認證 | 需要 Google Cloud API Key |
| Rate Limit | 免費額度 $200/月，約 40,000 requests |
| 台灣支援 | ✅ 完整支援 |

**資料品質：** ⭐⭐ (20%)

| 項目 | 評估 |
|------|------|
| 公司數量 | 高（本地商家多）|
| Email 獲取率 | 低（10-30%，需 Guessing）|
| Email 驗證 | 無（需自建 SMTP 驗證）|
| 公司相關性 | 中（包含非目標客戶）|

**維護成本：** ⭐ (10%)

| 項目 | 評估 |
|------|------|
| API 穩定性 | ✅ Google 維護，穩定 |
| 變更頻率 | 低 |
| 依賴性 | 低（免費額度足夠）|

**成本效益：** ⭐⭐⭐⭐⭐ (40%)

| 項目 | 評估 |
|------|------|
| 每筆成本 | $0（免費額度）|
| 適合場景 | 免費會員體驗 |

**綜合評分：** 90/100 ⭐⭐⭐⭐
**實作順序：** 第 1 優先

---

#### 模式二：製造商模式（Apollo + Hunter）

**技術難度：** ⭐⭐⭐ (30%)

| 項目 | 評估 |
|------|------|
| API 整合 | 中等，需串接兩個 API |
| Apollo Organization Search | 需要 Basic 方案（$49/月）|
| Hunter Domain Search | 需要 Starter 方案（$49/月）|
| 流程串接 | 公司搜尋 → Email 查詢 → 驗證 |

**資料品質：** ⭐⭐⭐⭐⭐ (50%)

| 項目 | 評估 |
|------|------|
| 公司數量 | 高（Apollo 資料庫大）|
| Email 獲取率 | 高（60-80%）|
| Email 驗證 | ✅ Hunter 內建驗證 |
| 公司相關性 | ✅ 可過濾員工數、產業 |

**維護成本：** ⭐⭐⭐ (20%)

| 項目 | 評估 |
|------|------|
| API 穩定性 | ✅ 付費 API，穩定 |
| 變更頻率 | 中（需監控額度）|
| 依賴性 | 高（需付費維持）|

**成本效益：** ⭐⭐⭐⭐ (30%)

| 項目 | 評估 |
|------|------|
| 每筆成本 | $3-5 TWD（$98 API / 500 leads）|
| 適合場景 | 付費會員、Vendor |

**綜合評分：** 130/150 ⭐⭐⭐⭐⭐
**實作順序：** 第 2 優先

---

#### 模式三：業務模式（LinkedIn + Hunter）

**技術難度：** ⭐⭐⭐⭐ (40%)

| 項目 | 評估 |
|------|------|
| LinkedIn 整合 | 困難，LinkedIn 有爬蟲限制 |
| Sales Navigator | 需付費（$99/月）或手動 |
| Hunter Email Finder | 可用，但需 name + domain |
| 流程串接 | LinkedIn → 查詢 → Email |

**資料品質：** ⭐⭐⭐⭐ (40%)

| 項目 | 評估 |
|------|------|
| 人員數量 | 中（需手動或付費）|
| Email 獲取率 | 高（Hunter 精準）|
| 職位精準度 | ✅ LinkedIn 職位準確 |
| 公司相關性 | ✅ 可精準鎖定決策者 |

**維護成本：** ⭐⭐⭐⭐ (30%)

| 項目 | 評估 |
|------|------|
| API 穩定性 | ⚠️ LinkedIn 常變更 |
| 變更頻率 | 高 |
| 依賴性 | 高（Sales Navigator）|

**成本效益：** ⭐⭐⭐ (20%)

| 項目 | 評估 |
|------|------|
| 每筆成本 | $5-10 TWD |
| 適合場景 | 企業版會員 |

**綜合評分：** 130/150 ⭐⭐⭐⭐
**實作順序：** 第 3 優先

---

#### 模式四：行銷模式（Google Search + Hunter）

**技術難度：** ⭐⭐⭐⭐ (35%)

| 項目 | 評估 |
|------|------|
| Google Search 爬蟲 | 困難，容易被擋 |
| Playwright 繞過 | 需要瀏覽器渲染 |
| 關鍵字搜尋 | 需優化關鍵字策略 |
| Hunter 批次查詢 | 可用 |

**資料品質：** ⭐⭐⭐ (30%)

| 項目 | 評估 |
|------|------|
| 公司數量 | 中（受爬蟲限制）|
| Email 獲取率 | 中（40-60%）|
| Email 驗證 | ✅ Hunter 內建 |
| 公司相關性 | ⚠️ 需過濾 |

**維護成本：** ⭐⭐⭐⭐⭐ (40%)

| 項目 | 評估 |
|------|------|
| API 穩定性 | ⚠️ 爬蟲不穩定 |
| 變更頻率 | 高（Google 常更新）|
| 依賴性 | 低（免費）|

**成本效益：** ⭐⭐⭐⭐ (30%)

| 項目 | 評估 |
|------|------|
| 每筆成本 | $1-2 TWD |
| 適合場景 | 大量名單 |

**綜合評分：** 135/150 ⭐⭐⭐⭐
**實作順序：** 第 4 優先

---

## 4. 實作順序與時程

### 4.1 實作順序（依難度排序）

| 順序 | 模式 | 難度評分 | 時程 | 成本 |
|------|------|---------|------|------|
| **1** | 一般模式 | ⭐⭐⭐⭐ (90) | 1 週 | $0 |
| **2** | 製造商模式 | ⭐⭐⭐⭐⭐ (130) | 2 週 | $98/月 |
| **3** | 業務模式 | ⭐⭐⭐⭐ (130) | 2 週 | $148/月 |
| **4** | 行銷模式 | ⭐⭐⭐⭐ (135) | 2 週 | $49/月 |

### 4.2 詳細時程

#### Week 1：一般模式（Google Maps）

**目標：** 免費會員可使用

**交付項目：**
- [ ] `google_maps_scraper.py`
- [ ] `/api/scrape/google-maps` endpoint
- [ ] Email Guessing 邏輯
- [ ] Global Pool 存入（source_mode="general"）
- [ ] Private Pool 同步
- [ ] 前端模式切換 UI

**成本：** $0

---

#### Week 2-3：製造商模式（Apollo + Hunter）

**目標：** 付費會員/Vendor 可使用

**交付項目：**
- [ ] `apollo_scraper.py`（公司搜尋）
- [ ] `hunter_scraper.py`（Email 查詢）
- [ ] `/api/scrape/manufacturer` endpoint
- [ ] 製造商過濾邏輯（員工數 < 500）
- [ ] Global Pool 存入（source_mode="manufacturer"）
- [ ] Email 驗證狀態存入（email_verified, email_confidence）
- [ ] 配額扣除邏輯

**成本：** $98/月（Apollo + Hunter）

---

#### Week 4-5：業務模式（LinkedIn + Hunter）

**目標：** 企業版會員/Vendor 可使用

**交付項目：**
- [ ] LinkedIn 整合（手動或 Sales Navigator）
- [ ] `/api/scrape/sales` endpoint
- [ ] 人員職位篩選（CEO, Purchasing Manager, etc.）
- [ ] contact_person, contact_position 欄位
- [ ] Global Pool 存入（source_mode="sales"）

**成本：** $148/月（Sales Navigator + Hunter）

---

#### Week 6-7：行銷模式（Google + Hunter）

**目標：** 專業版以上會員/Vendor 可使用

**交付項目：**
- [ ] `google_search_scraper.py`（Playwright）
- [ ] `/api/scrape/marketing` endpoint
- [ ] 關鍵字優化策略
- [ ] 批次 Hunter 查詢
- [ ] Global Pool 存入（source_mode="marketing"）

**成本：** $49/月（Hunter）

---

## 5. 資料庫更新

### 5.1 Global Pool 新增欄位

```sql
-- global_leads 表
ALTER TABLE global_leads ADD COLUMN IF NOT EXISTS source_mode VARCHAR(20);
ALTER TABLE global_leads ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE global_leads ADD COLUMN IF NOT EXISTS email_confidence INTEGER DEFAULT 0;
ALTER TABLE global_leads ADD COLUMN IF NOT EXISTS employee_count INTEGER;
ALTER TABLE global_leads ADD COLUMN IF NOT EXISTS company_type VARCHAR(20);
```

### 5.2 Private Pool 新增欄位

```sql
-- leads 表
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_confidence INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_person VARCHAR(100);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_position VARCHAR(100);
```

---

## 6. 下一步

### 待確認：

1. **API Key 管理**
   - [ ] Admin 統一設定 Hunter Key
   - [ ] Admin 統一設定 Apollo Key
   - [ ] 或讓 Vendor 使用自己的 Key？

2. **配額扣除時機**
   - [ ] 爬取時扣除？
   - [ ] 同步到私域池時扣除？

3. **開始實作？**
   - [ ] 從 Week 1 一般模式開始

---

**確認後立即開始實作！**
