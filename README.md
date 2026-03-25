# Linkora - AI B2B Outreach Platform

**AI 驅動的 B2B 開發信自動化平台**

---

## 📌 專案簡介

Linkora 是一套專為 B2B 業務開發設計的自動化平台，幫助外銷業務自動化開發陌生客戶：

- **智能爬蟲**：支援黃頁模式（Yellowpages）與**製造商模式**（Thomasnet / Bing / Google CSE）
- **AI 分類**：根據公司描述自動分類到對應產品線
- **Email 發現**：多層策略驗證找出公司 Email
- **開發信生成**：使用 GPT-4o-mini 生成個人化開發信
- **觸及率追蹤**：追蹤開信、點擊、回覆狀態

---

## 🚀 核心功能

### 最新更新 (2026-03-24)

**UX 全面重整**：
- 🎨 左側導覽分組顯示
- 📧 Email 補找功能（無 Email 客戶可補找）
- 👁️ 變數預覽（寄信前確認變數替換）
- 📊 觸及率頁面移除收費設定
- 🔍 搜尋記錄改為「探勘歷史」

---

### 1. AI 自動探勘 (Auto-Miner)

**功能說明**：
- 輸入產業關鍵字（如 `Car Parts`、`Cable Manufacturer`）
- AI 生成 5 組相關零件關鍵字
- 選擇**探勘模式**後系統自動搜尋
- 智能過濾並分類潛在客戶
- 自動發現公司 Email 並驗證

**探勘模式（可在前端切換）**：

| 模式 | 資料來源 | 適合場景 |
|------|----------|----------|
| 🏭 製造商模式（推薦） | Google CSE + Bing + Thomasnet | B2B 工業品、OEM、零件採購 |
| 📋 黃頁模式 | Yellowpages + Yelp + ScraperAPI | 本地服務業、零售、維修 |

**去重機制**：
- 自動檢查公司名稱是否已存在
- 檢查網域是否已寄過信
- 標記已寄信客戶

---

### 2. AI 智能分類

| 分類標籤 | 產品線 | 關鍵字範例 |
|---------|--------|-----------|
| NA-CABLE | 線材/線束 | cable, wire, harness |
| NA-NAMEPLATE | 銘牌/標籤 | nameplate, label, tag |
| NA-PLASTIC | 塑膠射出 | plastic, injection, molding |
| AUTO-* | 汽車零件 | engine, brake, suspension... |

---

### 3. Email 發現系統（三層策略）

**Layer 1：直接爬官網**
- 爬取公司官網首頁 + 聯絡頁
- 解析 `mailto:` 標籤
- Regex 掃描全頁

**Layer 2：Pattern 猜測 + SMTP 驗活**
- 猜測常見前綴（procurement, sales, info...）
- SMTP 驗證是否為有效信箱
- Catch-all 偵測防誤判

**Layer 3：Google Custom Search API**
- 用關鍵字搜尋公司網站
- 驗證網域真實性

---

### 4. 開發信生成

**使用 GPT-4o-mini**：
- Monaco Editor 即時預覽
- AI 變數自動替換
- 支援 PDF/文件附件
- 模板管理（按產業分組）

**信件變數**：
- `{{company_name}}` - 公司名稱
- `{{keywords}}` - 關鍵字
- `{{bd_name}}` - 業務代表
- `{{description}}` - 公司描述

---

### 5. 觸及率追蹤

**追蹤機制**：
- Tracking Pixel（開信追蹤）
- Click Redirect（點擊追蹤）
- 手動標記回覆

**漏斗分析**：
```
寄出 → 送達 → 開信 → 點擊 → 回覆
```

---

## 📊 頁面功能

| 頁面 | 功能 |
|------|------|
| Lead Engine | 客戶列表、搜尋篩選、Auto-Miner |
| 新增客戶 | 快速新增公司、AI 自動分類 |
| 寄信記錄 | Email Campaign 列表、狀態追蹤 |
| 觸及率 | 漏斗分析、產業維度統計 |
| 搜尋記錄 | Auto-Miner 執行日誌 |
| 信件模板 | Monaco Editor、AI 生成、預覽 |
| SMTP 設定 | 排程、SMTP 配置 |

---

## 💳 訂閱方案

| 方案 | 價格 | 客戶數 | 每月寄信 | 功能 |
|------|------|--------|---------|------|
| **免費** | NT$0 | 50 | 10 | 基本追蹤 |
| **專業** | NT$890/月 | 500 | 500 | AI 生成、點擊追蹤、Hunter.io |
| **企業** | NT$2990/月 | 無限 | 無限 | API、多用戶、專屬支援 |

### 用量限制

| 資源 | Free | Pro | Enterprise |
|------|------|-----|-----------|
| 客戶數 | 50 | 500 | 無限 |
| 每月寄信 | 10 | 500 | 無限 |
| Auto-Miner | 3次/月 | 30次/月 | 無限 |
| AI 信件生成 | ❌ | ✅ | ✅ |
| 點擊追蹤 | ❌ | ✅ | ✅ |
| Hunter.io | ❌ | ✅ | ✅ |
| 附件功能 | ❌ | ✅ | ✅ |

---

## 🛠️ 技術架構

### 後端
- **框架**：FastAPI (Python)
- **資料庫**：PostgreSQL (Render)
- **AI**：OpenAI GPT-4o-mini
- **爬蟲**：httpx + BeautifulSoup
- **排程**：APScheduler
- **Email**：SMTP + Tracking Pixel

### 前端
- **技術**：Vanilla HTML + CSS + JavaScript
- **編輯器**：Monaco Editor
- **UI 風格**：Dark SaaS (Linear/Vercel 風格)

### 部署
- **平台**：Render (Web Service + PostgreSQL)
- **網域**：`linkoratw.com`

---

## 📁 專案結構

```
corelink-b2b-engine-2.0-optimized/
├── backend/
│   ├── main.py              # FastAPI 主程式（含 lifespan 自動 migration）
│   ├── models.py            # SQLAlchemy 模型
│   ├── auth.py              # 認證模組
│   ├── database.py          # 資料庫連線
│   ├── migrations.py        # 自動補欄腳本（user_id 等）
│   ├── ai_service.py        # AI 服務
│   ├── email_tracker.py     # 追蹤系統
│   ├── free_email_hunter.py # 三層免費 Email 策略
│   ├── email_sender_job.py  # 寄信排程
│   ├── scrape_simple.py     # 黃頁爬蟲（ScraperAPI 繞過）
│   ├── manufacturer_miner.py # 製造商模式爬蟲（Bing + Thomasnet）
│   ├── logger.py            # 日誌系統
│   └── requirements.txt
├── frontend/
│   ├── index.html           # 主頁面（含模式切換 UI）
│   ├── styles.css
│   └── script.js            # 前端邏輯（含 miner_mode 參數）
├── docs/                    # 技術文件
├── start.sh                 # 啟動腳本（含 migration + 正確 PORT 綁定）
├── render.yaml              # Render 部署設定
├── Dockerfile
└── README.md
```

---

## 🔧 環境變數

### 必要變數

| 變數 | 說明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 金鑰 |
| `DATABASE_URL` | PostgreSQL 連線字串 |
| `ADMIN_PASSWORD` | 管理員密碼 |

### 選填變數

| 變數 | 說明 |
|------|------|
| `SMTP_USER` | SMTP 發信帳號 |
| `SMTP_PASSWORD` | SMTP 密碼 |
| `SMTP_SERVER` | SMTP 伺服器（預設 smtp.gmail.com）|
| `SMTP_PORT` | SMTP 埠號（預設 587）|
| `APP_BASE_URL` | 追蹤用 Base URL |
| `SCRAPER_API_KEY` | ScraperAPI Key（用於黃頁 / Thomasnet 繞過封鎖）|
| `GOOGLE_API_KEY` | Google Custom Search API Key（製造商模式可選）|
| `GOOGLE_CSE_ID` | Custom Search Engine ID（製造商模式可選）|

---

## 🚀 部署與開發生命週期 (Standard Lifecycle)

本專案採行嚴格的 **UAT (Staging) 優先策略**，確保所有更新在進入正式環境前皆經過驗證。

### 1. 開發流程 (Standard Workflow)
- **Staging (UAT)**: 開發與修補請推送到 `uat` 分支。Render 會自動部署至測試環境。
- **Verification**: 在 UAT 環境驗證功能（如：Auth、SMTP、Scraper）。
- **Production (PRD)**: 驗證無誤後，將 `uat` 合併至 `prd` 分支。Render 會自動更新正式環境。

### 2. 快速指令
使用專屬同步腳本簡化操作：

- **推送至測試 (UAT)**: `git push origin uat`
- **發布至正式 (PRD)**: `./scripts/sync.ps1 -Action deploy` (自動完成合併與推送)

### 3. Render 服務網址
- **正式環境 (PRD)**: [https://linkora-frontend.onrender.com](https://linkora-frontend.onrender.com)
- **測試環境 (UAT)**: [https://linkora-frontend-uat.onrender.com](https://linkora-frontend-uat.onrender.com)

---

## 🌐 共用網域設定

官網和後台共用同一網域：

```
linkoratw.com/           → 官網 (Vercel)
linkoratw.com/app/*      → 後台 (Render)
linkoratw.com/api/*      → API (Render)
linkoratw.com/track/*     → 追蹤 (Render)
```

### DNS 設定

```
CNAME   www   →   cname.vercel-dns.com
```

### Vercel Rewrite 規則

```json
{
  "rewrites": [
    { "source": "/app(.*)", "destination": "https://corelink-b2b-engine.onrender.com/app$1" },
    { "source": "/api(.*)", "destination": "https://corelink-b2b-engine.onrender.com/api$1" },
    { "source": "/track(.*)", "destination": "https://corelink-b2b-engine.onrender.com/track$1" }
  ]
}
```

---

## 🔐 安全性

- ✅ bcrypt 密碼 hash
- ✅ Session-based 認證
- ✅ 環境變數管理密碼
- ✅ CORS 設定
- ✅ 用量限制保護

---

## 📈 API Endpoints

### 認證

| Method | Endpoint | 說明 |
|--------|----------|------|
| POST | `/api/auth/register` | 用戶註冊 |
| POST | `/api/auth/login` | 登入 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/me` | 取得用戶資訊 |

### 客戶

| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/leads` | 取得所有客戶 |
| POST | `/api/leads` | 新增客戶 |
| POST | `/api/leads/{id}/generate-email` | 生成開發信 |

### 模板

| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/templates` | 取得所有模板 |
| POST | `/api/templates` | 新增模板 |
| POST | `/api/templates/ai-generate` | AI 生成模板 |
| POST | `/api/templates/test-send` | 傳送測試信 |

### 追蹤

| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/track/open?id=xxx` | 開信追蹤像素 |
| GET | `/track/click?id=xxx&url=yyy` | 點擊重導向 |

### 方案

| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/plans` | 取得所有方案 |
| GET | `/api/subscription` | 取得當前訂閱 |

---

## 📝 更新日誌

### v2.2-manufacturer (2026-03-24)
- 🏭 新增「製造商模式」爬蟲（Thomasnet + Bing + Google CSE）
- 🔄 Google CSE 400 時自動切換 Bing 備援
- 🔑 Thomasnet 整合 ScraperAPI 繞過封鎖
- 🗄️ `migrations.py` 嵌入 FastAPI `lifespan`，確保資料庫欄位自動補齊
- 🖥️ 前端新增探勘模式切換 UI

### v2.1-fixes (2026-03-23)
- 🐛 修復登入時 Session ID 未寫入 Cookie 導致狀態失效的嚴重問題
- 🐛 移除了發送測試信 API 尾端錯誤拷貝導致 500 Error 的殘留死碼
- ✨ 新增了後台的「登出」按鈕與對應清除狀態流程
- 💎 全站定價轉換為台幣（TWD），並統一了前後端顯示的方案規格

### v2.0-optimized (2026-03-23)
- ✨ Linkora 品牌重塑
- ✨ 新 UI 設計（Dark SaaS 風）
- ✨ Monaco Editor 整合
- ✨ AI 關鍵字生成
- ✨ Email 追蹤系統
- ✨ 訂閱系統基礎架構
- 🐛 多項 Bug 修復

### v1.0
- 初始版本
- 基本爬蟲功能
- Email 發現
- 開發信生成

---

## 👥 聯絡方式

- **Linkora** - AI B2B Outreach Platform
- **網站**：https://linkoratw.com
- **後台**：https://app.linkoratw.com
- **GitHub**：https://github.com/Kanewwe

---

## 📄 授權

MIT License

---

**Linkora** - 讓 AI 幫你開發全球客戶 🚀
