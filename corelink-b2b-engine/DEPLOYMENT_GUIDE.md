# Corelink B2B Sourcing Engine - 快速上線架設手冊 (Quick Start Guide)

本專案分為 **Backend (Python/FastAPI)** 與 **Frontend (Vanilla HTML/JS)** 兩個部分。此手冊提供從零開始的本地端與未來生產環境 (Production) 架設指南。

## 1. 系統環境需求 (Prerequisites)
- [Python 3.10+](https://www.python.org/downloads/)
- 終端機 (PowerShell 或 Git Bash)

---

## 2. 本地端開發環境設置 (Local Setup)

### 步驟 2.1：設定後端 API (Backend)
1. 開啟終端機 (Terminal) 並進入專案資料夾：
   ```bash
   cd d:/mcpserver/corelink-b2b-engine/backend
   ```
2. 建立 Python 虛擬環境：
   ```bash
   python -m venv venv
   ```
3. 啟動虛擬環境 (Windows PowerShell)：
   ```bash
   .\venv\Scripts\Activate.ps1
   ```
4. 安裝相依套件：
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic openai python-dotenv
   ```
   > 或使用 `pip install -r requirements.txt` (若我們後續產出了該檔案)。
5. 設定環境變數 (`.env`)：
   在 `backend/` 目錄下建立一個 `.env` 檔案，填入以下內容：
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=sqlite:///./corelink.db
   ```
6. 啟動 FastAPI 伺服器：
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *伺服器啟動後，可以前往 `http://localhost:8000/docs` 查看自動生成的 API 測試文件 (Swagger UI) 確保啟動成功。*

### 步驟 2.2：設定前端介面 (Frontend)
前端為純 HTML/JS 實作，不依賴複雜的打包工具 (如 Webpack/React)，只需一個簡單的 Web Server 即可運行。
1. 使用任何 HTTP 伺服器來啟動前端資料夾。例如開啟新的終端機視窗並輸入：
   ```bash
   cd d:/mcpserver/corelink-b2b-engine/frontend
   python -m http.server 3000
   ```
2. 打開瀏覽器前往 `http://localhost:3000` 即可使用系統面版。
3. （重要設定）請確認 `frontend/script.js` 裡的 API URL 已經指向 `http://localhost:8000`。

---

## 3. 雲端上線架設建議 (Production Deployment)

未來如果希望將系統部署到雲端供團隊共用，可以考慮下列快速開通的方案：

### 後端 API 部署 (Render / Railway)
- **推薦平台**：[Render (Free Tier可用)](https://render.com/) 或 Railway。
- **部署方式**：將專案推送到 GitHub 後，在 Render 上建立 "Web Service"，指定目錄為 `backend`。
- **Start Command (啟動指令)**：
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```
- **注意事項**：
  1. 需要將 `.env` 中的變數（如 `OPENAI_API_KEY`）在 Render 網頁後台的 Environment Variables 中設定。
  2. 免費方案的本機 SQLite 若容器重啟資料會消失。建議準備商轉時，將 `DATABASE_URL` 改為遠端的 PostgreSQL 服務 (例如 Render 內建的 Managed PostgreSQL 或是 Supabase 提供的免費資料庫)。

### 前端介面部署 (Vercel / Netlify)
- **推薦平台**：[Vercel](https://vercel.com/)
- **部署方式**：非常簡單，直接將 GitHub 上的 `frontend` 資料夾匯入 Vercel，系統會自動分配具有 HTTPS (SSL) 層級的專屬網址。
- **注意事項**：記得將 Vercel 上靜態網頁裡的 API URL 修改為上述 Render 所核發的真實後端網址 (例如 `https://corelink-api.onrender.com`)。

---

## 4. 專案目錄結構總覽
```text
corelink-b2b-engine/
├── DEPLOYMENT_GUIDE.md # 快速上線架設手冊
├── backend/            # Python API 服務
│   ├── main.py         # 伺服器主程式與 API 路由設定
│   ├── models.py       # SQL Schema 與資料庫模型
│   ├── database.py     # DB 連線管理
│   ├── ai_service.py   # AI 自動化處理邏輯 (Prompt 整合)
│   └── requirements.txt# Python 相依套件清單
└── frontend/           # Web UI 面版
    ├── index.html      # 主版面結構
    ├── styles.css      # 介面樣式設計 (CSS)
    └── script.js       # 與 API 溝通的互動邏輯
```
