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

## Core Tables

### users
用戶帳號表 (PostgreSQL)

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| email | VARCHAR(255) | Unique email |
| name | VARCHAR(100) | Display name |
| role | VARCHAR(20) | 'user' or 'admin' |
| is_active | BOOLEAN | Account status |

### leads
客戶名單表 (私有)

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INT | FK to users (Isolation) |
| global_id | INT | FK to global_leads (Link to Intelligence) |
| company_name | VARCHAR | Company name |
| domain | VARCHAR | Unique normalized domain |
| website_url | VARCHAR | Company website URL |
| email_candidates | VARCHAR | Comma-separated emails |
| contact_email | VARCHAR | Primary contact email |
| ai_tag | VARCHAR | Industry classification |
| extracted_keywords | TEXT | AI extracted keywords for the lead |
| scrape_location | TEXT | The source/geolocation of the scrape |
| status | VARCHAR | Scraped/Tagged/Sent/etc |

### global_leads (Isolation Pool)
全域中心化情報池，跨使用者共享高品質名單。

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| domain | VARCHAR(255) | Unique domain (Primary Key for deduplication) |
| company_name | VARCHAR(255) | Normalized company name |
| website_url | TEXT | Company website |
| contact_email | VARCHAR(255) | Extracted/Verified primary email |
| email_candidates | TEXT | List of possible emails (comma-separated) |
| ai_tag | VARCHAR(100) | Industry classification |
| extracted_keywords | TEXT | AI extracted keywords (Shared) |
| last_scraped_at | TIMESTAMP | Last update from any scraper |

### system_settings
系統與 API 金鑰設定表

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | INT | FK to users |
| key | VARCHAR(100) | Setting name (e.g., 'api_keys') |
| value | TEXT (JSON) | Setting values |

---

## Migration & Initialization
The `database.py` script automatically ensures the required schema exists before performing `create_all()`.

## Indexes

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_leads_user ON leads(user_id);
CREATE INDEX idx_leads_domain ON leads(domain);
CREATE INDEX idx_global_leads_domain ON global_leads(domain);
```

*Verified & Synchronized (v3.1.8)*
