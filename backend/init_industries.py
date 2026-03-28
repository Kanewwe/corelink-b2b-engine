"""
初始化行業標籤資料腳本
"""
import sys
sys.path.insert(0, '/Users/borenxiao/.qclaw/workspace/corelink-b2b-engine/backend')

from database import get_db
from industry_tags import init_industry_tags

db = next(get_db())
init_industry_tags(db)
db.close()
print("✅ 行業標籤初始化完成")
