# Linkora V2 — UI/UX 設計規範

> **版本：** 2.1.0 | **最後更新：** 2026-03-26 10:00 | **維護者：** Ann (AI)
> **狀態：** ✅ P0 + P1 + P2 全部完成 | 手機版 RWD (M1-M10) 完成 | Sidebar 雙模式完成

---

## 一、設計原則

| 原則 | 說明 |
|------|------|
| **Token First** | 所有色彩、間距、字型必須來自 CSS 變數，禁止硬編碼 |
| **元件統一** | 相同功能使用相同元件，禁止各頁面自行實作 |
| **一致骨架** | 每個頁面必須使用 `page-wrapper > page-header > page-body` 結構 |
| **Toast 回饋** | 所有操作（儲存/刪除/錯誤）必須有 Toast 通知，禁止 `alert()` |
| **手機優先** | 768px 以下自動切換 Drawer + TabBar，無橫向滾動 |

---

## 二、檔案結構

```
frontend/src/
├── styles/
│   ├── tokens.css       ← Design Token（全域 CSS 變數）
│   ├── components.css   ← 通用元件樣式庫 + RWD 規則
│   └── (M1-M10 RWD 規則已整合)
├── index.css            ← Tailwind base + 舊有全域樣式
├── main.tsx             ← 引入順序：index.css → tokens.css → components.css
└── components/
    └── Layout.tsx       ← 含 Sidebar Drawer + Bottom TabBar
```

---

## 三、Design Token 速查

### 色彩

| 變數 | 值 | 用途 |
|------|----|------|
| `--color-bg-base` | `#0d0f1e` | 最底層背景 |
| `--color-bg-card` | `#181b2e` | 卡片/面板背景 |
| `--color-bg-card-hover` | `#1e2240` | 卡片 hover |
| `--color-bg-input` | `#12142a` | 輸入框背景 |
| `--color-bg-table-head` | `#1a1d30` | 表格 thead |
| `--color-border` | `#252840` | 所有邊框 |
| `--color-border-light` | `#1e2138` | 淡邊框（分隔線）|
| `--color-primary` | `#5b7fff` | 主色（按鈕、連結、active）|
| `--color-primary-hover` | `#7b96ff` | 主色 hover |
| `--color-primary-glow` | `rgba(91,127,255,0.15)` | 主色光暈背景 |
| `--color-accent-teal` | `#4ecdc4` | Logo 漸層色 |
| `--color-success` | `#22c55e` | 成功狀態 |
| `--color-warning` | `#f59e0b` | 警告狀態 |
| `--color-danger` | `#ef4444` | 危險/錯誤狀態 |
| `--color-text-primary` | `#f0f2ff` | 主要文字 |
| `--color-text-secondary` | `#8b8fa8` | 次要文字（說明、副標）|
| `--color-text-muted` | `#4a4f6a` | 更淡（placeholder、disabled）|
| `--color-text-label` | `#6b7280` | 欄位標籤 |

### 間距

| 變數 | 值 | 用途 |
|------|----|------|
| `--space-page-x` | `32px` | 頁面左右內距 |
| `--space-page-y` | `28px` | 頁面上下內距 |
| `--space-section` | `24px` | Section 間距 |
| `--space-card` | `20px` | 卡片內距 |
| `--space-card-sm` | `14px` | 小卡片內距 |

### 字型

| 變數 | 值 | 用途 |
|------|----|------|
| `--font-size-page-title` | `22px` | 頁面主標題 |
| `--font-size-section-title` | `16px` | Section 標題 |
| `--font-size-body` | `14px` | 內文 |
| `--font-size-small` | `12px` | 小字（說明、副標）|
| `--font-size-label` | `11px` | 欄位標籤 |

---

## 四、頁面骨架規範

### 標準結構

```tsx
<div className="page-wrapper">

  {/* ① 頁面 Header（必填） */}
  <div className="page-header">
    <div>
      <div className="page-header__title-row">
        <h1 className="page-title">
          頁面中文名稱
          <span className="page-title__en">English Name</span>
        </h1>
        <span className="version-badge">LINKORA V2</span>
      </div>
      <p className="page-subtitle">頁面說明文字</p>
    </div>
    <div className="page-header__right">
      {/* 頁面主操作按鈕（選填）*/}
    </div>
  </div>

  {/* ② 警告/提示橫幅（有需要才出現）*/}
  <div className="page-banner page-banner--warning">...</div>

  {/* ③ 主內容區 */}
  {/* ... */}

</div>
```

### 頁面標題對照表 + `<title>` 標籤

| 路由 | 中文標題 | 英文副標 | `<title>` |
|------|---------|---------|----------|
| `/lead-engine` | 精準開發雷達 | Precision Radar | `Linkora - 精準開發雷達` |
| `/templates` | 智慧行銷劇本 | AI Scripts | `Linkora - 智慧行銷劇本` |
| `/campaigns` | 自動化投遞 | Automated Outreach | `Linkora - 自動化投遞` |
| `/analytics` | 成效分析雷達 | Performance Radar | `Linkora - 成效分析雷達` |
| `/history` | 開發紀錄專區 | Campaign Archive | `Linkora - 開發紀錄專區` |
| `/smtp` | 發信通道配置 | Email Channels | `Linkora - 發信通道配置` |
| `/admin/vendors` | 廠商管理 | Vendor Management | `Linkora - 廠商管理` |
| `/admin/settings` | 系統控制中心 | System Hub | `Linkora - 系統控制中心` |
| `/admin/members` | 會員管理中心 | Member Management | `Linkora - 會員管理` |
| `/admin/dashboard` | 系統監控 | System Monitor | `Linkora - 系統監控` |

---

## 五、通用元件使用規範

### 5-1 卡片 `.card`

```tsx
<div className="card">
  <div className="card__header">
    <h3 className="card__title">
      <Icon size={16} />
      標題
    </h3>
    {/* 右側操作（選填）*/}
  </div>
  {/* 內容 */}
</div>
```

### 5-2 統計卡片 `.stat-card`

```tsx
<div className="stats-grid">
  <div className="stat-card">
    <div className="stat-card__icon" style={{ background: 'rgba(91,127,255,0.15)' }}>
      <Icon size={20} style={{ color: 'var(--color-primary)' }} />
    </div>
    <div>
      <div className="stat-card__value">1,234</div>
      <div className="stat-card__label">標籤文字</div>
      <div className="stat-card__note">補充說明</div>
    </div>
  </div>
</div>
```

**RWD 規則：**
- `@media (max-width: 1024px)`: 2 欄
- `@media (max-width: 640px)`: 1 欄

### 5-3 Tab 導覽 `.tab-nav`

```tsx
<div className="tab-nav">
  <button className={`tab-nav__item ${activeTab === 'a' ? 'active' : ''}`} onClick={() => setActiveTab('a')}>
    <Icon size={14} /> Tab A
  </button>
  <button className={`tab-nav__item ${activeTab === 'b' ? 'active' : ''}`} onClick={() => setActiveTab('b')}>
    Tab B
  </button>
</div>
```

**樣式：** 透明底 + active 時藍色邊框 + 填色背景

### 5-4 按鈕系統

| Class | 用途 | 範例 |
|-------|------|------|
| `.btn-primary` | 主要操作（新增、儲存）| 新增廠商、儲存設定 |
| `.btn-outline` | 次要操作（取消、匯出）| 取消、重新整理 |
| `.btn-danger` | 危險操作（刪除）| 刪除、停用 |
| `.btn-icon-sm` | 表格行內操作 | 編輯、刪除圖示按鈕 |
| `.btn--sm` | 尺寸修飾符（小）| 搭配任何按鈕 |
| `.btn--lg` | 尺寸修飾符（大）| 搭配任何按鈕 |

```tsx
<button className="btn-primary"><Save size={14} />儲存</button>
<button className="btn-outline"><RefreshCw size={14} />重新整理</button>
<button className="btn-danger btn--sm"><Trash2 size={13} />刪除</button>
<button className="btn-icon-sm danger"><Trash2 size={14} /></button>
```

### 5-5 表單元件

```tsx
<div>
  <label className="form-label">欄位名稱</label>
  <div className="form-input-wrapper">
    <Icon size={14} className="input-icon" />
    <input className="form-input" placeholder="..." />
  </div>
  <span className="form-error-msg">錯誤訊息</span>
</div>
```

### 5-6 表格 `.data-table`

```tsx
<div className="card" style={{ padding: 0, overflow: 'hidden' }}>
  <table className="data-table">
    <thead>
      <tr>
        <th>欄位名稱</th>
      </tr>
    </thead>
    <tbody>
      {data.length === 0 ? (
        <tr><td colSpan={N}>
          <div className="empty-state">
            <div className="empty-state__icon">📭</div>
            <p className="empty-state__title">尚無資料</p>
            <p className="empty-state__desc">說明文字</p>
          </div>
        </td></tr>
      ) : data.map(item => (
        <tr key={item.id} data-label="欄位名稱">
          <td>{item.name}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

**RWD 規則（M9）：**
- `@media (max-width: 480px)`: 隱藏 `<thead>`，每個 `<tr>` 變成 flex column，`<td>` 加 `data-label` 屬性顯示欄位名稱

### 5-7 Badge

```tsx
<span className="badge badge--success">啟用</span>
<span className="badge badge--danger">停用</span>
<span className="badge badge--warning">待審</span>
<span className="badge badge--primary">主要</span>
<span className="badge badge--neutral">一般</span>
```

### 5-8 警告橫幅

```tsx
<div className="page-banner page-banner--warning">
  <AlertTriangle size={16} />
  <div>
    <div style={{ fontWeight: 600 }}>警告標題</div>
    <div style={{ fontSize: 12, opacity: 0.8 }}>警告訊息內容</div>
  </div>
  <button className="btn-primary btn--sm">操作按鈕</button>
</div>
```

**樣式：** `display: flex; align-items: center; justify-content: space-between;` 確保文字左、按鈕右

### 5-9 Loading 狀態

```tsx
// 全頁 Loading
if (loading) {
  return (
    <div className="page-loading">
      <div className="spinner" />
      <span>Loading...</span>
    </div>
  );
}
```

---

## 六、Sidebar 雙模式規範 (M11)

### 概述

Sidebar 提供兩種操作模式，使用者可透過底部切換按鈕自由切換。

### 展開模式 (Full Mode) — 250px

```
┌──────────────────────┐
│  L  Linkora           │
│                       │
│  主要功能             │
│  🔍 精準開發雷達      │
│                       │
│  寄信作業             │
│  📄 智慧行銷劇本      │
│  📤 自動化投遞        │
│                       │
│  分析                 │
│  📊 成效分析雷達      │
│  🕐 開發紀錄專區      │
│                       │
│  設定                 │
│  ⚙️ 發信通道配置      │
│                       │
│  管理 (Admin)         │  ← 僅 admin 角色可見
│  📺 系統監控          │
│  👤 會員管理          │
│  👥 廠商管理          │
│  🖥️ 系統控制中心      │
│                       │
│  ◀ 收合選單           │  ← 切換按鈕
│  [A] Admin ▌ 🚪       │  ← 使用者資訊 + 登出
└──────────────────────┘
```

**特徵：**
- 寬度 250px
- 完整顯示 icon + 文字標籤
- Section 標題以文字顯示（10px, uppercase, tracking-widest）
- Active 項目：藍色左邊框 + 背景色
- 使用者區域：頭像 + 名稱 + 角色 + 登出按鈕

### 收合模式 (Mini Mode) — 68px

```
┌──────┐
│  L   │
│      │
│  🔍  │  ← hover 顯示 tooltip「精準開發雷達」
│ ──── │  ← Section 分隔線 (6px, 白色10%)
│  📄  │  ← hover 顯示 tooltip「智慧行銷劇本」
│  📤  │
│ ──── │
│  📊  │
│  🕐  │
│ ──── │
│  ⚙️  │
│ ──── │
│  📺  │  ← Admin only
│  👤  │
│  👥  │
│  🖥️  │
│      │
│  ▶   │  ← hover 顯示「展開選單」
│  A   │  ← hover 顯示 email
└──────┘
```

**特徵：**
- 寬度 68px
- 僅顯示 icon（20px, 居中）
- Section 標題以 6px 分隔線代替
- Hover 時顯示 tooltip（右側彈出，帶三角箭頭）
- Active 項目：藍色光暈背景
- 使用者區域：僅頭像，hover 顯示 email

### Tooltip 規範

```tsx
<div className="relative group">
  <NavLink to={to} className="...">
    <Icon size={20} />
  </NavLink>
  {/* Tooltip */}
  <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 
    px-3 py-1.5 bg-[#1e2538] text-white text-xs font-medium 
    rounded-lg shadow-xl border border-white/10 
    whitespace-nowrap 
    opacity-0 invisible group-hover:opacity-100 group-hover:visible 
    transition-all z-50 pointer-events-none">
    {label}
    <div className="absolute right-full top-1/2 -translate-y-1/2 
      border-4 border-transparent border-r-[#1e2538]" />
  </div>
</div>
```

### 動畫規範

```css
/* Sidebar 寬度切換動畫 */
transition-all duration-300 ease-in-out

/* 展開: 250px */
/* 收合: 68px */
```

### 捲動行為

- `nav` 區塊設為 `flex-1 overflow-y-auto overflow-x-hidden`
- Logo 區域：`shrink-0`（固定不動）
- 底部切換按鈕 + 使用者區域：`shrink-0`（固定不動）
- 中間導覽區：可捲動，細捲軸 (`scrollbar-thin`)

### 角色權限

Admin 專屬區塊（`user?.role === 'admin'`）：
- 系統監控 (`/admin/dashboard`)
- 會員管理 (`/admin/members`)
- 廠商管理 (`/admin/vendors`)
- 系統控制中心 (`/admin/settings`)

### Icon 對照表

| 頁面 | Icon | Lucide Icon Name |
|------|------|-----------------|
| 精準開發雷達 | 🔍 | `Search` |
| 智慧行銷劇本 | 📄 | `FileText` |
| 自動化投遞 | 📤 | `Send` |
| 成效分析雷達 | 📊 | `BarChart2` |
| 開發紀錄專區 | 🕐 | `Clock` |
| 發信通道配置 | ⚙️ | `Settings` |
| 系統監控 | 📺 | `Monitor` |
| 會員管理 | 👤 | `UserCog` |
| 廠商管理 | 👥 | `Users` |
| 系統控制中心 | 🖥️ | `Cpu` |
| 登出 | 🚪 | `LogOut` |
| 收合 | ◀ | `ChevronLeft` |
| 展開 | ▶ | `ChevronRight` |

---

## 七、手機版 RWD 規範（M1-M10）（M1-M10）

### Breakpoints

- **768px (md)**: Tablet 臨界點，Sidebar → Drawer，TabBar 出現
- **640px (sm)**: 手機臨界點，統計卡片 1 欄，表格 → Card 模式
- **480px (xs)**: 小手機，進一步優化

### M1: Sidebar → Drawer

```css
@media (max-width: 768px) {
  .sidebar-drawer {
    position: fixed;
    top: 0; left: 0;
    width: 260px;
    height: 100vh;
    z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
  }
  .sidebar-drawer.open {
    transform: translateX(0);
  }
  .sidebar-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 199;
  }
}
```

### M2: 底部 TabBar

```css
.bottom-tabbar {
  display: flex;
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 60px;
  background: var(--color-bg-dark);
  border-top: 1px solid var(--color-border);
  z-index: 100;
}
.bottom-tabbar__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  font-size: 10px;
  color: var(--color-text-muted);
  transition: color 0.2s;
}
.bottom-tabbar__item.active {
  color: var(--color-primary);
}
```

**包含 6 個主要頁面：** 探勘、模板、投遞、分析、記錄、設定

### M3: 統計卡片 2 欄 → 1 欄

```css
@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .stats-grid { grid-template-columns: 1fr; }
}
```

### M4-M6: 雙欄頁面堆疊

```css
@media (max-width: 768px) {
  .lead-engine-grid { grid-template-columns: 1fr; }
  .smtp-grid { grid-template-columns: 1fr; }
  .analytics-grid { grid-template-columns: 1fr; }
}
```

### M7: Tab 文字截斷 → 換行

```css
@media (max-width: 768px) {
  .tab-nav {
    flex-wrap: wrap;
    gap: 4px;
  }
  .tab-nav__item {
    font-size: 11px;
    padding: 6px 12px;
  }
}
```

### M8: 篩選列換行

```css
@media (max-width: 768px) {
  .filter-bar {
    flex-wrap: wrap;
    gap: 8px;
  }
}
```

### M9: 表格 → Card 模式

```css
@media (max-width: 480px) {
  .data-table thead { display: none; }
  .data-table tbody tr {
    display: flex;
    flex-direction: column;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-card);
    margin-bottom: 10px;
    padding: 12px;
  }
  .data-table tbody td {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    border: none;
    font-size: 12px;
  }
  .data-table tbody td::before {
    content: attr(data-label);
    font-weight: 600;
    color: var(--color-text-muted);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-right: 8px;
    flex-shrink: 0;
  }
}
```

### M10: Monaco Editor 高度優化

```css
@media (max-width: 480px) {
  .monaco-editor-wrapper {
    min-height: 200px !important;
  }
}
```

---

## 八、禁止事項

| ❌ 禁止 | ✅ 改用 |
|---------|---------|
| `alert()` / `confirm()` | `toast.error()` / `toast.success()` |
| 硬編碼色碼 `#1e2330` | CSS 變數 `var(--color-bg-card)` |
| Section 標題加數字編號 `01. 02.` | 統一 `.card__title` |
| 各頁面自行實作 Tab 樣式 | `.tab-nav` 元件 |
| 空狀態只有純文字 | `.empty-state` 元件 |
| `className="bg-primary hover:bg-primary-dark ..."` 長串 | `.btn-primary` |
| 橫幅文字垂直斷行 | `display: flex; justify-content: space-between;` |
| 頁面 `<title>` 顯示 Dashboard | 動態更新為 `Linkora - 頁面名稱` |

---

## 九、完成狀態 Checklist

### ✅ P0 — 立即修正（全部完成）
- [x] Campaigns SMTP 橫幅文字排版
- [x] LeadEngine 雙重標題移除
- [x] 所有頁面 `<title>` 動態更新
- [x] SystemSettings Tab active 樣式統一
- [x] Templates 儲存按鈕改為 `btn-primary`
- [x] SystemSettings 儲存按鈕改為 `btn-primary`

### ✅ P1 — 本週修正（全部完成）
- [x] MemberAdmin 統計卡片改用 `stats-grid + stat-card`
- [x] MemberAdmin 角色卡改用 `card + RoleBadge`
- [x] Analytics select 套用 `form-select`
- [x] Analytics 進度條改中文標籤
- [x] SystemSettings API Key label 已是中文
- [x] SystemSettings Info Banner 套用 `page-banner--info`
- [x] SystemSettings 通用系統參數 Tab 加 disabled + badge
- [x] Layout 右上角 User Dropdown 含登出

### ✅ P2 — 下週優化（全部完成）
- [x] Analytics 補無資料 empty-state
- [x] Templates Monaco Editor min-height 400px
- [x] History 更新列表在 page-header__right
- [x] User Dropdown 登出功能
- [x] 全站 Toast 通知（react-hot-toast）

### ✅ 手機版 RWD（M1-M10 全部完成）
- [x] M1: Sidebar Drawer + overlay
- [x] M2: 底部 TabBar (6 個主要頁面)
- [x] M3: 統計卡片 2 欄 → 1 欄
- [x] M4: LeadEngine 雙欄堆疊
- [x] M5: SmtpSettings 雙欄堆疊
- [x] M6: Analytics 雙欄堆疊
- [x] M7: Tab 文字換行
- [x] M8: 篩選列換行
- [x] M9: 表格 → Card 模式 (data-label)
- [x] M10: Monaco Editor 高度優化

### ✅ Sidebar 雙模式（M11 完成）
- [x] 展開模式 (250px): icon + 文字標籤
- [x] 收合模式 (68px): 僅 icon + hover tooltip
- [x] Section 標題收合時變分隔線 + tooltip
- [x] 底部切換按鈕 (◀/▶)
- [x] 使用者區域收合時僅顯示頭像
- [x] Admin 管理區塊完整可捲動
- [x] 寬度切換 transition 動畫 300ms

---

## 十、待完成項目（下一階段）

### 新功能開發
- [ ] 中英文切換 (i18n) — DB 驅動 + localStorage 快取
- [ ] 語言管理後台 (`/admin/i18n`) — CRUD + 匯入/匯出
- [ ] 右上角 `LangSwitcher` 元件

### 進階優化
- [ ] 深色/淺色主題切換
- [ ] 無障礙 (a11y) 審計
- [ ] 性能優化 (Lighthouse)

---

*本文件由 Ann 自動生成並維護，每次 UI 重構後請同步更新。*
*最後驗收日期：2026-03-26 10:00 GMT+8*
