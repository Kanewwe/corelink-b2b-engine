# 爬蟲方案定案 — 歐美中小企業市場

> **目標市場：** 歐美中小企業（SME, 員工 < 500）
> **目標數量：** 1000-3000 筆/月
> **必要欄位：** 公司名稱 + Domain + Email（已驗證）
> **決策日期：** 2026-03-29

---

## 1. 技術方案確認

### ✅ Hunter.io 已驗證可用

**測試結果：**

| Domain | Emails | 有效率 | 備註 |
|--------|--------|--------|------|
| hubspot.com | 5 | 5/5 ✅ | 中大型公司 |
| figma.com | 3 | 3/3 ✅ | 中小企業 |
| airtable.com | 3 | 3/3 ✅ | 中小企業 |
| postman.com | 3 | 3/3 ✅ | 中小企業 |

**資料內容：**
```json
{
  "value": "mspillers@hubspot.com",      // Email
  "first_name": "Meghan",
  "last_name": "Spillers",
  "position": "Compensation Manager",     // 職位
  "department": "management",             // 部門
  "seniority": "senior",                  // 資歷
  "confidence": 99,                        // 可信度
  "verification": {"status": "valid"},    // 驗證狀態
  "linkedin": "https://linkedin.com/..."   // LinkedIn
}
```

**結論：Hunter.io 完全符合需求！**

---

## 2. Vendor 模式定位

### 2.1 Vendor 是什麼？

**定義：** 簽約合作夥伴（Outsourcing Partners），由 Admin 管理

**特性：**
- 無限探勘、無限郵件發送
- 由 Admin 設定批發價（pricing_config）
- 適合：代客開發公司、行銷代理商

### 2.2 Vendor 適合中小企業嗎？

**問題分析：**

| 方案 | 適用對象 | 優點 | 缺點 |
|------|---------|------|------|
| **Vendor 模式** | 代客開發公司 | 無限配額、穩定供應商關係 | 需付費給 Hunter.io |
| **Member 模式** | 一般中小企業 | 自助服務、成本可控 | 配額限制 |

**結論：**
- **Vendor 模式** → 適合「代理商/代客開發」角色
- **Member 模式** → 適合「終端中小企業」自助使用

### 2.3 推薦架構

```
┌─────────────────────────────────────────────────────┐
│                    Linkora 平台                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │  Admin   │───▶│  Vendor  │───▶│  Member  │     │
│  │(平台管理)│    │(代理商)   │    │(終端客戶)│     │
│  └──────────┘    └──────────┘    └──────────┘     │
│       │               │               │            │
│       ▼               ▼               ▼            │
│  管理系統         無限爬取        配額使用          │
│  設定API Key      批發價格        付費方案          │
│                                                     │
└─────────────────────────────────────────────────────┘

資料流：
Hunter.io API → Vendor 爬取 → Member 購買 Leads
```

---

## 3. 實作方案

### 3.1 Phase 1：Hunter.io 整合（1 週）

**目標：** 讓 Vendor 可以用 Hunter.io 爬取公司名單

**流程：**
```
1. Vendor 輸入關鍵字（例："electronics manufacturer"）
2. 系統呼叫 Hunter.io Domain Search
3. 取得：公司 domain + 員工 email + 驗證狀態
4. 存入 Leads 表
5. Vendor 可轉售給 Member
```

**技術要點：**
- Hunter.io API Key 由 Admin 設定（System Settings）
- 每次查詢扣 Hunter quota
- Email 驗證狀態存入 `mx_valid` 欄位

### 3.2 Phase 2：公司發現流程（2 週）

**問題：** Hunter.io 只能查「已知 domain」，無法搜尋公司

**解決方案：**

**方案 A：Apollo.io 付費（推薦）**
- $49/月，Organization Search
- 輸入關鍵字 → 取得公司列表（含 domain）
- 再用 Hunter.io 取得 email

**方案 B：Google Maps API**
- 免費額度較大
- 搜尋「electronics manufacturer near USA」
- 取得公司名稱 + 網站
- 再用 Hunter.io 取得 email

**方案 C：手動清單**
- 購買產業名錄
- 人工整理 domain 列表
- 用 Hunter.io 批次查詢

### 3.3 完整流程（推薦）

```
┌─────────────────────────────────────────────────────┐
│              Lead Generation Pipeline               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Step 1: 公司發現                                   │
│  ├─ Apollo.io Organization Search ($49/月)         │
│  │   keyword: "electronics manufacturer"            │
│  │   location: "United States"                      │
│  │   employee_count: 10-500                         │
│  │   → 100+ companies                               │
│  │                                                  │
│  └─ Google Maps API (免費)                         │
│      query: "plastic injection molding factory USA" │
│      → 50+ companies                               │
│                                                     │
│  Step 2: Email 獲取                                 │
│  ├─ Hunter.io Domain Search ($49/月)               │
│  │   domain: "company.com"                          │
│  │   → emails with verification status              │
│  │                                                  │
│  └─ Email Guessing (免費)                          │
│      info@domain.com, sales@domain.com              │
│      → 需要 SMTP 驗證                               │
│                                                     │
│  Step 3: Email 驗證                                 │
│  ├─ Hunter.io 內建驗證 ✅                           │
│  └─ 自建 SMTP 驗證（備援）                          │
│                                                     │
│  Step 4: 入庫                                       │
│  ├─ 存入 leads 表                                   │
│  ├─ 標記 email 驗證狀態                             │
│  └─ Vendor 可轉售給 Member                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 4. 成本估算

### 4.1 API 成本

| 服務 | 月費 | 額度 | 單位成本 |
|------|------|------|---------|
| **Hunter.io** | $49 | 1,000 domains | $0.049/domain |
| **Apollo.io** | $49 | 10,000 credits | $0.0049/credit |
| **總計** | $98 | 1,000 domains + 10,000 credits | — |

### 4.2 每月產出估算

**保守估計：**
- Apollo 搜尋：100家公司 × 50% email率 = **50 筆有效 Email**
- Hunter 查詢：1,000 domains × 60% email率 = **600 筆有效 Email**
- **總計：650 筆有效 Email/月**

**樂觀估計：**
- Apollo 搜尋：500家公司 × 60% = **300 筆**
- Hunter 查詢：1,000 domains × 80% = **800 筆**
- **總計：1,100 筆有效 Email/月**

### 4.3 成本效益

| 指標 | 保守 | 樂觀 |
|------|------|------|
| 月成本 | $98 | $98 |
| 有效 Email | 650 | 1,100 |
| 每筆成本 | **$0.15** | **$0.09** |

---

## 5. 實作步驟

### Week 1：Hunter.io 整合
- [ ] 更新 `scraper_router.py` 新增 Hunter.io 搜尋 endpoint
- [ ] 新增 `hunter_scraper.py` 模組
- [ ] 測試單一 domain 查詢
- [ ] 測試批次 domain 查詢
- [ ] 存入 leads 表（含 email 驗證狀態）

### Week 2：公司發現流程
- [ ] 評估 Apollo.io vs Google Maps API
- [ ] 實作公司搜尋 endpoint
- [ ] 整合 Hunter.io（Step 1 → Step 2）

### Week 3：Vendor 模式完善
- [ ] Vendor 可設定自己的 API Key
- [ ] 批發價格設定 UI
- [ ] Vendor dashboard

---

## 6. 下一步決策

### 需確認：

1. **公司發現來源？**
   - [ ] 購買 Apollo.io（$49/月）
   - [ ] 使用 Google Maps API（免費）
   - [ ] 手動整理公司列表

2. **Hunter.io 付費方案？**
   - Free: 25 searches/月（已用於測試）
   - Starter: $49/月，1,000 searches
   - Growth: $149/月，5,000 searches
   - **推薦：Starter（$49/月）**

3. **開發優先順序？**
   - [ ] 先 Hunter.io 整合（最快見效）
   - [ ] 先公司發現流程（完整方案）

---

**確認後立即開始實作！**
