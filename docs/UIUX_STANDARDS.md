# Linkora V2 — UI/UX 設計規範

> **版本：** 1.0.0 | **最後更新：** 2026-03-25 | **維護者：** Ann (AI)

---

## 一、設計原則

| 原則 | 說明 |
|------|------|
| **Token First** | 所有色彩、間距、字型必須來自 CSS 變數，禁止硬編碼 |
| **元件統一** | 相同功能使用相同元件，禁止各頁面自行實作 |
| **一致骨架** | 每個頁面必須使用 `page-wrapper > page-header > page-body` 結構 |
| **Toast 回饋** | 所有操作（儲存/刪除/錯誤）必須有 Toast 通知，禁止 `alert()` |

---

## 二、檔案結構

```
frontend/src/
├── styles/
│   ├── tokens.css       ← Design Token（全域 CSS 變數）
│   └── components.css   ← 通用元件樣式庫
├── index.css            ← Tailwind base + 舊有全域樣式
└── main.tsx             ← 引入順序：index.css → tokens.css → components.css
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

### 頁面標題對照表

| 路由 | 中文標題 | 英文副標 |
|------|---------|---------|
| `/lead-engine` | 精準開發雷達 | Precision Radar |
| `/templates` | 智慧行銷劇本 | AI Scripts |
| `/campaigns` | 自動化投遞 | Automated Outreach |
| `/analytics` | 成效分析雷達 | Performance Radar |
| `/history` | 開發紀錄專區 | Campaign Archive |
| `/smtp` | 發信通道配置 | Email Channels |
| `/admin/vendors` | 廠商管理 | Vendor Management |
| `/admin/settings` | 系統控制中心 | System Hub |
| `/admin/members` | 會員管理中心 | Member Management |

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
        <tr key={item.id}>
          <td>{item.name}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

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
  警告訊息內容
</div>
```

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

## 六、禁止事項

| ❌ 禁止 | ✅ 改用 |
|---------|---------|
| `alert()` / `confirm()` | `toast.error()` / `toast.success()` |
| 硬編碼色碼 `#1e2330` | CSS 變數 `var(--color-bg-card)` |
| Section 標題加數字編號 `01. 02.` | 統一 `.card__title` |
| 各頁面自行實作 Tab 樣式 | `.tab-nav` 元件 |
| 空狀態只有純文字 | `.empty-state` 元件 |
| `className="bg-primary hover:bg-primary-dark ..."` 長串 | `.btn-primary` |

---

## 七、一致性 Checklist

開發完成後，每個頁面須對照以下清單：

### 結構面
- [ ] 使用 `page-wrapper` 骨架
- [ ] `page-header` 含正確中文標題 + 英文副標 + `version-badge`
- [ ] `page-header__right` 有頁面主操作按鈕（若有）

### 元件面
- [ ] Tab 使用 `.tab-nav` 元件
- [ ] 統計卡片使用 `.stat-card` 元件
- [ ] 表格使用 `.data-table` 元件
- [ ] 空狀態使用 `.empty-state` 元件（含圖示 + 標題 + 說明）
- [ ] 按鈕使用 `.btn-primary` / `.btn-outline` / `.btn-danger` / `.btn-icon-sm`
- [ ] 卡片使用 `.card` 元件

### 視覺面
- [ ] 所有色彩來自 CSS Token（無硬編碼）
- [ ] Section 標題無數字編號
- [ ] Loading 使用 `.page-loading` + `.spinner`

### 互動面
- [ ] 所有操作後有 Toast 通知（無 `alert()`）
- [ ] 表單欄位有 focus 狀態
- [ ] 按鈕有 hover / disabled 狀態

---

## 八、待完成項目（P1 剩餘 + P2）

### P1 剩餘（逐頁套用）
- [ ] `LeadEngine.tsx` - 套用 `page-header` + `stat-card`
- [ ] `Templates.tsx` - Tab 換 `tab-nav`，Monaco Editor `min-height: 350px`，表單欄位順序重排
- [ ] `Campaigns.tsx` - 空狀態換 `empty-state`，篩選列換 `filter-bar`
- [ ] `History.tsx` - 「更新列表」移到 `page-header__right`
- [ ] `Analytics.tsx` - 套用 `page-header` + `stat-card`
- [ ] `SystemSettings.tsx` - Tab 換 `tab-nav`

### P2 細節優化
- [ ] RWD：統計卡片 < 768px 時為 2 欄
- [ ] RWD：側邊欄 < 768px 時收起（漢堡選單）
- [ ] RWD：表格 < 640px 時轉 Card 模式
- [ ] 右上角 User Info 補 `LangSwitcher` 元件（i18n 準備）

---

*本文件由 Ann 自動生成並維護，每次 UI 重構後請同步更新。*
