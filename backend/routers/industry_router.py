"""
Industry Tags API Router (v3.7.29)
行業標籤查詢 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from industry_tags import IndustryTag
import auth as auth_module

router = APIRouter()


@router.get("/industries")
def get_industries(
    level: int = None,
    parent_code: str = None,
    db: Session = Depends(get_db)
):
    """
    取得行業標籤列表
    - level: 1=一級行業, 2=二級行業
    - parent_code: 父級代碼（取得子行業）
    """
    query = db.query(IndustryTag).filter(
        IndustryTag.is_active == True
    )
    
    if level:
        query = query.filter(IndustryTag.level == level)
    
    if parent_code:
        query = query.filter(IndustryTag.parent_code == parent_code)
    
    tags = query.order_by(IndustryTag.sort_order).all()
    
    return {
        "total": len(tags),
        "industries": [t.to_dict() for t in tags]
    }


@router.get("/industries/tree")
def get_industry_tree(db: Session = Depends(get_db)):
    """取得行業樹狀結構"""
    # 取得一級行業
    level1 = db.query(IndustryTag).filter(
        IndustryTag.level == 1,
        IndustryTag.is_active == True
    ).order_by(IndustryTag.sort_order).all()
    
    tree = []
    for l1 in level1:
        node = l1.to_dict()
        
        # 取得子行業
        children = db.query(IndustryTag).filter(
            IndustryTag.parent_code == l1.code,
            IndustryTag.is_active == True
        ).order_by(IndustryTag.sort_order).all()
        
        node["children"] = [c.to_dict() for c in children]
        tree.append(node)
    
    return {
        "total": len(tree),
        "tree": tree
    }


@router.get("/industries/{code}")
def get_industry_by_code(
    code: str,
    db: Session = Depends(get_db)
):
    """取得單一行業標籤"""
    tag = db.query(IndustryTag).filter(
        IndustryTag.code == code
    ).first()
    
    if not tag:
        return {"error": "Not found"}
    
    return tag.to_dict()
