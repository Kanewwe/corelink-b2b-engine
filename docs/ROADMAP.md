# Linkora v3.2 → v3.5 長期 Roadmap

> **版本：** 1.1.0（2026-03-28 更新）  
> **適用對象：** Kane（技術創辦人）  
> **Review 頻率：** 每兩週一次（每個 Sprint 結束）

---

## 現況診斷（2026-03-28 v2 — 重大發現）

### 🔴 緊急（Blocker）— 所有爬蟲失效的根本原因

經過完整診斷，發現**三層次問題**疊加：

| 層次 | 問題 | 根本原因 | 狀態 |
|------|------|---------|------|
| **Token** | 錯誤 Apify key（JdJ vs GdJ）| 之前用錯誤 key 測試所有 actors | ✅ 已確認正確 key |
| **Actor Path** | Junipr 正確路徑是 `junipr~yellow-pages-scraper`（波浪號）| 之前用斜線路徑 | ✅ 已修復 |
| **Junipr Actor** | SUCCEEDED 但 items=0, datasetId=none | **Actor 已實質下架（2026-03已確認）** | 🔴 已確認 |
| **Direct Scraping** | YellowPages.com 回 403 Forbidden | 需要更換 UA 或 proxy | 🟡 需處理 |
| **Thomasnet** | `zen-studio/thomasnet-suppliers-scraper` → 404 | Actor 已下架 | 🔴 需替代方案 |
| **所有付費 Actors** | yellowpages-scraper → FAILED/404/400 | 帳號訂閱問題或 actors 下架 | 🔴 需重新評估 |

### 🟡 高優先（已修復）
| 問題 | 修復 |
|------|------|
| SystemSettings API 路由錯誤 | ✅ GET `/admin/settings` → `/system/settings` |
| 版本號顯示 V3.1.9 | ✅ 改為 `V3.2 (AI Intelligence)` |
| ScrapeMonitor TypeScript 錯誤 | ✅ 移除未使用變數 |

### 🔧 Sprint 0 新任務（更新後）

| Task | 優先 | 說明 |
|------|------|------|
| S0-A. Junipr 確認下架 | 🔴 | ✅ 已確認，items=0，需替代方案 | ✅ 已確認 |

### 📊 目前系統狀態（2026-03-28 09:00）
- Leads 總數：81（全部 email_candidates=null，無用）
- 所有 Apify YellowPages/Thomasnet actors 已確認失效
- Direct YellowPages → 403 Forbidden
- **結論：需採購 B2B Data API 或重構爬蟲策略**

---

## Sprint 切割

### Sprint 0：止血 & 穩定（1-2週）
**目標：** 讓爬蟲四模式**至少有一個**能完整跑通（爬到→入庫→有email）

| Task | 負責 | 預期產出 | 優先 |
|------|------|---------|------|
| S0-1. 確認 Junipr 狀態 | Ann | ✅ 已確認：items=0，Actor 已實質下架 | 🔴 |
| S0-2. Direct YellowPages 繞過 403 | Ann | 測試 Selenium/Playwright headless 方案 | 🔴 |
| S0-3. B2B Data API 整合 | Ann | Apollo.io / Hunter.io 取代 Apify scraper | 🔴 |
| S0-3. 清空舊 Leads，重新爬取乾淨測試 | Ann | 至少 10 筆有 email_candidates 的 Leads | 🔴 |
| S0-4. 清空舊 Leads，重新爬取 | Ann | 清理 81 筆無用資料，用新方案重新開始 | 🟡 |
| S0-5. 重建 `find_emails_free()` 支援超時 | Ann | free_email_hunter.py 可中断的 async 版本 | 🟡 |
| S0-6. 調整全域池去重邏輯 | Ann | domain 精確 > name 模糊 | 🟡 |
| S0-7. 前端 API 路由 + 版本號（已修） | Ann | SystemSettings 正常讀取設定 | ✅ |

**Definition of Done：**
- [ ] 免費黃頁模式可完成一個任務並入庫 10+ Leads
- [ ] Leads 有 email_candidates（非 null/空）
- [ ] Task #40+ 任務成功完成

---

### Sprint 1：爬蟲可靠化（3-4週）
**目標：** 四種模式都能穩定運作，資料品質達 80%

| Task | 負責 | 預期產出 | PR |
|------|------|---------|-----|
| S1-1. 四模式端對端測試 | Ann | 測試腳本 + 報告 | - |
| S1-2. ScrapeMonitor 實時日誌刷新 | Ann | 任務日誌每 5 秒自動刷新 | PR |
| S1-3. Hunter.io 整合完整測試 | Ann | hunter 模式有 contact_email | PR |
| S1-4. Email 驗證（MX check）| Ann | leads 有 mx_valid 標記 | PR |
| S1-5. Apify 備援 Actor 多層 fallback | Ann | 任一 actor 失敗自動切換備援 | PR |
| S1-6. 任務超時處理優化 | Ann | 10 分鐘超時後優雅重試 | PR |

**Definition of Done：**
- [ ] 四種模式都能完成並返回有 email 的 Leads
- [ ] 爬蟲成功率 > 80%
- [ ] ScrapeMonitor 可即時看日誌

---

### Sprint 2：AI 功能深化（5-8週）
**目標：** AI 功能成為差異化核心，不是裝飾

| Task | 負責 | 預期產出 |
|------|------|---------|
| S2-1. AI 成效摘要有數據 | Ann | Analytics 有真實摘要（需累積 EmailLog 數據）|
| S2-2. 最佳發送時間 UI 入口 | Ann | Campaigns 頁面有「🤖 AI 建議」按鈕 |
| S2-3. AI 回覆意圖分類 UI | Ann | Analytics 有回覆意圖儀表 |
| S2-4. AI 主旨 A/B 測試追蹤 | Ann | 實際寄出並追蹤開信率差異 |
| S2-5. AI Lead 評分 UI 完善 | Ann | 評分 + 標籤 + 簡報一站式展示 |

**Definition of Done：**
- [ ] AI 成效摘要有真實數據（非 mock）
- [ ] 每個 AI 功能有實際使用案例

---

### Sprint 3：系統穩定與監控（9-12週）
**目標：** 系統健康可測量，問題可預警

| Task | 負責 | 預期產出 |
|------|------|---------|
| S3-1. 爬蟲健康儀表 | Ann | AdminDashboard 有爬蟲成功率圖表 |
| S3-2. Email 送達率追蹤 | Ann | Analytics 有送達/開信/點擊率 |
| S3-3. 用量警報系統 | Ann | Admin 超配額自動通知 |
| S3-4. 自動化備份 | Ann | 每日自動備份 Postgres |
| S3-5. 效能優化 | Ann | API P95 < 500ms |

**Definition of Done：**
- [ ] Admin 可看到完整系統健康儀表
- [ ] 問題發生後 < 5 分鐘有警報

---

### Sprint 4：商業化準備（Q2 2026）
**目標：** 從 MVP 到可銷售的產品

| Task | 負責 | 預期產出 |
|------|------|---------|
| S4-1. 會員試用流程 | Ann | 7 天免費試用，信用卡直連 |
| S4-2. 付款整合（Stripe/LINE Pay）| Ann/Kane | 正式收款 |
| S4-3. Email 模板編輯器升級 | Ann | Drag-drop 所見即所得 |
| S4-4. CRM 整合（HubSpot/Salesforce）| Ann | 一鍵同步 Leads |
| S4-5. 白牌/經銷商方案 | Ann | Vendor 可有自己的品牌 |

---

## Review 框架（每兩週）

### Sprint Review 會議大綱（30 分鐘）

```
1. 完成了什麼？（Demo 3 分鐘）
   - 每個 Task 的實際產出截圖
   
2. 遇到了什麼阻礙？
   - 技術障礙 vs 商業決策需要

3. 下兩週的優先級？
   - 最多 3 個 Task，集中火力

4. 指標追蹤
   - [ ] Leads 總數：XX
   - [ ] 有 email Leads：XX (XX%)
   - [ ] 爬蟲成功率：XX%
   - [ ] AI 功能使用率：XX%
```

### 關鍵指標追蹤表

| 指標 | 目前值 | Sprint 0 目標 | Sprint 1 目標 |
|------|--------|--------------|--------------|
| Leads 總數 | 81 | 91+ | 200+ |
| 有 email_candidates | 0% | >50% | >80% |
| 有 contact_email | 0% | >20% | >50% |
| 爬蟲成功率 | ~20% | >50% | >80% |
| 任務完成率 | 1/4 | 2/4 | 4/4 |

---

## 待 Kane 決策的事

在開始 Sprint 0 之前，需要你回答：

1. **Hunter.io API Key**：目前有設定嗎？如果有，我可以直接測試 hunter 模式；如果沒有，是否要購買？

2. **測試關鍵字**：哪些是你的目標客戶行業？我需要用正確的關鍵字測試，才能驗證資料品質
   - 例：塑膠射出工廠（Plastic Injection Molding）？
   - 例：電子代工（EMS / Electronics Manufacturing）？
   - 例：其他？

3. **免費黃頁模式**：是否接受 Guessing email（info@domain.com）作為替代方案？還是要堅持抓到真實 email？

4. **製造商模式**：是否繼續投資 Thomasnet？還是放棄這個模式，只做黃頁？
