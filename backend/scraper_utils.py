import time
from database import SessionLocal
import models
from datetime import datetime

def log_scrape_health(task_id: int, message: str, level: str = "info", 
                      response_time: float = None, http_status: int = None,
                      keyword: str = None, page: int = None, items_found: int = 0):
    """
    SA v3.4: 紀錄爬蟲健康指標 (Health Monitoring)
    """
    db = SessionLocal()
    try:
        log_entry = models.ScrapeLog(
            task_id=task_id,
            level=level,
            message=message,
            keyword=keyword,
            page=page,
            items_found=items_found,
            response_time=response_time,
            http_status=http_status
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"⚠️ [Health Log Error] {e}")
    finally:
        db.close()

class Timer:
    """Helper to measure execution time"""
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start
