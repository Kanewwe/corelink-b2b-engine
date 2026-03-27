# Linkora 爬蟲測試計畫（v3.2）

> 建立日期：2026-03-27  
> 目標：嚴格驗證爬蟲功能與 Email 撈取正確性  
> 版本：Linkora UAT 環境

---

## 一、爬蟲架構總覽（最新版）

```
前端 LeadEngine.tsx
│
├── miner_mode: "manufacturer" → manufacturer_miner.py
│   ├── zen-studio/thomasnet-suppliers-scraper (主要)
│   └── jeeves_is_my_copilot/thomasnet-supplier-directory-scraper (備援)
│
├── miner_mode: "yellowpages" → scrape_simple.py
│   ├── junipr/yellow-pages-scraper (主要)
│   └── automation-lab/yellowpages-scraper (備援)
│
Email 補強層（每個 Item）：
├── extract_best_email() → 從 item 提取 email
├── find_emails_free() → 網頁解析 email
└── Domain Prefix Guessing → info@/sales@/contact@ (最終備援)
```

---

## 二、測試矩陣（Email 撈取為核心）

### T1 — Apify Actor 端點健康檢查

| ID | 測試目標 | 方法 | 成功標準 |
|----|---------|------|---------|
| T1.1 | Thomasnet Actor 可用 | 直接呼叫 Actor | 回傳 datasetItems ≥ 1 |
| T1.2 | Yellowpages Actor 可用 | 直接呼叫 Actor | 回傳 datasetItems ≥ 1 |
| T1.3 | Actor 有帶 email 回傳 | 檢查 items[].email / emails[] | 任一 item 含有效 email |
| T1.4 | Actor 網址解析正確 | 檢查 items[].website / items[].url | 可解析出 domain |
| T1.5 | 備援 Actor 正常 | 模擬主要 Actor 失敗 | 自動切換備援 |

### T2 — Email 撈取流程驗證

| ID | 測試目標 | 輸入 | 成功標準 |
|----|---------|------|---------|
| T2.1 | 從 item 直接取得 email | Apify 回傳含 email 的 item | contact_email 有值 |
| T2.2 | extract_best_email() 解析 | item.emails = ["a@test.com", "b@test.com"] | 回傳第一個 |
| T2.3 | 空 email 時進入備援 | item.email = null | 嘗試 find_emails_free() |
| T2.4 | 備援失敗時 Guessing | domain = "example.com" 無法解析 | 產生 info@example.com |
| T2.5 | Guessing 寫入正確欄位 | 無法驗證的 email | 寫入 email_candidates，不寫入 contact_email |
| T2.6 | 已驗證 email 寫入全域池 | email 直接來自 Apify | contact_email 寫入 global_leads |

### T3 — 不同市場與關鍵字

| ID | 市場 | 關鍵字 | 預期 Email 成功率 |
|----|------|--------|-----------------|
| T3.1 | US | "cable manufacturer" | ≥ 30% |
| T3.2 | US | "auto parts" | ≥ 25% |
| T3.3 | US | "plastic injection molding" | ≥ 30% |
| T4.4 | CA | "electronic components" | ≥ 20% |
| T3.5 | US | "restaurant equipment" | ≥ 15% |

### T4 — 用量配額正確性（v3.2 新增）

| ID | 測試目標 | 步驟 | 成功標準 |
|----|---------|------|---------|
| T4.1 | 配額檢查觸發 | 免費會員爬取超過 10 筆 | 任務回傳 quota_exceeded=True |
| T4.2 | 配額用完停止 | 接近配額時停止 | 新增數量 = 剩餘配額 |
| T4.3 | Vendor 無限爬取 | Vendor 角色執行爬蟲 | 無配額限制，正常完成 |
| T4.4 | 同步計入配額 | 全域池同步 1 筆 | increment_usage +1 |

---

## 三、測試資料設計（試算表追蹤）

### 測試資料表

| 執行日期 | 市場 | 關鍵字 | 爬蟲模式 | 總爬取數 | 有Email數 | Email成功率 | 無Email數 | 全域池寫入 | 任務狀態 |
|---------|------|--------|---------|---------|----------|-----------|----------|-----------|---------|
| 2026-03-27 | US | cable manufacturer | manufacturer | ? | ? | ? | ? | ? | ? |
| 2026-03-27 | US | auto parts | yellowpages | ? | ? | ? | ? | ? | ? |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

### 計算公式

```
Email 成功率 = 有Email數 / 總爬取數 × 100%
全域池寫入率 = global_leads 新增數 / 總爬取數 × 100%
```

---

## 四、手動測試 SOP（每個 Actor）

### Step 1: 確認 Actor 端點
```bash
# 測試 Thomasnet Actor
curl -s "https://api.apify.com/v2/acts/junipr~yellow-pages-scraper" \
  -H "Authorization: Bearer $APIFY_API_TOKEN" | jq .status

# 測試黃頁 Actor
curl -s "https://api.apify.com/v2/acts/junipr/yellow-pages-scraper" \
  -H "Authorization: Bearer $APIFY_API_TOKEN" | jq .status
```

### Step 2: 執行單頁測試（Dry Run）
```bash
# 測試黃頁模式
curl -X POST https://linkora-backend-uat.onrender.com/api/scrape-simple \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "market": "US",
    "pages": 1,
    "keyword": "cable manufacturer",
    "miner_mode": "yellowpages"
  }' | jq .
```

### Step 3: 檢查任務日誌
```bash
# 查看任務日誌
curl https://linkora-backend-uat.onrender.com/api/admin/scrape-tasks?limit=1 \
  -H "Authorization: Bearer <admin_token>" | jq .
```

### Step 4: 檢查 Leads 入庫
```bash
# 查看最新 Leads（檢查 email）
curl https://linkora-backend-uat.onrender.com/api/leads \
  -H "Authorization: Bearer <token>" | jq \
  '[.[] | {company_name, contact_email, email_candidates, ai_tag}] | .[-5:]'
```

### Step 5: 檢查全域池寫入
```bash
# 檢查全域池
curl https://linkora-backend-uat.onrender.com/api/global-pool/stats \
  -H "Authorization: Bearer <admin_token>" | jq .
```

---

## 五、Debug 問題排查清單

### Email 為空的常見原因

| 症狀 | 可能原因 | 排查方式 |
|------|---------|---------|
| 所有 items 都沒 email | Actor 沒有設定 extractEmails=true | 檢查 run_input |
| 只有部分有 email | 該公司黃頁頁面本來就沒有 | 正常，可接受 |
| email 全是 guess | `find_emails_free()` 全部失敗 | 檢查 free_email_hunter 是否正常 |
| contact_email 全空但 candidates 有值 | 所有 email 都經過 Guessing | 正常，顯示有嘗試但未驗證 |
| 全域池 email 為空 | Guessing email 未寫入 contact_email | v3.2 已修復 |

### 爬蟲卡住的排查

1. 檢查 `scrape_logs` 表：`level=error` 的記錄
2. 檢查 `scrape_tasks.status = Running` 是否超過 10 分鐘
3. 執行 `DELETE /api/admin/scrape-tasks/stale` 清理
4. 檢查 Render 後台日誌是否有 Python Exception

---

## 六、驗收標準（每次上線前必須通過）

| 等級 | 項目 | 標準 |
|------|------|------|
| 🔴 嚴重 | Email 欄位可寫入 DB | contact_email / email_candidates 非空時能正確寫入 |
| 🔴 嚴重 | 全域池同步正常 | 新增 Lead 時同步寫入 global_leads |
| 🔴 嚴重 | 配額檢查正常 | 超額時正確拒絕或停止 |
| 🟡 中等 | Email 成功率（US市場） | ≥ 20% |
| 🟡 中等 | 爬蟲任務完成率 | ≥ 90% |
| 🟡 中等 | 備援 Actor 正常 | 主要失敗時自動切換 |
| 🟢 低 | 文件同步更新 | SCRAPER_DOCUMENTATION.md 與實際一致 |

---

## 七、已知限制（不可修復或延後修復）

| 項目 | 說明 | 因應方式 |
|------|------|---------|
| TW 市場無資料 | YellowPages / ThomasNet 無台灣數據 | 需另找 TW 來源（如商業司） |
| UK/EU 市場低成功率 | YellowPages 主要覆蓋北美 | 使用 ThomasNet 製造商模式 |
| Email Guessing 無法驗證 | 只做前綴猜測，不做 SMTP 驗證 | 分離寫入 email_candidates |
| 爬蟲可能被封 | 大量請求觸發網站反爬 | 有 Apify 雲端代理 |

---

*測試計畫由 Ann 建立，2026-03-27 更新至 v3.2*
