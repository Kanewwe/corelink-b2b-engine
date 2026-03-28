"""
Industry Tags Model and Initial Data (v3.7.29)
行業分類系統
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from database import Base
from datetime import datetime


class IndustryTag(Base):
    """行業標籤主檔"""
    __tablename__ = "industry_tags"

    id = Column(Integer, primary_key=True, index=True)
    
    # 標籤代碼
    code = Column(String(20), unique=True, nullable=False)    # "MFG-ELEC"
    parent_code = Column(String(20))                          # "MFG"
    
    # 標籤名稱
    name_en = Column(String(100), nullable=False)             # "Electronics Manufacturing"
    name_zh = Column(String(100), nullable=False)             # "電子製造"
    name_short = Column(String(50))                           # "電子"
    
    # 標籤層級
    level = Column(Integer, default=1)                        # 1=一級, 2=二級
    
    # 搜尋關鍵字
    keywords = Column(String(500))                            # 相關關鍵字（逗號分隔）
    
    # 統計
    company_count = Column(Integer, default=0)
    
    # 顯示
    icon = Column(String(50))
    color = Column(String(20))
    
    # 排序
    sort_order = Column(Integer, default=0)
    
    # 狀態
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "parent_code": self.parent_code,
            "name_en": self.name_en,
            "name_zh": self.name_zh,
            "name_short": self.name_short,
            "level": self.level,
            "keywords": self.keywords,
            "company_count": self.company_count,
            "icon": self.icon,
            "color": self.color,
            "sort_order": self.sort_order,
            "is_active": self.is_active
        }


# 初始行業資料
INDUSTRY_DATA = [
    # 一級行業
    {"code": "MFG", "name_en": "Manufacturing", "name_zh": "製造業", "level": 1, "keywords": "工廠,生產,加工,製造", "icon": "🏭", "sort_order": 1},
    {"code": "TECH", "name_en": "Technology", "name_zh": "科技業", "level": 1, "keywords": "科技,軟體,硬體,電子", "icon": "💻", "sort_order": 2},
    {"code": "RETAIL", "name_en": "Retail", "name_zh": "零售業", "level": 1, "keywords": "零售,電商,批發", "icon": "🛒", "sort_order": 3},
    {"code": "SERVICE", "name_en": "Services", "name_zh": "服務業", "level": 1, "keywords": "服務,餐飲,旅遊,教育", "icon": "🏥", "sort_order": 4},
    {"code": "FINANCE", "name_en": "Finance", "name_zh": "金融業", "level": 1, "keywords": "金融,銀行,保險", "icon": "💰", "sort_order": 5},
    {"code": "HEALTH", "name_en": "Healthcare", "name_zh": "醫療健康", "level": 1, "keywords": "醫療,醫院,藥廠", "icon": "🏥", "sort_order": 6},
    {"code": "CONSTRUCTION", "name_en": "Construction", "name_zh": "建築營造", "level": 1, "keywords": "建築,工程,營造", "icon": "🏗️", "sort_order": 7},
    {"code": "TRANSPORT", "name_en": "Transportation", "name_zh": "運輸物流", "level": 1, "keywords": "運輸,物流,貨運", "icon": "🚛", "sort_order": 8},
    {"code": "ENERGY", "name_en": "Energy", "name_zh": "能源環保", "level": 1, "keywords": "能源,電力,環保", "icon": "⚡", "sort_order": 9},
    {"code": "AGRICULTURE", "name_en": "Agriculture", "name_zh": "農林漁牧", "level": 1, "keywords": "農業,漁業,畜牧", "icon": "🌾", "sort_order": 10},
    
    # 二級行業 - 製造業
    {"code": "MFG-ELEC", "parent_code": "MFG", "name_en": "Electronics Manufacturing", "name_zh": "電子製造", "level": 2, "keywords": "電子,PCB,半導體", "sort_order": 1},
    {"code": "MFG-MECH", "parent_code": "MFG", "name_en": "Mechanical Manufacturing", "name_zh": "機械製造", "level": 2, "keywords": "機械,車床,CNC", "sort_order": 2},
    {"code": "MFG-CHEM", "parent_code": "MFG", "name_en": "Chemical Manufacturing", "name_zh": "化學製造", "level": 2, "keywords": "化工,塑膠,材料", "sort_order": 3},
    {"code": "MFG-TEXTILE", "parent_code": "MFG", "name_en": "Textile Manufacturing", "name_zh": "紡織製造", "level": 2, "keywords": "紡織,成衣,布料", "sort_order": 4},
    {"code": "MFG-FOOD", "parent_code": "MFG", "name_en": "Food Processing", "name_zh": "食品加工", "level": 2, "keywords": "食品,飲料,加工", "sort_order": 5},
    {"code": "MFG-PLASTIC", "parent_code": "MFG", "name_en": "Plastic Manufacturing", "name_zh": "塑膠製造", "level": 2, "keywords": "塑膠,射出,模具", "sort_order": 6},
    {"code": "MFG-METAL", "parent_code": "MFG", "name_en": "Metal Processing", "name_zh": "金屬加工", "level": 2, "keywords": "金屬,沖壓,焊接", "sort_order": 7},
    {"code": "MFG-AUTO", "parent_code": "MFG", "name_en": "Auto Parts", "name_zh": "汽車零件", "level": 2, "keywords": "汽車,零件,車用", "sort_order": 8},
    
    # 二級行業 - 科技業
    {"code": "TECH-SOFTWARE", "parent_code": "TECH", "name_en": "Software Development", "name_zh": "軟體開發", "level": 2, "keywords": "軟體,APP,SaaS", "sort_order": 1},
    {"code": "TECH-HARDWARE", "parent_code": "TECH", "name_en": "Hardware", "name_zh": "硬體設備", "level": 2, "keywords": "硬體,設備,伺服器", "sort_order": 2},
    {"code": "TECH-SEMICON", "parent_code": "TECH", "name_en": "Semiconductor", "name_zh": "半導體", "level": 2, "keywords": "半導體,晶圓,IC", "sort_order": 3},
    {"code": "TECH-IOT", "parent_code": "TECH", "name_en": "IoT", "name_zh": "物聯網", "level": 2, "keywords": "IoT,物聯網,智慧", "sort_order": 4},
    {"code": "TECH-AI", "parent_code": "TECH", "name_en": "AI/ML", "name_zh": "AI/機器學習", "level": 2, "keywords": "AI,機器學習,人工智慧", "sort_order": 5},
    
    # 二級行業 - 零售業
    {"code": "RETAIL-ECOMMERCE", "parent_code": "RETAIL", "name_en": "E-commerce", "name_zh": "電商平台", "level": 2, "keywords": "電商,網購,平台", "sort_order": 1},
    {"code": "RETAIL-STORE", "parent_code": "RETAIL", "name_en": "Retail Store", "name_zh": "實體零售", "level": 2, "keywords": "零售,門市,店面", "sort_order": 2},
    {"code": "RETAIL-WHOLESALE", "parent_code": "RETAIL", "name_en": "Wholesale", "name_zh": "批發貿易", "level": 2, "keywords": "批發,貿易,進出口", "sort_order": 3},
    
    # 二級行業 - 服務業
    {"code": "SERVICE-RESTAURANT", "parent_code": "SERVICE", "name_en": "Restaurant", "name_zh": "餐飲", "level": 2, "keywords": "餐廳,美食,外食", "sort_order": 1},
    {"code": "SERVICE-HOTEL", "parent_code": "SERVICE", "name_en": "Hotel & Tourism", "name_zh": "旅遊住宿", "level": 2, "keywords": "飯店,旅遊,民宿", "sort_order": 2},
    {"code": "SERVICE-EDU", "parent_code": "SERVICE", "name_en": "Education", "name_zh": "教育培訓", "level": 2, "keywords": "教育,培訓,課程", "sort_order": 3},
    {"code": "SERVICE-CONSULT", "parent_code": "SERVICE", "name_en": "Consulting", "name_zh": "顧問諮詢", "level": 2, "keywords": "顧問,諮詢", "sort_order": 4},
    {"code": "SERVICE-MARKETING", "parent_code": "SERVICE", "name_en": "Marketing", "name_zh": "行銷廣告", "level": 2, "keywords": "行行銷,廣告,公關", "sort_order": 5},
    
    # 二級行業 - 金融業
    {"code": "FINANCE-BANK", "parent_code": "FINANCE", "name_en": "Banking", "name_zh": "銀行", "level": 2, "keywords": "銀行,信貸", "sort_order": 1},
    {"code": "FINANCE-INSURANCE", "parent_code": "FINANCE", "name_en": "Insurance", "name_zh": "保險", "level": 2, "keywords": "保險,壽險,產險", "sort_order": 2},
    {"code": "FINANCE-INVEST", "parent_code": "FINANCE", "name_en": "Investment", "name_zh": "投資理財", "level": 2, "keywords": "投資,理財,基金", "sort_order": 3},
    
    # 二級行業 - 醫療健康
    {"code": "HEALTH-HOSPITAL", "parent_code": "HEALTH", "name_en": "Hospital", "name_zh": "醫院診所", "level": 2, "keywords": "醫院,診所", "sort_order": 1},
    {"code": "HEALTH-PHARMA", "parent_code": "HEALTH", "name_en": "Pharmaceutical", "name_zh": "製藥", "level": 2, "keywords": "製藥,藥品", "sort_order": 2},
    {"code": "HEALTH-MEDICAL", "parent_code": "HEALTH", "name_en": "Medical Devices", "name_zh": "醫療器材", "level": 2, "keywords": "醫療器材,設備", "sort_order": 3},
    
    # 二級行業 - 建築營造
    {"code": "CONST-BUILD", "parent_code": "CONSTRUCTION", "name_en": "Construction Company", "name_zh": "建設公司", "level": 2, "keywords": "建設,建商", "sort_order": 1},
    {"code": "CONST-ENGINEER", "parent_code": "CONSTRUCTION", "name_en": "Engineering", "name_zh": "工程承包", "level": 2, "keywords": "工程,承包", "sort_order": 2},
    
    # 二級行業 - 運輸物流
    {"code": "TRANS-FREIGHT", "parent_code": "TRANSPORT", "name_en": "Freight", "name_zh": "貨運", "level": 2, "keywords": "貨運,物流", "sort_order": 1},
    {"code": "TRANS-WAREHOUSE", "parent_code": "TRANSPORT", "name_en": "Warehouse", "name_zh": "倉儲", "level": 2, "keywords": "倉倉儲,倉庫", "sort_order": 2},
    
    # 二級行業 - 能源環保
    {"code": "ENERGY-SOLAR", "parent_code": "ENERGY", "name_en": "Solar Energy", "name_zh": "太陽能", "level": 2, "keywords": "太陽能,光電", "sort_order": 1},
    {"code": "ENERGY-RECYCLE", "parent_code": "ENERGY", "name_en": "Recycling", "name_zh": "資源回收", "level": 2, "keywords": "回收,環保", "sort_order": 2},
]


def init_industry_tags(db):
    """初始化行業標籤資料"""
    # 使用本檔案定義的 IndustryTag 類別
    
    # 檢查是否已有資料
    existing = db.query(IndustryTag).first()
    if existing:
        print("ℹ️ Industry tags already initialized")
        return
    
    # 插入初始資料
    for data in INDUSTRY_DATA:
        tag = IndustryTag(**data)
        db.add(tag)
    
    db.commit()
    print(f"✅ Initialized {len(INDUSTRY_DATA)} industry tags")
