# 爬蟲實測結果 — 2026-03-29

> **目標：** 歐美市場，Email 需驗證
> **測試日期：** 2026-03-29

---

## 1. API 測試結果

### 1.1 Apollo.io

| 功能 | Free Plan | 付費 Plan |
|------|-----------|----------|
| Organization Enrichment | ✅ 可用 | ✅ |
| Organization Search | ⚠️ 可用但無過濾 | ✅ keyword/location 過濾 |
| People Search | ❌ 不可用 | ✅ 有 email |
| Mixed People Search | ❌ 不可用 | ✅ 有 email |

**結論：** Free plan 只能取得公司資料，無法取得 Email。需付費 $49+/月。

### 1.2 Hunter.io

| 功能 | 狀態 |
|------|------|
| Account Check | ❌ Key 無效 |
| Domain Search | ❌ Key 無效 |

**結論：** 需要購買新的 API Key（$49/月，1000 searches）。

### 1.3 Email 驗證測試

**自建驗證方案（免費）：**

| 方法 | 準確度 | 速度 | 備註 |
|------|--------|------|------|
| 格式驗證 | 低 | 快 | 只檢查格式 |
| MX 記錄檢查 | 中 | 快 | 確認 domain 有 mail server |
| SMTP 驗證 | 高 | 慢 | 大公司會擋 |

**測試結果：**
- `info@dell.com` — ✅ SMTP 通過
- `support@hp.com` — ❌ 550（信箱不存在）
- `contact@apple.com` — ❌ 550（被擋）
- `sales@asus.com` — ✅ MX 存在

**結論：** 中小企業 SMTP 驗證成功率較高，大企業會擋。

---

## 2. 方案評估（針對歐美市場）

### 方案 A1：Apollo.io Basic ($49/月)

**流程：**
```
1. Organization Search（keyword + location 過濾）
   → 取得公司列表（名稱、domain、電話、員工數）

2. People Search
   → 取得員工 email（職稱過濾：CEO、Sales Manager、Purchasing）

3. Email 驗證（自建 SMTP）
   → 確認 email 有效
```

**預期效果：**
- 公司數量：依關鍵字，約 100-1000+/月
- Email 獲取率：60-80%
- 驗證成功率：50-70%

**成本：** $49/月

**優點：**
- ✅ 資料品質最高
- ✅ API 穩定
- ✅ 可過濾中小企業（員工數 < 500）

**缺點：**
- ❌ 每月成本
- ❌ 台灣公司覆蓋率低

---

### 方案 A2：Apollo.io + Hunter.io 雙 API

**流程：**
```
1. Apollo Organization Search（免費 Enrichment）
   → 取得公司資料

2. Hunter.io Domain Search（$49/月）
   → 取得該公司的所有 email

3. Email 驗證
   → 過濾有效 email
```

**預期效果：**
- 公司數量：無限
- Email 獲取率：40-60%
- 驗證成功率：Hunter 內建驗證

**成本：** Hunter $49/月 + Apollo Free

**優點：**
- ✅ 不用 Apollo 付費
- ✅ Hunter 內建 email 驗證

**缺點：**
- ❌ Hunter 額度有限（1000 searches/月）
- ❌ 大公司 email 被 Hunter 擋

---

### 方案 B：Snov.io（替代 Hunter）

**Snov.io 定價：**
- Free: 50 credits/月
- Starter: $39/月（1000 credits）
- Pro: $69/月（5000 credits）

**功能：**
- Domain Search（類似 Hunter）
- Email Verification（內建）
- LinkedIn Integration

**優點：**
- ✅ 比 Hunter 便宜
- ✅ 內建 email 驗證

**缺點：**
- ❌ 資料庫比 Apollo 小
- ❌ 歐美覆蓋率不如 Apollo

---

### 方案 C：自建爬蟲 + Email Guessing + 驗證

**流程：**
```
1. 公司發現
   ├─ LinkedIn Company Search（需付費或手動）
   ├─ Google Maps Business（免費，但爬取困難）
   └─ 行業協會會員名單（免費，手動整理）

2. Email Guessing
   → info@domain.com, sales@domain.com, contact@domain.com

3. Email 驗證（自建 SMTP）
   → 過濾有效 email
```

**預期效果：**
- 公司數量：手動限制
- Email 獲取率：10-30%（Guessing）
- 驗證成功率：50-70%

**成本：** 免費

**優點：**
- ✅ 免費
- ✅ 彈性高

**缺點：**
- ❌ 維護成本高
- ❌ 資料量有限
- ❌ Email 品質低（Guessing）

---

## 3. 推薦方案

### 短期（1-2 週）

**方案 A2：Apollo Free + Hunter.io付費**

**理由：**
1. 快速驗證可行性
2. Hunter 有免費試用
3. 成本可控

**執行步驟：**
1. 註冊 Hunter.io（免費 25 searches）
2. 測試 10 個歐美公司 domain
3. 確認 email 獲取率 > 50%
4. 若通過，付費 $49/月

### 中期（1 個月後）

**方案 A1：Apollo.io Basic $49/月**

**理由：**
1. 資料品質最高
2. 可直接搜尋 People（Email）
3. 支援 keyword/location 過濾

**條件：**
- Hunter 測試證明需求可行
- 需要大量公司名單（> 500/月）

---

## 4. 待執行

### 立即可做

1. **註冊 Hunter.io 免費帳號**
   - 取得 API Key
   - 測試 25 個 domain searches
   - 確認 email 獲取率

2. **測試 Snov.io 免費方案**
   - 比較 Hunter vs Snov
   - 選擇成本效益最佳

### 需決策

- [ ] 是否購買 Hunter.io（$49/月）？
- [ ] 是否購買 Apollo.io Basic（$49/月）？
- [ ] 是否同時購買兩個 API（$98/月）？

---

## 5. 成本效益試算

| 方案 | 月成本 | 預估公司數 | 預估有效 Email | 每筆成本 |
|------|--------|-----------|---------------|---------|
| Hunter.io | $49 | 1000 domains | 400-600 | $0.08-0.12 |
| Apollo Basic | $49 | 10,000 credits | 500-800 | $0.06-0.10 |
| Hunter + Apollo | $98 | 1000 + 10000 | 800-1200 | $0.08-0.12 |

---

## 下一步

**請確認：**
1. 是否要我協助註冊 Hunter.io 免費試用？
2. 測試完成後，是否願意付費 $49/月？
3. 目標數量：每月需要多少筆有效 Email？
