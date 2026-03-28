# BEPG 快速技術指南 (Backend Engineering Guide)

## 🏗️ 核心架構 (Backend v3.6 - Modular)
Linkora 後端於 v3.6 轉變為 **模組化架構** (Modular APIRouter)。採用 FastAPI 分層路由，將 `main.py` 精簡為啟動骨幹，主要邏輯分佈於 `routers/` 各模組。

## 🚀 快速跳轉 (Quick Links)
- 📡 **[API 手冊 (v3.6 同步)](API.md)**: 所有 Endpoint、Auth 與 Pydantic Schema。
- 🛠️ **[綜合開發指標與規範](DEVELOPMENT_GUIDE.md)**: 本地運行、資料庫遷移與編碼標準。
- 🤖 **[探勘引擎技術原理](SCRAPER_DOCUMENTATION.md)**: 四階段發現法與 Failover 實作。

## 🛠️ 常見 BE 任務 (SOP)
1. **新增 API 接口**：確定功能領域（Auth, Leads, Email, Scraper, Admin, Track），在 `backend/routers/` 對應檔案中實作並更新 `API.md`。
2. **資料庫變更**：更新 `models.py` 後，同步至 `database.py` 的 `_run_migrations` 或正式 Alembic 腳本。
3. **優化後端性能**：檢查 `main.py` 的 `catch_exceptions_middleware` 記錄的處理時間（X-Process-Time）。

---
*OpenClaw Optimized Guide - Role: BEPG*
