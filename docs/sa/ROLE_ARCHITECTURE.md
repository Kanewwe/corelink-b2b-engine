# Linkora - 角色權限架構 (Role Architecture)

本文件定義了 Linkora v3.1.8 的三角色體系（Admin, Vendor, Member）及其多租戶隔離與業務計費邏輯。

---

## 1. 核心角色定義 (Role Definitions)

### 1.1 Admin (全域管理員)
- **職責**: 平台營運、簽約 Vendor 審核、全系統數據監控、API Keys 管理。
- **權限**: 擁有最高控制權，可進入 `System Control Center` 配置全域參數。

### 1.2 Vendor (簽約合作夥伴/簽約供應商)
- **職責**: 作為 B2B 探勘服務商，為其客戶代操。
- **特權**: 專屬的無限 Leads 與無上限發信配額，並具備自定義 SMTP 域名。
- **結帳**: 依據「發送量 / 觸及率」與平台 Admin 進行月結分潤。

### 1.3 Member (終端用戶/一般業務)
- **職責**: 個人開發信與名單管理。
- **分級**: 分為 Free (10 leads), Pro (100 leads), Enterprise (500 leads)。

---

## 2. 數據隔離實作 (The Isolation Wall)

Linkora 採用 PostgreSQL **Schema (綱要)** 作為硬性環境隔離屏障：

- **多租戶原理**: 系統根據 `APP_ENV` (UAT / PRD) 自動切換物理連接路徑。
- **SearchPath**: 在 `database.py` 中，系統會透過 `options="-c search_path=uat"` 指令，確保 SQLAlchemy 查詢絕不會跨越 Schema 邊界。

---

## 3. 業務計費矩陣 (Billing Matrix)

| 計費指標 | 說明 | 結算週期 |
| :--- | :--- | :--- |
| **Leads Scraped** | 總採集到的有效 B2B 客戶數 | 按次 / 按量 |
| **Reach Events** | 客戶點擊或開信的成效次數 | 按成效 (CPA) |
| **Wholesale Fee** | 平台向 Vendor 收取的批發單價 | 月結 (Net 30) |

---
*Created by Antigravity AI - Linkora Core Principles v3.1.8*
