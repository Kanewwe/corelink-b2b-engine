# Linkora 開發與維護指南 (Development Guide)

本指南集結了 Linkora 平台（React + FastAPI + PostgreSQL）的開發標準、生命週期規範與資料庫維護流程，所有開發人員與 Agent 皆須嚴格遵守。

---

## 1. 快速啟動 (Quick Start)

### 後端 (Backend)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
- **配置**: 確保 `/backend/.env` 已設定 `OPENAI_API_KEY` 與 `DATABASE_URL`。

### 前端 (Frontend)
```bash
cd frontend
npm install
npm run dev
```

---

## 2. 編碼規範與防垃圾政策 (Coding Standards)

為了維護專案的純粹性，請遵循以下「零容忍」規定：
1. **嚴禁根目錄雜亂**：所有代碼必須在 `backend/` 或 `frontend/` 下執行。嚴禁提交暫存檔、自動生成的測試腳本或備份檔。
2. **清理舊邏輯**：當功能遷移至 3.0 或 3.1 以上架構後，必須徹底移除舊代碼，嚴禁保留「已註解掉」的無效片段。
3. **前端元件**：必須使用 **Tailwind CSS** 進行樣式開發，嚴禁寫大量的 Inline Style。

---

## 3. 資料庫遷移與環境隔離 (Database & Migration)

Linkora 採用 **Schema-based** 隔離技術，在單一 PostgreSQL 實例中達成環境區分。

### 自動遷移邏輯
- 系統啟動時會透過 `jobs/__init__.py` 的 `run_startup_tasks()` 自動建立表。
- **同步要求**：當您在 `models.py` 新增欄位時，**必須同步**更新 `database.py` 中的 `_run_migrations` 函數。
- 系統會在啟動時其背景線程自動執行 `ALTER TABLE ADD COLUMN IF NOT EXISTS` 以補齊欄位，確保不阻塞啟動。

### 環境切換
- `APP_ENV=production` -> 使用預設的 `public` schema。
- `APP_ENV=uat` -> 使用 `uat` schema。

---

## 4. 標準開發生命週期與 VCP 規則 (Lifecycle & VCP)

Linkora 採行 **VCP (Verify-Commit-Push)** 強制規則，所有開發任務必須以此閉環結束。

### 第一階段：驗證 (Verify)
- 修改代碼後，必須先通過本地檢查。
- **後端**: 執行 `./scripts/test.ps1` (或 `pytest`) 確保邏輯無誤。
- **前端**: 必須通過 `npm run build` 確認編譯無誤，嚴禁提交帶有 Lint Error 的代碼。

### 第二階段：提交與推送 (Commit & Push)
- **指令**: `./scripts/sync.ps1 -Action commit -Message "Your Message"`。
- **目標**: 必須推送至 `uat` 分支。`uat` 是唯一受信任的準生產測試環境。
- **自動化**: Agent 在完成任務時，必須主動執行此動作。

### 第三階段：正式發佈 (Production)
- **Gatekeeper**: 必須獲得 User 顯性批准後，才可將 `uat` 合併至 `prd`。
- **發佈**: 使用 `./scripts/sync.ps1 -Action deploy`。

---

## 5. 提交前檢查清單 (Pre-push Checklist - P0)
- [ ] **[P0]** `./scripts/test.ps1` 執行成功。
- [ ] **[P0]** `npm run build` 通過無誤。
- [ ] **[P0]** 代碼已成功推送至 `uat` 分支。
- [ ] `backend/requirements.txt` 已更新。
- [ ] `migrations.py` 已包含所有新增的 DB 欄位。
- [ ] 根目錄與 `backend/` 目錄下無雜亂產出的暫存檔。

---
*Created by Antigravity AI - Unified Linkora Development Guide v3.6.0 (Modular)*
