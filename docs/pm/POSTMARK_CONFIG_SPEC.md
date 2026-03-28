# PM Spec: Postmark Email Channel Configuration (v3.5)

> **版本**：1.0.0 (2026-03-28)  
> **目標**：實現「分秒級」配置 Postmark 專業發信通道，取代初階 SMTP，降低垃圾信風險。

---

## 🎨 頁面設計與交互引導 (UX Flow)

配置頁面由目前的單一表單改為 **「引導式嚮導 (Config Wizard)」** 模式，共分為 5 個核心步驟。

### Step 1: 帳號連結與 API 授權 (The Hook)
- **視覺重點**：顯示 Postmark 官方 Logo 與「推薦」標誌。
- **欄位設計**：
    - `Server API Token` (必填)：輸入框類型為 `password`，具備「顯示/隱藏」眼球圖示。
    - 旁邊附帶問號圖示：點擊彈出「如何前往 Postmark 取得 Token」截圖指引。
- **功能連結**：一鍵跳轉至 [Postmark Signup](https://postmarkapp.com/signup)。

### Step 2: 寄件人身份定義 (Identity)
- **欄位設計**：
    - `From Email` (必填)：預設帶入用戶帳號，但允許變更。
    - `From Name` (選填)：預設為「Linkora Outreach」。
    - `Message Stream` (進階)：預設設為 `outbound`。
- **即時提示**：下方顯示「注意：此 Email 必須已在 Postmark 通過 Sender Signature 驗證」。

### Step 3: DNS 強制合規建議 (Health)
- **核心內容**：針對用戶的域名自動產出 SPF、DKIM、DMARC 的 TXT/CNAME 指引。
- **動態輔助**：如果用戶尚未在 Postmark 完成驗證，呈現「狀態：待驗證 ⚠️」紅字警告。
- **外部資源**：連結至 [Postmark Domain Verification Help](https://postmarkapp.com/support/article/1057-how-to-verify-your-domain)。

### Step 4: 通道即時測試 (Verification)
- **操作區塊**：
    - 測試收件人：預設填入登入者 Email。
    - 按鈕：「立即發送測試郵件 ✨」。
- **反饋機制**：
    - 成功：顯示「🎉 發送成功！請檢查收件箱（含垃圾郵箱）」。
    - 失敗：渲染 Postmark API 回傳的精確錯誤訊息（例如：`Invalid API Token`, `Inactive Sender Signature`）。

### Step 5: 成功激活與切換 (Activation)
- **配置切換**：儲存後，系統自動將 `Email_Channel_Provider` 切換為 `Postmark`。
- **降級路徑**：下方保留「切換回傳統 SMTP」鏈結，供進階用戶自訂。

---

## 🏗️ 後端架構與 API 規劃 (System Architecture)

### 1. 資料模型演進 (Model Change)
`SMTPSettings` 表將重新命名或擴展為 `EmailChannelSettings`：

| 欄位 | 類型 | 說明 |
| :--- | :--- | :--- |
| `provider` | Enum | `smtp`, `postmark`, `resend` (預設為 `postmark`) |
| `api_token` | Encrypted String | Postmark Server Token / API Key |
| `message_stream`| String | `outbound`, `broadcast` (預設為 `outbound`) |
| `is_active` | Boolean | 當前是否正在使用此通道 |

### 2. 邏輯分支 (Dispatch Logic)
在 `email_sender_job.py` 中引入 Provider Factory：

```python
def send_via_postmark(api_token, from_email, to_email, subject, body):
    # 使用官方 postmark-python SDK
    # 支援 X-PM-Message-Stream 標頭
    pass

def send_via_smtp(host, user, pwd, ...):
    # 現行的 smtplib 邏輯
    pass
```

### 3. API 端點擴展
- `GET /api/settings/email-channel`：獲取當前通道類型與配置摘要。
- `POST /api/settings/postmark`：儲存並驗證 Postmark Token。
- `POST /api/test/postmark`：觸發測試信 API。

---

## 📈 商業指標分析 (KPI)

- **Deliverability**：目標讓 v3.5 用戶的 Cold Email 進入收件箱比率提升至 **90%+**。
- **Setup Time**：目標配置完成時間從傳統的 10+ 分鐘縮短至 **3 分鐘**（只需 API Token）。

---
*Created by Antigravity AI - System Optimization v3.5*
