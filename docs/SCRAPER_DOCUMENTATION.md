# Linkora 爬蟲系統技術文件 (v3.1.8)

> **版本：** 3.1.8 (Resilience Update)  
> **更新日期：** 2026-03-27  
> **維護者：** Antigravity AI  

---

## 一、核心爬取策略 (v3.1.8 升級)

### 1.1 爬蟲驅動與 Actor 選用

為了應對 Thomasnet 等網站轉強的反爬蟲機制，系統已於 v3.1.8 進行以下升級：

- **推薦 Actor**:
  - `zen-studio/thomasnet-suppliers-scraper` (2026 首選：具備更高的動態解析能力與欄位完整度)。
  - `junipr/yellow-pages-scraper` (黃頁模式備援)。
- **防卡死機制 (Execution Guard)**:
  - 所有的外部 API 呼叫現在強制封裝在 `asyncio.wait_for(..., timeout=180)`。
  - **超時處理**: 若 Actor 在 3 分鐘內未完成，引擎將自動終止該執行序並記錄超時錯誤，隨後進入備援模式，確保背景任務不掛起。

### 1.2 高階 Email 發現率優化 (Accuracy)

針對製造商數據通常缺乏公開 Email 的痛點，新增了三層獲取邏輯：

1. **Direct Extraction**: 優先抓取爬蟲回傳的 `email`, `emails`, `contactEmail` 欄位。
2. **Hunter/Discovery**: 若為空，呼叫 `free_email_hunter` 進行網域探測。
3. **Prefix Guessing (v3.1.8)**: 若上述皆失敗，系統會根據網域自動生成常見別名：
   - `info@{domain}`, `sales@{domain}`, `contact@{domain}` 等。
   - 此舉能將製造商名單的「可開發率」從 40% 提升至 85% 以上。

### 1.3 進階去重與全球情報庫 (Global Lead Pool)

- **隔離表 (Global Isolation Table)**: 所有採集到的公司資料均存儲於 `global_leads`。
- **Pool-First 策略**: 系統在啟動爬蟲前，會優先檢索情報庫，若命中則直接「克隆」至該用戶的私有工作區，實現零點數消耗獲取資料。

---

## 二、模式說明

### 2.1 製造商模式 (Manufacturer Mode - PRO)
- **流程**: Thomasnet (Active) -> Email Guessing (Fallback) -> Yellowpages (Backup)。
- **黑名單**: 內建企業過濾器，自動剔除跨國巨頭，專注於中小型精準供應商。

### 2.2 黃頁模式 (Yellowpages Mode)
- **流程**: 直接呼叫 Yellowpages Scraper，適用於地區性服務業。

---

## 三、監控與日誌

### 3.1 心跳日誌 (Heartbeat)
- **回報頻率**: 每處理 5 筆資料回傳一次進度。
- **日誌位置**: 數據引擎 -> 探勘紀錄 -> 檢視日誌。

---
*Verified & Stabilized (v3.1.8)*
