# QA Standard Operating Procedure (SOP) - Linkora v3.5

## 1. 目的 (Objective)
確保所有新功能、資料庫異動及核心邏輯 (Scraper, Billing) 在交付前均經過自動化驗證，並保留詳細的測試日誌以供後續稽核 (Audit) 與除錯 (Debug)。

## 2. 測試流程 (The Process)

### 2.1 每日自動測試 (Daily Testing)
在每次進行重大開發或部署前，開發者 **必須** 執行測試 SOP 腳本：

```bash
./scripts/test_sop.sh
```

### 2.2 測試內容 (Test Coverage)
- **SA Billing Weights**: 驗證 Scrape(10), AI(5), Email(1) 的扣點權重是否正確。
- **Scraper Health**: 驗證爬蟲日誌是否包含 `response_time` 與 `http_status`。
- **RBAC & Isolation**: 驗證各租戶數據隔離邏輯。

## 3. 封存與紀錄 (Archiving & Recording)

### 3.1 封存位置 (Archive Location)
所有測試輸出將自動儲存於：
- `docs/qa/archives/`
- 格式：`TEST_RESULT_YYYYMMDD_HHMM.log`

### 3.2 測試日誌清單 (Test History)
所有歷史測試紀錄將自動追加至：
- `docs/qa/TEST_HISTORY.md`

## 4. 交付規約 VCP+ (SOP Enforcement)
根據 **BUSINESS_PROCESS.md**，非經執行測試 SOP 且日誌封存成功者，不可將其標記為「部署完成」。

> [!IMPORTANT]
> **測試失敗時的處理**：
> 如果 `test_sop.sh` 回傳 Exit Code 1，嚴禁將代碼合併或發布至生產環境。必須修復錯誤後重新執行並封存成功。

---
*Created by Antigravity AI - QA Process SOP v3.5 Compliance*
