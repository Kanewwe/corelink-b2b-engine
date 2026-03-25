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
## 🚀 Standard Deployment Procedure (UAT -> PRD)
To maintain stability, follow this flow for all releases:

### 1. Deploy to UAT (Staging)
- All development and bug fixes must be committed to the `uat` branch first.
- **Push**: `git push origin uat`.
- Render staging environment will automatically build and deploy.

### 2. UAT Verification
- Verify all changes at the **UAT URL** (e.g., `linkora-v2-staging.onrender.com`).
- Check specifically for:
  - Auth redirects and session persistence.
  - SMTP connectivity with sandbox credentials.
  - Template rendering in the Monaco editor.

### 3. Promote to Production (PRD)
- Only after UAT is confirmed, merge `uat` into `prd`:
  ```bash
  git checkout prd
  git merge uat
  git push origin prd
  ```
- This triggers the final production deployment on Render.

---
## 🛠️ Commands (Workflow)
- **Sync Device**: `/pull` or `./scripts/sync.ps1 -Action pull`
- **Submit Work**: `/commit` or `./scripts/sync.ps1 -Action commit -Message "text"`
- **Staging Release**: `git push origin uat`
- **Production Release**: `./scripts/sync.ps1 -Action deploy` (Automates the merge & push to PRD)
---
## 🧪 Testing & Standards
- **Zero-Garbage Policy**: No temporary files in root or core folders.
- **Workflow**: Follow `docs/TESTING.md` before merging to **PRD**.
- **Standards**: Strictly follow `docs/DEVELOPMENT_STANDARDS.md`.
- **Render**: Deploys only from **PRD** branch.
