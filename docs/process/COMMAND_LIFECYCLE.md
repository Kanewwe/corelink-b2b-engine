# Linkora 指令生命週期 (Command Lifecycle)

本文件定義了一項開發需求（指令）從發出到完全落地的完整路徑。這套流程旨在確保 **需求不偏離、程式品質穩定、且具備可追蹤性**。

## 📊 7 階段交付模型 (The 7-Stage Delivery Model)

### 1. Ingestion (指令輸入)
- **來源**：用戶請求 (User Request)。
- **目標**：識別任務目標、優先級與相關背景（Corpus context）。
- **產出**：明確的開發意圖。

### 2. Analysis & Context Mapping (語意分析與上下文對照)
- **動作**：AI 代理人比對 Knowledge Items (KIs)、現行代碼架構與 API 路徑。
- **目標**：確保不重複造輪子，並遵循現有的技術規範（如 v3.7 安全機制）。

### 3. Planning & Review (方案建立與審核)
- **動作**：建立 `implementation_plan.md`。
- **指標 [CRITICAL]**：重大邏輯變更必須獲得用戶批准。
- **目標**：達成技術共識，降低實作過程中的不確定性。

### 4. Implementation (執行實作)
- **動作**：進行程式碼編輯 (Code Editing)、工具調用、環境設定。
- **目標**：將核准的計畫轉化為實際代碼。

### 5. Verification (品質校驗)
- **動作**：本地建置 (`npm run build`)、自動化測試、UI 模擬驗證。
- **指標**：**Definition of Done (DoD)** 包含「無 Lint 錯誤」及「核心路徑通過驗證」。

### 6. Promotion (交付推播)
- **動作**：Git Push 觸發 CI/CD 流程同步至 UAT 環境。
- **目標**：將變更推向準生產環境進行最終預覽。

### 7. Final Review & Archiving (最終歸檔與成果回顧)
- **動作**：更新 `walkthrough.md` 與任務結算 (Task Cleanup)。
- **目標**：沉澱技術經驗並正式結項。

---

## 🛡️ 品質基準 (Quality Standards)

1.  **完整性**：所有新增接口必須具備 X-Signature (HMAC) 校驗或對應之安全層。
2.  **穩定性**：所有 SQLAlchemy 操作必須遵循 v3.7 的 Session 解耦規範。
3.  **可讀性**：關鍵邏輯必須包含清晰的中文註釋 (v3.1.8+ 標準)。

---
*Last Updated: 2026-03-28*
