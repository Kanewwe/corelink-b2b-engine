# Linkora Database Schema

## Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    plans    │     │    users    │     │  sessions   │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id (PK)     │     │ id (PK)     │     │ id (PK)     │
│ name        │◄────│ plan_id (FK)│     │ user_id (FK)│
│ display_name│     │ email       │────►│ expires_at  │
│ price_*     │     │ password    │     │ created_at  │
│ max_*       │     │ name        │     └─────────────┘
│ feature_*   │     │ company_name│
└─────────────┘     │ role        │
                    │ is_active   │
        ▲           │ is_verified │
        │           └─────────────┘
        │                 │
        │                 │
        │     ┌───────────┴───────────┐
        │     │                       │
┌───────┴─────┴───────┐   ┌─────────┴────────┐    ┌──────────────────┐
│  subscriptions       │   │    usage_logs    │    │  system_settings │
├─────────────────────┤   ├──────────────────┤    ├──────────────────┤
│ id (PK)             │   │ id (PK)          │    │ id (PK)          │
│ user_id (FK)        │   │ user_id (FK)     │    │ user_id (FK)     │
│ plan_id (FK)        │   │ period_year      │    │ key (UNIQUE)     │
│ status              │   │ period_month     │    │ value (JSON)     │
│ billing_cycle       │   │ customers_count  │    └──────────────────┘
│ current_period_*    │   │ emails_sent_*    │
│ trial_*             │   │ autominer_*      │
│ payment_*          │   │ templates_*      │
└─────────────────────┘   └──────────────────┘

┌──────────────────────────────────────────────────────────┐
│                       leads                              │
├──────────────────────────────────────────────────────────┤
│ id (PK)                                                │
│ user_id (FK) ───────────► users.id                     │
│ company_name, website_url, domain                       │
│ email_candidates, ai_tag, status                        │
│ contact_*, address, phone                               │
│ source_domain, scrape_location                          │
└──────────────────────────────────────────────────────────┘
          │
          │ (1:N)
          ▼
┌─────────────────────┐     ┌─────────────────────────────┐
│  scrape_tasks       │     │      scrape_logs            │
├─────────────────────┤     ├─────────────────────────────┤
│ id (PK)            │     │ id (PK)                    │
│ user_id (FK)        │─────│ task_id (FK)               │
│ market, keywords    │     │ level (info/error)         │
│ miner_mode, status  │     │ message, created_at        │
└─────────────────────┘     └─────────────────────────────┘
```

## Tables

### plans
方案定義表

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(50) | Unique identifier ('free', 'pro', 'enterprise') |
| display_name | VARCHAR(100) | Display name |
| price_monthly | DECIMAL(10,2) | Monthly price |
| price_yearly | DECIMAL(10,2) | Yearly price |
| max_customers | INT | Customer limit (-1 = unlimited) |
| max_emails_month | INT | Email limit per month |
| max_templates | INT | Template limit |
| max_autominer_runs | INT | Auto-Miner runs per month |
| feature_* | BOOLEAN | Feature flags |
| is_active | BOOLEAN | Whether plan is available |

### users
用戶帳號表

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| email | VARCHAR(255) | Unique email |
| password_hash | VARCHAR(255) | bcrypt hash |
| name | VARCHAR(100) | Display name |
| company_name | VARCHAR(200) | Company name |
| role | VARCHAR(20) | 'user' or 'admin' |
| is_active | BOOLEAN | Account status |
| is_verified | BOOLEAN | Email verified |
| verify_token | VARCHAR(255) | Email verification token |
| reset_token | VARCHAR(255) | Password reset token |
| reset_expires | TIMESTAMP | Reset token expiry |
| last_login_at | TIMESTAMP | Last login time |
| created_at | TIMESTAMP | Creation time |

### sessions
登入 Session 表

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| user_id | INT | FK to users |
| ip_address | VARCHAR(45) | Client IP |
| user_agent | TEXT | Browser user agent |
| expires_at | TIMESTAMP | Session expiry |
| created_at | TIMESTAMP | Creation time |
| last_active_at | TIMESTAMP | Last activity |

### subscriptions
訂閱紀錄表

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INT | FK to users |
| plan_id | INT | FK to plans |
| status | VARCHAR(20) | active/cancelled/expired/trial |
| billing_cycle | VARCHAR(10) | monthly/yearly |
| current_period_start | TIMESTAMP | Current period start |
| current_period_end | TIMESTAMP | Current period end |
| trial_start | TIMESTAMP | Trial start |
| trial_end | TIMESTAMP | Trial end |
| payment_provider | VARCHAR(50) | stripe/ecpay/manual |
| payment_subscription_id | VARCHAR(255) | External subscription ID |
| cancelled_at | TIMESTAMP | Cancellation time |

### usage_logs
每月用量追蹤表

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INT | FK to users |
| period_year | INT | Year (e.g., 2026) |
| period_month | INT | Month (1-12) |
| customers_count | INT | Total customers |
| emails_sent_count | INT | Emails sent this month |
| autominer_runs_count | INT | Auto-Miner runs this month |
| templates_count | INT | Total templates |

**Unique constraint:** (user_id, period_year, period_month)

### leads
客戶名單表

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INT | FK to users |
| company_name | VARCHAR | Company name |
| website_url | VARCHAR | Website URL |
| domain | VARCHAR | Domain name |
| email_candidates | VARCHAR | Comma-separated emails |
| mx_valid | INT | MX validation result |
| description | TEXT | Company description |
| extracted_keywords | VARCHAR | AI extracted keywords |
| ai_tag | VARCHAR | Industry classification |
| status | VARCHAR | Scraped/Tagged/Sent/etc |
| assigned_bd | VARCHAR | Business developer |
| contact_name | VARCHAR | Contact person name |
| contact_role | VARCHAR | Contact role |
| contact_email | VARCHAR | Contact email |
| phone | VARCHAR | Phone number |
| address | VARCHAR | Street address |
| city | VARCHAR | City |
| state | VARCHAR | State/Province |
| zip_code | VARCHAR | Postal code |
| categories | VARCHAR | Business categories |
| source_domain | VARCHAR | Source website |
| scrape_location | VARCHAR | Scrape target location |
| employee_count | VARCHAR | Employee count estimate |
| revenue_range | VARCHAR | Revenue estimate |
| email_sent | BOOLEAN | Email sent flag |
| email_sent_at | TIMESTAMP | Email sent time |

### email_templates
信件模板表

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INT | FK to users |
| name | VARCHAR | Template name |
| tag | VARCHAR | Industry tag (NA-CABLE, etc) |
| subject | VARCHAR | Email subject line |
| body | TEXT | HTML email body |
| is_default | BOOLEAN | Default template flag |
| attachment_url | VARCHAR | Optional attachment URL |

### email_logs
Email 追蹤日誌表

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INT | FK to users |
| log_uuid | VARCHAR(36) | Unique tracking ID |
| lead_id | INT | FK to leads |
| template_id | INT | FK to templates |
| recipient | VARCHAR(255) | Recipient email |
| subject | VARCHAR(500) | Email subject |
| sent_at | TIMESTAMP | Send time |
| status | VARCHAR(50) | pending/delivered/bounce |
| opened | BOOLEAN | Has been opened |
| opened_at | TIMESTAMP | First open time |
| open_count | INT | Open count |
| clicked | BOOLEAN | Has been clicked |
| clicked_at | TIMESTAMP | First click time |
| click_count | INT | Click count |
| clicked_urls | JSON | Array of clicked URLs |
| replied | BOOLEAN | Has been replied |
| replied_at | TIMESTAMP | Reply time |
| reply_source | VARCHAR(50) | manual/imap/webhook |

### system_settings
系統與 API 金鑰設定表 (新增於 v2.6)

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INT | FK to users |
| key | VARCHAR(100) | Setting name (e.g., 'api_keys') |
| value | TEXT (JSON) | Setting values |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

### scrape_logs
爬蟲任務詳細日誌 (新增於 v2.6)

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| task_id | INT | FK to scrape_tasks |
| level | VARCHAR(20) | info, warning, success, error |
| message | TEXT | Log message |
| extra_data | TEXT (JSON) | Optional structured data |
| created_at | TIMESTAMP | Log time |

## Indexes

```sql
-- Users
CREATE INDEX idx_users_email ON users(email);

-- Sessions
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- Subscriptions
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- Leads
CREATE INDEX idx_leads_user ON leads(user_id);

-- Email Logs
CREATE INDEX idx_email_logs_uuid ON email_logs(log_uuid);

-- Scrape Logs
CREATE INDEX idx_scrape_logs_task ON scrape_logs(task_id);
```

## Deployment Environment Variables

| 設定 | 值 | 說明 |
|------|-----|------|
| **Name** | `linkora-api` (PRD) / `linkora-api-uat` (UAT) | 服務名稱 |
| **Region** | `oregon` (與資料庫同區) | 部署區域 |
| **Runtime** | `Docker` | 執行環境 |
| **Branch** | `prd` (正式) / `uat` (測試) | Git 分支對應 |
| `DATABASE_URL` | (from PostgreSQL) | PostgreSQL 連線字串 |
| `APP_ENV` | `production` 或 `uat` | 環境切換 (Schema 選項) |

*註：API Key 現在優先讀取資料庫中的 `system_settings`。*

## Migration from v1.0

```sql
-- 1. Add user_id to existing tables
ALTER TABLE leads ADD COLUMN user_id INT REFERENCES users(id);
ALTER TABLE email_campaigns ADD COLUMN user_id INT REFERENCES users(id);
ALTER TABLE email_templates ADD COLUMN user_id INT REFERENCES users(id);
ALTER TABLE email_logs ADD COLUMN user_id INT REFERENCES users(id);

-- 2. Create admin user
INSERT INTO users (email, password_hash, name, role, is_active, is_verified)
VALUES ('admin@linkoratw.com', '$2b$12$...', 'Admin', 'admin', true, true);

-- 3. Assign existing data to admin
UPDATE leads SET user_id = 1 WHERE user_id IS NULL;
UPDATE email_campaigns SET user_id = 1 WHERE user_id IS NULL;
UPDATE email_templates SET user_id = 1 WHERE user_id IS NULL;
UPDATE email_logs SET user_id = 1 WHERE user_id IS NULL;

-- 4. Add NOT NULL constraints
ALTER TABLE leads ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE email_campaigns ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE email_templates ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE email_logs ALTER COLUMN user_id SET NOT NULL;
```

## Migration to v2.6 (Database-First Config)

本專案已支援資料庫優先的 API Key 管理模式 (v2.6)。

### 手動填寫 API Key (直接 SQL 或透過 UI)
```sql
INSERT INTO system_settings (user_id, key, value)
VALUES (1, 'api_keys', '{"openai_key": "sk-...", "apify_token": "apify_...", "hunter_key": "...", "openai_model": "gpt-4o-mini"}');
```
