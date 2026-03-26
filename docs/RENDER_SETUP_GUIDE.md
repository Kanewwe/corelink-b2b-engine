# Render 部署與資料庫設定經驗總結 (RENDER_SETUP_GUIDE.md)

本文件紀錄了在 Linkora 2.0 專案中，針對 Render 平台進行 PostgreSQL 遷移與環境切分的技術經驗與最佳實踐。

## 1. Render API 整合經驗

### API 存取要點
- **Endpoint**: 所有的 PostgreSQL 相關操作建議使用 `v1/postgres` 而非舊版的 `v1/postgresql` 或 `v1/databases`。
- **權限控制**: 通過 `Authorization: Bearer <API_KEY>` 進行驗證。
- **資訊提取**: 
    - `GET /v1/owners`: 取得 `ownerId` (Workspace ID)，這是建立服務的必要參數。
    - `GET /v1/postgres/{id}/connection-info`: 可直接取得 `internal` 與 `external` 連線字串，包含密碼。

### 自動化限制
- **免費層級限制**: Render 每個帳號限制只能有一個「啟用的、免費的 (Active Free Tier)」資料庫。
- **失敗情境**: 若嘗試透過 API 建立第二個免費資料庫，會回傳 `400 Bad Request` 與錯誤訊息 `cannot have more than one active free tier database`。

## 2. PostgreSQL & 環境切分 (PRD/UAT)

### Schema-based 多租戶隔離
由於上述的免費層級限制，我們採用了 **Schema (綱要) 隔離法** 在單一實例中達成 PRD/UAT 分離：
- **Production**: 使用預設的 `public` schema。
- **UAT**: 使用獨立的 `uat` schema。

### FastAPI/SQLAlchemy 實作技巧
- **search_path**: 在 `create_engine` 时使用 `connect_args={"options": "-c search_path=uat"}` 可以讓該 Session 的所有操作都限制在特定 Schema 中，且完全不需修改 Model 代碼。
- **SSL 強制**: Render PostgreSQL 遠端連線必須啟用 SSL。連線字串應明確包含 `sslmode=require` 以免部分 Driver (如 `psycopg2`) 報錯。

## 3. 部署最佳實踐 (Best Practices)

1. **環境變數驅動**: 
    - 使用 `APP_ENV` (如 `production`, `uat`) 作為邏輯切換的核心支柱。
    - 透過 `os.getenv("DATABASE_URL")` 讓 Render 自動注入連線資訊。
2. **自動初始化**:
    - 在應用程式啟動時 (`lifespan` 或 `main.py` 頂層) 呼叫 `init_db()`。
    - 實作 `CREATE SCHEMA IF NOT EXISTS` 邏輯，確保非 `public` 環境在首次啟動時能自動建立隔離空間。
3. **資料庫迁移管理**:
    - 由於 SQLite 與 PostgreSQL 的語法細微差異（如 Boolean vs Integer, Timestamp 處理），建議使用通用性強的 `ALTER TABLE ADD COLUMN IF NOT EXISTS` 邏輯。

## 4. 總結
Render 是一個對開發者非常友善的平台，透過 API 可以大幅減少手動設定的時間。在面對成本限制（免費層級）時，利用 PostgreSQL 的 Schema 功能是目前最符合經濟效益且結構嚴謹的解決方案。

---
*Created by Antigravity AI on 2026-03-26*
