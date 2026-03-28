# Linkora 爬蟲情境分析與處理策略

> **日期：** 2026-03-29
> **版本：** 1.0

---

## 1. 核心情境：相同公司重複爬取

### 1.1 情境描述

**問題：** 
- 用戶 A 爬取「electronics manufacturer」→ 公司 X 入庫
- 用戶 B 也爬取「electronics manufacturer」→ 公司 X 再次入庫？
- 或用戶 A 用不同關鍵字「circuit board」→ 公司 X 又入庫？

**風險：**
- 私域池重複（同一用戶重複）
- 全域池重複（不同用戶重複）
- API 費用浪費
- Email 可能更新（舊的失效，新的有效）

---

## 2. 所有情境分析

### 情境 1：全域庫已有，用戶私域池沒有

```
全域庫：公司 X（email: old@test.com, confidence: 60）
用戶 A：私域池無公司 X
用戶 A 爬取關鍵字 → 公司 X 被找到

處理：
  ✅ 直接從全域庫同步到私域池
  ✅ 不花費 API quota
  ✅ 扣除用戶配額

結果：
  用戶 A 私域池：公司 X（email: old@test.com）
```

---

### 情境 2：全域庫已有，用戶私域池也有（同一用戶重複爬取）

```
全域庫：公司 X（email: old@test.com, confidence: 60）
用戶 A：私域池有公司 X（email: old@test.com）
用戶 A 再次爬取 → 公司 X 被找到

處理：
  ⚠️ 檢測到重複
  ❓ 是否要更新？

選項 A：跳過（不更新）
  - 優點：保留用戶自訂資料
  - 缺點：可能錯過更新的 email

選項 B：提示用戶選擇
  - 顯示：全域庫有新資料，是否更新？
  - 用戶可選擇：更新 / 保留舊的

選項 C：自動更新（全域庫較新時）
  - 比較 updated_at 或 email_confidence
  - 全域庫較新 → 自動更新

【建議】選項 B：提示用戶選擇
```

---

### 情境 3：全域庫已有，但 Email 品質較差

```
全域庫：公司 X（email: guessed@x.com, confidence: 30, source: "guessed"）
用戶 A 爬取 → Hunter 返回新 email

處理：
  🔍 比較 email_confidence
  - 全域庫：30（Guessing）
  - 新爬取：95（Hunter 驗證）
  
  ✅ 更新全域庫（新的品質較好）
  ✅ 同步到私域池

結果：
  全域庫：公司 X（email: verified@x.com, confidence: 95, source: "hunter"）
```

---

### 情境 4：全域庫已有，但 Email 已失效

```
全域庫：公司 X（email: old@x.com, confidence: 60, verified_at: 2026-01-01）
用戶 A 爬取 → Hunter 返回 "invalid"

處理：
  🔍 檢測到 email 已失效
  
  ✅ 更新全域庫：
     - email_verified: FALSE
     - email_confidence: 0
     - email_candidates: 保留舊的 candidates
  
  ⚠️ 通知用戶：此公司 email 可能已失效

結果：
  全域庫：公司 X（email: null, verified: FALSE）
```

---

### 情境 5：全域庫沒有，第一次爬取

```
全域庫：無公司 X
用戶 A 爬取 → 找到公司 X

處理：
  ✅ 存入全域庫
  ✅ 同步到用戶 A 私域池
  ✅ 花費 API quota
  ✅ 扣除用戶配額

結果：
  全域庫：公司 X（新增）
  用戶 A：公司 X（同步）
```

---

### 情境 6：不同用戶爬取同一家公司

```
全域庫：公司 X（email: test@x.com）
用戶 A：私域池有公司 X
用戶 B：私域池無公司 X
用戶 B 爬取 → 公司 X 被找到

處理：
  ✅ 從全域庫同步到用戶 B 私域池
  ✅ 不花費 API quota
  ✅ 扣除用戶 B 配額
  ✅ 更新全域庫 sync_count

結果：
  全域庫：公司 X（sync_count: 2）
  用戶 A：公司 X（保留）
  用戶 B：公司 X（同步）
```

---

### 情境 7：同一公司，不同 domain

```
問題：公司 X 可能有兩個網址
  - x-corp.com
  - xcorp.com

全域庫：
  - 記錄 1：公司 X（domain: x-corp.com）
  - 記錄 2：公司 X（domain: xcorp.com）

處理：
  🔍 用 company_name 去重（ILIKE 匹配）
  
  ✅ 合併策略：
     - 保留兩條記錄（domain 不同）
     - 但標記為同一公司（company_group_id）
     - Email 合併到 email_candidates

結果：
  全域庫：
    - 記錄 1：公司 X（domain: x-corp.com, group_id: 1）
    - 記錄 2：公司 X（domain: xcorp.com, group_id: 1）
```

---

### 情境 8：公司改名或被收購

```
全域庫：公司 X（domain: x.com）
現實：公司 X 被公司 Y 收購，domain 改為 y.com

處理：
  🔍 檢測：domain 不同，但 company_name 相似
  
  ⚠️ 需要人工審核或 AI 判斷
  
  ✅ 建議：新增一條記錄，標記為 "acquired"

結果：
  全域庫：
    - 記錄 1：公司 X（domain: x.com, status: "acquired"）
    - 記錄 2：公司 Y（domain: y.com, acquired_from: "X"）
```

---

### 情境 9：用戶刪除私域池的公司，再重新爬取

```
用戶 A：私域池有公司 X
用戶 A 刪除公司 X
用戶 A 再次爬取 → 公司 X 被找到

處理：
  ✅ 從全域庫同步（全域庫還在）
  ✅ 不花費 API quota
  ✅ 扣除用戶配額

結果：
  用戶 A：公司 X（重新同步）
```

---

### 情境 10：全域庫公司資料過期

```
全域庫：公司 X（email: old@x.com, updated_at: 2025-01-01）
現在：2026-03-29（超過 1 年）

處理：
  🔍 檢測資料過期（超過 6 個月）
  
  ✅ 重新驗證：
     - 呼叫 Hunter 重新查詢
     - 更新 email 和驗證狀態
  
  ⚠️ 或標記為 "needs_refresh"
```

---

## 3. 重複公司處理策略

### 3.1 偵測重複的維度

| 維度 | 權重 | 去重方式 |
|------|------|---------|
| **domain** | 50% | 精確匹配 |
| **company_name** | 30% | ILIKE 模糊匹配 |
| **website_url** | 10% | 精確匹配 |
| **phone** | 10% | 精確匹配 |

### 3.2 重複處理流程

```
爬取到新公司資料
    ↓
【Step 1】檢查全域庫
    ├─ domain 精確匹配 → 找到重複
    │
    └─ 無 domain 匹配
         ↓
【Step 2】檢查 company_name
    ├─ ILIKE 匹配（相似度 > 80%）→ 可能重複
    │
    └─ 無匹配 → 新公司

【Step 3】如果找到重複
    ├─ 比較資料新舊
    │   ├─ 新資料較好 → 更新全域庫
    │   └─ 舊資料較好 → 跳過或合併
    │
    └─ 同步到私域池
        ├─ 用戶已有 → 提示是否更新
        └─ 用戶沒有 → 直接同步
```

### 3.3 更新規則

**全域庫更新規則：**

| 欄位 | 更新條件 |
|------|---------|
| `contact_email` | 新的 email_verified=TRUE 或 confidence 更高 |
| `email_candidates` | 合併（去重）|
| `email_confidence` | 取最大值 |
| `email_verified` | 新的為 TRUE 則 TRUE |
| `employee_count` | 保留最新值 |
| `phone` | 合併（非空值）|
| `updated_at` | 每次更新 |

**私域池更新規則：**

| 欄位 | 更新條件 |
|------|---------|
| `contact_email` | 用戶可選擇是否更新 |
| `email_candidates` | 自動合併 |
| `status` | 不更新（保留用戶狀態）|
| `tags` | 不更新（保留用戶標籤）|
| `notes` | 不更新（保留用戶筆記）|

---

## 4. 完整業務流程

### 4.1 爬取流程（含重複處理）

```python
def scrape_leads(keyword, mode, user_id, filters):
    """
    完整爬取流程（含重複檢查和更新）
    """
    results = {
        "total": 0,
        "from_global": 0,
        "from_api": 0,
        "updated": 0,
        "skipped": 0,
        "cost_twd": 0
    }
    
    # Step 1: 查全域庫
    global_results = query_global_pool(keyword, mode, filters)
    results["total"] = len(global_results)
    
    for company in global_results:
        # 檢查用戶私域池是否已有
        existing = check_user_private_pool(user_id, company["domain"])
        
        if existing:
            # 比較資料新舊
            if should_update(existing, company):
                # 提示用戶或自動更新
                update_private_pool(existing, company)
                results["updated"] += 1
            else:
                results["skipped"] += 1
        else:
            # 同步到私域池
            sync_to_private_pool(user_id, company)
            results["from_global"] += 1
    
    # Step 2: 如果全域庫不夠，爬取新的
    if results["total"] < filters.get("min_results", 50):
        # 呼叫外部 API
        new_companies = call_external_api(keyword, mode, filters)
        
        for company in new_companies:
            # 檢查全域庫是否已有（重複檢查）
            existing_global = check_global_pool(company["domain"], company["company_name"])
            
            if existing_global:
                # 更新全域庫（如果新資料較好）
                if should_update_global(existing_global, company):
                    update_global_pool(existing_global, company)
                    results["updated"] += 1
                else:
                    results["skipped"] += 1
            else:
                # 新公司，存入全域庫
                save_to_global_pool(company)
                results["from_api"] += 1
            
            # 同步到私域池
            sync_to_private_pool(user_id, company)
    
    # Step 3: 計算費用
    results["cost_twd"] = calculate_cost(results)
    
    return results


def should_update(existing, new_data):
    """
    判斷是否應該更新現有資料
    """
    # Email 品質更好
    if new_data.get("email_verified") and not existing.email_verified:
        return True
    
    if new_data.get("email_confidence", 0) > existing.email_confidence:
        return True
    
    # 資料較新
    if new_data.get("updated_at") > existing.updated_at:
        return True
    
    return False
```

### 4.2 用戶選擇更新 UI

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ 發現重複公司                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  您的私域池已有此公司：                                       │
│                                                             │
│  【現有資料】                                                │
│  公司：Tech Corp                                            │
│  Email：old@tech.com（未驗證）                               │
│  新增時間：2026-01-15                                        │
│                                                             │
│  【全域庫新資料】                                            │
│  公司：Tech Corp                                            │
│  Email：info@tech.com（已驗證 ✅）                           │
│  更新時間：2026-03-29                                        │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  偵測到全域庫有更新的 Email 資料                              │
│                                                             │
│  [ ] 自動更新 Email（推薦）                                  │
│  [ ] 保留現有資料                                            │
│  [ ] 合併 Email candidates                                   │
│                                                             │
│  [取消] [確認]                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. DB 更新

### 5.1 global_leads 新增欄位

```sql
ALTER TABLE global_leads ADD COLUMN IF NOT EXISTS 
    company_group_id INTEGER,          -- 公司群組ID（同一公司不同domain）
    status VARCHAR(20) DEFAULT 'active', -- active|acquired|closed
    needs_refresh BOOLEAN DEFAULT FALSE, -- 是否需要重新驗證
    last_verified_at TIMESTAMP,        -- 最後驗證時間
    acquired_from VARCHAR(200);         -- 被收購前的公司名
```

### 5.2 leads 新增欄位

```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS
    data_source VARCHAR(20),           -- "global_sync"|"new_scrape"|"updated"
    last_global_sync_at TIMESTAMP;     -- 最後從全域庫同步時間
```

---

## 6. 總結

### 情境數量：10 種

| 情境 | 處理方式 |
|------|---------|
| 1. 全域庫有，私域池無 | 直接同步 |
| 2. 全域庫有，私域池有 | 提示用戶選擇 |
| 3. 全域庫 Email 較差 | 更新全域庫 |
| 4. Email 已失效 | 標記失效，保留 candidates |
| 5. 全域庫無，第一次 | 存入全域庫 + 同步 |
| 6. 不同用戶同公司 | 各自同步，不重複花費 |
| 7. 同公司不同 domain | 建立群組，合併 candidates |
| 8. 公司改名/收購 | 新增記錄，標記關聯 |
| 9. 用戶刪除後重爬 | 從全域庫同步 |
| 10. 資料過期 | 重新驗證或標記 |

### 核心原則

1. **全域庫優先** — 避免重複花費 API
2. **品質優先** — Email 品質更好時更新
3. **用戶控制** — 重要更新前提示用戶選擇
4. **資料保留** — 不刪除舊資料，合併或標記

---

**確認後更新業務流程文件！**
