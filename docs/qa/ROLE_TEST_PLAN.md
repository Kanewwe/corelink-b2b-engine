# Linkora 角色權限完整測試計畫 (Role Test Plan)

本文件詳述 Linkora v3.1.8 的多角色存取控制 (RBAC) 測試標準，確保不同方案用戶的資料隔離與功能權限符合設計。

---

## 1. 測試環境 (Test Environment)
- **分支**: `uat` (使用 `uat` schema)
- **URL**: `https://linkora-frontend-uat.onrender.com`
- **數據隔離**: 通過 `SearchPath` 的動態切換進行驗證。

---

## 2. Admin (管理員) 測試矩陣

| 功能項目 | 測試動作 | 預期結果 |
| :--- | :--- | :--- |
| **System Hub** | 更新全域 OpenAI API Key | `/api/system/settings` 返回新 Key 且爬蟲能恢復正常。 |
| **Vendor CRUD** | 新增一個 Vendor B 帳號 | 資料庫 `users` 有新 Record 且 `role='vendor'`。 |
| **Dashboard** | 查看全系統 Leads 總量 | 能顯示所有用戶（不分 Vendor）的歷史 Lead 統計數據。 |

---

## 3. Vendor (簽約廠商) 測試矩陣

| 功能項目 | 測試動作 | 預期結果 |
| :--- | :--- | :--- |
| **Team Analytics** | 存取 `Analytics` 頁面 | 應僅顯示旗下 Member 的統計數，不包含其他 Vendor。 |
| **Unlimited Leads** | 執行累積超過 50 筆的探勘 | 探勘任務應繼續成功（無方案限制阻攔）。 |
| **Billing Audit** | 導出對帳單 CSV | CSV 應正確根據 `outreach` 單價計算總金額。 |

---

## 4. Member (一般會員) 測試矩陣

| 方案 (Plan) | 測試動作 | 預期結果 |
| :--- | :--- | :--- |
| **Free版 (10)** | 探勘第 11 筆 Lead | 系統攔截請求並噴出 429 錯誤。 |
| **Pro版 (100)** | 執行製造商探勘模式 | 應成功啟動 (Free 版此按鈕為灰階/鎖定)。 |
| **Enterprise** | 呼叫 `/api/leads` (Bearer Token) | 外部 API 能正常回傳 JSON 數據。 |

---

## 5. SQL 驗證腳本 (PostgreSQL)

```sql
-- 驗證資料歸屬與隔離權
SELECT u.email, u.role, u.vendor_id, l.company_name 
FROM users u 
JOIN leads l ON u.id = l.user_id 
ORDER BY u.vendor_id, u.id;
```

---
*Created by Antigravity AI - QA Standards v3.1.8*
