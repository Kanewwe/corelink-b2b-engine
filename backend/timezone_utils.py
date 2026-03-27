"""
Timezone Utilities (v2.7.2)
統一時間處理，解決 UTC 與業務時區不一致問題。

設計決策：
- DB 儲存：統一使用 UTC (ISO 8601 with timezone)
- 業務邏輯：使用 Asia/Taipei (台灣時間 GMT+8)
- API 回傳：帶時區資訊，讓前端處理本地化
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

# 台灣時區 (GMT+8)
TAIPEI_TZ = timezone(timedelta(hours=8))

def now_utc() -> datetime:
    """取得當前 UTC 時間 (帶時區資訊)"""
    return datetime.now(timezone.utc)

def now_taipei() -> datetime:
    """取得當前台灣時間"""
    return datetime.now(TAIPEI_TZ)

def to_utc(dt: datetime) -> datetime:
    """將 datetime 轉換為 UTC"""
    if dt.tzinfo is None:
        # 假設無時區的時間為 UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def to_taipei(dt: datetime) -> datetime:
    """將 datetime 轉換為台灣時間"""
    if dt.tzinfo is None:
        # 假設無時區的時間為 UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TAIPEI_TZ)

def format_iso(dt: datetime) -> str:
    """格式化為 ISO 8601 字串 (帶時區)"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def format_display(dt: datetime, tz: str = "Asia/Taipei") -> str:
    """格式化為顯示用字串 (台灣時間)"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    if tz == "Asia/Taipei":
        dt = dt.astimezone(TAIPEI_TZ)
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_period_taipei() -> tuple:
    """
    取得當前台灣時間的年月，用於用量統計。
    回傳: (year, month)
    """
    now = now_taipei()
    return now.year, now.month

# 向後相容的別名
utcnow = now_utc  # 取代 datetime.utcnow()
