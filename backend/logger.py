"""
System logger for background tasks.
"""

SYSTEM_LOGS = []

def add_log(message: str):
    """Add a log entry with timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    SYSTEM_LOGS.append(entry)
    print(entry)
    # Keep last 200 logs
    if len(SYSTEM_LOGS) > 200:
        SYSTEM_LOGS.pop(0)
