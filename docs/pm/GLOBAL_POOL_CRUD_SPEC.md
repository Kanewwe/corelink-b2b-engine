# 情資庫檢視器 CRUD 功能規格

> **日期：** 2026-03-29
> **目標：** 為系統控制中心的情資庫檢視器新增「編輯」和「刪除」單筆資料功能

---

## 1. 現有功能

### 1.1 前端位置
- 檔案：`frontend/src/pages/SystemSettings.tsx`
- Tab：`explorer`（情資庫檢視器）
- 兩個子 Tab：
  - 全域池 (Shared) — `globalLeads`
  - 用戶工作區 (Private) — `allUserLeads`

### 1.2 現有 API

| API | 用途 | 狀態 |
|-----|------|------|
| `GET /api/admin/all-leads` | 取得所有用戶 leads | ✅ 存在 |
| `GET /api/admin/global-leads` | 取得全域池 leads | ⚠️ 前端呼叫但後端未實作 |

### 1.3 現有問題
- 全域池 API 不存在（`/admin/global-leads`）
- 無法編輯單筆資料
- 無法刪除單筆資料
- 只能清空整個全域池（危險）

---

## 2. 新增功能規格

### 2.1 功能清單

| 功能 | 說明 | 適用 |
|------|------|------|
| **編輯單筆** | 修改公司名、Email、電話等欄位 | 全域池 + 用戶工作區 |
| **刪除單筆** | 刪除單一公司記錄 | 全域池 + 用戶工作區 |
| **批次刪除** | 勾選多筆後批次刪除 | 全域池 + 用戶工作區 |
| **行業標籤編輯** | 編輯行業分類標籤 | 全域池 |

### 2.2 UI 設計

#### 表格新增操作欄

```
┌─────────────────────────────────────────────────────────────┐
│  管理員情資庫檢視器                    [全域池] [用戶工作區] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  搜尋：[...] [刷新]                                          │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐│
│  │公司名稱│網域│Email│AI標籤│來源│操作              ││
│  ├────────────────────────────────────────────────────────┤│
│  │Tech Corp│tech.com│✅info@│電子│Apollo│[編輯][刪除]││
│  │ABC Mfg  │abc.com │⚠️sales@│機械│Apify│[編輯][刪除]││
│  └────────────────────────────────────────────────────────┘│
│                                                             │
│  已選 0 筆  [批次刪除]                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 編輯 Modal

```
┌─────────────────────────────────────────────────────────────┐
│  編輯公司資料                                    [關閉]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  公司名稱：[Tech Corp                              ]        │
│                                                             │
│  網域：[tech.com                                   ]        │
│                                                             │
│  網站：[https://tech.com                           ]        │
│                                                             │
│  聯絡信箱：[info@tech.com                          ]        │
│  驗證狀態：[✅ 已驗證]                                      │
│                                                             │
│  電話：[+1-555-12345                              ]        │
│                                                             │
│  地址：[123 Main St, CA, USA                      ]        │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  行業分類：                                                  │
│  一級：[製造業 ▼]                                           │
│  二級：[電子製造 ▼]                                         │
│                                                             │
│  標籤：[電子] [PCB] [半導體] [+新增]                         │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  員工數：[250]                                              │
│                                                             │
│  備註：[                                                  ]  │
│                                                             │
│  [取消] [儲存變更]                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 刪除確認 Modal

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ 確認刪除                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  確定要刪除這筆資料嗎？                                       │
│                                                             │
│  公司：Tech Corp                                            │
│  網域：tech.com                                             │
│                                                             │
│  ⚠️ 此操作無法復原                                           │
│                                                             │
│  [取消] [確認刪除]                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 後端 API 設計

### 3.1 新增 API

#### 全域池 API

```python
# GET /api/admin/global-leads
# 取得全域池所有 leads
@router.get("/admin/global-leads")
def get_admin_global_leads(
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    leads = db.query(models.GlobalLead).order_by(
        models.GlobalLead.id.desc()
    ).offset(skip).limit(limit).all()
    return [l.to_dict() for l in leads]


# PATCH /api/admin/global-leads/{lead_id}
# 編輯全域池單筆資料
@router.patch("/admin/global-leads/{lead_id}")
def update_global_lead(
    lead_id: int,
    payload: GlobalLeadUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    lead = db.query(models.GlobalLead).filter(
        models.GlobalLead.id == lead_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該公司")
    
    # 更新欄位
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(lead, key, value)
    
    lead.updated_at = datetime.utcnow()
    db.commit()
    
    add_log(f"Admin {current_user.email} 更新全域池公司: {lead.company_name}")
    return lead.to_dict()


# DELETE /api/admin/global-leads/{lead_id}
# 刪除全域池單筆資料
@router.delete("/admin/global-leads/{lead_id}")
def delete_global_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    lead = db.query(models.GlobalLead).filter(
        models.GlobalLead.id == lead_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該公司")
    
    company_name = lead.company_name
    
    # 刪除相關的私域池記錄（FK cascade）
    db.query(models.Lead).filter(
        models.Lead.global_id == lead_id
    ).update({"global_id": None})
    
    db.delete(lead)
    db.commit()
    
    add_log(f"Admin {current_user.email} 刪除全域池公司: {company_name}")
    return {"message": "已刪除", "company_name": company_name}


# POST /api/admin/global-leads/batch-delete
# 批次刪除全域池資料
@router.post("/admin/global-leads/batch-delete")
def batch_delete_global_leads(
    payload: BatchDeletePayload,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    leads = db.query(models.GlobalLead).filter(
        models.GlobalLead.id.in_(payload.ids)
    ).all()
    
    count = len(leads)
    for lead in leads:
        # 清除相關私域池 FK
        db.query(models.Lead).filter(
            models.Lead.global_id == lead.id
        ).update({"global_id": None})
        db.delete(lead)
    
    db.commit()
    
    add_log(f"Admin {current_user.email} 批次刪除全域池 {count} 筆資料")
    return {"message": f"已刪除 {count} 筆", "count": count}
```

#### 用戶工作區 API

```python
# PATCH /api/admin/leads/{lead_id}
# 編輯用戶私域池單筆資料
@router.patch("/admin/leads/{lead_id}")
def update_user_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    lead = db.query(models.Lead).filter(
        models.Lead.id == lead_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(lead, key, value)
    
    lead.updated_at = datetime.utcnow()
    db.commit()
    
    add_log(f"Admin {current_user.email} 更新用戶名單: {lead.company_name}")
    return lead.to_dict()


# DELETE /api/admin/leads/{lead_id}
# 刪除用戶私域池單筆資料
@router.delete("/admin/leads/{lead_id}")
def delete_user_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    lead = db.query(models.Lead).filter(
        models.Lead.id == lead_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    
    company_name = lead.company_name
    user_email = lead.user.email if lead.user else "Unknown"
    
    db.delete(lead)
    db.commit()
    
    add_log(f"Admin {current_user.email} 刪除用戶 {user_email} 的名單: {company_name}")
    return {"message": "已刪除", "company_name": company_name}
```

### 3.2 Pydantic Schemas

```python
class GlobalLeadUpdate(BaseModel):
    company_name: Optional[str] = None
    domain: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    industry_code: Optional[str] = None
    industry_name: Optional[str] = None
    sub_industry_code: Optional[str] = None
    sub_industry_name: Optional[str] = None
    industry_tags: Optional[str] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None

class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    domain: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
    lead_score: Optional[int] = None

class BatchDeletePayload(BaseModel):
    ids: list[int]
```

---

## 4. 前端實作

### 4.1 新增 State

```typescript
// 編輯 Modal
const [editingLead, setEditingLead] = useState<any | null>(null);
const [showEditModal, setShowEditModal] = useState(false);

// 刪除確認
const [deletingLead, setDeletingLead] = useState<any | null>(null);
const [showDeleteModal, setShowDeleteModal] = useState(false);

// 批次選擇
const [selectedIds, setSelectedIds] = useState<number[]>([]);
```

### 4.2 新增 API Functions

```typescript
// api.ts
export const getAdminGlobalLeads = () => fetchWithAuth('/admin/global-leads');

export const updateGlobalLead = (id: number, data: any) => 
  fetchWithAuth(`/admin/global-leads/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data)
  });

export const deleteGlobalLead = (id: number) => 
  fetchWithAuth(`/admin/global-leads/${id}`, {
    method: 'DELETE'
  });

export const batchDeleteGlobalLeads = (ids: number[]) => 
  fetchWithAuth('/admin/global-leads/batch-delete', {
    method: 'POST',
    body: JSON.stringify({ ids })
  });

export const updateAdminLead = (id: number, data: any) => 
  fetchWithAuth(`/admin/leads/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data)
  });

export const deleteAdminLead = (id: number) => 
  fetchWithAuth(`/admin/leads/${id}`, {
    method: 'DELETE'
  });
```

### 4.3 表格新增操作欄

```tsx
<table className="leads-table">
  <thead>
    <tr>
      <th><input type="checkbox" onChange={handleSelectAll} /></th>
      <th>公司名稱</th>
      <th>網域</th>
      <th>Email</th>
      {explorerTab === 'users' && <th>所屬成員</th>}
      <th>AI 標籤</th>
      <th>來源</th>
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    {leads.map(lead => (
      <tr key={lead.id}>
        <td>
          <input 
            type="checkbox" 
            checked={selectedIds.includes(lead.id)}
            onChange={() => handleSelectOne(lead.id)}
          />
        </td>
        <td>{lead.company_name}</td>
        {/* ... 其他欄位 ... */}
        <td>
          <div style={{ display: 'flex', gap: 8 }}>
            <button 
              onClick={() => handleEdit(lead)}
              className="btn-icon-sm"
              title="編輯"
            >
              <Edit2 size={14} />
            </button>
            <button 
              onClick={() => handleDelete(lead)}
              className="btn-icon-sm danger"
              title="刪除"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </td>
      </tr>
    ))}
  </tbody>
</table>
```

---

## 5. 實作清單

### 5.1 後端

- [ ] 新增 `GET /api/admin/global-leads`
- [ ] 新增 `PATCH /api/admin/global-leads/{id}`
- [ ] 新增 `DELETE /api/admin/global-leads/{id}`
- [ ] 新增 `POST /api/admin/global-leads/batch-delete`
- [ ] 新增 `PATCH /api/admin/leads/{id}`
- [ ] 新增 `DELETE /api/admin/leads/{id}`
- [ ] 新增 Pydantic schemas

### 5.2 前端

- [ ] 新增 API functions（`api.ts`）
- [ ] 新增編輯 Modal
- [ ] 新增刪除確認 Modal
- [ ] 表格新增操作欄
- [ ] 新增批次選擇功能
- [ ] 新增批次刪除功能

---

## 6. 測試項目

- [ ] 全域池編輯單筆
- [ ] 全域池刪除單筆
- [ ] 全域池批次刪除
- [ ] 用戶工作區編輯單筆
- [ ] 用戶工作區刪除單筆
- [ ] 刪除全域池時私域池 FK 清除
- [ ] 操作日誌記錄

---

**規格完成，確認後開始實作！**
