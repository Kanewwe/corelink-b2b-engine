import os
import json
import models
from database import SessionLocal

def get_api_key(db, tool_name: str, user_id: int = None) -> str:
    """
    獲取 API Key：優先從資料庫讀取，找不到才回退到環境變數。
    Priority: 
    1. 該使用者的個人設定 (User-specific)
    2. 管理員的全局設定 (Admin/User 1)
    3. 環境變數 (.env)
    """
    
    # 1. 嘗試從資料庫讀取
    try:
        # 搜尋順序：當前使用者 -> 管理員 (User 1)
        search_ids = []
        if user_id: search_ids.append(user_id)
        if 1 not in search_ids: search_ids.append(1)
        
        for uid in search_ids:
            setting = db.query(models.SystemSetting).filter(
                models.SystemSetting.user_id == uid,
                models.SystemSetting.key == "api_keys"
            ).first()
            
            if setting and setting.value:
                keys_data = json.loads(setting.value)
                
                # 工具名稱對應
                mapping = {
                    "openai": "openai_key",
                    "apify": "apify_token",
                    "hunter": "hunter_key",
                    "openai_model": "openai_model",
                    "google": "google_key",
                    "google_cse_id": "google_cse_id"
                }
                
                db_key = mapping.get(tool_name)
                if db_key and keys_data.get(db_key):
                    val = str(keys_data[db_key]).strip()
                    if val:
                        return val
    except Exception as e:
        # 若資料庫查詢失敗，靜默失敗並回退到環境變數
        pass

    # 2. 回退到環境變數
    env_mapping = {
        "openai": "OPENAI_API_KEY",
        "apify": "APIFY_API_TOKEN",
        "hunter": "HUNTER_API_KEY",
        "openai_model": "OPENAI_MODEL",
        "google": "GOOGLE_API_KEY",
        "google_cse_id": "GOOGLE_CSE_ID"
    }
    
    if tool_name == "apify":
        # Apify 傳統上可能用 APIFY_TOKEN 或 APIFY_API_TOKEN
        return os.getenv("APIFY_API_TOKEN") or os.getenv("APIFY_TOKEN")
    
    env_var = env_mapping.get(tool_name)
    return os.getenv(env_var) if env_var else None

def get_openai_model(db, user_id: int = None) -> str:
    """獲取 OpenAI 模型名稱 (預設 gpt-4o-mini)"""
    return get_api_key(db, "openai_model", user_id) or "gpt-4o-mini"
