# Linkora 2.0 - Agent Skill Book (OpenClaw / Developer Guide)

This guide is optimized for AI agents to quickly understand Linkora 2.0 and avoid excessive token consumption.

---

## 🏗️ Project Architecture

### Backend (Python/FastAPI)
- **Framework**: FastAPI (Asynchronous API).
- **ORM**: SQLAlchemy 2.0.
- **Database**: SQLite (Development) / PostgreSQL (Production).
- **Auth**: JWT (JSON Web Tokens) with a custom `require_role` dependency factory.
- **Task Control**: Native Python `threading` for background scraping tasks.

### Frontend (TypeScript/React)
- **Bundler**: Vite (Fast HMR).
- **Router**: React Router v6.
- **State**: React Context API (`AuthContext`) for auth and globals.
- **Styling**: Tailwind CSS (Utility-first).
- **API**: Centralized `fetchWithAuth` wrapper in `api.ts`.

---

## 🧩 Key Components & Services

### Shared Frontend Components
- **RoleGuard**: Protects routes based on `user.role`.
- **Sidebar**: Dynamic navigation based on role.
- **Stats Card**: Reusable card with HSL gradients for the dashboard.
- **Accordion History**: Expansion cards for `ScrapeTasks`.

### Backend Services
- **Auth Service**: Password hashing (bcrypt) and Token generation.
- **Scraper Service**: `manufacturer_miner.py` (AI-enhanced) and `scrape_simple.py`.
- **Tracker Service**: `email_tracker.py` computes engagement rates.

---

## 💾 Database Schema (Detailed)

### `users` (Core Auth)
- `id`: PK
- `email`: Unique login
- `password_hash`: Bcrypt
- `role`: 'admin', 'vendor', 'member'
- `vendor_id`: FK(users.id), links members to their vendor organization.

### `vendors` (Business Config)
- `id`: PK
- `user_id`: FK(users.id, unique), links to the vendor user account.
- `company_name`: Vendor company name.
- `pricing_config`: JSON (Wholesale price per lead, e.g., `{"per_lead": 50}`).

### `leads` (Scraped Data)
- `id`: PK
- `user_id`: FK(users.id), owner of the lead.
- `company_name`, `website_url`, `contact_email`: Core data.
- `ai_tag`: Industry classification.
- `status`: 'Scraped', 'Contacted', etc.

### `scrape_tasks` (Job Tracking)
- `id`: PK
- `user_id`: FK(users.id)
- `market`, `keywords`, `miner_mode`: Job parameters.
- `status`: 'Running', 'Completed', 'Failed'.
- `leads_found`: Count of leads generated.

### `email_logs` (Engagement)
- `id`: PK
- `user_id`: FK(users.id)
- `log_uuid`: Unique ID for tracking pixel.
- `opened`, `clicked`, `replied`: Tracking booleans.
- `sent_at`: Timestamp.

---

## 📂 Critical Paths (Token-Saving)
Instead of reading the whole tree, focus on these files:
- **API Mapping**: `frontend/src/services/api.ts` (Single source of truth for all BE calls).
- **Database Schema**: `backend/models.py` (Refer to this for any DB changes).
- **Business Logic**: `backend/main.py` (All endpoints and filtering logic).
- **RBAC Logic**: `backend/auth.py` and `frontend/src/components/RoleGuard.tsx`.
- **Scraper Core**: `backend/scrape_simple.py` and `backend/manufacturer_miner.py`.

---

## 🛠️ Development Rules

### 1. Backend Standards
- **Endpoint Protection**: Always use `Depends(require_role([...]))` for any business logic.
- **Models**: Use `to_dict()` method in SQLAlchemy models for JSON responses.
- **Migrations**: Add new tables to `backend/migrations.py` to ensure auto-migration in Docker.

### 2. Frontend Standards
- **Styling**: Strictly **Tailwind CSS**. Use glassmorphism (`glass-panel`) and `input-field` architecture.
- **Aesthetics**: Premium, high-contrast dark theme with consistent HSL gradients.
- **Naming**: Use Professional/Precision terminology (e.g., '精準開發雷達', '智慧行銷劇本').
- **Icons**: Use `lucide-react`.
- **Feedback**: Always use `react-hot-toast` for async operations.

### 3. New Advanced Features (Linkora v2.0+)
- **精準開發雷達 (Keyword Token System)**：在 `LeadEngine.tsx` 中，關鍵字以互動式權杖 (Chips) 形式管理，支援多組關鍵字聯動探勘與 AI 聯想建議。
- **系統控制中心 (System Hub)**：集中管理 API 金鑰 (OpenAI, Hunter.io, Google) 與系統變數映射。僅限 `admin` 使用。
- **變數映射 (Variable Mapping)**：使用 `SystemSetting` 儲存技術變數與顯示標籤的對應關係。
- **發信通道 (SMTP)**：採用分組式、圖示化配置介面，提升認證設定的直覺性。

---

## 💰 Resource & Billing Logic
- **Vendors** are outsourcing shops. They pay Linkora based on usage.
- **Billing Query**: Check `GET /api/engagements` in `main.py`. 
- **Calculation**: Lead Count * Vendor Price (from `vendors.pricing_config`).

---

## 🚀 Quick Execution
- **Local Dev**: `npm run dev` (Frontend), `uvicorn main:app --reload` (Backend).
- **Docker**: `docker-compose up --build`.
- **Init DB**: `POST /api/init-db` to create new tables like `system_settings`.

---
**Note for AI Agent**: Do not re-scan `node_modules` or `dist`. Stick to the logical files mentioned above to save context window.
