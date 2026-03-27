## Database Engine: PostgreSQL Only (v3.1.8)

As of version 3.1.8, **SQLite is officially deprecated and unsupported**. The system strictly requires a PostgreSQL instance.

### 🧬 Connectivity & SSL
- **Force SSL**: All remote connections (specifically those on `render.com`) are forced to use `sslmode=require`.
- **Driver**: Using `postgresql://` (SQLAlchemy 2.0+ compatible).

### 🚀 Schema Isolation (Multi-Tenancy)
The system uses PostgreSQL Schemas for environment isolation:
- **`public`**: Production environment.
- **`uat`**: Staging/User Acceptance Testing.
- Switching is controlled by the `APP_ENV` environment variable.

### 🛡️ Settings Persistence & Fallback
To prevent configuration loss during user sessions or infrastructure restarts:
- **User 1 Fallback**: If a user's `system_settings` (API Keys, etc.) are missing, the API automatically retrieves settings from **User ID 1 (Primary Admin)**.
- **Table**: `system_settings` stores JSON blobs.

---

## Tables

### users
用戶帳號表 (PostgreSQL)

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| email | VARCHAR(255) | Unique email |
| ... | ... | ... |

### global_leads (Isolation Pool)
全域中心化情報池，用於跨使用者去重與資料共享。

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| domain | VARCHAR(255) | Unique domain (Primary Key for deduplication) |
| ... | ... | ... |
| global_id | INT | Link from private `leads` table |

---

## Migration & Initialization
The `database.py` script automatically ensures the required schema exists before performing `create_all()`.
EXT (JSON) | Optional structured data |
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
