# 🚀 Linkora B2B Lead Gen & AI Outreach (v3.1.8)

![Version](https://img.shields.io/badge/Version-v3.1.8--resilience-blue?style=flat-glass)
![Environment](https://img.shields.io/badge/Environment-UAT-orange?style=flat-glass)
![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20Postgres-61dafb?style=flat-glass)

Linkora 是一套專門為 B2B 團隊設計的**自動化客戶開發平台**。透過 AI 技術實作「精準探勘、個人化聯繫、與多租戶用量管理」的一站式解決方案。

---

## 📢 最新動態 (What's New)
> [!NOTE]
> 擷取自 `CHANGELOG.md` 的最新三次更新。

- **[v3.1.8] 🏭 製造商引擎重構**: 全面升級至 `zen-studio` 爬蟲，實作 180s 任務強制超時保護。
- **[v2.7.2] 🌏 時區本地化**: 後端統一採用台灣時區 (UTC+8) 統計報表，優化成效漏斗計算。
- **[v2.7.1] 🛡️ 全域隔離池**: 實作跨用戶去重，優先從情報庫同步，大幅節省 API 呼叫成本。

---

## 👔 職能導覽入口 (Role Portal)
根據您的角色，快速點選下方的 **README 行動指南** 以獲取對應的 SOP：

| 職能入口 (Portals) | 核心職責 | 快速作業 (SOP) |
| :--- | :--- | :--- |
| **👑 [PM Portal](docs/pm/)** | 產品規劃、Roadmap | 需求審核、案量決策 |
| **🏗️ [SA Portal](docs/sa/)** | 架構設計、Agent 優化 | 多租戶隔離設計、性能調優 |
| **🖥️ [Backend (BEPG)](docs/bepg/)** | API 規格、爬蟲引擎 | 接口測試、DB 遷移 |
| **🎨 [Frontend (FEPG)](docs/fepg/)** | UI/UX 標準、React 組件 | 用戶體驗優化、視覺調整 |
| **🧪 [QA Portal](docs/qa/)** | 驗收基準、各角色測試 | 版本驗收、權限邊界測試 |
| **🚀 [DevOps Portal](docs/devops/)** | 部署、在線監控、除錯 | 災難復原、SQL 數據補全 |
| **📊 [DBA Portal](docs/dba/)** | 資料庫 Schema、隔離切換 | 資料遷移、索引優化 |
| **💼 [Business Portal](docs/business/)** | 業務 ROI、定價與營收 | 市場分析、轉換率追蹤 |

---

## 🛠️ 快速啟動 (Quick Start)

### 1. 本地啟動 (開發環境)
```bash
# 啟動後端與前端靜態掛載
cd backend && python main.py
```

### 2. 環境變數配置
請參考各職能入口中的 `.env.example` 說明進行設定。

---

## 📚 詳細資源
- 📜 **[完整更新日誌 (Changelog)](CHANGELOG.md)**
- 📖 **[全域技術白皮書 (Handbook)](project_handbook.md)**

---
*Created by Antigravity AI - System Optimization v3.1.8*
