# SA 快速技術架構指南 (System Architect Guide)

## 🏗️ 全域架構 (Architecture)
Linkora v3.1.8 採用 **PostgreSQL Schema-based** 多租戶隔離架構，確保數據邊界與擴展性。

## 🚀 快速跳轉 (Quick Links)
- 📋 **[核心需求與邏輯規範](REQUIREMENTS_LOGIC.md)**: 已完成需求的技術邏輯與追蹤矩陣。
- 📊 **[系統功能規格與執行計畫](FUNCTIONAL_SPECIFICATION.md)**: 未來 Sprints (v3.3-v3.5) 的詳細設計與排程。
- 🏗️ **[角色權限架構 (RBAC)](ROLE_ARCHITECTURE.md)**: Admin / Vendor / Member 權限劃分與對帳邏輯。
- 🛡️ **[名單隔離與全域同步架構](LEAD_ISOLATION_ARCHITECTURE.md)**: `leads` 與 `global_leads` 的同步原理。
- 🤖 **[Agent 技術手冊 (Skill Book)](AGENT_SKILL_BOOK.md)**: 針對 AI Agent 優化的技術細節與路徑。

## 🛠️ 常見 SA 任務 (SOP)
1. **設計新資料表**：務必考慮 Schema 隔離，並同步更新 `AGENT_SKILL_BOOK.md`。
2. **審核權限擴充**：確認是否有越權威脅 (Horizontal/Vertical Privilege Escalation)。
3. **優化數據同步**：調整 `global_leads` 的去重邏輯以節省採集成本。

---
*OpenClaw Optimized Guide - Role: SA*
