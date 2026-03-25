# Linkora 2.0 完整測試與發佈流程 (Testing & Deployment Flow)

在將程式碼從 `uat` 合併至 `prd` (正式環境) 之前，請務必執行以下檢查。

---

## 1. 環境與依賴檢查 (Environment)
- [ ] 檢查 `backend/.env` 是否包含正確的 API Keys (Scraper, SMTP)。
- [ ] 執行 `pip install -r backend/requirements.txt` 確保後端依賴更新。
- [ ] 執行 `npm install` 確保前端依賴更新。

## 2. 後端驗證 (Backend)
- [ ] 啟動後端：`uvicorn main:app --host 0.0.0.0 --port 8000 --reload`。
- [ ] 存取 `http://localhost:8000/api/health` 確保系統正常。
- [ ] 檢查資料庫遷移：啟動時是否成功建立新 Table (如 `vendors`)。

## 3. 前端產出檢查 (Frontend Build)
- [ ] 執行生產環境編譯：`npm run build`。
- [ ] 確保 `dist/` 資料夾成功產生且無報錯。

## 4. 業務功能測試 (Business Logic)
- [ ] **Admin**: 進入 `http://localhost:5173/admin/vendors` 測試「新增/編輯/刪除」廠商。
- [ ] **Vendor**: 進入 `Analytics` 頁面，確認「批發結算金額」是否根據 Lead 數量正確計算。
- [ ] **Member**: 執行一次簡單探勘 (Scrape)，確認 `History` 頁面有產生新的任務卡片。
- [ ] **Email**: 測試發送一封測試信，確認 `email_logs` 有記錄且開信追蹤有效。

## 5. 發佈至正式環境 (Deployment)
- [ ] 確認 `uat` 分支測試無誤。
- [ ] 執行自動化發佈指令：`./scripts/sync.ps1 -Action deploy -Message "Release v2.x"`。
- [ ] 到 Render Dashboard 確認 `linkora-frontend` 與 `linkora-backend` 開始自動建置。

---
> [!IMPORTANT]
> **嚴禁** 直接在 `prd` 分支修改代碼。所有修改必須先在 `uat` 驗證。
