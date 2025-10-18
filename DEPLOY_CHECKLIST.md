# Vercel 部署檢查清單

在重新部署到 Vercel 之前，請確認以下項目：

## ✅ 必須完成的項目

- [ ] **環境變數已設定**
  - [ ] `SUPABASE_URL` 已在 Vercel 設定
  - [ ] `SUPABASE_ANON_KEY` 或 `SUPABASE_KEY` 已設定
  - [ ] 變數設定在正確的環境（Production/Preview）

- [ ] **程式碼已更新**
  - [ ] `src/db_config.py` - 動態讀取環境變數 ✓
  - [ ] `src/main_flask.py` - 所有路由改為同步 ✓
  - [ ] `api/index.py` - Vercel 入口點正確 ✓
  - [ ] `vercel.json` - 配置正確 ✓

- [ ] **本機測試通過**
  - [ ] `python test_vercel_ready.py` 全部通過 ✓

## 🚀 部署流程

### 1. 提交變更
```bash
git add .
git commit -m "Fix Vercel serverless compatibility - resolve 503 errors"
git push origin main
```

### 2. 等待 Vercel 自動部署
- 前往 Vercel Dashboard
- 查看 Deployments 頁面
- 等待構建完成（通常 1-3 分鐘）

### 3. 驗證部署

#### A. 檢查健康狀態
```bash
curl https://your-app.vercel.app/api/health
```
預期：`"db_ready": true`

#### B. 測試 GET 請求
```bash
curl https://your-app.vercel.app/api/notes
```
預期：HTTP 200，返回筆記陣列

#### C. 測試 POST 請求
```bash
curl -X POST https://your-app.vercel.app/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","content":"Hello","event_date":"2025-10-18","event_time":"14:30"}'
```
預期：HTTP 201，返回新建的筆記物件

#### D. 前端測試
1. 訪問應用首頁
2. 嘗試建立新筆記
3. 確認能夠儲存、編輯、刪除

## ❌ 如果仍然失敗

### 檢查 Function Logs
1. 前往 Vercel Dashboard → Deployments
2. 點擊最新的部署
3. 點擊 "Functions" 標籤
4. 查看錯誤日誌

### 常見錯誤及解決方法

**錯誤：503 Service Unavailable**
- 原因：環境變數未設定或錯誤
- 解決：檢查 `/api/health` 端點，確認 `db_ready: true`

**錯誤：Database not configured**
- 原因：Vercel 讀不到環境變數
- 解決：
  1. 檢查變數名稱拼寫（區分大小寫）
  2. 確認設定在 Production 環境
  3. 重新部署

**錯誤：Supabase connection failed**
- 原因：金鑰無效或過期
- 解決：
  1. 前往 Supabase Dashboard → Settings → API
  2. 重新複製 anon key
  3. 更新 Vercel 環境變數

**錯誤：Timeout / Cold start**
- 原因：首次請求需要初始化
- 解決：這是正常現象，後續請求會更快

## 📋 部署後確認

- [ ] `/api/health` 返回 `db_ready: true`
- [ ] GET `/api/notes` 正常工作
- [ ] POST `/api/notes` 返回 201
- [ ] 前端可以建立筆記
- [ ] 前端可以編輯筆記
- [ ] 前端可以刪除筆記
- [ ] 日期時間正確儲存和顯示

## 🎯 成功指標

✓ 所有 API 端點返回預期狀態碼
✓ 前端操作流暢無錯誤
✓ Function Logs 沒有錯誤訊息
✓ 資料正確儲存到 Supabase

## 📞 需要幫助？

如果完成以上步驟後仍有問題：

1. 收集以下資訊：
   - `/api/health` 的完整回應
   - Vercel Function Logs 的錯誤訊息
   - 瀏覽器 Console 的錯誤（F12）
   - POST 請求的完整 payload

2. 檢查相關文件：
   - `VERCEL_DEPLOY_GUIDE.md` - 詳細部署指南
   - `README.md` - 專案說明

3. 逐步排查：
   - 先確認環境變數
   - 再確認 Supabase 連線
   - 最後確認 RLS 政策
