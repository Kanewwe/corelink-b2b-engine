# Linkora API Documentation

## 認證方式

### Session-based Auth（新）
使用 Cookie 進行認證，適合瀏覽器前端。

```
POST /api/auth/login
Cookie: session_id=<uuid>
```

### Bearer Token（舊）
使用 Authorization header，適合外部 API 呼叫。

```
Authorization: Bearer <token>
```

---

## 認證 API

### POST /api/auth/register
用戶註冊

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "User Name",
  "company_name": "Acme Corp"
}
```

**Response:**
```json
{
  "message": "註冊成功",
  "session_id": "uuid-string",
  "user": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "User Name",
      "role": "user"
    },
    "plan": {
      "name": "free",
      "display_name": "免費方案",
      "max_customers": 50,
      "max_emails_month": 10,
      "features": {
        "ai_email": false,
        "attachments": false,
        "click_track": false
      }
    },
    "usage": {
      "customers": { "used": 0, "limit": 50 },
      "emails_month": { "used": 0, "limit": 10 }
    }
  }
}
```

---

### POST /api/auth/login
用戶登入

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "message": "登入成功",
  "session_id": "uuid-string",
  "user": { ... }
}
```

---

### POST /api/auth/logout
用戶登出

**Response:**
```json
{
  "message": "已登出"
}
```

---

### GET /api/auth/me
取得當前用戶資訊

**Headers:**
```
Cookie: session_id=<uuid>
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "User Name",
    "company_name": "Acme Corp",
    "role": "user",
    "is_verified": false
  },
  "plan": {
    "name": "free",
    "display_name": "免費方案",
    "features": { ... },
    "max_customers": 50,
    "max_emails_month": 10
  },
  "usage": {
    "customers": { "used": 12, "limit": 50 },
    "emails_month": { "used": 3, "limit": 10 },
    "autominer_runs": { "used": 1, "limit": 3 },
    "templates": { "used": 1, "limit": 1 }
  },
  "subscription": {
    "status": "active",
    "current_period_end": "2026-04-23T00:00:00"
  }
}
```

---

## 方案 API

### GET /api/plans
取得所有方案列表

**Response:**
```json
[
  {
    "id": 1,
    "name": "free",
    "display_name": "免費方案",
    "price_monthly": 0,
    "price_yearly": 0,
    "max_customers": 50,
    "max_emails_month": 10,
    "features": {
      "ai_email": false,
      "attachments": false,
      "click_track": false,
      "open_track": true
    }
  },
  {
    "id": 2,
    "name": "pro",
    "display_name": "專業方案",
    "price_monthly": 890,
    "price_yearly": 8900,
    "max_customers": 500,
    "max_emails_month": 500,
    "features": {
      "ai_email": true,
      "attachments": true,
      "click_track": true,
      "open_track": true
    }
  }
]
```

---

### GET /api/subscription
取得當前用戶訂閱資訊

**Response:** 與 `/api/auth/me` 相同

---

## 客戶 API

### GET /api/leads
取得所有客戶

**Headers:** `Cookie: session_id=<uuid>`

**Query Parameters:**
- `search` - 搜尋公司名稱
- `status` - 狀態篩選
- `tag` - 產業標籤篩選

**Response:**
```json
[
  {
    "id": 1,
    "company_name": "Acme Cable Corp",
    "website_url": "https://acmecable.com",
    "domain": "acmecable.com",
    "email_candidates": "info@acmecable.com",
    "ai_tag": "NA-CABLE",
    "status": "Tagged",
    "assigned_bd": "Johnny",
    "contact_name": "John Smith",
    "contact_role": "Procurement Manager",
    "created_at": "2026-03-23T10:00:00"
  }
]
```

---

### POST /api/leads
新增客戶

**Headers:** `Cookie: session_id=<uuid>`

**Request:**
```json
{
  "company_name": "Acme Cable Corp",
  "website_url": "https://acmecable.com",
  "description": "Custom cable assembly manufacturer"
}
```

**Response:**
```json
{
  "id": 1,
  "company_name": "Acme Cable Corp",
  "ai_tag": "NA-CABLE",
  "status": "Tagged",
  ...
}
```

---

### POST /api/leads/{id}/generate-email
為客戶生成開發信

**Headers:** `Cookie: session_id=<uuid>`

**Response:**
```json
{
  "campaign_id": 1,
  "subject": "Partnership Opportunity - Acme Cable Corp",
  "content": "<html>...personalized email...</html>"
}
```

---

## 模板 API

### GET /api/templates
取得所有模板

**Headers:** `Cookie: session_id=<uuid>`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Cable Standard Template",
    "tag": "NA-CABLE",
    "subject": "Partnership Opportunity - {{company_name}}",
    "body": "<html>...</html>",
    "is_default": true
  }
]
```

---

### POST /api/templates
新增模板

**Headers:** `Cookie: session_id=<uuid>`

**Request:**
```json
{
  "name": "New Template",
  "tag": "NA-CABLE",
  "subject": "Subject Line - {{company_name}}",
  "body": "<html>HTML content...</html>",
  "is_default": false
}
```

---

### POST /api/templates/ai-generate
AI 生成模板

**Headers:** `Cookie: session_id=<uuid>`

**Request:**
```json
{
  "prompt": "Write a professional outreach email for cable manufacturers",
  "style": "professional",
  "language": "english"
}
```

**Response:**
```json
{
  "success": true,
  "html": "<html>Generated email...</html>"
}
```

---

### POST /api/templates/test-send
傳送測試信

**Headers:** `Cookie: session_id=<uuid>`

**Response:**
```json
{
  "success": true,
  "message": "測試信已寄出"
}
```

---

## 爬蟲 API

### POST /api/scrape-simple
觸發簡化爬蟲

**Headers:** `Cookie: session_id=<uuid>`

**Request:**
```json
{
  "market": "US",
  "pages": 3,
  "keywords": ["car parts", "cable assembly", "wire harness"],
  "location": "California",
  "miner_mode": "manufacturer"
}
```

> `miner_mode` 可選値：`"manufacturer"`（預設，適合 B2B 工業品）或 `"yellowpages"`（適合本地服務業）。

**Response:**
```json
{
  "message": "Scraping started for US with 3 keywords"
}
```

---

## 關鍵字 API

### POST /api/keywords/generate
AI 生成相關關鍵字

**Headers:** `Cookie: session_id=<uuid>`

**Request:**
```json
{
  "keyword": "cable",
  "count": 5
}
```

**Response:**
```json
{
  "success": true,
  "keywords": [
    "cable assembly",
    "wire harness",
    "cable connector",
    "cable gland",
    "heat shrink cable"
  ]
}
```

}
```

---

## 系統設定 API

### GET /api/system/settings
取得所有系統設定（包含 API 金鑰與變數映射等）

**Headers:** `Cookie: session_id=<uuid>`

**Response:**
```json
[
  {
    "key": "api_keys",
    "value": {
      "openai_key": "sk-...",
      "openai_model": "gpt-4o",
      "hunter_key": "..."
    },
    "updated_at": "2026-03-25T10:00:00"
  },
  {
    "key": "variable_mapping",
    "value": {
      "company_name": "公司名稱",
      "bd_name": "業務負責人"
    },
    "updated_at": "2026-03-25T10:00:00"
  }
]
```

---

### POST /api/system/settings
更新指定的系統設定項目

**Headers:** `Cookie: session_id=<uuid>`

**Request:**
```json
{
  "key": "variable_mapping",
  "value": {
    "company_name": "公司名稱",
    "location": "營業據點"
  }
}
```

**Response:**
```json
{
  "message": "設定已儲存"
}
```

---

## 追蹤 API（無需認證）

### GET /track/open
開信追蹤像素

**Query Parameters:**
- `id` - Email log UUID

**Response:** 1x1 transparent PNG

---

### GET /track/click
點擊追蹤重導向

**Query Parameters:**
- `id` - Email log UUID
- `url` - 原始 URL（URL encoded）

**Response:** 302 Redirect to target URL

---

## 觸及率 API

### GET /api/engagements
取得觸及率統計

**Headers:** `Cookie: session_id=<uuid>`

**Response:**
```json
{
  "records": [
    {
      "id": 1,
      "log_uuid": "uuid",
      "company_name": "Acme Corp",
      "ai_tag": "NA-CABLE",
      "status": "delivered",
      "opened": true,
      "clicked": false,
      "replied": false
    }
  ],
  "tag_stats": {
    "NA-CABLE": {
      "total": 10,
      "delivered": 9,
      "opened": 4,
      "clicked": 2,
      "replied": 1
    }
  },
  "stats": {
    "total_sent": 10,
    "delivered": 9,
    "delivered_rate": 90.0,
    "opened": 4,
    "open_rate": 44.4,
    "clicked": 2,
    "click_rate": 22.2,
    "replied": 1,
    "reply_rate": 11.1
  }
}
```

---

### POST /api/engagements/{log_uuid}/reply
手動標記回覆

**Headers:** `Cookie: session_id=<uuid>`

**Response:**
```json
{
  "message": "Email marked as replied"
}
```

---

## 錯誤回應

### 401 Unauthorized
```json
{
  "detail": "請先登入"
}
```

### 403 Forbidden
```json
{
  "detail": {
    "error": "feature_not_available",
    "message": "此功能需要升級至專業方案",
    "current_plan": "free",
    "required_plan": "pro"
  }
}
```

### 429 Usage Limit Exceeded
```json
{
  "detail": {
    "error": "usage_limit_exceeded",
    "message": "本月 email 用量已達上限（10/10）",
    "type": "email",
    "used": 10,
    "limit": 10,
    "upgrade_required": true,
    "current_plan": "free"
  }
}
```
