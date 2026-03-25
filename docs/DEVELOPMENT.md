# Development Lifecycle - Linkora V2

This document defines the strict development standards and the lifecycle for Linkora V2. All team members (and agents) must adhere to these rules.

---

## 🔄 Standard Development Lifecycle

The lifecycle follows a **UAT-First** approach to maximize platform stability.

### Phase 1: Feature Development (Branch: `uat`)
- All code changes, new features, and bug fixes must be committed to the `uat` branch.
- Changes are pushed to GitHub: `git push origin uat`.
- Render automatically triggers a build for the **UAT Staging Services**.

### Phase 2: Mandatory UAT Verification
- Features must be tested end-to-end on the [UAT Staging Site](https://linkora-frontend-uat.onrender.com).
- Verification includes:
  - Database schema integrity (migrations).
  - Auth session stability.
  - SMTP connectivity.
  - Scraper bypass efficiency.

### Phase 3: User Approval (The Gatekeeper) 🛡️
- **CRITICAL**: Once UAT is verified, the developer must provide the results to the User.
- **Strict Rule**: Developers or agents are **NOT** permitted to propose or perform a Production (`prd`) deployment until the User has explicitly approved the changes on the UAT environment.

### Phase 4: Promotion to Production (Branch: `prd`)
- Only after obtaining User approval, the `uat` branch is merged into `prd`.
- Merge and Push: `git checkout prd` -> `git merge uat` -> `git push origin prd`.
- Render automatically updates the **Live Production Services**.

---

## 🛠️ Tooling & Automation

### Sync Script: `./scripts/sync.ps1`
A unified PowerShell script for managing environments:
- `-Action pull`: Pulls the latest changes from both branches.
- `-Action commit`: Consolidates local changes.
- `-Action deploy`: Automates the merging of `uat` into `prd` (requires clean state).

---

## 🧪 Coding Standards

- **FastAPI**: Ensure all new routes have a corresponding Pydantic schema for validation.
- **Monitoring**: Every major module should log its health status via `logger.add_log`.
- **Environment Isolation**: Never use production API keys in local dev without explicit permission. Use sandbox credentials in `uat`.

---
**Linkora** - Engineering Excellence 🚀📐
