# QA 快速驗收指南 (Quality Assurance Guide)

## 🎯 驗收目標
確保 Linkora 平台各功能模組的可靠性與環境隔離性。

## 🚀 快速跳轉 (Quick Links)
- 🧪 **[跨角色測試計畫 (RBAC Matrix)](ROLE_TEST_PLAN.md)**: 角色權限、配額限制與隔離驗證。
- 🤖 **[探勘引擎負壓測試 (Scraper QA)](SCRAPER_TEST_PLAN.md)**: 多模式、超時攔截與 Failover 測試。

## 🛠️ 常見 QA 任務 (SOP)
1. **執行 UAT 驗收**：推送到 `uat` 分支後，從 `Admin Hub` 進行全功能測試。
2. **驗證資料庫隔離**：使用 `SQL` 檢查 `uat` schema 下的 `leads` 所屬性。
3. **測試爬蟲穩定性**：執行不同 `keywords` 組合並查看 `SCRAPER_TEST_PLAN.md` 指標。

---
*OpenClaw Optimized Guide - Role: QA*
