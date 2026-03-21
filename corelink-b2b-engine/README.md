# Corelink B2B Engine (Optimized)

AI-powered B2B lead generation engine with automatic email discovery.

## What's New (v2.0)

### 🎯 Rule-Based Classification (Token Saver)
- Replaced GPT Prompt 1 with keyword matching
- Saves OpenAI API tokens - only uses GPT for email generation
- Faster classification, same accuracy

### 📧 Automatic Email Discovery
- Auto-discovers company domain from name
- Validates email capability via DNS MX record
- Generates email candidates: info@, contact@, sales@, hello@, support@

### 🗄️ PostgreSQL Ready
- Migrated from SQLite to PostgreSQL
- Works with Render Managed PostgreSQL (free tier available)
- Auto-configuration via DATABASE_URL env var

### 🔒 Security Improvements
- Moved hardcoded credentials to environment variables
- API token authentication
- Admin password configurable

## Quick Start

### Local Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
uvicorn main:app --reload --port 8000
```

Frontend is served by the backend at http://localhost:8000

### Deploy to Render

1. Push this repo to GitHub
2. Create a new Render account
3. Create "New Web Service" → connect your repo
4. Create "New PostgreSQL" database
5. Set environment variables in Render dashboard:
   - `OPENAI_API_KEY`
   - `SMTP_USER` (optional, for real email sending)
   - `SMTP_PASSWORD` (optional)
6. Deploy!

See `DEPLOYMENT_GUIDE.md` for detailed instructions.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/login | Authenticate and get token |
| POST | /api/leads | Create new lead (auto-classified) |
| GET | /api/leads | List all leads |
| POST | /api/leads/{id}/generate-email | Generate email for lead |
| POST | /api/scrape | Trigger background scraper |
| GET | /api/campaigns | List all email campaigns |
| GET | /api/system-logs | View background task logs |
| GET | /health | Health check |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | For email generation (GPT-4o-mini) |
| `DATABASE_URL` | Yes | PostgreSQL connection string (auto-set by Render) |
| `ADMIN_USER` | No | Admin username (default: admin) |
| `ADMIN_PASSWORD` | No | Admin password (change in production!) |
| `API_TOKEN` | No | API auth token (change in production!) |
| `SMTP_USER` | No | Email sender address |
| `SMTP_PASSWORD` | No | Email app password |

## Classification Labels

| Label | Product Line | Assigned Rep | Keywords |
|-------|-------------|--------------|----------|
| NA-CABLE | Cable assemblies | Johnny | wire, harness, cable, connector |
| NA-NAMEPLATE | Industrial nameplates | Richard | nameplate, label, tag, badge |
| NA-PLASTIC | Plastic parts/molding | Jason | plastic, injection, molding, polymer |

---

Powered by Corelink From Concept to Connect
