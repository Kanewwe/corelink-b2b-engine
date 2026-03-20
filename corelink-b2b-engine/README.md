# Corelink B2B Sourcing Engine 🚀

這是一個由 AI 驅動的 B2B 業務開發與潛在客戶自動化引擎。本系統專門針對來自企業名錄（如 ThomasNet）的北美中小企業製造商，並透過進階的 OpenAI Prompt 全自動抓取客戶特徵，產生具備高轉換率的客製化開發信。

---

## 🔥 核心特色 (Key Features)

1. **智慧化客戶貼標與分流 (Prompt 1)**
   - 使用 GPT-4o-mini 解析公司簡介與業務內容。
   - 自動分派產品線標籤 (`NA-CABLE`, `NA-NAMEPLATE`, `NA-PLASTIC`) 並指派最適合的業務代表 (Johnny, Richard, Jason)。
   - 自動萃取 2-4 個核心業務關鍵字，做為後續開發信破冰 (Icebreaker) 的關鍵素材。

2. **全自動化網頁爬蟲 (Auto-Scraper Crawler)**
   - 透過 FastAPI BackgroundTasks 在背景非同步執行分頁爬蟲。
   - 自動過濾不相關的企業，只將吻合標籤的潛在客戶存入系統，實現完全零人工輸入 (Zero-Touch)。

3. **高轉換率客製化信件生成 (Prompt 2)**
   - 將萃取出的「核心業務關鍵字」無縫注入每個客戶專屬開發信的第一段，讓客戶感受到我們對他們業務的深入了解 (Personalization)。

4. **自動化排程發信 (APScheduler Job)**
   - 背景定時排程每 2 分鐘會自動掃描「草稿 (Draft)」狀態的信件，並透過 SMTP 依序寄出，寄出後自動將狀態更新為已發送 (`Sent`)。

5. **高級質感視覺化控制台 (Premium Glassmorphic UI)**
   - **絕對輕量化：** 全程使用 Vanilla HTML/CSS/JS 打造，不依賴肥大的前端框架，隨開即用。
   - **視覺美學：** 採用現代化的深色模式 (Dark-Mode) 搭配毛玻璃 (Glassmorphism) 特效，為業務團隊帶來頂級的系統操作體驗。
   - **發信紀錄查詢 (Campaign Logs)：** 提供統一的歷史紀錄看板，可即時查詢所有 AI 生成的信件主旨、對象與發送狀態。

6. **系統存取安全控制 (Auth Gateway)**
   - 前後端 API 傳輸皆經由 Bearer Token 進行保護。
   - 系統預設白名單帳號：
     - `KaneXiao` (預設密碼：`admin123`)
     - `JasonXiao` (預設密碼：`admin123`)

---

## 🛠 目錄結構 (Directory Structure)
```text
corelink-b2b-engine/
├── backend/
│   ├── main.py             # 系統進入點與 API 路由設定
│   ├── models.py           # SQLAlchemy 資料庫模型 (Leads, Emails)
│   ├── database.py         # SQLite 資料庫連線設定
│   ├── ai_service.py       # AI Prompt 核心邏輯 (分類判斷與信件生成)
│   ├── scraper.py          # 自動化分頁爬蟲模組
│   ├── email_sender_job.py # 定時排程發信模組 (APScheduler)
│   └── .env                # 環境設定檔 (存放 OpenAI API Key 與 SMTP 密碼)
├── frontend/
│   ├── index.html          # 使用者介面與全螢幕登入閘道
│   ├── styles.css          # 毛玻璃特效與深色質感樣式檔
│   └── script.js           # 前後端 API 串接、權限控管與畫面切換邏輯
├── DEPLOYMENT_GUIDE.md     # 部署與雲端上線教學手冊
└── README.md               # 本專案說明檔
```

---

## 🚀 快速啟動 (Local Setup)

1. **準備後端環境 (Backend)**
   開啟終端機並執行：
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **設定環境變數**
   請確保已在 `backend/.env` 檔案中正確填寫您的 `OPENAI_API_KEY`，若有需要真實發信，請一併填寫 SMTP 的發信帳號與應用程式密碼。

3. **啟動 API 伺服器**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

4. **啟動前端網頁 (Frontend)**
   請開啟另一個新的終端機視窗並執行：
   ```bash
   cd frontend
   python -m http.server 3000
   ```
   接著打開瀏覽器前往 `http://localhost:3000` 即可進入登入閘道。

---
*Powered by Advanced Agentic AI Custom Solutions.*
