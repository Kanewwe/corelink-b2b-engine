---
name: Linkora V2 Engine Skill
description: Core technical instructions for managing and developing the Linkora B2B Lead Gen & Outreach platform.
---

# Linkora V2 Engine Skill

This skill is designed for AI agents to maintain and develop the Linkora 2.0 B2B platform efficiently.

## 🏗️ Project Architecture

### Backend (FastAPI)
- **Framework**: FastAPI (Async).
- **ORM**: SQLAlchemy 2.0.
- **Auth**: JWT RBAC (Admin, Vendor, Member).
- **Core Files**: `backend/main.py` (API), `backend/models.py` (DB).

### Frontend (React/Vite)
- **Stack**: React 18, TypeScript, Tailwind CSS.
- **Auth**: `AuthContext.tsx` + `RoleGuard.tsx`.
- **API**: `frontend/src/services/api.ts` (Dynamic `fetchWithAuth`).

---

## 🧩 Business Logic: Wholesale Billing
- **Vendors** pay Linkora per Lead found by their team.
- **Aggregation**: Total Leads (Vendor + Members) * `vendor.pricing_config['per_lead']`.
- **Dashboard**: `Analytics.tsx` handles role-based financial views.

---

## 💾 Database Schema (Critical Tables)
- `users`: `email`, `role`, `vendor_id`.
- `vendors`: `user_id`, `company_name`, `pricing_config` (JSON).
- `leads`: `company_name`, `contact_email`, `status`, `user_id`.
- `scrape_tasks`: `keywords`, `status`, `leads_found`, `user_id`.
- `email_logs`: `log_uuid`, `opened`, `clicked`, `replied`, `user_id`.

---

## 📂 Search & Token Optimization
- **Do NOT read**: `node_modules`, `dist`, `.venv`.
- **Key Configs**: `render.yaml` (Production), `docker-compose.yml` (Local).
- **Styling**: Always use **Tailwind**. Icons: `lucide-react`.

---
## 🚀 Commands
- **Dev**: `npm run dev` / `uvicorn main:app --reload`.
- **Deploy**: Push to GitHub triggering Render auto-deploy.
