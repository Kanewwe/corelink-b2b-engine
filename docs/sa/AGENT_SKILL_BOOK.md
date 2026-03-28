# Linkora v3.1.8 - Agent Skill Book (AI Developer Guide)

This guide is optimized for AI agents to quickly understand Linkora’s modern architecture (v3.1.8) and avoid excessive token consumption.

---

## 🏗️ Core Architecture (v3.1.8)

### Backend (Python/FastAPI)
- **Framework**: FastAPI (Asynchronous).
- **ORM**: SQLAlchemy 2.0.
- **Database**: **PostgreSQL Only** (SQLite is deprecated).
- **Environment Isolation**: **Schema-based**. UAT uses `uat` schema; PRD uses `public`.
- **Auth**: **Session-based Cookies** (httponly). JWT is deprecated for Web UI.
- **Task Control**: `APScheduler` for background email campaigns and mining.

### Frontend (TypeScript/React)
- **Bundler**: Vite.
- **State**: React Context API (`AuthContext`).
- **Styling**: Tailwind CSS + Glassmorphism.
- **Editor**: Monaco Editor for AI Email Templates.

---

## 🧩 Key Service Logic

### 1. Scraper Service (`manufacturer_miner.py`)
- **Engine**: Zen-studio / Apify.
- **Resilience**: 180s hard timeout to prevent task hang.
- **Lead Discovery**: Four-stage method (Reservoir Check → Live Scrape → Enrichment → Persistence).

### 2. Auth Service (`auth.py`)
- **Session Management**: Uses `Session` table to track active users.
- **RBAC**: `Depends(require_role(["admin", "vendor", "member"]))`.

---

## 💾 Database Schema (v3.1.8 Summary)

### `users`
- `role`: 'admin', 'vendor', 'member'.
- `vendor_id`: FK to users.id (for member-vendor association).

### `leads` (Private) & `global_leads` (Public Intelligence)
- **Sync Logic**: Leads found via scraper are contributed to `global_leads` and cloned to user's `leads`.
- **Isolation**: Users only see leads where `leads.user_id == current_user.id`.

### `system_settings` (The Hub)
- Stores API Keys and Variable Mappings.
- **Fallback**: Member settings default to Admin (User ID 1) settings if not customized.

## 🛡️ Database Governance (Critical)
- **Source of Truth**: The `backend/migrations.py` script is the **ONLY** authorized way to modify the database schema.
- **Rule**: Never execute `ALTER TABLE` manually via SQL clients. Always add the column to the `tables_to_patch` dictionary in `migrations.py` and run the script.
- **Isolation**: Always check `APP_ENV` to ensure you are patching the correct schema (`uat` vs `public`).

---

## 🧪 Testing & Standards

## 📂 Critical Paths for AI Agents
- **API Definition**: `frontend/src/services/api.ts`.
- **Auth & Guard**: `frontend/src/components/RoleGuard.tsx`.
- **DB Models**: `backend/models.py`.
- **Main Entry**: `backend/main.py`.
- **Migration Logic**: `backend/migrations.py`.

---

## 🛠️ Performance & Token Saving Rules
1. **Never scan `node_modules` or `dist`**.
2. **Database First**: Always check `models.py` before proposing field changes.
3. **Schema Awareness**: Remember that `search_path` is set dynamically. Do not assume `public` schema for UAT data.

---
*Created by Antigravity AI - Optimized for Linkora v3.1.8*
