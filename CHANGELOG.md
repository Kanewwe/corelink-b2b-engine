# 📝 Linkora 更新日誌 (Changelog)

本文件紀錄了 Linkora 平台從初始版本至今的開發歷程、功能迭代與錯誤修復。

---

## [v3.1.8-resilience] - 2026-03-27
### 🏭 製造商引擎重構 (Engine Resilience)
- **核心升級**：全面升級至 `zen-studio` 爬蟲驅動，支援深度抓取與更好的反爬繞過。
- **防卡死保護**：實作 180s 任務強制超時，徹底解決背景探勘任務「卡死」的問題。
- **Email Guessing 2.0**：新增基於網域的自動前綴猜測機制，大幅提升製造商 Lead 的聯繫資訊獲取率。
- **資料庫穩定性**：全面轉向 PostgreSQL 並實作 SSL 強制連線，確保數據在雲端環境的持久性。

## [v2.7.2-localization] - 2026-03-27
- 🌏 **時區本地化**：後端統一採用台灣時區 (UTC+8) 進行日誌記錄與儀表板統計。
- 📊 **成效漏斗優化**：修復開信與點擊統計在跨月份時的計算誤差。

## [v2.7.1-isolation] - 2026-03-26
- 🛡️ **全域隔離池 (Global Isolation Pool)**：實作跨用戶去重邏輯，節省探勘與 AI API 呼叫成本。
- 🧬 **探勘智控**：智能判斷情報庫存量，若資料充足則優先從全域池同步，不重複發動外部探勘。

## [v2.7.0-linkora-pro] - 2026-03-26
- 🎨 **Pro 視覺標準**：導入 `bg-glass-panel` 毛玻璃高質感深色模式。
- ⚙️ **系統控制中心**：全新 `admin` 專屬管理後台，集成 API Key 管理與變數映射。
- 🏷️ **中文化標籤映射**：支援將工程變數（如 `{{company_name}}`）映射為親切的中文標籤。
- 📧 **SMTP 配置優化**：圖像化配置分組，修復佈局切斷。

## [v2.5-postgresql-sync] - 2026-03-26
### 🚀 PostgreSQL Migration & Environment Isolation
- **Database Migration**: Fully migrated from SQLite to PostgreSQL on Render.
- **Schema-based Isolation**: Implemented `public` (PRD) and `uat` (UAT) schema switching via `APP_ENV`.
- **Auth Unification**: Updated `auth.py` and `main.py` to support both Bearer tokens and Session cookies.
- **Initialization**: Automated schema and table creation in `init_db`.

## [v2.4-stabilization] - 2026-03-25
- ⚙️ 新增「系統控制中心 (System Hub)」，集中管理 API 金鑰。
- 🏷️ 變數映射功能正式遷移至系統控制中心。
- 🎨 全站 UI/UX 升級為 Linkora Pro「玻璃面板」視覺標準。
- 🛠️ 修復 SMTP 佈局切斷與 Autofill 視覺異常問題。

## [v2.2-manufacturer] - 2026-03-24
- 🏭 新增「製造商模式」爬蟲（Thomasnet + Bing + Google CSE）。
- 🔄 Google CSE 400 時自動切換 Bing 備援。
- 🔑 Thomasnet 整合 ScraperAPI 繞過封鎖。
- 🗄️ `migrations.py` 嵌入 FastAPI `lifespan`，確保資料庫欄位自動補齊。

## [v2.1-fixes] - 2026-03-23
- 🐛 修復登入時 Session ID 未寫入 Cookie 導致狀態失效的嚴重問題。
- ✨ 新增後台「登出」按鈕與清除狀態流程。
- 💎 全站定價轉換為台幣（TWD），並統一前後端方案規格。

## [v2.0-optimized] - 2026-03-23
- ✨ Linkora 品牌重塑與新 UI 設計（Dark SaaS 質感）。
- ✨ Monaco Editor 整合與 AI 關鍵字生成。
- ✨ Email 追蹤系統與訂閱系統基礎架構。

## [v1.0] - 2026-03-21
- 初始版本：基本爬蟲、Email 發現、AI 開發信生成。

---
*Created by Antigravity AI - Document Cleanup Task*