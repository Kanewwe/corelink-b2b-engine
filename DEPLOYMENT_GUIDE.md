# Deployment Guide - Linkora B2B Engine

This guide describes the professional deployment workflow for Linkora V2, utilizing branch-based environment isolation on Render.

## 🏗️ Architecture Overview

| Environment | Branch | Purpose | URL |
|-------------|--------|---------|-----|
| **UAT (Staging)** | `uat` | Feature testing & verification | [linkora-frontend-uat.onrender.com](https://linkora-frontend-uat.onrender.com) |
| **Production** | `prd` | Live system for users | [linkora-frontend.onrender.com](https://linkora-frontend.onrender.com) |

---

## 🚀 Deployment Workflow

### 1. Development & Staging (UAT)
All new features, bug fixes, and configuration changes must be pushed to the `uat` branch first.

```bash
# Push changes to STAGING
git add .
git commit -m "feat: your change"
git push origin uat
```
Render will automatically detect the push to `uat` and redeploy the **UAT Services**.

### 2. Mandatory Verification
Perform full end-to-end testing on the **UAT URL**. Confirm that:
- Authentication works as expected.
- Emails generate and send correctly.
- Scraper operates without errors.

> [!IMPORTANT]
> **Strict Rule**: You must obtain explicit user approval after UAT verification before proceeding to the next step.
> **DBA Rule**: If the deployment includes database changes, the DBA must perform the verification on Render Shell before final approval.

### 3. Promotion to Production (PRD)
Once UAT is verified and approved, promote the changes to the `prd` branch using the provided sync script.

```powershell
# Using the sync script (Windows)
./scripts/sync.ps1 -Action deploy
```
*This command merges `uat` into `prd` and pushes to the remote repository, triggering the **Production Services** redeploy on Render.*

---

## 🔧 Render Configuration (Blueprint)

The infrastructure is managed via `render.yaml`. 

### Key Services:
- **`linkora-backend`**: Production API (tracks `prd`).
- **`linkora-backend-uat`**: Staging API (tracks `uat`).
- **`linkora-frontend`**: Production Web (tracks `prd`).
- **`linkora-frontend-uat`**: Staging Web (tracks `uat`).

### Environment Variables:
Ensure the following variables are consistent across both sets of services:
- `DATABASE_URL`: Connection string to the PostgreSQL instance.
- `OPENAI_API_KEY`: GPT-4o-mini access.
- `ALLOWED_ORIGINS`: Set to `*` or specific frontend URLs.
- `PORT`: Must be set to `10000`.

---

## 🗄️ Database Verification (DBA SOP)
If the deployment contains **Database Schema Migrations**, the DBA must execute the following checks on the **Render Dashboard -> Shell**:

### 1. Verification Commands
Use `psql` (automatically connected in Render Shell) to verify table structures:

```sql
-- Check ScrapeLog for Health Monitoring (v3.4)
\d+ scrape_logs;
-- Expect: response_time (FLOAT), http_status (INT) columns exist.

-- Check TransactionLog for Billing (v3.5)
\d+ transaction_logs;
-- Expect: Table exists with user_id, action_type, point_delta.
```

### 2. Post-Migration Audit
1.  Check **Backend Logs** for `[System] Database schema check completed`.
2.  Update **[Migration Log](file:///Users/borenxiao/corelink-b2b-engine/docs/process/MIGRATION_LOG.md)** with the verification timestamp and DBA name.

---

## ⚙️ Post-Deployment Initialization
After successfully deploying to a new environment, the Administrator should:
1. Log in with admin credentials.
2. Navigate to **系統控制中心 (System Hub)**.
3. Configure the following required API Keys:
   - `openai_key` (Required for AI features).
   - `hunter_key` (Optional, for advanced email discovery).
   - `google_cse_id` & `google_api_key` (Optional, for better search results).
4. Save the configuration to ensure the Lead Engine is fully operational.

---

## 🛠️ Maintenance Commands

- **Pull latest metadata**: `./scripts/sync.ps1 -Action pull`
- **Check UAT Status**: Use Render Dashboard to monitor `linkora-backend-uat` logs.

---
**Linkora** - AI B2B Outreach System 🚀
