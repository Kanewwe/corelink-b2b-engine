# Deployment Guide - Linkora B2B Engine

## Prerequisites

- GitHub account
- Render account (free tier available)
- OpenAI API key

## Step 1: Prepare Your Repository

1. Push the optimized code to GitHub:
```bash
cd /tmp/corelink-optimized
git init
git add .
git commit -m "Initial commit - Corelink B2B Engine v2.0"
git remote add origin https://github.com/YOUR_USERNAME/corelink-b2b-engine.git
git push -u origin main
```

## Step 2: Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **PostgreSQL**
3. Configure:
   - Name: `corelink-db`
   - Region: Oregon (or closest to your users)
   - Plan: **Free** (for dev/testing) or Starter ($7/month)
4. Click **Create Database**
5. Note the **Internal Database URL** (you'll need it later)

## Step 3: Create Web Service on Render

1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `linkora-api`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Runtime**: `Docker`
   - **Plan**: **Free**

> ✅ Render 會自動偵測 `Dockerfile`，並透過 `start.sh` 啟動，自動執行資料庫 migration。

## Step 4: Set Environment Variables

In Render Web Service → **Environment** tab, add:

| Key | Value | Notes |
|-----|-------|-------|
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API key |
| `DATABASE_URL` | *(auto-linked)* | Link from PostgreSQL database |
| `ADMIN_USER` | `admin` | Change to your preferred username |
| `ADMIN_PASSWORD` | `your_secure_password` | **Generate a strong password!** |
| `API_TOKEN` | `your_random_token` | **Generate a random string!** |
| `SCRAPER_API_KEY` | `c38c...` | ScraperAPI key (for Yellowpages + Thomasnet) |
| `SMTP_USER` | `your_email@gmail.com` | Optional: for real email sending |
| `SMTP_PASSWORD` | `your_app_password` | Optional: Gmail app password |
| `GOOGLE_API_KEY` | *(optional)* | For Manufacturer Mode (Google CSE) |
| `GOOGLE_CSE_ID` | *(optional)* | For Manufacturer Mode (Google CSE) |

### How to Link Database
1. In Environment tab, click **Add Environment Variable**
2. Select **Database** → choose your `corelink-db`
3. Render will auto-populate `DATABASE_URL`

## Step 5: Deploy

1. Click **Create Web Service**
2. Wait for build (2-3 minutes)
3. Check logs for any errors
4. Once deployed, visit your service URL

## Step 6: Verify Deployment

### Health Check
```
GET https://your-service.onrender.com/health
```
Should return: `{"status": "healthy"}`

### Login Test
```bash
curl -X POST https://your-service.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```
Should return: `{"token":"...","username":"admin"}`

## Step 7: Deploy Frontend (Optional - Same Service)

The backend already serves the frontend static files at the root URL.
Just visit `https://your-service.onrender.com/` in your browser.

### Alternative: Deploy Frontend to Vercel

If you want frontend on a separate domain:

1. Go to [Vercel](https://vercel.com/)
2. Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Deploy
5. **Important**: Update `script.js` API_BASE_URL to point to your Render backend

## Troubleshooting

### Database Connection Error
- Check `DATABASE_URL` is correctly linked
- Verify database is in same region as web service

### Import Errors
- Check `requirements.txt` includes all dependencies
- Verify build logs for missing packages

### Email Not Sending
- Check SMTP credentials are correct
- For Gmail, use App Password (not regular password)
- Enable 2FA on Gmail, then generate App Password

### Scraping Returns 0 Results
- Non-US IPs are often blocked by Yellowpages (403). Make sure `SCRAPER_API_KEY` is correctly set.
- Try switching to **Manufacturer Mode** which uses Bing and Thomasnet instead.

### Database Column Missing Error (`UndefinedColumn`)
- This means `migrations.py` did not run. Check Render logs for `✅ 資料庫結構確認完成`.
- As of v2.2, migrations run automatically inside `lifespan()` in `main.py`.

### Rate Limiting from Scraping
- Reduce scraping frequency or keywords
- Use ScraperAPI for more stable results

## Security Checklist

Before going live:

- [ ] Change `ADMIN_PASSWORD` to a strong password
- [ ] Generate random `API_TOKEN` (32+ characters)
- [ ] Don't commit `.env` file to git
- [ ] Enable HTTPS (automatic on Render)
- [ ] Consider adding rate limiting to API

## Cost Estimate (Free Tier)

| Service | Free Tier Limits |
|---------|------------------|
| Render Web Service | 750 hours/month |
| Render PostgreSQL | 1 GB storage, 97 connections |
| OpenAI API | Pay per use (~$0.01-0.02 per email generated) |

## Need Help?

- Check Render logs in dashboard
- Check `api/system-logs` endpoint for background task errors
- Open an issue on GitHub
