# Linkora Deployment Guide

## Overview

Linkora 部署在 Render 平台上，包含：
- **Web Service**: FastAPI 後端 + 前端靜態檔案
- **PostgreSQL**: 資料庫

## Prerequisites

- GitHub 帳號
- Render 帳號
- OpenAI API Key
- 網域（可選）

## Step 1: Push to GitHub

```bash
git clone https://github.com/Kanewwe/corelink-b2b-engine.git
cd corelink-b2b-engine
git checkout -b v2.0-optimized
git push origin v2.0-optimized
```

## Step 2: Create PostgreSQL Database

1. 前往 [dashboard.render.com](https://dashboard.render.com)
2. 點 **New** → **PostgreSQL**
3. 設定：
   - **Name**: `linkora-db`
   - **Plan**: Free（測試用）或 Starter（生產用）
   - **Region**: 選擇靠近你的區域
4. 建立完成後，複製 **Internal Database URL**

## Step 3: Create Web Service

1. 點 **New** → **Web Service**
2. 連接 GitHub repo
3. 選擇 `v2.0-optimized` 分支
4. 設定：

| 設定 | 值 |
|------|-----|
| **Name** | `linkora-api` |
| **Region** | 選擇靠近你的區域 |
| **Runtime** | `Docker` |
| **Branch** | `v2.0-optimized` |
| **Root Directory** | (留空) |
| **Instance Type** | Free 或 Starter |

5. 點 **Create Web Service**

## Step 4: Configure Environment Variables

在 Render Dashboard → 你的 Web Service → **Environment** 新增：

### 必要變數

| Variable | Value | Description |
|----------|--------|-------------|
| `DATABASE_URL` | (from PostgreSQL) | PostgreSQL 連線字串 |
| `OPENAI_API_KEY` | `sk-...` | OpenAI API Key |
| `ADMIN_PASSWORD` | `your_secure_password` | 管理員密碼 |
| `APP_BASE_URL` | `https://linkoratw.com` | 追蹤用 Base URL |

### 選填變數

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_USER` | - | SMTP 發信帳號 |
| `SMTP_PASSWORD` | - | SMTP 密碼 |
| `SMTP_SERVER` | `smtp.gmail.com` | SMTP 伺服器 |
| `SMTP_PORT` | `587` | SMTP 埠號 |
| `GOOGLE_API_KEY` | - | Google CSE API Key |
| `GOOGLE_CSE_ID` | - | Custom Search Engine ID |

## Step 5: Deploy

1. Render 會自動偵測 `Dockerfile` 並部署
2. 等待 Build 完成（約 2-5 分鐘）
3. 確認 Service URL（如 `https://linkora-api.onrender.com`）

## Step 6: Verify Deployment

```bash
curl https://your-service.onrender.com/health
```

預期輸出：
```json
{
  "status": "healthy",
  "database_url": "set",
  "admin_user": "none"
}
```

## Domain Setup (Optional)

### Render Custom Domain

1. Render Dashboard → Web Service → **Settings** → **Custom Domains**
2. 新增你的網域（如 `linkoratw.com`）
3. 按指示設定 DNS

### DNS Settings

```
CNAME   www   →   your-service.onrender.com
```

## Environment Variables Reference

### Required
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_PASSWORD=your_secure_password
APP_BASE_URL=https://your-domain.com
```

### Optional - SMTP
```bash
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Gmail App Password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Optional - Google Custom Search (for Email Finder Layer 3)
```bash
GOOGLE_API_KEY=AIzaSy...
GOOGLE_CSE_ID=xxxxxxxx...
```

## Troubleshooting

### Build Fails
- 檢查 `requirements.txt` 格式
- 確認 Python 版本（建議 3.9+）

### Database Connection Error
- 確認 `DATABASE_URL` 正確
- 確認 PostgreSQL 已啟動

### 502 Bad Gateway
- 檢查後端是否正常啟動
- 查看 Render Logs

### CORS Error
- 確認後端 CORS 設定允許你的網域

## Local Development

```bash
# Clone and setup
git clone https://github.com/Kanewwe/corelink-b2b-engine.git
cd corelink-b2b-engine
git checkout v2.0-optimized

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your values

# Run
uvicorn main:app --reload
```

## Docker Deployment

```bash
# Build locally
docker build -t linkora .

# Run locally
docker run -p 5000:5000 \
  -e DATABASE_URL=postgresql://... \
  -e OPENAI_API_KEY=sk-... \
  -e ADMIN_PASSWORD=password \
  linkora
```

## Monitoring

### Render Logs
- Dashboard → Your Service → **Logs**
- 即時查看後端輸出

### Health Check
```bash
curl https://your-service.onrender.com/health
```

## Update Deployment

只要推送新 commit 到 `v2.0-optimized` 分支，Render 會自動重新部署。

```bash
git add .
git commit -m "Your changes"
git push origin v2.0-optimized
```

## Rollback

Render Dashboard → Your Service → **Deploys** → 選擇舊版本 → **Redeploy**
