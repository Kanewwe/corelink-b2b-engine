"""
Linkora B2B Engine - main.py (v3.6 Clean Backend)

這個檔案是純粹的應用骨幹（≤150 行）：
  - 創建 FastAPI app
  - 設定 Middleware
  - 設定 lifespan（非阻塞啟動）
  - 掛載所有 Router（解耦後的模組）
  - 掛載靜態檔案（前端）

業務邏輯已全部移至：
  - routers/auth_router.py
  - routers/leads_router.py
  - routers/email_router.py
  - routers/scraper_router.py
  - routers/admin_router.py
  - routers/track_router.py
  - jobs/__init__.py (startup tasks)
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import os
import time
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

import email_tracker
from logger import add_log

# ─── Timezone ────────────────────────────────────────────────────────────────
TAIPEI_TZ = timezone(timedelta(hours=8))


# ─── Lifespan (Non-blocking — v3.5+ 規範) ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    v3.6 完全非阻塞啟動。
    所有 DB 操作（init_db, migrations, plan seeding, admin bootstrap）
    全部在 daemon thread 內執行，確保 /api/health 秒速回應 Render 探針。
    """
    def startup_worker():
        try:
            from jobs import run_startup_tasks
            run_startup_tasks()
        except Exception as e:
            add_log(f"🚨 [Startup] Worker error: {e}")

    threading.Thread(target=startup_worker, daemon=True).start()

    # 設定追蹤 base URL（無 DB 依賴，可同步執行）
    base_url = os.getenv("APP_BASE_URL", "https://linkoratw.com")
    email_tracker.set_track_base_url(base_url)

    # 啟動寄信排程器
    try:
        import email_sender_job
        sender_thread = threading.Thread(target=email_sender_job.start_scheduler, daemon=True)
        sender_thread.start()
        add_log("✉️ [System] Email scheduler started (v3.6)")
    except Exception as e:
        add_log(f"🚨 [System] Scheduler error: {e}")

    yield


# ─── App Init ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Linkora B2B Engine API",
    version="3.6.0",
    description="Commercial B2B Lead Generation & Outreach Platform",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global Error Middleware ──────────────────────────────────────────────────
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        response.headers["X-Process-Time"] = str(time.time() - start_time)
        return response
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        add_log(f"🔥 [API Error] {request.method} {request.url.path}: {e}")
        # Return JSON instead of raising, to prevent "Unexpected token I" in frontend
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(e),
                "path": request.url.path,
                "msg": "Internal Server Error (Captured by Middleware)",
                "trace": error_trace if os.getenv("APP_ENV") != "production" else None
            }
        )


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    """極簡健康檢查，確保 Render 啟動不被 DB 鎖死"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "linkora-v3.6-clean"
    }


# ─── Mount Routers ────────────────────────────────────────────────────────────
from routers import auth_router, leads_router, email_router, scraper_router, admin_router, track_router, ai_router

app.include_router(auth_router.router,    prefix="/api", tags=["Auth"])
app.include_router(leads_router.router,   prefix="/api", tags=["Leads"])
app.include_router(email_router.router,   prefix="/api", tags=["Email"])
app.include_router(ai_router.router,     prefix="/api", tags=["AI Intelligence"])
app.include_router(scraper_router.router, prefix="/api", tags=["Scraper"])
app.include_router(admin_router.router,   prefix="/api", tags=["Admin"])
app.include_router(track_router.router,               tags=["Tracking"])


# ─── Static Files (Frontend SPA) ─────────────────────────────────────────────
possible_paths = [
    os.path.join(os.path.dirname(__file__), "frontend"),
    os.path.join(os.path.dirname(__file__), "..", "frontend"),
    "/app/frontend",
]
frontend_path = next((p for p in possible_paths if os.path.exists(p)), None)

if frontend_path:
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.api_route("/", methods=["GET", "HEAD"])
    async def read_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/{file_path:path}")
    async def serve_spa(file_path: str):
        full_path = os.path.join(frontend_path, file_path)
        if os.path.isfile(full_path):
            return FileResponse(full_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Linkora API v3.6 is running. Frontend not found."}
