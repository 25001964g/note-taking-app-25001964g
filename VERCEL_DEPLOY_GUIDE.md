# Vercel 部署指南

## 已修復的問題

✓ **異步處理問題**：將所有 Flask 路由從 `async def` 改為同步 `def`，使用 `_run_async()` 輔助函數安全執行異步操作
✓ **環境變數讀取**：改為動態讀取環境變數，避免在模組導入時快取過時的值
✓ **多種金鑰支援**：支援 `SUPABASE_KEY`、`SUPABASE_ANON_KEY`、`SUPABASE_SERVICE_ROLE_KEY`
✓ **健康檢查端點**：新增 `/api/health` 用於診斷環境配置
✓ **錯誤處理改善**：POST 失敗時提供更詳細的錯誤訊息和日誌

## 部署步驟

### 1. 在 Vercel 設定環境變數

前往您的 Vercel 專案 → Settings → Environment Variables，新增以下變數：

**必需變數：**
- `SUPABASE_URL` = `https://nasmrxzpyvatumbrypxf.supabase.co`（您的 Supabase 專案 URL）
- `SUPABASE_ANON_KEY` = `<您的 Supabase anon key>`

**可選變數：**
- `APP_DEBUG` = `true`（開發/除錯時使用，生產環境建議設為 `false`）

**重要提示：**
- 確保這些環境變數設定在正確的環境（Production / Preview / Development）
- 變數名稱必須完全一致（區分大小寫）
- 設定完成後需要重新部署才會生效

### 2. 重新部署

設定環境變數後，有兩種方式重新部署：

**方式 A：透過 Git 推送**
```bash
git add .
git commit -m "Fix Vercel serverless compatibility"
git push origin main
```

**方式 B：在 Vercel Dashboard 手動重新部署**
1. 前往 Deployments 頁面
2. 點擊最新的部署
3. 點擊右上角的三點選單 → Redeploy
4. 選擇 "Redeploy with existing Build Cache" 或 "Redeploy without Cache"

### 3. 驗證部署

部署完成後，請按照以下步驟驗證：

#### 3.1 檢查健康端點

在瀏覽器或使用 curl 訪問：
```bash
curl https://note-taking-app-25001964g.vercel.app/api/health
```

**預期回應（成功）：**
```json
{
  "status": "ok",
  "db_ready": true,
  "env": {
    "has_supabase_url": true,
    "has_supabase_key": true
  }
}
```

**如果 db_ready 為 false：**
- 檢查環境變數是否正確設定
- 確認變數名稱拼寫正確
- 確認設定在正確的環境（Production/Preview）
- 重新部署

#### 3.2 測試 GET 端點

```bash
curl https://note-taking-app-25001964g.vercel.app/api/notes
```

應該返回 200 和筆記列表（可能是空陣列）。

#### 3.3 測試 POST 端點

```bash
curl -X POST https://note-taking-app-25001964g.vercel.app/api/notes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "測試筆記",
    "content": "這是一個測試",
    "event_date": "2025-10-18",
    "event_time": "14:30"
  }'
```

**預期回應（成功）：**
- HTTP 狀態碼：201
- 返回包含 `id` 的筆記物件

**如果仍返回 503：**
1. 檢查 Vercel 的 Function Logs（Dashboard → Deployments → 選擇部署 → Functions 標籤）
2. 確認環境變數已正確讀取（查看日誌中的 "Environment check" 訊息）
3. 確認 Supabase 專案可訪問且 RLS 政策允許插入

### 4. 前端測試

訪問您的應用首頁：
```
https://note-taking-app-25001964g.vercel.app
```

嘗試：
- 建立新筆記（包含標題、內容、日期、時間）
- 查看筆記列表
- 編輯筆記
- 刪除筆記

## 常見問題排查

### Q: POST 仍然返回 503

**可能原因：**
1. 環境變數未設定或設定錯誤
2. Supabase URL 或 Key 無效
3. Supabase RLS（Row Level Security）政策阻止插入

**排查步驟：**
1. 先訪問 `/api/health`，確認 `db_ready: true`
2. 如果 `db_ready: false`，檢查環境變數
3. 如果 `db_ready: true` 但 POST 仍失敗：
   - 設定 `APP_DEBUG=true` 查看詳細錯誤
   - 檢查 Vercel Function Logs
   - 檢查 Supabase Dashboard → Authentication → Policies

### Q: 找不到頁面（404）

**解決方法：**
- 確認 `vercel.json` 的路由配置正確
- 檢查 `api/index.py` 是否存在
- 嘗試清除構建快取並重新部署

### Q: Function 執行超時

**解決方法：**
- 檢查 Supabase 連線是否正常
- 確認沒有無限迴圈或長時間運算
- 考慮使用 Vercel Pro 方案以獲得更長的超時時間

### Q: 日期/時間格式錯誤

前端已設定為強制使用 YYYY-MM-DD 和 HH:MM 格式。如果仍有問題：
- 檢查 Supabase `notes` 表的欄位類型（`event_date` 應為 DATE，`event_time` 應為 TIME）
- 查看 POST 請求的 payload（在 Function Logs 中）

## 技術細節

### 檔案修改摘要

1. **src/db_config.py**
   - 改為動態讀取環境變數
   - 支援多種金鑰變數名稱
   - 移除型別註解以支援較舊的 Python 版本

2. **src/main_flask.py**
   - 將 `translate_note` 從 `async def` 改為 `def`
   - 改善 `_run_async()` 輔助函數以支援 serverless 環境
   - 新增詳細的環境變數日誌
   - 改善錯誤訊息

3. **api/index.py**
   - 改善路徑處理
   - 新增註解說明

4. **vercel.json**
   - 移除舊版的 `builds` 和 `routes` 配置
   - 改用新版的 `rewrites` 配置
   - Vercel 會自動檢測和部署 Python 函數
   - 避免 "unused-build-settings" 警告

### Vercel Serverless 限制

- **執行時間限制**：免費方案 10 秒，Pro 方案 60 秒
- **記憶體限制**：1024 MB（免費方案）
- **套件大小限制**：預設 50 MB
- **無法使用背景任務**：每個請求都是獨立的 function 執行

### 最佳實踐

1. **環境變數管理**：使用 Vercel 的環境變數管理，不要在程式碼中硬編碼
2. **錯誤處理**：所有路由都有完整的 try-catch 和日誌
3. **健康檢查**：定期檢查 `/api/health` 端點
4. **監控**：在 Vercel Dashboard 查看 Function Logs 和 Analytics

## 獲取 Supabase 金鑰

如果您還沒有 Supabase 金鑰：

1. 前往 [Supabase Dashboard](https://app.supabase.com)
2. 選擇您的專案（nasmrxzpyvatumbrypxf）
3. 前往 Settings → API
4. 複製以下內容：
   - **Project URL**（用於 `SUPABASE_URL`）
   - **anon public key**（用於 `SUPABASE_ANON_KEY`）

⚠️ **安全提示**：
- `anon key` 可以安全地在前端使用
- 如需完整資料庫權限，使用 `service_role key`（但不要在前端暴露）
- 使用 RLS（Row Level Security）政策保護資料

## 支援

如果遇到其他問題：
1. 查看 Vercel Function Logs
2. 檢查 `/api/health` 端點回應
3. 使用 `APP_DEBUG=true` 獲取詳細錯誤訊息
4. 檢查 Supabase Dashboard 的 Logs
