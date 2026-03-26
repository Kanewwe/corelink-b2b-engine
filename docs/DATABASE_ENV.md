# 資料庫環境管理指南 (DATABASE_ENV.md)

本指南說明如何在 Linkora 2.0 中切換 **Production (PRD)** 與 **UAT (測試)** 環境。

## 1. 環境架構

我們在同一個 Render PostgreSQL 實例中使用 **Schema (綱要)** 進行隔離：

| 環境 | Schema | 說明 |
| :--- | :--- | :--- |
| **Production** | `public` | 正式環境資料 |
| **UAT** | `uat` | 測試與驗收環境資料 |

## 2. 如何切換環境

系統會根據環境變數 `APP_ENV` 自動切換：

### 本地切換方式
編輯 `backend/.env` 檔案，調整 `APP_ENV`：
- `APP_ENV=production` (預設為正式資料)
- `APP_ENV=uat` (切換為測試資料)

### Render 雲端切換方式
在 Render Dashboard 的 **Environment** 設定中：
1. 找到 `APP_ENV` 變數。
2. 點擊編輯，修改為 `production` 或 `uat`。
3. 儲存後系統會自動重新啟動並連接至對應的 Schema。

## 3. 自動初始化
當切換至 `uat` 時，後端在啟動時會自動執行：
- `CREATE SCHEMA IF NOT EXISTS uat;` (若不存在則建立)
- `Base.metadata.create_all()` (自動在該 Schema 建立所有資料表)

## 4. 注意事項
- **資料不共用**：PRD 與 UAT 的資料（使用者、探勘任務、名單）是完全分開的。
- **SSL 連線**：連接 Render 時必須附帶 `sslmode=require`。
- **API Token**：建議在 UAT 環境使用不同的 `API_TOKEN` 以確保安全性。

---
*Created by Antigravity AI on 2026-03-26*
