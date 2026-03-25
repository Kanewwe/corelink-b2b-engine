# Linkora 2.0 開發與維護規範 (Development Standards)

本規範旨在維護 Linkora 2.0 (React + FastAPI) 的純粹性與架構一致性，防止出現冗餘或損壞的代碼。

---

## 🚫 零容忍：拒絕垃圾資料 (Anti-Garbage Policy)

1. **嚴禁在根目錄亂放檔案**：所有功能開發必須在 `backend/` 或 `frontend/` 對應路徑執行。嚴禁產生如 `test_xxx.py` 或 `backup_old.js` 的暫存檔。
2. **產出物管理**：
   - 所有前端產出應存在 `dist/` (由 build 指令產生)，不應簽入 Git。
   - 後端產出（如生成的 CSV、圖片）應存在特定資料夾並設定 `.gitignore`。
3. **刪除過時邏輯**：當功能遷移至 2.0 (React) 後，必須徹底移除對應的傳統 HTML/JS 邏輯，不可保留「註解掉」的舊代碼。

---

## 📂 專案架構規範 (Project Structure)

- **Backend**: 基於 `FastAPI`。必須使用 `models.py` 定義 Table，使用 `schemas.py` (Pydantic) 處理介面。
- **Frontend**: 基於 `Vite + React + TS`。所有 UI 元件必須使用 **Tailwind CSS**，嚴禁寫 Inline Style 或大量 CSS 檔案。
- **Assets**: 所有的圖片、語系檔、設定檔請放在 `frontend/src/assets` 或 `backend/static`。

---

## 🛠️ 開發流程與指令規範 (Workflow Rules)

1. **依賴管理**：
   - 新增 Python 庫必須更新 `backend/requirements.txt`。
   - 新增 NPM 套件必須使用 `npm install --save` 並提交 `package-lock.json`。
2. **資料庫變更**：
   - 嚴禁直接手改 DB 欄位。所有變更必須更新 `backend/migrations.py` 中的 `tables_to_patch` 邏輯。
3. **AI Agent 安全規範**：
   - AI 在執行任何 `write_to_file` 之前，必須先確認檔案是否已存在，避免覆蓋毀損。
   - 大規模重構前必須執行 `git commit`。

---

## ✅ 提交與部署前檢查表 (Pre-push Checklist)

- [ ] **Lint 檢查**：確保無語法錯誤 (Syntax Error)。
- [ ] **Build 檢查**：`npm run build` 必須成功通過。
- [ ] **功能回歸**：
  - 登入機制是否失效？
  - 成效分析 (Analytics) 數據是否能正常載入？
  - 探勘核心 (Scraper) 是否能正常啟動任務計畫？

---
> [!IMPORTANT]
> **開發人員 (Human/AI) 注意**：Linkora 2.0 的核心價值在於「乾淨」與「高效」。若發現代碼開始變得臃腫或雜亂，請優先執行 Refactor (重構) 而非繼續疊加功能。
