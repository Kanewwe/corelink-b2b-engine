# Linkora B2B 業務流程手冊 (Business Process)

本文件詳述 Linkora v3.1.8 的業務流程，涵蓋從探勘、聯繫到對帳的完整生命週期。

---

## 1. 核心業務流程 (The Lead Lifecycle)

1.  **探勘階段 (Discovery)**: Member 啟動「製造商」或「黃頁」模式。系統實作 **Four-stage Discovery**，優先從全域情報池同步以節省 API 成本。
2.  **分類與標籤 (Classification)**: AI (GPT-4o-mini) 自動將 Leads 依產業（如 `NA-CABLE`）進行分類，並萃取關鍵字。
3.  **開發與投遞 (Outreach)**: 使用 AI 生成個人化內容。發信過程由 `APScheduler` 背景執行。
4.  **成效追蹤 (Analytics)**: 透過 Pixel 與 Redirect 追蹤開信與點擊，提供漏斗分析。

---

## 2. 協作模型 (Collaboration Roles)

| 角色 | 關鍵責任 (v3.1.8) |
| :--- | :--- |
| **👑 Admin** | 整合 API Keys (System Hub)，審核簽約 Vendor 的批發單價與用量。 |
| **🏭 Vendor** | 管理旗下 Member 的數據產出，作為代操服務商向其客戶收費。 |
| **👷 Member** | 第一線操作：篩選產業關鍵字、編寫模板、執行發信任務。 |

---

## 3. 預期效益與 KPI (Value Analysis)

- **自動化探勘**: 節省業務人員 80% 的手動搜尋時間。
- **高轉換率**: AI 標籤化讓開發信更精準，預期回覆率提升 25%+。
- **全域去重**: 透過共享情報池，大幅減少重複採集相同網域的 API 點數支出。

---
*Created by Antigravity AI - Business Excellence v3.1.8*
