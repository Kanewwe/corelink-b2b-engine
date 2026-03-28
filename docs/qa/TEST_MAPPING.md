# Linkora 業務功能與測試對照表 (TEST_MAPPING)

本文件將 `BUSINESS_PROCESS.md` 中的核心業務流程與對應的自動化/手動測試案例進行映射，確保功能穩定性。

> **版本：** 1.0.0 (v3.1.8 同步)

---

## 一、探勘引擎 (Prospecting Engine)

| 業務流程 | 測試案例 (Automated/Manual) | 狀態 | 來源文件 |
| :--- | :--- | :--- | :--- |
| **黃頁模式 (YP)** | `backend/tests/test_scraper_sync.py` (Mock Apify) | [x] | SYNC |
| **製造商模式 (MN)** | `backend/tests/test_scraper_sync.py` (Mock Thomasnet) | [x] | SYNC |
| **隔離池同步 (Global Sync)** | `backend/tests/test_scraper_sync.py` (Domain Lookup) | [x] | SYNC |
| **去重邏輯 (Dedupe)** | `backend/tests/test_scraper_sync.py` (Unique Domain) | [x] | SYNC |

---

## 二、多租戶隔離 (Multi-tenancy & Isolation)

| 業務流程 | 測試案例 (Automated/Manual) | 狀態 | 來源文件 |
| :--- | :--- | :--- | :--- |
| **Admin 存取權** | `backend/tests/test_rbac_isolation.py` (Full access) | [x] | RBAC |
| **Vendor 資料隔離** | `backend/tests/test_rbac_isolation.py` (Cross-Vendor check) | [x] | RBAC |
| **Member 方案限制** | `backend/tests/test_usage_limits.py` (429 Error) | [x] | LIMITS |

---

## 三、郵件行銷與追蹤 (Engagement & Tracking)

| 業務流程 | 測試案例 (Automated/Manual) | 狀態 | 來源文件 |
| :--- | :--- | :--- | :--- |
| **郵件 Log 生成** | `backend/tests/test_campaign_tracking.py` (Log count) | [x] | TRACKING |
| **開信點擊追蹤** | `backend/tests/test_campaign_tracking.py` (Status update) | [x] | TRACKING |
| **AI 郵件生成** | Manual: `/api/leads/{id}/generate-email` | [ ] | AI |

---

## 四、方案與計費 (Plans & Billing)

| 業務流程 | 測試案例 (Automated/Manual) | 狀態 | 來源文件 |
| :--- | :--- | :--- | :--- |
| **客戶數上限** | `backend/tests/test_usage_limits.py` | [x] | LIMITS |
| **功能開關 (Feature Flag)** | `backend/tests/test_usage_limits.py` (e.g. Hunter.io access) | [x] | LIMITS |

---

## 五、維護腳本 (Maintenance)

| 指令/腳本 | 預期結果 | 狀態 | 說明 |
| :--- | :--- | :--- | :--- |
| `./scripts/test.sh` | 全系統測試通過 (Backend) | [x] | Mac Test Runner |
| `python check_fks.py` | 無外鍵錯誤 | [ ] | DB Integrity |

---
*Created by Antigravity AI - QA Mapping v3.1.8*
