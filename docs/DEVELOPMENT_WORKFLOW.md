# 開發與資料庫遷移流程規範 (DEVELOPMENT_WORKFLOW.md v2.7.1)

本文件定義了 Linkora 2.0 的開發生命週期，特別是針對 **Schema 變更**、**API Key 動態配置** 與 **全域功能控管 (v2.7.1)** 如何從開發環境安全過渡到正式環境 (PRD) 的標準作業程序。

## 1. 開發階段 (Development)
- **模型同步**：邊做邊執行，並即時更新遷移指令。
    - 當你在 `models.py` 新增欄位時，**必須同步**在 `backend/migrations.py` 的 `tables_to_patch` 字典中加入該欄位。
    - **禁止**直接操作資料庫介面而不記錄，這會導致 PRD 部署時內容遺失。
- **外部工具與全域配置測試**：
    - 開發新功能時，應通過 `config_utils.get_api_key` 或 `get_general_setting` 來讀取配置，禁止直接使用 `os.getenv`。

## 2. API Key 與全域配置 (Configuration Management v2.7.1)
- **動態性**：所有的外部 API Key 與全域開關 (如 `enable_global_sync`) 應優先設置於資料庫中的 `system_settings` 表。
- **配置步驟**：
    1. 在核心功能的 `view_file` 或 `api.ts` 查找對應的介面。
    2. 通過管理界面（Admin Dashboard -> System Settings）進行測試設置。
    3. 確認功能在 UAT 環境讀取的是資料庫配置而非本地 `.env`。

## 3. 驗收階段 (UAT Verification)
- **目標**：驗證 SQL 變更在 PostgreSQL 上的相容性與配置生效。
- **操作**：
    - 將程式碼推送至 `uat` 分支。
    - 在 Render 設置 `APP_ENV=uat`。
    - 觀察啟動日誌，確認 `init_db()` 自動建立了 `uat` schema，且 `migrations.py` 已正確套用累計變更。
    - **重要**：手動在 UAT 資料庫中插入測試用 API Key，確認爬蟲與 AI 功能正常運行。

## 4. 正式發布 (PRD Release) 🚀
- **核心：一致性維護**。
- **操作**：
    1. **審核**：合併至 `main` 分支前，最後一次檢查 `backend/migrations.py` 與 `config_utils.py` 的對一性。
    2. **切換**：在 Render 設置 `APP_ENV=production`。
    3. **執行**：啟動服務，系統會自動在 `public` schema 執行累積的 `ALTER TABLE` 指令。
    4. **配置同步**：將 UAT 驗證過的 API Key 正確同步到 PRD 資料庫的 `system_settings` 表中。

## 5. 總結
資料庫與配置變更採取「**程式碼優先 (Code-First) & 腳本自動化**」原則。只要始終保持 `migrations.py` 同步，並通過 `config_utils` 讀取配置，就能確保開發成果能 1:1 完整、動態地繼承到各個環境。

---
*Created by Antigravity AI on 2026-03-26 v2.6.0*
