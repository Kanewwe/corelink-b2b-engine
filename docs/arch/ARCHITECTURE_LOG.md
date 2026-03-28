# Linkora 系統架構技術日誌 (Architecture Tech Log)

> **版本：** v3.7.21 (2026-03-29)  
> **狀態：** 核心架構穩定，進入移動端與效能優化階段。

---

## 🏗️ 核心技術堆疊 (The Stack)

### 1. 後端 (Backend Engine)
- **框架**：FastAPI (Python 3.10+) - 選用理由：非同步 I/O 處理高併發爬蟲與郵件任務。
- **資料庫 ORM**：SQLAlchemy 1.4 / 2.0 (Async Session) - 支援複雜的 Leads 關係查詢。
- **驗證機制**：JWT (JSON Web Token) + Bearer Token - 確保跨服務調用的安全性。
- **背景任務**：APScheduler / asyncio tasks - 定時執行探勘 (Scrape) 與投遞任務。

### 2. 前端 (Frontend Dashboard)
- **框架**：React 18 + Vite - 高效能建置與模組化開發。
- **狀態管理**：React Context API (Auth, UI State) - 輕量化系統狀態同步。
- **樣式系統**：Vanilla CSS + Tailwind-like Utilities - 保持極致的加載速度與動畫流暢度。
- **圖表庫**：Recharts / Lucide React - 視覺化開發成效。

### 3. 基礎設施 (Infrastructure)
- **託管平台**：Render (PaaS) - 分為 Web Service (API) 與 Static Site (Frontend)。
- **資料庫**：Postgres (Managed) - 處理大規模企業級 Lead 資料。
- **通訊協議**：RESTful API / CORS Enabled (v3.7.20 已結構化解決 Missing Header 問題)。

---

## 📡 關鍵數據流 (Data Flow)

1.  **探勘流 (Mining)**：Scraper -> SQLAlchemy -> Postgres (Leads Table)。
2.  **認證流 (Auth)**：Login -> JWT Issue -> LocalStorage -> API Request Header。
3.  **遙測流 (Telemetry)**：Email Sent -> Pixel Track -> Webhook -> DB -> UI Analytics。

---

## ⚠️ 性能預警與脆弱點 (Performance & Bottlenecks)

### 1. 爬蟲延遲 (Scraper Latency)
- **現象**：當大量併發挖掘時，外部 API 響應時間可能增加。
- **優化方案**：已實作多策略瀑布執行 (Multi-strategy Waterfall)，確保單一來源失效時自動切換。

### 2. 資料庫連線池 (DB Pooling)
- **現象**：Render Small 實例有連線數限制。
- **優化方案**：在 `main.py` 與各頁面邏輯中實施嚴格的 `db.close()` 與非同步解耦。

### 3. AI 評分耗時 (AI Scoring)
- **現象**：對 Lead 進行全自動背景研究與評分需等待 LLM 響應。
- **優化方案**：異步處理，前端顯示 Loading 狀態，完成後推送更新。

---
*本文件旨在作為系統效能診斷的「地圖」，由 Linkora Tech Lead 模組維護。*
