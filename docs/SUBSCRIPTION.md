# Linkora 訂閱系統架構

## 概述

Linkora 採用訂閱制商业模式，提供三種方案讓不同規模的企業使用。

## 方案定義

| 欄位 | Free | Pro | Enterprise |
|------|------|------|------------|
| **價格** | $0/月 | $29/月 | $99/月 |
| **客戶數上限** | 50 | 500 | 無限 |
| **每月寄信** | 10 | 500 | 無限 |
| **Auto-Miner 次數** | 3/月 | 30/月 | 無限 |
| **模板數** | 1 | 10 | 無限 |

## 功能開關

| 功能 | Free | Pro | Enterprise |
|------|------|------|------------|
| 開信追蹤 | ✅ | ✅ | ✅ |
| AI 信件生成 | ❌ | ✅ | ✅ |
| 夾帶附件 | ❌ | ✅ | ✅ |
| 點擊追蹤 | ❌ | ✅ | ✅ |
| Hunter.io 整合 | ❌ | ✅ | ✅ |
| CSV 匯入 | ❌ | ✅ | ✅ |
| API 存取 | ❌ | ❌ | ✅ |

## 資料模型

### users
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,  -- bcrypt
  name VARCHAR(100),
  company_name VARCHAR(200),
  role VARCHAR(20) DEFAULT 'user',    -- 'user' or 'admin'
  is_active BOOLEAN DEFAULT TRUE,
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### sessions
```sql
CREATE TABLE sessions (
  id VARCHAR(36) PRIMARY KEY,  -- UUID
  user_id INT REFERENCES users(id),
  ip_address VARCHAR(45),
  user_agent TEXT,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  last_active_at TIMESTAMP DEFAULT NOW()
);
```

### plans
```sql
CREATE TABLE plans (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL,  -- 'free', 'pro', 'enterprise'
  display_name VARCHAR(100),
  price_monthly DECIMAL(10,2),
  max_customers INT DEFAULT 50,
  max_emails_month INT DEFAULT 10,
  max_templates INT DEFAULT 1,
  max_autominer_runs INT DEFAULT 5,
  feature_ai_email BOOLEAN DEFAULT FALSE,
  feature_attachments BOOLEAN DEFAULT FALSE,
  feature_click_track BOOLEAN DEFAULT FALSE,
  feature_open_track BOOLEAN DEFAULT TRUE
);
```

### subscriptions
```sql
CREATE TABLE subscriptions (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  plan_id INT REFERENCES plans(id),
  status VARCHAR(20) DEFAULT 'active',  -- 'active', 'cancelled', 'expired'
  current_period_start TIMESTAMP,
  current_period_end TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### usage_logs
```sql
CREATE TABLE usage_logs (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  period_year INT NOT NULL,
  period_month INT NOT NULL,
  customers_count INT DEFAULT 0,
  emails_sent_count INT DEFAULT 0,
  autominer_runs_count INT DEFAULT 0,
  templates_count INT DEFAULT 0,
  UNIQUE(user_id, period_year, period_month)
);
```

## 認證流程

```
用戶請求
    ↓
檢查 session_id Cookie
    ↓
查詢 sessions 表（未過期）
    ↓
取得 user_id
    ↓
查詢 subscriptions（有效訂閱）
    ↓
取得 plan
    ↓
根據 plan 決定權限
```

## 權限檢查

### check_feature(feature_name)
檢查方案是否包含某功能：
```python
@ Depends(check_feature("ai_email"))
```

### check_usage_limit(limit_type)
檢查用量是否超限：
```python
@ Depends(check_usage_limit("email"))
```

## 用量追蹤

### 每月重置
- `usage_logs` 依據 `period_year` + `period_month` 區分
- 每月第一天自動建立新紀錄

### 更新時機
| 操作 | 更新欄位 |
|------|---------|
| 新增客戶 | `customers_count++` |
| 寄出 Email | `emails_sent_count++` |
| Auto-Miner 執行 | `autominer_runs_count++` |
| 新增模板 | `templates_count++` |

## 未來擴展

### 金流整合
- Stripe（國際信用卡）
- 綠界 ECPay（台灣本地）

### 試用期
```python
subscription.trial_start = datetime.utcnow()
subscription.trial_end = datetime.utcnow() + timedelta(days=14)
```

### 升級/降級
- 升級：立即生效，按比例計費
- 降級：下次帳單週期生效
