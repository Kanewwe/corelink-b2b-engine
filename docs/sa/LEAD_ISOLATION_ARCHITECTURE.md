# Linkora 名單隔離與全域同步架構 (Lead Isolation & Sync)

本文件詳述 Linkora 如何處理「全域共享情報」與「個人私有工作區」之間的資料同步與權屬邏輯。

---

## 1. 雙層資料模型 (The Dual-Layer Model)

為了平衡「資料累積」與「用戶隱私/客製化」，系統採用雙層結構：

### 層級 A：全域情報池 (Global Lead Pool)
- **資料表**: `global_leads`
- **定位**: 系統的「通用百科全書」。
- **唯一性**: 以 **`domain` (網域)** 為唯一鍵 (Primary Key for Logic)。例如 `apple.com` 在全域池中只會有一筆紀錄。
- **內容**: 存放最原始、公開、經過去重清洗的企業資訊（名稱、Email、描述、產業標籤）。
- **共享性**: 所有成員共享，但不直接編輯。

### 層級 B：用戶私有區 (Private Workspace)
- **資料表**: `leads`
- **定位**: 使用者的「個人通訊錄」。
- **唯一性**: 以 `(user_id, domain)` 組合為準。不同用戶可以擁有相同的公司。
- **關連**: 透過 **`global_id`** 欄位鏈結回全域池。
- **內容**: 存放用戶個人的開發進度（標籤、備註、是否已寄信、個人的 Email 修改）。

---

## 2. 同步機制 (Synchronization Flow)

### 2.1 探勘時的「情報先行」邏輯
當爬蟲（如製造商模式）抓到一個 Domain 時：
1. **私有檢查**: 檢查該用戶的 `leads` 表中是否已存在此 Domain？有則跳過。
2. **全域檢索**: 若私有區無資料，檢索 `global_leads`。
3. **雲端克隆 (Sync)**: 
   - 若全域池有資料，直接將其內容「拷貝」一份到用戶的私有 `leads` 中。
   - 標記 `global_id`，達成「免爬取、零點數、即時獲取」。
4. **外部採集 (Live Scrape)**: 
   - 若全域也無資料，才啟動 Apify Actor 進行遠端抓取。
   - 抓取後，先存入 `global_leads` (貢獻情報)，再同步至 `leads` (交付結果)。

---

## 3. 數據合併與覆寫 (Merge & Override)

當前端讀取客戶詳情時，後端執行以下邏輯：
- **優先級**: **個人私有資料 > 全域通用資料**。
- **場景**: 如果用戶修改了某個客戶的 Email，系統會將修改存在私有 `leads` 表，且不再顯示全域池中的舊 Email。
- **權限**: 只有管理員（Admin）可以透過「情報修正提案 (Global Proposals)」來更新全域池的內容。

---

## 4. 關鍵代碼位置 (Backend)

- **`models.py`**: 定義 `Lead` (私有) 與 `GlobalLead` (全域) 模型。
- **`scrape_utils.py`**: 
    - `sync_from_global_pool()`: 判斷是否執行同步。
    - `save_to_global_pool()`: 將採集結果更新至情報庫。
- **`main.py`**:
    - `/api/leads`: 查詢時的合併邏輯。
    - `/api/admin/global-pool/*`: 管理全域池的接口。

---

## 5. 常見修改建議

如果您希望修改此架構，可以從以下切入：
- **去重條件**: 目前以 Domain 為主，若您希望以「公司名稱+地址」去重，需修改 `sync_from_global_pool`。
- **同步內容**: 目前同步 Email, Desc。若想增加同步 Social Links，需修改 `save_to_global_pool` 與對應模型。
- **隔離牆**: 若需要特定的「團隊共享」而非「全系統共享」，需引入 `team_id` 概念。

---
*Last Updated: 2026-03-27 by Antigravity AI*
