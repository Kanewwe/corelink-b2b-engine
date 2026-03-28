"""
Linkora Crawler Health Job (v3.5)
-------------------------------
定期執行核心探勘策略的健康檢查，確保 API Token 指標與 Actor 結構有效。
不入庫，僅寫入 ScrapeLog 便於監控。
"""

import asyncio
from typing import Dict, Any
from datetime import datetime
from database import SessionLocal
import models
from research_bench import ResearchBench
from logger import add_log

async def run_crawler_health_check():
    """ Runs a sample scrape for a fixed keyword and logs health to DB """
    db = SessionLocal()
    try:
        # 1. 確保有一個系統級別的 "Health Monitor" 任務記錄
        # 我們搜尋最近一個小時內的健康監測任務，若無則建立
        health_task = db.query(models.ScrapeTask).filter(
            models.ScrapeTask.user_id == 1, # 預設 Admin ID
            models.ScrapeTask.miner_mode == "health_check",
            models.ScrapeTask.status == "Running"
        ).first()

        if not health_task:
            health_task = models.ScrapeTask(
                user_id=1,
                market="US",
                keywords="HEARTBEAT",
                miner_mode="health_check",
                pages_requested=1,
                status="Running"
            )
            db.add(health_task)
            db.commit()
            db.refresh(health_task)

        task_id = health_task.id
        bench = ResearchBench(user_id=1)
        
        # 2. 測試 Thomasnet 策略
        from scraper_utils import log_scrape_health
        add_log("💓 [Health] Starting crawler heartbeat...")
        
        res = await bench.strategies["thomasnet"].run("fastener manufacturer", "US", 1)
        
        level = "success" if res["success"] else "error"
        log_scrape_health(
            task_id=task_id,
            level=level,
            message=f"Thomasnet Strategy Health: {res['error'] if not res['success'] else 'Healthy'}",
            keyword="fastener manufacturer",
            page=1,
            items_found=res["count"],
            response_time=res["execution_time"]
        )

        # 3. 標記任務完成
        health_task.status = "Completed"
        health_task.completed_at = datetime.utcnow()
        health_task.leads_found = res["count"]
        db.commit()

        add_log(f"🏁 [Health] Heartbeat finished. Success: {res['success']}, Found: {res['count']}")

    except Exception as e:
        add_log(f"🚨 [Health] Error during health check: {e}", level="error")
    finally:
        db.close()

def run_health_check_sync():
    """ Sync wrapper for BackgroundScheduler """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_crawler_health_check())
    finally:
        loop.close()
