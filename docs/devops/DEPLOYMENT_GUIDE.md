# Linkora 綜合部署指南 (Deployment Guide)

本文件整合了 Linkora 從開發到生產環境的部署流程、資料庫配置與 Render 平台的最佳實踐。

---

## 1. 快速部署 (Render)

### 前置作業
- GitHub Repo 連結
- Render 帳號（包含 PostgreSQL 與 Web Service 權限）
- OpenAI API Key

### 部署架構
- **Web Service**: FastAPI 容器化後端。
- **PostgreSQL**: 核心資料儲存。
- **Static Site (Optional)**: 若前端單獨部署於 Vercel/Netlify。

---

## 2. 資料庫設定與環境隔離

### 免費層級限制
Render 每個帳號限制只能有一個「啟用的、免費的」資料庫。為此，我們採用了 **Schema (綱要) 隔離法**：

- **Production**: 使用預設的 `public` schema。
- **UAT (Staging)**: 使用獨立的 `uat` schema。

### 環境變數設定 (`APP_ENV`)
透過 `APP_ENV` 變數來控制系統連接的 Schema：
- `APP_ENV=production` -> 使用 `public`
- `APP_ENV=uat` -> 自動建立並載入 `uat` schema

---

## 3. 環境變數清單 (Environment Variables)

| 變數名 | 範例/建議值 | 說明 |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://user:pass@host/db?sslmode=require` | **必填**，需含 SSL 強制連線 |
| `APP_ENV` | `production` / `uat` | **必填**，決定 DB Schema 與隔離邏輯 |
| `OPENAI_API_KEY` | `sk-...` | **必填**，AI 代碼與信件生成核心 |
| `ADMIN_PASSWORD` | `your_secure_pass` | **必填**，管理員後台密鑰 |
| `APP_BASE_URL` | `https://linkoratw.com` | **必填**，追蹤 Pixels 與點擊重導向的基礎網址 |
| `SCRAPER_API_KEY` | `c38c...` | 選填，ScraperAPI 用於繞過 Yellowpages 封鎖 |

---

## 4. 常見問題與安全性提示 (Security & FAQ)

1. **SSL 強制連線**：由於 Render PostgreSQL 的安全性要求，連線字串必須包含 `sslmode=require`，否則部分 Driver (如 `psycopg2`) 會發生連線錯誤。
2. **SQLite 資料不持久**：雲端環境嚴禁使用 SQLite (除非用於測試唯讀數據)。請務必確保 `DATABASE_URL` 已正確設定為遠端 PostgreSQL。
3. **任務逾時 (Task Timeout)**：針對製造商探勘任務，系統設定了 180s 的強制中斷機制，以防止背景任務堆積與卡死。

---
*Created by Antigravity AI - Unified Deployment Documentation*
