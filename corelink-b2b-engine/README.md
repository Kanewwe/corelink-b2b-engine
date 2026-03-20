# Corelink B2B Sourcing Engine 🚀

A scalable B2B sourcing and lead generation platform built dynamically with AI. The engine specifically targets North American SME Manufacturers from directories (like ThomasNet) and automatically generates highly personalized outreach emails using advanced OpenAI Prompts.

---

## 🔥 Key Features

1. **Intelligent Lead Tagging (Prompt 1)**
   - Extracts insights from company descriptions using GPT-4o-mini.
   - Automatically assigns Product Tags (`NA-CABLE`, `NA-NAMEPLATE`, `NA-PLASTIC`) and assigns the appropriate BD (Johnny, Richard, Jason).
   - Extracts 2-4 core business keywords for deeper personalization later.

2. **Automated Auto-Scraper (Web Crawler)**
   - Run background scraping tasks (FastAPI BackgroundTasks) to fetch companies page by page.
   - Automatically filters out irrelevant companies and saves only the targeted ones.

3. **Highly-Personalized Auto-Drafts (Prompt 2)**
   - Generates contextualized, professional outreach emails injecting the previously extracted business keywords to increase the reply rate ("Personalization Icebreaker").

4. **Premium Glassmorphic UI Dashboard**
   - No frontend framework bloat. Built entirely with Vanilla HTML/CSS/JS.
   - Dark-mode, glassmorphism UI for a stunning visual experience.

5. **Access Control (Auth Gateway)**
   - Secured endpoints requiring Bearer Token authentication.
   - Default Accounts:
     - `KaneXiao` (Password: `admin123`)
     - `JasonXiao` (Password: `admin123`)

---

## 🛠 Directory Structure
```text
corelink-b2b-engine/
├── backend/
│   ├── main.py         # Entrypoint & FastAPI Routes
│   ├── models.py       # SQLAlchemy Schema (Leads, Emails)
│   ├── database.py     # SQLite Connection Setup
│   ├── ai_service.py   # System Prompts (Prompt 1 & Prompt 2)
│   ├── scraper.py      # Automated Pagination & Directory Crawler
│   └── .env            # OPENAI_API_KEY storage
├── frontend/
│   ├── index.html      # UI Markup & Login Modal
│   ├── styles.css      # Glassmorphic UI Design styling
│   └── script.js       # API Fetching & Auth Logic
├── DEPLOYMENT_GUIDE.md # 部署與雲端上線教學手冊
└── README.md           # This file
```

---

## 🚀 Quick Start (Local Setup)

1. **Setup the Backend**
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Environment Variables**
   Ensure `backend/.env` exists and contains your `OPENAI_API_KEY`.
3. **Run API Server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
4. **Launch Frontend**
   ```bash
   cd frontend
   python -m http.server 3000
   ```
   Navigate to `http://localhost:3000` in your browser. Log in using `KaneXiao` / `admin123`.

---

*Designed and Built for Corelink using advanced Agentic Code capabilities.*
