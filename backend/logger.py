"""
System logger for background tasks.
"""

SYSTEM_LOGS = []

def add_log(message: str):
    """Add a log entry with timestamp (in-memory only)."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    SYSTEM_LOGS.append(entry)
    print(entry)
    # Keep last 200 logs
    if len(SYSTEM_LOGS) > 200:
        SYSTEM_LOGS.pop(0)


def add_task_log(db, task_id: int, level: str, message: str, 
                 keyword: str = None, page: int = None, items_found: int = None):
    """
    Write a persistent log entry to scrape_logs table.
    
    Args:
        db: SQLAlchemy session
        task_id: ScrapeTask ID
        level: 'info' | 'warning' | 'error' | 'success'
        message: Log message text
        keyword: Optional keyword being scraped
        page: Optional page number
        items_found: Optional count of items found
    """
    try:
        log = models.ScrapeLog(
            task_id=task_id,
            level=level,
            message=message,
            keyword=keyword,
            page=page,
            items_found=items_found,
        )
        db.add(log)
        db.commit()
    except Exception:
        pass  # Don't let logging break the scraper
