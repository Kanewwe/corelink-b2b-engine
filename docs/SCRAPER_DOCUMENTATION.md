# Linkora 爬蟲系統技術文件 (v2.6)

> **版本：** 2.6.0  
> **建立日期：** 2026-03-26  
> **維護者：** Antigravity AI  
> **適用範圍：** UAT/PRD 環境

---

## 一、系統架構 (Database-First Config)

### 1.1 動態配置流程 (New in v2.6)

從 v2.6 開始，所有外部工具的 API Key 優先從資料庫讀取，確保無需重新部署即可更新服務：

```
┌──────────────────┐      ┌────────────────────────┐      ┌─────────────────────┐
│   管理員/使用者   │ ───► │ 系統設定 (DB)            │ ───► │ config_utils.py     │
│   (設定介面)      │      │ system_settings 表      │      │ (優先排序邏輯)        │
└──────────────────┘      └────────────────────────┘      └──────────┬──────────┘
                                                                     │
                                             ┌───────────────────────┴───────────────────────┐
                                             ▼                       ▼                       ▼
                                   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
                                   │ OpenAI (GPT-4o)  │    │ Apify (Scraper)  │    │ Hunter.io (Email)│
                                   └──────────────────┘    └──────────────────┘    └──────────────────┘
```

### 1.2 爬蟲任務流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                          後端 API 層                                 │
│  POST /api/scrape-simple (主要入口)                                  │
│  ├── miner_mode: "yellowpages"  → scrape_simple.py (Apify 版)       │
│  ├── miner_mode: "manufacturer" → manufacturer_miner.py (Apify 版)   │
│  └── email_strategy: "free" / "hunter"                              │
└─────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          資料來源層 (Apify 優先)                    │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Yellowpages 模式 (Apify Actor)                                  │ │
│  │ • Actor: automation-lab/yellowpages-scraper                     │ │
│  │ • 備援：Mock Mode (當 API Key 失敗時)                           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ 製造商模式 (Apify 混合模式)                                      │ │
│  │ • Thomasnet Scraper (Apify)                                     │ │
│  │ • Yellowpages Scraper (Apify 備援)                              │ │
│  │ • 排除 ENTERPRISE_BLACKLIST (不爬跨國大企業)                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、API 規格 (無變更)

### 2.1 啟動爬蟲任務
- **Endpoint**: `POST /api/scrape-simple`
- **Auth**: `Bearer <token>`
- **Body**: 原有規格不變，後端會自動根據 `user_id` 查找對應的 Key。

---

## 三、外部工具設定 (API Key Management)

### 3.1 關鍵字對照表

在 `system_settings` 的 `api_keys` JSON 中，應包含以下 Key：

| JSON Key | 對應工具 | 說明 |
|----------|----------|------|
| `openai_key` | OpenAI | 用於 AI 標籤分類與開發信生成 |
| `openai_model` | OpenAI | 指定模型 (如 `gpt-4o-mini`, `gpt-4o`) |
| `apify_token` | Apify | 用於 Yellowpages 與 Manufacturer 模式 |
| `hunter_key` | Hunter.io | 用於找到目標公司聯絡人的 Email |
| `google_key` | Google Search | (備援) Google Custom Search API Key |

### 3.2 讀取優先級
1. **User Setting**: 使用者自己設定的 Key。
2. **Admin Setting**: 管理員 (id:1) 設定的全局 Key。
3. **Environment**: `.env` 檔案中的變數。

---

## 四、日誌與監控 (New in v2.6)

### 4.1 資料庫日誌 (scrape_logs)
所有的爬蟲步驟、成功新增、跳過原因、網絡錯誤等，現在都會寫入 `scrape_logs` 表，以便在後台「Scrape Monitor」中即時查看。

### 4.2 任務狀態
- `Running`: 正在執行。
- `Completed`: 任務正常結束。
- `Failed`: 遭遇不可恢復錯誤。
- `Retried->#ID`: 該任務已被重試。

---

## 五、開發者指南

### 5.1 如何新增工具 Key
1. 在 `config_utils.py` 的 `mapping` 字典中新增工具對應。
2. 在 `docs/DATABASE.md` 更新文件。
3. 使用 `get_api_key(db, "your_tool", user_id)` 讀取設定。

---
*本文件由 Antigravity AI 持續更新中*
