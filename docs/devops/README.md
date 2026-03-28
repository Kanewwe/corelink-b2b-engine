# DevOps 快速運維手冊 (Operations Guide)

## 🚀 雲端架構 (Render / Web Service)
Linkora 目前部署於 **Render**，並使用 PostgreSQL 作為核心存儲。

## 🚀 快速跳轉 (Quick Links)
- 🚀 **[雲端部署與監控指南](DEPLOYMENT_GUIDE.md)**: 部署架構、環境變數與 SSL 強制連線配置。
- 🛠️ **[探勘引擎除錯與故障排除](SCRAPER_DEBUG_GUIDE.md)**: Apify 失敗攔截、403 Bypass 與 SQL 補全手冊。

## 🛠️ 常見 DevOps 任務 (SOP)
1. **處理任務卡死**：檢查 `manufacturer_miner` 的超時日誌。
2. **監控 DB 連線**：確認 Render Postgres 的 `sslmode=require` 設定。
3. **擴展資源**：調整 `APP_ENV` 生態鏈與對應的資源配額。

---
*OpenClaw Optimized Guide - Role: DevOps*
