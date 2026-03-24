# Changelog - Linkora B2B Outreach Platform

All notable changes to this project will be documented in this file.

## [v2.2-manufacturer] - 2026-03-24

### 🏭 New: Manufacturer Mode (B2B Sourcing Engine)
- **New file** `manufacturer_miner.py`: Multi-source B2B manufacturer scraper
  - Google Custom Search API (primary)
  - Bing Search (automatic fallback when Google CSE fails)
  - Thomasnet via ScraperAPI (US B2B directory)
- **Query expansion**: Keywords like `car battery` automatically expanded to B2B variants (`OEM supplier factory`, `manufacturer small medium enterprise`, etc.)
- **Frontend toggle**: Added Mining Mode selector to Auto-Miner panel (Manufacturer Mode / Yellowpages Mode)
- **API**: `POST /api/scrape-simple` now accepts `miner_mode` field (`"manufacturer"` or `"yellowpages"`)

### 🗄️ Database Migration Reliability Fix
- `migrations.py`: Upgraded to "force-alter" strategy — directly attempts `ALTER TABLE ADD COLUMN` and gracefully ignores "already exists" errors. Added verbose diagnostic logs.
- `main.py` `lifespan()`: Now calls `run_migrations()` on every app startup, bypassing `start.sh` execution issues.

### 🚀 Deployment Fixes
- `start.sh`: Correctly binds to `${PORT}` env var (required by Render)
- ScraperAPI integrated in Thomasnet scraper to bypass 403 blocks

---

## [v2.0-optimized] - 2026-03-23

### 🚀 New Features

#### Brand & UI Redesign
- **Brand Rename**: Corelink → Linkora
- **New Logo**: Connected node icon design
- **Color System**: Dark SaaS style (Linear/Vercel inspired)
  - Primary: `#4F8EF7` (Brand Blue)
  - Accent: `#6EE7B7` (Mint Green)
  - Background: `#0F1117` / `#161B27`
- **Sidebar Redesign**: SVG icons, user avatar section
- **Page Transitions**: 150ms fade-in animation

#### Auto-Miner (Lead Engine)
- **AI Keyword Generator**: Generate 5 related part-focused keywords
- **Multi-Keyword Scraping**: Scrapes multiple keywords in sequence
- **Yellowpages integration**: With ScraperAPI premium bypass for geo-blocked regions

#### Email Finder
- **3-Layer Strategy v2**:
  - Layer 1: Website scraping (mailto, regex, meta tags)
  - Layer 2: Pattern guess + SMTP verify (ports 587/465/25)
  - Layer 3: Google Custom Search API
- **Bug Fixes**:
  - EMAIL_REGEX double-escape fixed
  - SMTP ports (587/465/25 fallback)
  - Catch-all detection
  - Real browser User-Agent rotation
  - Global 30s timeout protection

#### Email Tracking System
- **New Model**: `EmailLog` with full engagement tracking
- **Tracking Pixel**: `/track/open?id=xxx`
- **Click Redirect**: `/track/click?id=xxx&url=yyy`
- **漏斗分析**: Sent → Delivered → Opened → Clicked → Replied

#### Subscription System
- **New Models**:
  - `Plan`: Plan definitions (Free/Pro/Enterprise)
  - `User`: User accounts with bcrypt passwords
  - `Session`: Session-based auth (UUID)
  - `Subscription`: Subscription records
  - `UsageLog`: Monthly usage tracking
- **Auth Endpoints**:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
  - `GET /api/auth/me`
  - `GET /api/plans`
  - `GET /api/subscription`
- **Permission System**:
  - Feature flags per plan
  - Usage limits per month
  - `check_feature()` dependency
  - `check_usage_limit()` dependency

#### Template System v2
- **Monaco Editor**: Syntax highlighting, line numbers, auto-indent
- **3 Tabs**: Create/Edit, Existing Templates, Attachments
- **AI Generation**: Prompt → GPT → HTML
- **Split View**: Editor + Live Preview
- **Variable Chips**: Click to insert `{{company_name}}`, etc.
- **Test Email**: Send to own email

### 📈 Performance Improvements
- Rule-based classification (saves GPT tokens)
- DNS MX verification (free email validation)
- Background tasks (non-blocking)
- Deduplication mechanism

### 🐛 Bug Fixes
- Session token authentication
- Template view visibility (duplicate elements removed)
- SMTP verification ports
- Google search rate limiting
- Page scroll support

### 📦 Dependencies Added
- `bcrypt==4.1.2` - Password hashing
- `httpx==0.25.0` - Async HTTP client
- `dnspython==2.6.1` - DNS resolution
- `beautifulsoup4==4.12.2` - HTML parsing

---

## [v1.0] - 2026-03-21

### Initial Release
- Basic scraper (Yahoo search dorking)
- Email finder (MX verification)
- AI classification (GPT-4o-mini)
- Email template system
- SMTP scheduler
- Basic frontend

---

## Migration Notes

### v1.0 → v2.0

#### Database Changes
```sql
-- Add user_id to existing tables
ALTER TABLE leads ADD COLUMN user_id INT;
ALTER TABLE email_campaigns ADD COLUMN user_id INT;
ALTER TABLE email_templates ADD COLUMN user_id INT;
ALTER TABLE email_logs ADD COLUMN user_id INT;

-- Create new tables
CREATE TABLE plans (...);
CREATE TABLE users (...);
CREATE TABLE sessions (...);
CREATE TABLE subscriptions (...);
CREATE TABLE usage_logs (...);
```

#### API Changes
- Old: `Authorization: Bearer <token>` header
- New: `Cookie: session_id=<uuid>`

#### Environment Variables
```bash
# New required variables
APP_BASE_URL=https://linkoratw.com

# Optional (for Email Finder Layer 3)
GOOGLE_API_KEY=xxx
GOOGLE_CSE_ID=xxx
```
