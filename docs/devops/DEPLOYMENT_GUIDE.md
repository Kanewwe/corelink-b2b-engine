# Linkora 綜合部署指南 (Deployment Guide)

本文件整合了 Linkora 從開發到生產環境的部署流程、資料庫配置與 Render 平台的最佳實踐。

---

## 1. 快速部署 (Render)

### 前置作業
- GitHub Repo 連結
- Render 帳號（包含 PostgreSQL 與 Web Service 權限）
- OpenAI API Key、Apify API Token

### 部署架構
- **Web Service**: FastAPI，Docker 容器化後端（`Dockerfile.backend`）
- **Static Site**: React/Vite 前端（`frontend/`）
- **PostgreSQL**: 核心資料儲存（Render Managed）

---

## 2. 資料庫設定與環境隔離

### 免費層級限制
Render 每個帳號限制只能有一個「啟用的、免費的」資料庫。採用 **Schema 隔離法**：

| 環境 | Schema | APP_ENV |
|------|--------|---------|
| Production | `public` | `production` |
| UAT | `public` | `uat` |

> [!WARNING]
> **切記**: `search_path=uat` 強制設定已在 v3.5 移除。若資料庫無手動建立 `uat` schema，PostgreSQL 握手會崩潰。UAT 環境請直接使用 `public` schema。

---

## 3. 環境變數清單（完整版）

### 必填（缺少則後端無法啟動）

| 變數名 | 建議值 | 說明 |
|--------|--------|------|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | **必填**，含 SSL（Render 自動附帶） |
| `APP_ENV` | `uat` / `production` | **必填**，決定 Schema 隔離邏輯 |
| `OPENAI_API_KEY` | `sk-proj-...` | **必填**，AI 功能核心 |
| `ADMIN_PASSWORD` | `YourSecurePass` | **必填**，管理員密鑰 |
| `API_TOKEN` | `secure-token-2024` | **必填**，舊版 API 驗證 |
| `APP_BASE_URL` | `https://linkora-frontend-uat.onrender.com` | **必填**，追蹤 Pixel 基礎網址 |

### 業務功能（缺少則對應功能失效，但不影響啟動）

| 變數名 | 建議值 | 說明 |
|--------|--------|------|
| `APIFY_API_TOKEN` | `apify_api_xxx` | 探勘/爬蟲功能依賴 |
| `HUNTER_API_KEY` | `xxx` | Email 查找（Hunter.io） |
| `GOOGLE_API_KEY` | `AIza...` | Google Custom Search |
| `GOOGLE_CSE_ID` | `xxx` | Google 搜尋引擎 ID |
| `SMTP_USER` | Gmail 帳號 | 寄信功能 |
| `SMTP_PASSWORD` | SMTP 應用密碼 | 寄信功能 |
| `SMTP_SERVER` | `smtp.gmail.com` | 有預設值 |
| `SMTP_PORT` | `587` | 有預設值 |
| `EMAIL_SCHEDULER_ENABLED` | `true` | 排程寄信，預設關閉 |

### 安全強化（選填）

| 變數名 | 建議值 | 說明 |
|--------|--------|------|
| `ADMIN_USER` | `linkora_admin` | 預設 `admin`，建議修改 |
| `ALLOWED_ORIGINS` | `https://linkora-frontend-uat.onrender.com` | 目前程式碼直接寫死 `*`，Render 設定無效 |

---

## 4. Dockerfile 設定規範

```dockerfile
FROM python:3.10          # ✅ 必須使用完整版，slim 版有 C 擴展相容性問題
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
RUN apt-get update && apt-get install -y gcc libpq-dev
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
```

> [!CAUTION]
> **禁止使用 `python:3.10-slim`**：在 Render 環境中，slim 映像檔缺少 glibc 子組件，導致 `psycopg2` / `bcrypt` 在**運行時**（非建構時）崩潰，表現為 `earlyExit: true`。

---

## 5. 啟動邏輯規範（v3.5+ 非阻塞模式）

> [!IMPORTANT]
> **核心原則：FastAPI 的 `lifespan` 必須在 1 秒內完成 `yield`，否則 Render 健康探針超時判為失敗。**

### ✅ 正確做法：所有 DB 操作移入背景線程

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    import threading
    def async_init():
        init_db()
        run_migrations()
        init_default_plans()
        ensure_admin_exists()
    threading.Thread(target=async_init, daemon=True).start()
    yield  # ← FastAPI 立即開始監聽，Render 探針通過
```

### ❌ 錯誤做法：任何阻塞性 DB 呼叫在主線程執行

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()          # ← 這裡可能阻塞 20-40 秒
    run_migrations()   # ← Render 探針早已超時宣告失敗
    yield
```

---

## 6. requirements.txt 規範

### 必備套件（不可缺少）

| 套件 | 原因 |
|------|------|
| `python-multipart` | FastAPI OAuth2 / Form 驗證必須有 |
| `psycopg2-binary` | PostgreSQL 連線驅動 |
| `pydantic==1.10.x` | 注意：v2 語法不相容，請鎖定 v1 |

> [!WARNING]
> `pydantic` 目前鎖定 **v1**（`1.10.12`）。若升級至 v2，所有 Pydantic 模型語法都需重寫（`validator` → `field_validator`、`orm_mode` → `from_attributes` 等）。

---

## 7. 常見部署失敗 SOP（血淚教訓 v3.5）

### 7.1 `update_failed` — 後端容器啟動失敗

排查順序：
1. **看 Render Events API**：確認是 `build_ended: succeeded` 之後的 `deploy_ended: failed` → 代表 **運行時錯誤**，非建構問題。
2. **最常見原因清單**：

| 症狀 | 原因 | 修復 |
|------|------|------|
| `NameError: name 'X' is not defined` | 頂層缺少 import | 在 `main.py` 最上方補上對應 import |
| `earlyExit: true` | lifespan 阻塞超時 or 運行時崩潰 | 確認所有 DB 操作在 `threading.Thread` 內執行 |
| `ModuleNotFoundError` | requirements.txt 缺少套件 | 補上對應套件並重建映像（`pip install` 在 build 階段） |
| `AttributeError: module 'X' has no attr 'Y'` | 函數名稱錯誤 | 用 `grep -n "^def "` 確認實際函數名稱 |
| `TypeError: argument of type 'NoneType'` | 對 `None` 做字串操作 | 在操作前加 `if DATABASE_URL` 判斷 |

### 7.2 `build_failed` — 前端建構失敗

| 症狀 | 原因 | 修復 |
|------|------|------|
| `error TS6133: 'X' is declared but its value is never read` | TypeScript strict mode 下未使用的 import | 移除 import 聲明 |
| `Cannot find module 'lucide-react'` | import 存在但本地沒安裝 | `npm ci` 會重建；確認 `package.json` 有正確版本 |
| PostCSS / Tailwind 錯誤 | Tailwind v3/v4 plugin 混用 | 統一使用 `tailwindcss: "3.4"` 並移除 `@tailwindcss/postcss` |

### 7.3 Render API 診斷指令

```bash
# 列出所有服務
curl -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/services?limit=10"

# 查看最近部署狀態
curl -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=3"

# 查看環境變數（審計是否缺漏）
curl -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/services/{SERVICE_ID}/env-vars"

# 查看啟動事件（區分 build 失敗 vs. runtime 失敗）
curl -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/services/{SERVICE_ID}/events?limit=20"
```

---

## 8. main.py 複雜度警告 (v3.5 教訓)

> [!CAUTION]
> **`main.py` 超過 500 行即應進行拆分。**  
> 目前 `main.py` 已達 2,339 行，是部署脆弱性的根本原因。  
> 任何一個 import 失敗都會讓整個 App 無法啟動。  
> 詳見重構計畫 `v3.6 Clean Backend`。

**重構方向**：
- `routers/` — 按業務功能拆分路由
- `schemas/` — 集中 Pydantic 模型
- `jobs/` — 背景任務獨立管理

---

## 9. 部署前 Checklist

```
□ main.py 頂部有完整 typing import（Optional, List, Dict, Any, os, time）
□ requirements.txt 包含 python-multipart==0.0.6
□ Dockerfile 使用 python:3.10（非 slim）
□ lifespan 內所有 DB 操作都在 threading.Thread 內
□ DATABASE_URL 不含 search_path 強制 schema 設定
□ Render 環境變數已設定：DATABASE_URL, APP_ENV, OPENAI_API_KEY,
  ADMIN_PASSWORD, API_TOKEN, APP_BASE_URL, APIFY_API_TOKEN
□ 前端所有 import 的 icon/套件在 package.json 中有版本鎖定
□ TypeScript 無 TS6133 unused import 錯誤
```

---

*最後更新：2026-03-28 by Antigravity AI — v3.5 恢復部署血淚紀錄*
