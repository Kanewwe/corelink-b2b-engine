# Corelink B2B Engine v2.0

**AI 驅動的 B2B 業務開發自動化平台**

---

## 📌 專案簡介

Corelink B2B Engine 是一套專為 B2B 業務開發設計的自動化平台，整合了：

- **智能爬蟲**：自動從歐美黃頁網站撈取潛在客戶
- **AI 分類**：根據公司描述自動分類到對應產品線
- **Email 發現**：透過 DNS MX 記錄驗證自動找出公司 Email
- **開發信生成**：使用 GPT-4o-mini 生成個人化開發信
- **自動寄信**：支援 SMTP 排程自動發送

---

## 🚀 核心功能

### 1. 全自動探勘引擎 (Auto-Miner)

**功能說明**：
- 輸入產業關鍵字（如 `Cable Manufacturer`）
- 系統自動搜尋美國/歐洲黃頁網站
- 智能過濾並分類潛在客戶
- 自動發現公司 Email 並驗證

**支援平台**：
- 美國：Yellowpages, Yelp, Superpages
- 歐洲：Europages, Yell, PagesJaunes

**去重機制**：
- 自動檢查公司名稱是否已存在
- 檢查網域是否已寄過信
- 標記已寄信客戶，避免重複聯繫

---

### 2. AI 智能分類

**分類邏輯**：
- 使用規則式關鍵字比對（節省 GPT Token）
- 支援 13 種產業分類

| 分類標籤 | 產品線 | 負責人 | 關鍵字範例 |
|---------|--------|--------|-----------|
| NA-CABLE | 線材/線束 | Johnny | cable, wire, harness, connector |
| NA-NAMEPLATE | 銘牌/標籤 | Richard | nameplate, label, tag, badge |
| NA-PLASTIC | 塑膠射出 | Jason | plastic, injection, molding, polymer |
| AUTO-ENGINE | 汽車引擎 | General | engine, piston, crankshaft |
| AUTO-BRAKE | 汽車煞車 | General | brake, rotor, caliper |
| AUTO-SUSPENSION | 汽車懸吊 | General | suspension, shock, strut |
| AUTO-ELECTRICAL | 汽車電系 | General | alternator, starter, sensor |
| AUTO-BODY | 汽車鈑金 | General | bumper, fender, door panel |
| AUTO-INTERIOR | 汽車內裝 | General | seat, dashboard, trim |
| AUTO-TRANSMISSION | 汽車變速 | General | transmission, gearbox, clutch |
| AUTO-EXHAUST | 汽車排氣 | General | exhaust, muffler, catalytic |
| AUTO-COOLING | 汽車冷卻 | General | radiator, thermostat, coolant |

---

### 3. Email 自動發現

**運作流程**：
1. 從公司名稱猜測網域（如 `Tesla` → `tesla.com`）
2. 搜尋引擎驗證網域是否存在
3. DNS MX 記錄檢查（確認可收信）
4. 產生 Email 候選清單

**Email 候選格式**：
- `info@domain.com`
- `contact@domain.com`
- `sales@domain.com`
- `hello@domain.com`
- `support@domain.com`

**標記機制**：
- Generic Email（如 `info@`）會顯示 ⚠️ 警示
- 建議進一步尋找個人信箱

---

### 4. 開發信生成

**使用 GPT-4o-mini**：
- 根據公司名稱、描述、關鍵字生成個人化信件
- 針對不同產品線使用不同模板
- 包含 Corelink Slogan：`From Concept to Connect`

**信件模板管理**：
- 可自建模板，支援變數：
  - `{{company_name}}` - 公司名稱
  - `{{keywords}}` - 關鍵字
  - `{{bd_name}}` - 業務代表名稱
- 每個產品線可設定預設模板
- 支援模板預覽功能

---

### 5. 自動寄信排程

**排程設定**：
- 執行時間：可設定每日幾點執行（預設 09:00）
- 發送間隔：每封信之間延遲秒數（預設 30 秒）
- 每日上限：最多寄幾封信（預設 50 封）

**SMTP 支援**：
- Gmail（需應用程式密碼）
- Outlook/Hotmail
- Yahoo
- 自訂 SMTP 伺服器

**測試連線**：
- 提供「測試連線」按鈕
- 即時驗證 SMTP 是否可用

---

## 📊 頁面功能說明

### 頁面 1：Lead Engine（客戶管理）

**功能列表**：
- 🔍 **搜尋**：依公司名稱搜尋
- 🏷️ **狀態篩選**：已分類 / 已生成信件 / 已寄信
- 🏭 **產業篩選**：Cable / Nameplate / Plastic / Auto Parts
- 🕷️ **Auto-Miner**：輸入關鍵字自動探勘
- 📋 **客戶列表**：顯示公司、負責人、關鍵字、Email
- ✨ **生成開發信**：一鍵生成個人化信件
- ✓ **標記已寄**：手動標記已寄信狀態

**客戶卡片資訊**：
- 公司名稱 + 已寄信徽章
- AI 分類標籤（彩色）
- 負責人
- 狀態
- 關鍵字
- 網域
- Email 候選

---

### 頁面 2：新增客戶

**欄位**：
- 公司名稱（必填）
- 公司網站（選填）

**AI 自動處理**：
- 分析公司描述
- 自動分類產業
- 自動萃取關鍵字
- 自動發現 Email

---

### 頁面 3：寄信記錄

**功能**：
- 📅 日期篩選
- 🏷️ 狀態篩選：草稿 / 已寄出 / 已送達 / 退信 / 失敗
- 📧 查看信件內容
- 🔄 重新寄送
- ✓ 標記回覆

**狀態定義**：
| 狀態 | 說明 | 顏色 |
|------|------|------|
| Draft | 草稿 | 藍色 |
| Sent | 已寄出 | 黃色 |
| Delivered | 已送達 | 綠色 |
| Bounced | 退信 | 紅色 |
| Failed | 失敗 | 紅色 |

---

### 頁面 4：觸及率分析

**統計項目**：
- 各行業別觸及統計
- Open Rate（開信率）
- Click Rate（點擊率）
- Reply Rate（回覆率）
- Bounce Rate（退信率）

**收費標準設定**：
- 基本費用
- 每筆客戶費用
- 開信追蹤費用
- 點擊追蹤費用
- 美元報價

**報價試算**：
- 輸入客戶數量
- 自動計算總費用（台幣/美元）

---

### 頁面 5：搜尋記錄

**功能**：
- 結構化 Log 顯示
- 每次 Auto-Miner 執行摘要
- 顯示：關鍵字、市場、執行時間、新增/跳過/失敗數量
- 完整時間戳（YYYY-MM-DD HH:MM:SS）
- 匯出 CSV
- 清除記錄

---

### 頁面 6：信件模板

**功能**：
- 新增/編輯/刪除模板
- 按產品線分組顯示
- 設為預設模板
- 預覽信件功能

**變數支援**：
- `{{company_name}}` - 公司名稱
- `{{keywords}}` - 關鍵字
- `{{bd_name}}` - 業務代表
- `{{description}}` - 公司描述

---

### 頁面 7：SMTP 設定

**設定項目**：
- SMTP 伺服器
- 埠號
- 發信帳號
- 應用程式密碼（可切換顯示/隱藏）

**排程設定**：
- 執行時間
- 發送間隔
- 每日上限

**測試功能**：
- 測試連線按鈕
- 即時回饋成功/失敗

**常見 SMTP 設定參考表**：
| 服務 | 伺服器 | 埠號 | 備註 |
|------|--------|------|------|
| Gmail | smtp.gmail.com | 587 | 需啟用 2FA + 應用程式密碼 |
| Outlook | smtp-mail.outlook.com | 587 | 使用 Microsoft 帳號 |
| Yahoo | smtp.mail.yahoo.com | 587 | 需啟用「允許應用程式」 |

---

## 🛠️ 技術架構

### 後端
- **框架**：FastAPI
- **資料庫**：PostgreSQL（支援 SQLite）
- **AI**：OpenAI GPT-4o-mini
- **排程**：APScheduler
- **Email 驗證**：DNS MX Record

### 前端
- **技術**：Vanilla HTML + CSS + JavaScript
- **UI 風格**：Glassmorphic Dark Mode
- **特色**：響應式設計、即時日誌

### 部署
- **平台**：Render
- **方式**：Docker
- **資料庫**：Render Managed PostgreSQL

---

## 📦 環境變數

| 變數 | 必填 | 說明 |
|------|------|------|
| `OPENAI_API_KEY` | ✅ | OpenAI API 金鑰 |
| `DATABASE_URL` | ✅ | PostgreSQL 連線字串（Render 自動注入） |
| `ADMIN_USER` | ❌ | 管理員帳號（預設：admin） |
| `ADMIN_PASSWORD` | ✅ | 管理員密碼 |
| `API_TOKEN` | ✅ | API 認證 Token |
| `SMTP_USER` | ❌ | SMTP 發信帳號 |
| `SMTP_PASSWORD` | ❌ | SMTP 密碼 |

---

## 🔐 安全性

- ✅ 密碼從程式碼移至環境變數
- ✅ API Token 認證
- ✅ SMTP 密碼可切換顯示/隱藏
- ✅ 爬蟲速率限制（避免被封鎖）
- ✅ .env 不納入版本控制

---

## 📈 效能優化

- **規則式分類**：取代 GPT Prompt 1，節省 Token
- **DNS MX 驗證**：免費 Email 驗證，無需第三方 API
- **背景任務**：爬蟲和寄信在背景執行，不阻塞 UI
- **去重機制**：避免重複處理相同公司

---

## 🚀 快速開始

### 本機開發

```bash
# 複製專案
git clone https://github.com/Kanewwe/corelink-b2b-engine.git
cd corelink-b2b-engine

# 設定環境變數
cp backend/.env.example backend/.env
# 編輯 .env 填入你的值

# 安裝依賴
cd backend
pip install -r requirements.txt

# 啟動服務
uvicorn main:app --reload
```

### 部署到 Render

1. 推送程式碼到 GitHub
2. 在 Render 建立 PostgreSQL 資料庫
3. 建立 Web Service，連接 GitHub repo
4. 設定環境變數
5. 部署！

詳細步驟請參考 `DEPLOYMENT_GUIDE.md`

---

## 📝 授權

MIT License

---

## 👥 聯絡方式

- **Corelink** - From Concept to Connect
- GitHub: https://github.com/Kanewwe/corelink-b2b-engine

---

**Corelink B2B Engine v2.0** - 讓 B2B 業務開發更智慧、更高效！