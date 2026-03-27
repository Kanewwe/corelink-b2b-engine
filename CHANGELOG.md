## [v3.2.0] - 2026-03-27

### 🔴 Critical Security Fix: 用量配額漏洞修復

#### 問題描述
- 爬蟲 (`scrape_simple.py`, `manufacturer_miner.py`) 新增 Lead 時未計算用量
- Member 可以透過爬蟲無限探勘，繞過配額限制
- 全域池同步也未計入配額

#### 修復內容
- **配額檢查**: 爬蟲開始前呼叫 `check_user_quota()` 檢查剩餘配額
- **即時追蹤**: 爬取過程中即時檢查是否超過配額
- **用量計算**: 新增 Lead 後呼叫 `increment_usage("customers_count")`
- **同步計入**: 全域池同步也算使用量（業務決策）

### 📁 修改檔案
- `backend/auth.py` - 新增 `check_user_quota()` 函式
- `backend/scrape_simple.py` - 用量檢查 + 計算
- `backend/manufacturer_miner.py` - 用量檢查 + 計算

---

## [v3.1.9] - 2026-03-27

### 🐛 Critical Bug Fixes (全域池 / 私域池 / 時區)

#### 全域池修復
- **BUG-1**: `clear_global_pool` 現在會先清除私域 `global_id` 引用，避免 FK 懸空
- **BUG-2**: `domain` 空字串正規化為 `None`，避免 unique constraint 問題
- **BUG-3**: Proposal 通過後同步更新所有私域 Lead (只更新未被個人覆寫的)
- **BUG-4**: `company_name` 改用 `ilike` 做模糊比對，減少重複資料
- **BUG-5**: Email Guessing 結果只存到 `email_candidates`，不污染全域池 `contact_email`
- **BUG-6**: `save_to_global_pool` 更新時補足 `industry_taxonomy`

#### 時區修復
- **TZ-1**: `UsageLog.get_or_create` 使用台灣時間計算年月，確保用量週期正確
- **TZ-2**: API 回傳時間改用 ISO format 帶時區，讓前端處理本地化
- 新增 `timezone_utils.py` 統一時間處理

### 📁 新增檔案
- `backend/timezone_utils.py` - 時區工具函式

### 🔧 修改檔案
- `backend/scrape_utils.py` - 全域池同步邏輯修復
- `backend/manufacturer_miner.py` - Email Guessing 標記來源
- `backend/models.py` - 時區統一處理
- `backend/main.py` - 清空全域池 + Proposal 同步 + 時區修復

---

## [v3.1.8] - 2026-03-27

### 🛡️ Engine Resilience & Accuracy
- **Modernized Scraper**: Switched to `zen-studio/thomasnet-suppliers-scraper` for superior B2B data extraction.
- **Hang Protection**: Implemented 180s execution timeouts for all external crawler calls to prevent background process hangs.
- **Email Discovery 2.0**: Added automated **Prefix Guessing** (`info@`, `sales@`, etc.) when direct email extraction fails, increasing manufacturer lead capture rates.
- **Improved Logging**: Optimized heartbeat frequency (every 5 items) for better real-time monitoring without log bloat.

### 🧬 Infrastructure Stabilization
- **PostgreSQL Enforcement**: Officially deprecated SQLite and enforced strict PostgreSQL connectivity with SSL requirements.
- **Settings Persistence**: Implemented User ID 1 fallback for system settings to guarantee configuration availability across admin accounts.
- **Indentation & Whitespace Fixes**: Resolved critical `IndentationError` in `database.py` that caused deployment failures.

## [v3.0.0] - 2026-03-27

### 🧠 Shared Lead Intelligence (Dual-Layer Data Model)
- **Dual-Layer Architecture**: Separation of **Canonical Facts** (shared corporate data) and **User Overlays** (personal overrides, notes, tags).
- **Personal Overrides**: Users can now modify company names, emails, and notes without affecting the global database.
- **Global Proposals**: Implemented a crowd-sourced data quality system where users suggest corrections to shared data.
- **Admin Resolution**: Dedicated interface for administrators to approve/reject data proposals and verify global facts.

### 🎨 UI/UX Revolution
- **Lead Detail Drawer**: A high-speed flyout panel for managing individual lead intelligence and overrides.
- **Intelligence Hub**: Rebranded System Settings with real-time stats, sync rules, and proposal management.
- **Data Provenance Badges**: Visual indicators (Global vs Personal) to clarify data accuracy and source.

### 🛠️ Core Engine
- **Atomic Synchronization**: Scrapers now automatically link to `global_id` and respect the dual-layer boundaries.
- **Smart Merging**: Backend `to_dict` logic dynamically merges canonical and personal layers (Priority: Personal > Global).

## [v2.7.1] - 2026-03-26

### 🚀 全域探勘隔離池 (Global Lead Pool) 與 系統控管中心
- **Global Lead Pool**: 實作 `GlobalLead` 模型，支援跨使用者的高品質名單同步，大幅降低 API 探勘成本。
- **System Settings Hub**: 開放「一般 (General)」設定分頁，提供全域池統計、同步開關與資料維護（清空池）功能。
- **UI 視覺化提示**: 在客戶列表中新增 `GLOBAL SYNC` 與 `LIVE SCRAPE` 標記，提升資料來源透明度。
- **工業級產業分類**: 整合 v2.7 產業 Taxonomy，優化 AI 標籤精準度與自動分類規則。
- **Scraper 智慧同步**: 採集重構，支援根據系統設定決定是否與全域池進行同步。

### 🛠️ 技術優化
- **API 擴展**: 新增 `/api/admin/global-pool/stats` 與 `/api/admin/global-pool/clear` 端點。
- **配置效能**: 優化 `config_utils` 讀取邏輯，支援 `general_settings` 階層式覆蓋。
- **TypeScript 強化**: 修復前端型別定義，減少隱含 `any` 造成的潛在風險。

## [v2.5-postgresql-sync] - 2026-03-26

### 🚀 PostgreSQL Migration & Environment Isolation
- **Database Migration**: Fully migrated from SQLite to PostgreSQL on Render.
- **Schema-based Isolation**: Implemented `public` (PRD) and `uat` (UAT) schema switching via `APP_ENV`.
- **Auth Unification**: Updated `auth.py` and `main.py` to support both Bearer tokens and Session cookies.
- **Initialization**: Automated schema and table creation in `init_db`.

### 📚 New Documentation
- **[DATABASE_ENV.md]**: Guide for environment management and schema switching.
- **[DEVELOPMENT_WORKFLOW.md]**: Formalized UAT-to-PRD release and migration process.
- **[RENDER_SETUP_GUIDE.md]**: Technical insights on Render API and Postgres setup.

## [v2.4-stabilization] - 2026-03-25

### 🚀 Formalized Deployment Lifecycle
- **Dual Environments**: Established dedicated **UAT (Staging)** and **PRD (Production)** services on Render.
- **UAT-First Policy**: Mandatory verification in UAT before promoting any code to Production.
- **Render Blueprints**: Updated `render.yaml` to manage both environments with branch isolation (`uat` vs `prd`).
- **Sync Script**: Introduced `./scripts/sync.ps1` for automated staging and production deployment.

### 🐛 Critical Bug Fixes & Stability
- **Authentication**: Resolved `AuthContext` race condition where users were redirected to login before the session was fully initialized.
- **SMTP & Templates**: Implemented functional backend handlers for `/api/settings/smtp` and `/api/templates`.
- **System Health**: Added `/api/health` endpoint for Render health monitoring.
- **Code Fix**: Resolved `NameError` in `main.py` by fixing forward references for authentication dependencies.

### 🛠️ Infrastructure
- **Region Optimization**: Moved UAT services to `oregon` to match database region for lower latency.
- **Port Mapping**: Corrected Docker port binding for Render (`PORT=10000`).

---

## [v2.3-ux-redesign] - 2026-03-24

### 🎨 Major UX Redesign

#### Navigation
- **Grouped Sidebar**: 主要功能 / 寄信作業 / 分析 / 設定
- **Removed**: 新增客戶 nav item (整合進 Lead Engine)

#### Lead Engine
- **Email Strategy + Mining Mode**: Moved BEFORE CTA button
- **Empty State**: 引導文字 + 手動新增按鈕
- **Filter Bar**: 只在有客戶時顯示
- **Batch Operations**: 全選、補找 Email、批次寄信、批次刪除
- **Missing Email Warning**: 「X 筆尚未找到 Email」提示

#### Email Templates
- **Default Tab**: 改為「現有模板」列表
- **HTML Editor**: min-height 400px
- **Pill Toggle**: 語言風格/信件語言改為 Pill 按鈕
- **Variable Preview**: 寄信前預覽變數替換結果
- **Toast Notifications**: 儲存成功通知

#### Campaign Logs (寄信記錄)
- **SMTP Warning Card**: 未設定時顯示警告 + CTA
- **Status Badges**: 已送出/已開信/已點擊/退信
- **Batch Operations**: 批次重寄、批次刪除

#### Engagements (觸及率)
- **Removed**: 收費標準設定區塊
- **KPI Row**: 寄出總數/開信率/點擊率/退信率
- **Industry Stats**: 各行業統計
- **Individual Tracking**: 個別追蹤記錄

#### Search Logs → 探勘歷史
- **Renamed**: 搜尋記錄 → 探勘歷史
- **Collapsible System Logs**: 系統日誌預設折疊

#### SMTP Settings
- **Single Button**: 排程按鈕改為單一狀態顯示

### 🆕 New API Endpoints

```
POST /api/leads/{lead_id}/find-email     # 單一客戶補找 Email
POST /api/leads/batch-find-emails        # 批次補找 Email
```

### 🗄️ Database Changes

```sql
ALTER TABLE leads ADD COLUMN email_source VARCHAR(50);  -- Email 來源記錄
```

### 🐛 Bug Fixes
- JavaScript syntax error (missing function opening brace)
- Duplicate view sections in HTML
- Navigation click handlers not working
- Template fetch error handling (empty array vs error)

---

## [v2.2-manufacturer] - 2026-03-24

### 🏭 New: Manufacturer Mode (B2B Sourcing Engine)
- **New file** `manufacturer_miner.py`: Multi-source B2B manufacturer scraper
  - Google Custom Search API (primary)
  - Bing Search (automatic fallback when Google CSE fails)
  - Thomasnet via ScraperAPI (US B2B directory)
- **Query expansion**: Keywords like `car battery` automatically expanded to B2B variants
- **Frontend toggle**: Mining Mode selector (Manufacturer / Yellowpages)
- **API**: `POST /api/scrape-simple` accepts `miner_mode` field

### 🗄️ Database Migration Reliability Fix
- `migrations.py`: Force-alter strategy with graceful error handling
- `main.py` `lifespan()`: Auto-run migrations on startup

---

## [v2.0-optimized] - 2026-03-23

### 🚀 New Features

#### Brand & UI Redesign
- **Brand Rename**: Corelink → Linkora
- **New Logo**: Connected node icon design
- **Color System**: Dark SaaS style
- **Sidebar Redesign**: SVG icons, user avatar section

#### Auto-Miner (Lead Engine)
- **AI Keyword Generator**: Generate 5 related keywords
- **Multi-Keyword Scraping**: Sequential scraping
- **Yellowpages integration**: With ScraperAPI bypass

#### Email Finder
- **3-Layer Strategy**: Website → Pattern guess → Google CSE
- **Bug Fixes**: EMAIL_REGEX, SMTP ports, catch-all detection

#### Email Tracking System
- **Tracking Pixel**: `/track/open?id=xxx`
- **Click Redirect**: `/track/click?id=xxx&url=yyy`

#### Subscription System
- **Models**: Plan, User, Session, Subscription, UsageLog
- **Auth**: Session-based with bcrypt
- **Permission**: Feature flags + usage limits

#### Template System v2
- **Monaco Editor**: Syntax highlighting
- **AI Generation**: Prompt → GPT → HTML
- **Variable Chips**: Click to insert

---

## [v1.0] - 2026-03-21

### Initial Release
- Basic scraper (Yahoo search dorking)
- Email finder (MX verification)
- AI classification (GPT-4o-mini)
- Email template system
- SMTP scheduler

---

## Migration Notes

### v2.2 → v2.3

```sql
ALTER TABLE leads ADD COLUMN email_source VARCHAR(50);
```

### v1.0 → v2.0

```sql
ALTER TABLE leads ADD COLUMN user_id INT;
ALTER TABLE email_campaigns ADD COLUMN user_id INT;
ALTER TABLE email_templates ADD COLUMN user_id INT;
ALTER TABLE email_logs ADD COLUMN user_id INT;

CREATE TABLE plans (...);
CREATE TABLE users (...);
CREATE TABLE sessions (...);
CREATE TABLE subscriptions (...);
CREATE TABLE usage_logs (...);
```

#### API Changes
- Old: `Authorization: Bearer <token>`
- New: `Cookie: session_id=<uuid>`