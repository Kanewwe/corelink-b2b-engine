# 開發與資料庫遷移流程規範 (DEVELOPMENT_WORKFLOW.md)

本文件定義了 Linkora 2.0 的開發生命週期，特別是針對 **Schema 變更** 如何從開發環境安全過渡到正式環境 (PRD) 的標準作業程序。

## 1. 開發階段 (Development)
- **原則**：邊做邊執行，並即時更新遷移指令。
- **操作**：
    - 當你在 `models.py` 新增欄位時，**必須同步**在 `backend/migrations.py` 的 `tables_to_patch` 字典中加入該欄位。
    - 在本地測試時，執行 `python backend/migrations.py` 確認 SQL 語法正確且欄位已成功新增。
    - **禁止**手動操作資料庫介面新增欄位而不記錄，這會導致 PRD 部署時漏掉內容。

## 2. 驗收階段 (UAT Verification)
- **目標**：驗證 SQL 變更在 PostgreSQL 上的相容性。
- **操作**：
    - 將程式碼推送至 `uat` 分支。
    - 在 Render 設置 `APP_ENV=uat`。
    - 觀察啟動日誌，確認 `init_db()` 自動建立了 `uat` schema，且 `migrations.py` 已正確套用所有累積的變更。
    - 若 UAT 測試發現欄位定義有誤，在 `migrations.py` 中修正後重新執行。

## 3. 正式發布 (PRD Release) 🚀
- **核心：變更累積與一致性**。
- **操作**：
    1. **審核**：在合併到 `main` 分支前，最後一次檢查 `backend/migrations.py`，確保它包含了自上次發布以來**所有**的新增欄位與資料表。
    2. **切換**：在 Render 設置 `APP_ENV=production`。
    3. **執行**：啟動服務，系統會自動在 `public` schema 執行累積的 `ALTER TABLE` 指令。
    4. **驗證**：檢查 `public` schema 的欄位是否完整，避免 PRD 缺少 UAT 階段新增的功能。

## 4. 防呆檢查清單 (Anti-Failure Checklist)
- [ ] 欄位名稱是否與 `models.py` 100% 一致？
- [ ] 資料型態 (Integer, Text, Boolean) 在 Postgres 中是否支援？
- [ ] 預設值 (Default Value) 是否符合邏輯？
- [ ] 是否所有 `migrations.py` 的變更都已提交 (Git Commit)？

## 5. 總結
資料庫變更採取「**程式碼優先 (Code-First) & 腳本自動化**」原則。只要始終保持 `migrations.py` 與 `models.py` 同步，就能確保 UAT 的開發成果能 1:1 完整繼承到 PRD。

---
*Created by Antigravity AI on 2026-03-26*
