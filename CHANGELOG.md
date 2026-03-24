# Changelog - Linkora B2B Outreach Platform

All notable changes to this project will be documented in this file.

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