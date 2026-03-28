---
name: Linkora v3.1.8 Engine Skill
description: Core technical instructions for managing and developing the Linkora B2B Lead Gen & Outreach platform.
---

# Linkora v3.1.8 Engine Skill

This skill is designed for AI agents to maintain and develop the Linkora v3.1.8 B2B platform efficiently.

---

## 🏗️ Project Architecture (v3.1.8)

### Backend (FastAPI)
- **Framework**: FastAPI (Async).
- **ORM**: SQLAlchemy 2.0.
- **Database**: **PostgreSQL Only** (SQLite is deprecated).
- **Auth**: **Session-based Cookies** (httponly).
- **Control**: APScheduler for background campaigns.

### Frontend (React/Vite)
- **Stack**: React 18, TypeScript, Tailwind CSS.
- **Theme**: Linkora Pro Glassmorphism.

---

## 🧩 Business Logic: Wholesale & Isolation
- **Role Isolation**: Schema-based (`uat` vs `public`).
- **Data Sync**: Global Lead Pool syncs with Private Lead Pool to reduce scraping costs.
- **Billing**: Vendor billing base on team-wide lead discovery.

---

## 💾 Database Schema (Critical Tables)
- `users`: `email`, `role`, `vendor_id`.
- `leads` / `global_leads`: Core discovery data.
- `system_settings`: The Hub for API Keys & mappings.

---

## 🚀 Role-based Documentation (Canonical)
- 🏗️ **Architecture**: `docs/sa/README.md`
- 📡 **API Specs**: `docs/bepg/API.md`
- 🤖 **Scraper Logic**: `docs/bepg/SCRAPER_DOCUMENTATION.md`
- 🛰️ **DevOps & Debug**: `docs/devops/README.md`
- 🧬 **DB & Schema**: `docs/dba/DATABASE_ENV.md`

## 🛠️ Automated Task Routing (LWE) & VCP Rule
When receiving a task, classify it and prioritize the corresponding guides:
1. **Bugfix Path** (Keywords: *fix, bug, error, fail*):
   - Check `docs/devops/SCRAPER_DEBUG_GUIDE.md` -> `docs/qa/ROLE_TEST_PLAN.md`.
2. **Feature Path** (Keywords: *add, new, feat, request*):
   - Check `docs/pm/ROADMAP.md` -> `docs/sa/ROLE_ARCHITECTURE.md` -> `docs/bepg/API.md`.
3. **Optimizing Path** (Keywords: *slow, optimization, refactor*):
   - Check `docs/dba/DATABASE.md` -> `docs/sa/README.md`.

---

## 📦 Mandatory Delivery Rule: VCP (Verify-Commit-Push)
Before declaring a task as **"Done"**, the Agent MUST:
1. **V (Verify)**: Run `./scripts/test.ps1` (or relevant logic test) and ensure zero errors.
2. **C (Commit)**: Prepare a detailed commit message reflecting the actual changes.
3. **P (Push)**: Execute the **`/commit`** workflow to push changes to the `uat` branch.
   - *Constraint*: ALL work must eventually reach the `uat` branch to be considered successful.

---

## 🧪 Testing & Standards
- **Local Dev**: Follow `docs/bepg/DEVELOPMENT_GUIDE.md`.
- **QA Standards**: Follow `docs/qa/README.md` (RBAC & Scraper stress tests).
- **Verification Script**: Always use `./scripts/test.ps1` for backend/sync checks.
- **Zero-Garbage Policy**: No temporary files in root or core folders.

---
*Created by Antigravity AI - System Optimization v3.1.8*
