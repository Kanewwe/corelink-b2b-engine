# BEPG 快速技術指南 (Backend Engineering Guide)

## 🏗️ 核心架構 (Backend v3.1.8)
Linkora 後端基於 **FastAPI** + **SQLAlchemy 2.0**，採用異步模式與 `APScheduler` 背景任務排程。

## 🚀 快速跳轉 (Quick Links)
- 📡 **[API 手冊 (v3.1.8 同步)](API.md)**: 所有 Endpoint、Auth 與 Pydantic Schema。
- 🛠️ **[綜合開發指標與規範](DEVELOPMENT_GUIDE.md)**: 本地運行、資料庫遷移與編碼標準。
- 🤖 **[探勘引擎技術原理](SCRAPER_DOCUMENTATION.md)**: 四階段發現法與 Failover 實作。

## 🛠️ 常見 BE 任務 (SOP)
1. **新增 API 接口**：務必在 `API.md` 更新對應規格，並檢查 `require_role`。
2. **資料庫變更**：更新 `models.py` 後，同步至 `migrations.py` 的字典。
3. **優化爬蟲性能**：調整 `SCRAPER_DOCUMENTATION.md` 中提到的 Actor ID 或逾時控制。

---
*OpenClaw Optimized Guide - Role: BEPG*
