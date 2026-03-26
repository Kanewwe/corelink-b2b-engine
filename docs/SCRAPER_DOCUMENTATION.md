# Linkora 爬蟲系統技術文件 (v2.7.1)

> **版本：** 2.7.1 (Isolation Pool)  
> **更新日期：** 2026-03-26  
> **維護者：** Antigravity AI  

---

## 一、核心爬取策略 (v2.6 升級重點)

### 1.1 Email 撈取方式 (Apify 加強版)

為了提升 Email 獲取率，我們從 v2.6 開始採用 **Deep Extraction** (深層提取) 技術，由原本的搜尋結果解析，變更為進入公司詳細頁面進行主動探測：

- **核心原理**：Apify Actor 會自動分析每個公司的官方網站，尋找 `mailto:` 連結、聯絡頁面、隱含的 Email 字串。
- **關鍵參數 (API 層級)**：
  - `"extractEmails": True` (開啟深層提取)
  - `"includeDetails": True` (進入詳細頁面)
- **Email 解析優先級**：
  - 我們會同時檢查多個回傳欄位：`email` -> `emails` -> `contactEmail`。
  - 第一個有效的 Email 會被存入 `contact_email`，其餘候選者會存入 `email_candidates` 作為備援。
- **推薦 Actor**：
  - `junipr/yellow-pages-scraper` (主推，包含詳細 Email 提取)
  - `memo23/thomasnet-scraper` (製造商模式首選)

### 1.2 進階去重與全域隔離池 (Lead Isolation Pool) - v2.7

為了極大化資料價值並降低 API 成本，系統導入了「隔離池」機制：

- **隔離表 (Global Isolation Table)**: 所有採集到的唯一公司資料均會存儲於 `global_leads` 表。
- **同步優先策略 (Global-First)**:
    1. **預檢索**: 在執行高成本的 Apify 爬蟲前，系統會比對全域池。
    2. **無縫同步**: 若全域池已存在該公司，系統將直接「同步 (Sync)」至該使用者的私有名單。
    3. **雙向存儲**: 全新採集的資料會同時寫入「私有名單」與「全域隔離池」。
- **優點**: 
    - 節省超過 50% 的重複採集費用。
    - 即使 Apify 餘額用盡，仍能從全域池獲得歷史採集結果。

### 1.3 進階去重邏輯 (Multi-Stage Deduplication)

1. **Domain 檢查 (Level 1)**：
   - 這是最精確的去重方式。系統會將網址標準化為 Domain (例如 `bosch.com`)。
   - 若資料庫中已有相同 Domain 的 Lead，系統會立即跳過，避免因公司名稱微調 (如 Inc vs LLC) 導致的誤判。
2. **名稱檢查 (Level 2)**：
   - 若無法提取到 Domain，則會比對公司名稱。
   - 名稱經過去空格與小寫化後進行嚴格比對。
3. **分用戶隔離**：
   - 所有的去重檢查皆在 `user_id` 層級進行。這意味著不同的使用者可以擁有相同的客戶，但同一個使用者絕對不會在名單中看到重複的項目。

### 1.4 智慧探勘控制 (v2.7.1 新增)

- **同步開關 (Global Sync Toggle)**: 
    - 管理員可於「系統設定」->「一般」中控制 `enable_global_sync` 開關。
    - **開啟 (預設)**：先檢索 `GlobalLead` 全域池，有則直接同步，無則執行外部採集並將結果回饋到全域池。 (節省成本)。
    - **關閉**: 直接對外部 API 進行即時採樣 (Live Scrape)，不與全域池互動。
- **數據完整性**: 每次同步或採集均會更新 `last_scraped_at`。

---

## 二、模式說明

### 2.1 製造商模式 (Manufacturer Mode - PRO)
- **目標**：搜尋中小型 B2B 製造商。
- **流程**：
  1. 優先使用 **Thomasnet Scraper** (北美最權威製造商目錄)。
  2. 若結果不足，自動切換至 **Yellowpages (Pro)** 模式，並加上 `manufacturer` 關鍵字補償。
- **過濾機制**：內建 `ENTERPRISE_BLACKLIST`，自動排除 Bosch、Siemens 等跨國大企業，專注於中型與小型的真實採購商。

### 2.2 黃頁模式 (Yellowpages Mode - Original)
- **目標**：各行業、地區性的中小企業。
- **流程**：直接呼叫 **Junipr Yellowpages Scraper**。
- **適用場景**：不僅限於製造商，適用於維修店、各類 B2C 零售、本地服務業。

---

## 三、監控與日誌

### 3.1 爬蟲日誌 (scrape_logs)
- 每次探勘任務的所有步驟都會記錄在 `scrape_logs`。
- 管理員可於「Scrape Monitor」查看，一般用戶可於「開發紀錄專區」查看總結果。

### 3.2 狀態定義
- `Running`: 正在執行。
- `Completed`: 成功結束，顯示最終新增、跳過與錯誤筆數。
- `Failed`: 遭遇不可恢復錯誤 (如 API 餘額不足)。

---
*本文件由 Antigravity AI 持續更新中*
