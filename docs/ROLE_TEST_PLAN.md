# Linkora B2B 引擎 — 角色測試計畫

> **版本：** 1.0.0  
> **建立日期：** 2026-03-26  
> **適用對象：** Admin / Vendor / Member 三種角色

---

## 一、角色權限矩陣

| 功能模組 | Admin (管理員) | Vendor (委外廠商) | Member (一般會員) |
|----------|---------------|------------------|------------------|
| **探勘功能** | | | |
| 精準開發雷達 (爬蟲) | ✅ | ✅ | ✅ |
| 黃頁模式 | ✅ | ✅ | ✅ |
| 製造商模式 | ✅ | ✅ | ✅ |
| **郵件功能** | | | |
| 智慧行銷劇本 (模板) | ✅ | ✅ | ✅ |
| 自動化投遞 (寄信) | ✅ | ✅ | ✅ |
| **分析功能** | | | |
| 成效分析雷達 | ✅ 全系統 | ✅ 個人/公司資料 | ✅ 個人資料 |
| 開發紀錄專區 | ✅ 全系統 | ✅ 個人/公司資料 | ✅ 個人資料 |
| **管理功能** | | | |
| 發信通道配置 | ✅ | ✅ | ✅ |
| 會員管理 | ✅ | ❌ | ❌ |
| 委外廠商管理 | ✅ | ❌ | ❌ |
| 系統控制中心 | ✅ | ❌ | ❌ |
| **帳務功能** | | | |
| 批發對帳 (Vendor) | ❌ | ✅ 三維度對帳 | ❌ |
| 用量監控 | ✅ 全系統 | ✅ 各維度累計 | ✅ 個人資料 |

---

## 二、角色測試計畫

### 2.1 Admin (管理員) 測試

#### A1 — 系統管理功能

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| A1.1 | 登入 admin@linkora.com | 成功，顯示 Admin 側邊欄 |
| A1.2 | 進入「會員管理」 | 可見所有會員列表 |
| A1.3 | 進入「委外廠商管理」 | 可見所有廠商列表 |
| A1.4 | 進入「系統控制中心」 | 可見 API 設定頁面 |
| A1.5 | 查看「成效分析雷達」 | 可切換查看所有廠商數據 |

#### A2 — 會員管理操作

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| A2.1 | 搜尋會員 (by email) | 正確過濾結果 |
| A2.2 | 編輯會員角色 (member → vendor) | 更新成功，Toast 通知 |
| A2.3 | 停用會員帳號 | is_active = false，無法登入 |
| A2.4 | 重設會員密碼 | 生成臨時密碼，可登入 |
| A2.5 | 查看會員用量統計 | 顯示 leads / emails / open rate |

#### A3 — 廠商管理操作

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| A3.1 | 新增委外廠商 | 建立廠商帳號 + 定價設定 |
| A3.2 | 編輯廠商定價 | 更新 per_lead 價格 |
| A3.3 | 停用廠商帳號 | 旗下會員無法登入 |
| A3.4 | 查看廠商對帳報表 | 顯示批發應付金額 |

#### A4 — 系統設定

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| A4.1 | 設定 OpenAI API Key | 加密儲存，可測試 AI 功能 |
| A4.2 | 設定 Hunter.io Key | Email 發現策略可用 hunter |
| A4.3 | 設定 Google CSE | 製造商模式可用 |
| A4.4 | 編輯變數標籤映射 | 模板編輯器顯示自定義標籤 |

---

### 2.2 Vendor (委外廠商) 測試

#### V1 — 登入與權限

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| V1.1 | 登入廠商帳號 | 成功，側邊欄無「管理」選項 |
| V1.2 | 嘗試進入 /admin/members | 403 Forbidden |
| V1.3 | 嘗試進入 /admin/vendors | 403 Forbidden |
| V1.4 | 嘗試進入 /admin/settings | 403 Forbidden |

#### V2 — 旗下會員管理

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| V2.1 | 查看「成效分析雷達」 | 僅顯示旗下會員數據 |
| V2.2 | 查看「開發紀錄專區」 | 僅顯示旗下會員任務 |
| V2.3 | 查看用量統計 | 彙整旗下所有會員用量 |

#### V3 — 批發對帳

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| V3.1 | 查看對帳報表 | 顯示本月累積 leads × 單價 |
| V3.2 | 確認對帳金額 | 狀態更新為「已確認」 |
| V3.3 | 匯出對帳 CSV | 下載成功，格式正確 |

---

### 2.3 Member (一般會員) 測試

#### M1 — 登入與權限

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| M1.1 | 登入一般會員帳號 | 成功，側邊欄無「管理」選項 |
| M1.2 | 嘗試進入 /admin/* | 全部 403 Forbidden |
| M1.3 | 嘗試查看其他會員資料 | 403 Forbidden |

#### M2 — 核心功能

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| M2.1 | 執行黃頁爬蟲 | 任務啟動，History 顯示記錄 |
| M2.2 | 執行製造商爬蟲 | 任務啟動，需有 GOOGLE_API_KEY |
| M2.3 | 建立郵件模板 | 儲存成功，可使用變數 |
| M2.4 | 執行自動化投遞 | 郵件發送，狀態追蹤正常 |
| M2.5 | 查看個人成效分析 | 僅顯示自己的數據 |

#### M3 — 用量限制

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| M3.1 | 超出每月 leads 配額 | 提示升級方案 |
| M3.2 | 超出每月郵件配額 | 提示升級方案 |
| M3.3 | 查看用量儀表 | 正確顯示已用/剩餘 |

---

## 三、跨角色互動測試

### 3.1 Vendor → Member 關係

```
### 3.1 平台資源分配測試 (Admin → Vendor)
1. Admin 建立 Vendor A (簽約合約)
2. Admin 為 Vendor A 設定 `pricing_config` (發送$0, 觸及$5, 成交$500)
3. Vendor A 執行大量開發任務
4. Admin 查核該 Vendor A 的對帳報表是否正確彙總三維度數據
```

### 3.2 權限隔離測試

| 測試項 | 操作 | 預期結果 |
|--------|------|---------|
| X1 | Member A 嘗試查看 Member B 的 leads | 403 Forbidden |
| X2 | Vendor A 嘗試查看 Vendor B 的資料 | 403 Forbidden |
| X3 | Vendor A 嘗試查看 Admin 下的 Member | 403 Forbidden |
| X4 | Admin 查看任意用戶資料 | 200 OK |

---

## 四、自動化測試腳本

### 4.1 角色權限測試

```python
# tests/test_roles.py

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_admin_can_access_admin_routes():
    """Admin 可存取所有管理路由"""
    # Login as admin
    # Try access /api/admin/members
    # Expect 200
    pass

def test_vendor_cannot_access_admin_routes():
    """Vendor 不可存取管理路由"""
    # Login as vendor
    # Try access /api/admin/members
    # Expect 403
    pass

def test_member_cannot_access_admin_routes():
    """Member 不可存取管理路由"""
    # Login as member
    # Try access /api/admin/members
    # Expect 403
    pass

def test_vendor_can_only_see_own_members():
    """Vendor 僅可查看旗下會員"""
    # Login as vendor
    # Get /api/analytics
    # Verify only own members' data
    pass

def test_member_can_only_see_own_data():
    """Member 僅可查看自己的資料"""
    # Login as member A
    # Try get member B's leads
    # Expect 403
    pass
```

### 4.2 業務流程測試

```python
# tests/test_business_flow.py

def test_vendor_member_workflow():
    """完整 Vendor-Member 業務流程"""
    # 1. Admin 建立 Vendor
    # 2. Admin 建立 Member，指定給 Vendor
    # 3. Member 執行爬蟲
    # 4. Vendor 查看對帳報表
    # 5. Admin 查看全系統報表
    pass
```

---

## 五、測試環境設定

### 5.1 測試帳號

| 角色 | Email | Password | 用途 |
|------|-------|----------|------|
| Admin | admin@linkora.com | (env 設定) | 全系統管理 |
| Vendor A | vendor-a@test.com | test123 | 廠商測試 |
| Vendor B | vendor-b@test.com | test123 | 隔離測試 |
| Member A1 | member-a1@test.com | test123 | Vendor A 旗下 |
| Member A2 | member-a2@test.com | test123 | Vendor A 旗下 |
| Member B1 | member-b1@test.com | test123 | Vendor B 旗下 |

### 5.2 測試資料

```sql
-- 初始化測試資料
INSERT INTO users (email, role, is_active) VALUES
('vendor-a@test.com', 'vendor', true),
('vendor-b@test.com', 'vendor', true),
('member-a1@test.com', 'member', true),
('member-a2@test.com', 'member', true),
('member-b1@test.com', 'member', true);

-- 設定 vendor_id 關係
UPDATE users SET vendor_id = (SELECT id FROM users WHERE email = 'vendor-a@test.com')
WHERE email IN ('member-a1@test.com', 'member-a2@test.com');

UPDATE users SET vendor_id = (SELECT id FROM users WHERE email = 'vendor-b@test.com')
WHERE email = 'member-b1@test.com';
```

---

## 六、測試排程

| 階段 | 時間 | 內容 |
|------|------|------|
| Day 1 | 2h | Admin 功能完整測試 |
| Day 1 | 2h | Vendor 功能完整測試 |
| Day 2 | 2h | Member 功能完整測試 |
| Day 2 | 2h | 跨角色互動測試 |
| Day 3 | 4h | 自動化測試腳本開發 |
| Day 4 | 4h | 整合測試與錯誤修復 |

---

## 七、驗收標準

- [ ] Admin 可完整管理會員、廠商、系統設定
- [ ] Vendor 僅可查看旗下會員資料與對帳報表
- [ ] Member 僅可查看自己的資料，無法存取他人資料
- [ ] 權限隔離嚴格，無越權存取漏洞
- [ ] 跨角色資料彙整正確 (Vendor 看到旗下會員彙總)
- [ ] 自動化測試覆蓋率 > 80%

---

*測試計畫由 Ann 建立*
