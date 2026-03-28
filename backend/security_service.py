import hmac
import hashlib
import os
import time
import json
from fastapi import Request, HTTPException

# 簽名密鑰 (應設置於環境變數)
SECRET_KEY = os.getenv("LINKORA_SECURITY_SECRET", "linkora-dev-secret-key-123456")

# 簽名有效期（秒）- 防止重放攻擊
SIGNATURE_EXPIRY = 300 

def generate_signature(payload: str, timestamp: str) -> str:
    """產生 HMAC-SHA256 簽名"""
    message = f"{timestamp}.{payload}".encode('utf-8')
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature

async def verify_request_signature(request: Request):
    """
    驗證請求簽名 (Middleware 級別)
    Header 需包含: 
    - X-Linkora-Signature: 簽名結果
    - X-Linkora-Timestamp: 產生簽名的時間戳 (ms)
    """
    # 略過 GET 請求或健康檢查
    if request.method == "GET" or "/health" in request.url.path:
        return

    # 開發環境跳過驗證 (可選)
    if os.getenv("APP_ENV") == "development" and not request.headers.get("X-Linkora-Signature"):
        return

    signature = request.headers.get("X-Linkora-Signature")
    timestamp = request.headers.get("X-Linkora-Timestamp")

    if not signature or not timestamp:
        raise HTTPException(status_code=403, detail="缺少安全簽名標頭 (Missing Security Signature)")

    # 驗證時間戳是否過期 (Replay Attack Protection)
    try:
        ts_float = float(timestamp) / 1000.0
        if abs(time.time() - ts_float) > SIGNATURE_EXPIRY:
            raise HTTPException(status_code=403, detail="簽名已過期 (Signature Expired)")
    except (ValueError, TypeError):
        raise HTTPException(status_code=403, detail="無效的時間戳格式")

    # 讀取 Body
    body = await request.body()
    payload = body.decode('utf-8') if body else ""

    # 重新計算簽名
    expected_sig = generate_signature(payload, timestamp)

    if not hmac.compare_digest(signature, expected_sig):
        # 為了除錯，紀錄 payload (生產環境應關閉)
        # print(f"DEBUG: Payload={payload}, Timestamp={timestamp}, Expected={expected_sig}")
        raise HTTPException(status_code=403, detail="安全校驗失敗 (Security Verification Failed)")
