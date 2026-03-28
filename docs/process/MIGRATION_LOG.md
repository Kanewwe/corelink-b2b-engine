# Linkora Database Migration & Audit Log

This document tracks all database schema changes (PostgreSQL). Every entry must be verified by a DBA on the **Render Dashboard Shell** as per the [VCP+ Protocol](file:///Users/borenxiao/corelink-b2b-engine/docs/process/BUSINESS_PROCESS.md).

## 🗄️ Migration History

| Version | Date | Description | Status | DBA Sign-off |
|---------|------|-------------|--------|--------------|
| **v3.4.0** | 2026-03-28 | Scraper Health Integration (response_time, http_status) | 🚀 Deployed | Pending |
| **v3.5.0** | 2026-03-28 | Billing Engine Foundation (transaction_logs table) | 🚀 Deployed | Pending |
| **v3.6.0** | 2026-03-28 | Security Hardening (CSP / API Origin Isolation) | 🚀 Deployed | ✅ Verified |
| **v3.7.0** | 2026-03-28 | Inbound Inbox & Delivery Telemetry (inbound_emails table) | 🚀 Deployed | Pending |

---

## 🔍 Verification Checklist (SOP)

For every migration marked as "Pending", the DBA must:
1.  **Login** to Render Dashboard.
2.  **Open Shell** for `linkora-backend-uat` (or `-prd`).
3.  **Command**: `\d+ table_name`
4.  **Confirm**: Columns/Indexes match the `migrate_vX_Y.py` code.
5.  **Log Results**: Update the "DBA Sign-off" column below.

---

## 📝 Change Details

### v3.4.0 / v3.5.0 (2026-03-28)
- **Target Table**: `scrape_logs`, `transaction_logs`
- **Key Fields**:
  - `scrape_logs.response_time`: float
  - `scrape_logs.http_status`: int
  - `transaction_logs`: New table for point system.
- **Migration Script**: `backend/migrate_v3_4.py`
- **Status Update**: Deployed to UAT via **Self-Healing Startup**.

---
*Created by Antigravity AI - DBA Audit System v3.5*
