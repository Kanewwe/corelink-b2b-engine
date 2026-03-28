# Linkora v3.1.8-resilience API 手冊 (API Documentation)

本文件定義了 Linkora 後端（FastAPI）的 RESTful 接口規範，支援 **Session-based (Cookie)** 與 **Bearer Token** 雙重驗證。

---

## 🔐 認證機制 (Authentication)

### 1. 用戶登入 (Login)
`POST /api/auth/login`
- **Request**: `{ "email": "...", "password": "..." }`
- **Response**: 返回 `session_id` Cookie 並設定為 `httponly`。

### 2. 當前用戶資訊 (Me)
`GET /api/auth/me`
- **Response**: 返回用戶基礎資料、訂閱方案（Free/Pro/Ent）與當月用量。

---

## 🏭 探勘引擎 (Lead Engine)

### 1. 智慧探勘任務 (Advanced Scrape)
`POST /api/scrape-simple`
- **Request**:
```json
{
  "market": "US",
  "keywords": ["car parts", "wire harness"],
  "miner_mode": "manufacturer",
  "pages": 3
}
```
- **核心邏輯**: 系統會優先執行 **全域隔離池 (Pool Check)** 跳過重複爬取。

### 2. 關鍵字 AI 擴展 (Keyword Gen)
`POST /api/keywords/generate`
- **Request**: `{ "keyword": "cable", "count": 5 }`
- **Response**: `{ "success": true, "keywords": [...] }`

---

## 📈 成效分析 (Analytics)

### 1. 儀表板統計 (Dashboard Stats)
`GET /api/dashboard/stats`
- **Response**: `{ "total_leads": 120, "sent_month": 45, "open_rate": "15%", ... }`

---

## ⚙️ 系統設定與管理 (Admin & System)

### 1. 全域系統設定 (System Hub - 管理員專屬)
`GET /api/system/settings`
- **定位**: 獲取全站 API Keys (OpenAI, Hunter, ScraperAPI) 與變數映射配置。

### 2. 更新系統設定
`POST /api/system/settings`
- **Request**: `{ "key": "api_keys", "value": { "openai_key": "sk-...", ... } }`

### 3. 資料庫初始化 (DB Init)
`POST /api/init-db`
- **Role**: 強制執行 `migrations.py` 並建立所有 Schema 表格。

### 4. 系統日誌流 (System Logs)
`GET /api/system-logs`
- **Response**: 返回最近 100 條系統核心日誌。

### 5. 名單診斷 (Debug Leads)
`GET /api/debug-leads`
- **Response**: 返回當前所有名單的狀態分布與全域池同步統計。

---

## 📊 追蹤接口 (Unauthenticated)

| Method | Endpoint | 說明 |
| :--- | :--- | :--- |
| **GET** | `/track/open?id=<uuid>` | 開信追蹤像素 (1x1 PNG) |
| **GET** | `/track/click?id=<uuid>&url=<enc>` | 點擊追蹤重導向 (302) |

---
*Created by Antigravity AI - Linkora API Standards v3.1.8*
