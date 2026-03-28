# Linkora 探勘引擎：運作原理解析 (v3.2)

> 本文件說明 Linkora 爬蟲的核心運作流程。  
> 版本：v3.2.0 | 更新：2026-03-27

---

## 一、核心流程：四階段發現法

### 階段一：情報庫預檢 (The Reservoir Check)
- **目的**: 節省金錢 (API 點數) 與時間。
- **動作**: 系統先在資料庫的 **`global_leads` (全域情報池)** 尋找是否有匹配的公司。
- **邏輯**: 
  - 優先用 `domain` 查詢（精確匹配）
  - 次要用 `company_name` 模糊比對（大小寫不敏感）
- **結果**: 
  - 若有，直接將資料「同步」到您的帳號下（即時完成，計入配額）
  - 若無，才進入下一階段

### 階段二：精準雲端探勘 (Deep Scrape)
- **目的**: 獲取最新實時資料。
- **動作**: 啟動 Apify 雲端爬蟲。
  - **製造商模式**: 呼叫 `zen-studio/thomasnet-suppliers-scraper` + `junipr/yellow-pages-scraper` (備援)
  - **黃頁模式**: 呼叫 `junipr/yellow-pages-scraper` + `automation-lab/yellowpages-scraper` (備援)
- **保護機制**: 每個任務限時 **180 秒**，超過則自動終止

### 階段三：Email 深度補強 (Email Enrichment)
- **目的**: 解決「抓到公司但沒 Email」的痛點。

#### Email 取得優先順序（v3.2）

```
1. Apify Actor 直接回傳
   └── items[].email / items[].emails / items[].contactEmail
   
2. extract_best_email() 解析
   └── 優先: contactEmail > emails[0] > email
   
3. find_emails_free() 網頁解析（僅 Manufacturer 模式）
   └── 掃描官網隱含的聯絡資訊
   
4. Domain Prefix Guessing（最終備援）
   └── 依序嘗試: info@ → sales@ → contact@ → hello@ → admin@ → office@
```

#### Email 寫入規則（v3.2 修復）
| 來源 | 寫入 contact_email | 寫入 email_candidates |
|------|--------------------|-----------------------|
| Apify 直接回傳 | ✅ 是 | ✅ 是 |
| find_emails_free() | ✅ 是 | ✅ 是 |
| Domain Prefix Guessing | ❌ 否 | ✅ 是 |

> ⚠️ **重要**：Guess 來的 email 不會寫入 `contact_email`（已驗證欄位），只寫入 `email_candidates`。這是為了避免污染全域池的高信心資料。

### 階段四：入庫與同步 (Persistence)
- **動作**: 
  - 資料存入您的 **私有名單 (`leads`)** + 計入配額
  - 同時備份一份到 **全域情報池 (`global_leads`)**
  - 全域池的 `contact_email` 只寫入已驗證的 email

---

## 二、用量配額制度（v3.2）

| 角色 | 配額 | 說明 |
|------|------|------|
| Admin | 無限 | 系統管理者 |
| Vendor | 無限 | 簽約合作夥伴 |
| Member - 免費 | 10 leads / 月 | 超額拒絕爬蟲 |
| Member - 專業 | 100 leads / 月 | - |
| Member - 企業 | 500 leads / 月 | - |

**重要**：全域池同步也計入配額（業務決策：同步也算使用量）。

---

## 三、全域池 / 私域池架構（v3.0）

### 資料流向
```
全域情報池 (global_leads)
     │
     │ sync_from_global_pool()
     │ ✅ 同步時也計入配額
     │
     ▼
私有名單 (leads) ← user_id 隔離
     │
     │ save_to_global_pool()
     │ ✅ 只有新增（live scrape）才寫入全域池
     │ ✅ 更新時補足 industry_taxonomy
     │
     ▼
全域情報池 (global_leads) ← 共享給所有用戶
```

### 顯示優先權（Personal > Global）
- `display_name = override_name or company_name`
- `display_email = override_email or contact_email`

---

## 四、如何調優與修改？

如果您是開發者，想修改邏輯：

| 目標 | 修改檔案 | 函式 |
|------|---------|------|
| 想換爬蟲 Actor | `manufacturer_miner.py` | `actor_id` 變數 |
| 想改去重條件 | `scrape_utils.py` | `sync_from_global_pool()` |
| 想改 email 取得策略 | `scrape_simple.py` / `manufacturer_miner.py` | `extract_best_email()` |
| 想改全域池同步邏輯 | `scrape_utils.py` | `save_to_global_pool()` |
| 想改用量配額邏輯 | `auth.py` | `check_user_quota()` |

---

## 五、API Key 取得位置（優先順序）

1. 會員個人設定（User.system_settings）
2. 管理員設定（User ID 1 的 system_settings）
3. 環境變數（fallback）

---

*本文件由 Ann 維護，v3.2.0 更新*
