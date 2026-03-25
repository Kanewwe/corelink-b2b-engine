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

## 🛠️ Maintenance Commands

- **Pull latest metadata**: `./scripts/sync.ps1 -Action pull`
- **Check UAT Status**: Use Render Dashboard to monitor `linkora-backend-uat` logs.

---
**Linkora** - AI B2B Outreach System 🚀
