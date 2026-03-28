# DBA 快速技術指南 (Database Admin Guide)

## 🗄️ 資料庫架構 (PostgreSQL v3.1.8)
Linkora 採用 **Schema-based (uat/public)** 環境隔離，並透過 `search_path` 動態選取分層。

## 🚀 快速跳轉 (Quick Links)
- 📊 **[資料庫概覽與全域同步](DATABASE.md)**: `leads` 與 `global_leads` 的數據結構與鏈結。
- 🧬 **[環境切換與 Schema 管理](DATABASE_ENV.md)**: `APP_ENV` 如何影響 Schema 自動建立。
- 🛡️ **[名單隔離技術架構](LEAD_ISOLATION_ARCHITECTURE.md)**: `user_id` 與 `global_id` 的權威性比對。

## 🛠️ 常見 DBA 任務 (SOP)
1. **執行資料遷移**：檢查 `migrations.py` 的字典是否涵蓋所有新欄位。
2. **處理多租戶擴展**：監控 `uat` schema 下的表格大小與索引密度。
3. **優化查詢**：針對 `domain` 與 `website_url` 的索引效能進行微調。

---
*OpenClaw Optimized Guide - Role: DBA*
