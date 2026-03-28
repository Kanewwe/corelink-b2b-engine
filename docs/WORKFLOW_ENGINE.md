# 🚀 Linkora 需求執行至驗收工作流 (LWE)

本文件定義了 Linkora v3.1.8 的自動化任務路由邏輯，將「輸入內容」轉化為「具體路徑」與「驗收標準」。

---

## 🧭 任務決策矩陣 (Task Decision Matrix)

當接收到一個新任務時，請根據以下關鍵字進行自動路由：

| 任務類型 (Scenario) | 識別關鍵字 (Keywords) | 啟動路徑 (Path) | 核心依賴 SOP |
| :--- | :--- | :--- | :--- |
| **🐞 錯誤修復** | `修復`, `Bug`, `500/404`, `失敗`, `不行` | **Path A: Bugfix** | `docs/devops/` & `docs/qa/` |
| **✨ 新功能開發** | `新增`, `開發`, `功能`, `擴充`, `想要` | **Path B: Feature** | `docs/sa/` & `docs/bepg/` |
| **⚙️ 系統優化** | `變慢`, `加速`, `優化`, `調整`, `重構` | **Path C: Optimizing** | `docs/dba/` & `docs/sa/` |
| **📊 業務決策** | `分析`, `成本`, `ROI`, `方案`, `會員` | **Path D: Business** | `docs/pm/` & `docs/business/` |

---

## 📈 執行到驗收之連鎖 (End-to-End Chains)

### Path A: BugfixChain (快速止血)
1. **[QA]**: 複現 Bug 並記錄於 Issue。參考 `docs/qa/ROLE_TEST_PLAN.md`。
2. **[DevOps]**: 若是爬蟲問題，先用 `docs/devops/SCRAPER_DEBUG_GUIDE.md` 搶救。
3. **[PG]**: 執行代碼修正。
4. **[Delivery]**: 執行 `./scripts/test.ps1` 驗證，成功後執行 `/commit` 推送到 `uat`。

### Path B: FeatureChain (標準開發)
1. **[PM]**: 確認需求優先級。參考 `docs/pm/ROADMAP.md`。
2. **[SA]**: 定義 DB Schema 與隔離權限。參考 `docs/sa/ROLE_ARCHITECTURE.md`。
3. **[PG]**: 分支開發 (`feat/*`)。參考 `docs/bepg/DEVELOPMENT_GUIDE.md`。
4. **[QA]**: 執行整合測試。
5. **[Delivery]**: 執行 `./scripts/test.ps1` 驗證，成功後執行 `/commit` 推送到 `uat`。

---

## ✅ 驗收標準定義 (Definition of Done)

- [ ] **[P0] 代碼已成功推送到 `uat` 分支。**
- [ ] **[P0] 執行 `./scripts/test.ps1` 且無報錯。**
- [ ] 符合 `docs/qa/` 定義的角色權限隔離測試。
- [ ] 若涉及資料庫變更，`docs/dba/` 的 `migrations.py` 已更新且成功運行。
- [ ] API 文件 `docs/bepg/API.md` 已同步最新規格。
- [ ] 經 PM 或 User 確認符合業務預期回報 (ROI)。

---
*Created by Antigravity AI - Efficiency Engine v3.1.8*
