## 🏗️ 前端技術架構 (v3.1.8)
Linkora 前端基於 **Vite** + **React 18**，採用 **Tailwind CSS 3.4** 實作玻璃質感。

## 🚀 快速跳轉 (Quick Links)
- 🎨 **[UI/UX 視覺與組件標準](UIUX_STANDARDS.md)**: HSL 顏色、Glass Panel 與按鈕組件規範。
- 🛡️ **[權限守衛 (RoleGuard)](../../frontend/src/components/RoleGuard.tsx)**: 本身實作了跨角色的路由攔截邏輯。
- 📡 **[API 門戶 (api.ts)](../../frontend/src/services/api.ts)**: 統一處理 `API_BASE_URL` 與 `fetchWithAuth`。

---

## 🛠️ 組件開發規範 (Components SOP)

### 1. 範本編輯器 (Monaco Editor)
- **套件**: `@monaco-editor/react`
- **用途**: 用於開發信模板的代碼級編輯，支援 `{{company_name}}` 標籤高亮。
- **規範**: 務必套用 `theme="vs-dark"` 並設定 `options={{ minimap: { enabled: false } }}`。

### 2. 用戶反饋 (Toast)
- **套件**: `react-hot-toast`
- **用法**: 統一使用 `toast.success()` 或 `toast.error()`。
- **配置**: 全局 `Toaster` 已掛載於 `App.tsx`，背景色應符合 Glassmorphism 透明色調。

---

## 🔐 認證與 API 整合

### 1. API_BASE_URL 自動切換
系統會根據 `window.location.hostname` 自動判定：
- `localhost` -> `http://localhost:8000`
- `*` -> `/api` (交由後端 Nginx/FastAPI 靜態掛載處理)

### 2. 身分驗證 (Auth)
- **Token 存儲**: 登入成功後存於 `localStorage.getItem('token')`。
- **雙重驗證**: 呼叫 API 時會同時攜帶 Bearer Token 與 Session Cookie。

---
*OpenClaw Optimized Guide - Role: FEPG*
