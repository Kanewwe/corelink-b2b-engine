from datetime import datetime

# --- Global Log Buffer for UI visibility ---
SYSTEM_LOGS = []

def add_log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    SYSTEM_LOGS.append(full_msg)
    # Keep only the last 50 logs
    if len(SYSTEM_LOGS) > 50:
        SYSTEM_LOGS.pop(0)
    print(full_msg)
