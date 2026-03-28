# Linkora 訂閱與方案手冊 (Subscription)

本文件定義了 Linkora v3.1.8 的商業方案、功能限制及其底層資料庫實作。

---

## 1. 方案定義 (Plan Definitions)

| 欄位 | 免費方案 (Free) | 專業方案 (Pro) | 企業方案 (Ent) |
| :--- | :--- | :--- | :--- |
| **價格 (Monthly)** | NT$0 | NT$890 | NT$2,990 |
| **客戶數上限 (Leads)** | 50 | 500 | **無限制** |
| **每月寄信額度** | 10 | 500 | **無限制** |
| **Auto-Miner 次數** | 3 | 30 | **無限制** |
| **模板 (Templates)** | 1 | 10 | **無限制** |

---

## 2. 功能開關 (Feature Matrix)

| 功能項目 | Free | Pro | Enterprise |
| :--- | :--- | :--- | :--- |
| **開信追蹤 (Open)** | ✅ | ✅ | ✅ |
| **AI 信件生成 (GPT)** | ❌ | ✅ | ✅ |
| **郵件附件 (Attach)** | ❌ | ✅ | ✅ |
| **點擊追蹤 (Click)** | ❌ | ✅ | ✅ |
| **Hunter.io 整合** | ❌ | ✅ | ✅ |
| **CSV 批量匯入** | ❌ | ✅ | ✅ |
| **API 存取權限** | ❌ | ❌ | ✅ |

---

## 3. 資料庫架構 (Schema Reference)

### `plans` (方案參數表)
儲存各方案的硬性限制與功能開關。

### `usage_logs` (用量統計表)
- **維度**: 依據 `user_id` + `period_year` + `period_month` 進行複合唯一鍵 (Unique) 限制。
- **重置週期**: 每月 1 號系統自動初始化新紀錄。

---

## 4. 權限檢查邏輯 (Auth Logic)

後端在執行核心動作（發信、探勘）前會透過 `auth_module.check_usage_limit` 進行攔截：
1. 查詢該用戶當月的 `usage_logs`。
2. 比對當前對應方案 (`plans`) 的 `max_*` 值。
3. 若超過則回傳 `429 Too Many Requests`。

---
*Created by Antigravity AI - Linkora Commercial Policy v3.1.8*
