# Linkora 業務流程文件 — v4.0

> **最後更新：** 2026-03-29
> **版本：** v4.0（爬蟲四模式 + 全域庫優化）

---

## 1. 角色與權限

### 1.1 角色定義

| 角色 | 定位 | 配額 | 限制 |
|------|------|------|------|
| **Admin** | 平台管理員 | 無限 | 管理系統、API Key |
| **Vendor** | 簽約合作夥伴 | 無限爬取 | 寄信次數上限 |
| **Member（付費）** | 付費會員 | 依方案 | 依方案 |
| **Member（免費）** | 免費會員 | 10 leads/月 | 僅一般模式 |

### 1.2 Vendor 收費模式

| 項目 | 價格（台幣）|
|------|-----------|
| 寄送 | $20/封 |
| 觸及（開信）| $200/次 |
| 回覆 | $1,000/次 |
| 訂單 | 5% 抽成 |

---

## 2. 爬蟲四模式

### 2.1 模式定義

| 模式 | 目標客群 | 資料來源 | Email 來源 | 適用角色 |
|------|---------|---------|-----------|---------|
| **一般模式** | 本地服務業 | Google Maps | Guessing | 免費會員 |
| **製造商模式** | B2B 工廠 | Apollo.io | Hunter.io | 付費/Vendor |
| **業務模式** | 決策者 | LinkedIn | Hunter.io | 企業版/Vendor |
| **行銷模式** | 大量名單 | Google Search | Hunter.io | 專業版/Vendor |

### 2.2 各模式流程

#### 一般模式（Google Maps）

```
用戶輸入關鍵字 + 地點
    ↓
【Step 1】查全域庫
    ├─ 有資料 → 同步到私域池（免費）
    └─ 無資料 → 呼叫 Google Maps API
        ↓
    取得公司名稱、電話、地址、網站
        ↓
    Email Guessing（info@, sales@, contact@）
        ↓
    存入全域庫 + 同步私域池
```

#### 製造商模式（Apollo + Hunter）

```
用戶輸入關鍵字 + 地點 + 員工數範圍
    ↓
【Step 1】查全域庫
    ├─ 有資料 → 同步到私域池（免費）
    └─ 無資料 → 呼叫 Apollo.io
        ↓
    取得公司列表（domain、員工數、產業）
        ↓
    過濾重複（全域庫已有）
        ↓
    呼叫 Hunter.io 取得 Email（含驗證）
        ↓
    更新/存入全域庫 + 同步私域池
```

#### 業務模式（LinkedIn + Hunter）

```
用戶輸入關鍵字 + 職位篩選
    ↓
【Step 1】查全域庫
    ├─ 有資料 → 同步到私域池（免費）
    └─ 無資料 → LinkedIn 搜尋
        ↓
    取得人員姓名、職位、公司
        ↓
    呼叫 Hunter.io Email Finder
        ↓
    存入全域庫（含 contact_person）+ 同步私域池
```

#### 行銷模式（Google + Hunter）

```
用戶輸入關鍵字
    ↓
【Step 1】查全域庫
    ├─ 有資料 → 同步到私域池（免費）
    └─ 無資料 → Google Search 爬蟲
        ↓
    取得公司網站列表
        ↓
    呼叫 Hunter.io Domain Search（批次）
        ↓
    存入全域庫 + 同步私域池
```

---

## 3. 全域庫/私域池架構

### 3.1 資料流向

```
外部 API（Apollo/Hunter/Google）
    ↓
全域庫（Global Pool）
    ├─ 去重：domain UNIQUE
    ├─ 更新：品質更好時更新
    └─ 統計：sync_count, last_synced_at
    ↓
同步到私域池（Private Pool）
    ├─ 檢查：user_id + domain 去重
    ├─ 更新：提示用戶選擇
    └─ 扣除：用戶配額
```

### 3.2 優先級

```
1. 全域庫優先 → 避免重複花費 API
2. 品質優先 → Email 品質更好時更新
3. 用戶控制 → 重要更新前提示選擇
```

---

## 4. 重複處理策略

### 4.1 重複偵測維度

| 維度 | 權重 | 方式 |
|------|------|------|
| domain | 50% | 精確匹配 |
| company_name | 30% | ILIKE 模糊匹配 |
| website_url | 10% | 精確匹配 |
| phone | 10% | 精確匹配 |

### 4.2 更新規則

**全域庫更新：**
- Email 品質更好 → 更新
- 資料較新 → 更新
- Email candidates → 合併

**私域池更新：**
- 提示用戶選擇
- 保留用戶自訂資料（status, tags, notes）

---

## 5. 10 種情境處理

| 情境 | 處理 |
|------|------|
| 1. 全域庫有，私域池無 | 直接同步 |
| 2. 全域庫有，私域池有 | 提示用戶選擇更新 |
| 3. 全域庫 Email 較差 | 用新資料更新全域庫 |
| 4. Email 已失效 | 標記失效，保留 candidates |
| 5. 全域庫無 | 存入 + 同步 |
| 6. 不同用戶同公司 | 各自同步，不重複花費 |
| 7. 同公司不同 domain | 建立群組，合併 candidates |
| 8. 公司改名/收購 | 新增記錄，標記關聯 |
| 9. 用戶刪除後重爬 | 從全域庫同步 |
| 10. 資料過期 | 重新驗證或標記 needs_refresh |

---

## 6. 配額管理

### 6.1 扣除時機

- **同步到私域池時**扣除用戶配額
- 從全域庫同步也扣除（但 API quota 免費）

### 6.2 配額追蹤

```python
def decrement_user_quota(user_id, quota_type, amount):
    """
    扣除用戶配額
    quota_type: "leads" | "emails"
    """
    usage = db.query(UsageLog).filter(
        UsageLog.user_id == user_id,
        UsageLog.quota_type == quota_type,
        UsageLog.month == current_month
    ).first()
    
    usage.used += amount
    
    # 檢查是否超額
    plan = get_user_plan(user_id)
    if usage.used > plan.quota:
        raise QuotaExceededError()
```

---

## 7. 費用計算

### 7.1 API 費用

| API | 月費 | 額度 | 單位成本 |
|-----|------|------|---------|
| Google Maps | $0（$200 免費額度）| 40,000 | $0 |
| Apollo.io | $49/月 | 10,000 credits | $0.005/credit |
| Hunter.io | $49/月 | 1,000 domains | $0.049/domain |

### 7.2 費用節省範例

**情境：** 100 家公司，60 家在全域庫

```
不使用全域庫：
  - Hunter: 100 次 = $4.90 USD = $157 TWD

使用全域庫：
  - 全域庫同步：60 家 = $0
  - Hunter: 40 次 = $1.96 USD = $63 TWD

節省：$94 TWD (60%)
```

---

## 8. 用戶操作流程

### 8.1 爬取流程

```
1. 選擇模式（一般/製造商/業務/行銷）
2. 輸入關鍵字和篩選條件
3. 系統查全域庫，顯示可免費同步數量
4. 用戶選擇：
   - 直接同步全域庫資料
   - 繼續爬取新資料
   - 兩者都做
5. 顯示結果和費用
6. 確認同步到私域池
```

### 8.2 處理重複

```
1. 偵測到重複公司
2. 比較新舊資料
3. 顯示差異
4. 用戶選擇：
   - 更新 Email
   - 保留現有
   - 合併 candidates
```

---

## 9. 系統設定

### 9.1 API Key 管理

- **Admin 統一設定** Hunter.io / Apollo.io Key
- 所有用戶共用平台 API 配額
- Admin 可監控用量

### 9.2 參數配置

```json
{
  "scraper": {
    "global_pool_priority": true,
    "auto_update_better_email": true,
    "prompt_user_on_duplicate": true,
    "max_api_calls_per_day": 1000,
    "data_expiry_months": 6
  }
}
```

---

## 10. 監控與報表

### 10.1 監控指標

- 全域庫大小
- 每日同步次數
- API 費用
- 重複率
- Email 驗證率

### 10.2 報表

- 每日爬取統計
- 費用報表
- 用戶配額使用

---

**文件版本：** v4.0
**下次審查：** 2026-04-01
