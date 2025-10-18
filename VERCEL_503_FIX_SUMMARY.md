# Vercel 503 錯誤修復摘要

## 問題描述
在 Vercel 部署後，POST `/api/notes` 端點返回 503 錯誤，導致無法儲存筆記。

## 根本原因分析

### 1. **異步/同步不相容**
- Flask 在 WSGI/serverless 環境下不支援 `async def` 路由
- `translate_note` 路由使用了 `async def`，導致執行錯誤

### 2. **環境變數快取問題**
- `db_config.py` 在模組導入時讀取環境變數並快取
- Vercel serverless 環境下，環境變數可能在導入後才設定
- 導致 DB 初始化失敗，返回 503

### 3. **事件循環管理問題**
- 原有的 `_run_async()` 在某些 serverless 環境下無法正確處理事件循環
- 可能導致 "Event loop is closed" 錯誤

## 實施的修復

### 1. 修復 `src/db_config.py`

**變更前：**
```python
# 在導入時讀取並快取環境變數
_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_KEY = os.getenv("SUPABASE_KEY")
```

**變更後：**
```python
def _read_env():
    """每次呼叫時動態讀取環境變數"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return url, key

def init_supabase_if_needed() -> bool:
    # 每次都重新讀取環境變數
    url, key = _read_env()
    # ...
```

**效果：**
- ✓ 支援延遲設定的環境變數
- ✓ 支援多種金鑰變數名稱
- ✓ 避免冷啟動時的初始化失敗

### 2. 修復 `src/main_flask.py` - 異步處理

**變更前：**
```python
@app.route('/api/notes/<note_id>/translate', methods=['POST'])
async def translate_note(note_id):
    note = await Note.get_by_id(note_id)
    # ...
```

**變更後：**
```python
@app.route('/api/notes/<note_id>/translate', methods=['POST'])
def translate_note(note_id):
    note = _run_async(Note.get_by_id(note_id))
    # ...
```

**效果：**
- ✓ 所有路由都是同步函數
- ✓ 使用 `_run_async()` 安全執行異步操作
- ✓ 相容 WSGI 和 serverless 環境

### 3. 改善 `_run_async()` 函數

**變更前：**
```python
def _run_async(coro):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # 建立新循環...
    # ...
```

**變更後：**
```python
def _run_async(coro):
    """使用 asyncio.run() 簡化事件循環管理"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
        if loop.is_running():
            # 使用線程池執行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)
```

**效果：**
- ✓ 更穩健的事件循環管理
- ✓ 處理循環關閉的情況
- ✓ 支援巢狀事件循環（如果需要）

### 4. 增強錯誤診斷

**新增功能：**
- `/api/health` 端點顯示環境變數狀態
- POST 端點增加詳細日誌
- 支援 `APP_DEBUG=true` 顯示詳細錯誤

**範例日誌：**
```
Environment check - SUPABASE_URL exists: True
Environment check - SUPABASE_KEY exists: True
DB initialization result: True
Creating note with title: Test and content length: 5
Incoming tags: test,demo
Incoming event_date: 2025-10-18 event_time: 14:30
```

### 5. 優化 `vercel.json`

**變更：**
- 移除舊版的 `builds` 和 `routes` 配置
- 改用新版的 `rewrites` 配置
- Vercel 現在會自動檢測 Python 函數
- 簡化配置，避免 "unused-build-settings" 警告

### 6. 改善 `api/index.py`

**變更：**
- 明確設定 Python 路徑
- 新增註解說明 Vercel 的運作方式

## 測試與驗證

### 建立的測試工具

1. **test_vercel_ready.py** - Vercel 就緒性檢查
   - 驗證模組導入
   - 驗證環境變數
   - 驗證 Flask 應用建立
   - 驗證異步輔助函數

2. **verify_api.py** - API 端點驗證
   - 測試健康檢查端點
   - 測試 GET/POST/DELETE 操作
   - 可用於本地和 Vercel 環境

### 測試結果

```
✓ Imports              PASS
✓ Environment          PASS
✓ App Creation         PASS
✓ Async Helper         PASS
```

## 部署指南

完整的部署說明請參考：
- `VERCEL_DEPLOY_GUIDE.md` - 詳細部署指南
- `DEPLOY_CHECKLIST.md` - 快速檢查清單

### 快速部署步驟

1. **設定環境變數**（在 Vercel Dashboard）
   ```
   SUPABASE_URL=https://nasmrxzpyvatumbrypxf.supabase.co
   SUPABASE_ANON_KEY=<your-key>
   ```

2. **推送程式碼**
   ```bash
   git add .
   git commit -m "Fix Vercel serverless compatibility"
   git push origin main
   ```

3. **驗證部署**
   ```bash
   curl https://your-app.vercel.app/api/health
   # 應返回 "db_ready": true
   ```

## 影響範圍

### 修改的檔案
- ✓ `src/db_config.py` - 環境變數處理
- ✓ `src/main_flask.py` - 路由和異步處理
- ✓ `api/index.py` - Vercel 入口點
- ✓ `vercel.json` - 部署配置

### 新增的檔案
- ✓ `test_vercel_ready.py` - 就緒性測試
- ✓ `verify_api.py` - API 驗證工具
- ✓ `VERCEL_DEPLOY_GUIDE.md` - 部署指南
- ✓ `DEPLOY_CHECKLIST.md` - 檢查清單
- ✓ `VERCEL_503_FIX_SUMMARY.md` - 本文件

### 未修改的檔案
- `src/models/note_supabase.py` - 模型邏輯保持不變
- `src/static/index.html` - 前端程式碼保持不變
- `requirements.txt` - 依賴保持不變

## 預期結果

修復後的行為：

### ✓ 成功情境
- GET `/api/notes` → 200，返回筆記列表
- POST `/api/notes` → 201，建立新筆記
- PUT `/api/notes/:id` → 200，更新筆記
- DELETE `/api/notes/:id` → 200，刪除筆記
- GET `/api/health` → 200，顯示 `db_ready: true`

### ⚠️ 部分失敗情境（環境變數未設定）
- GET `/api/notes` → 200，返回空陣列 + 警告標頭
- POST `/api/notes` → 503，明確錯誤訊息
- GET `/api/health` → 503，顯示 `db_ready: false`

## 後續監控

部署後建議監控以下指標：

1. **Function Logs**（Vercel Dashboard）
   - 查看是否有未預期的錯誤
   - 確認環境變數正確載入

2. **健康檢查**
   - 定期訪問 `/api/health`
   - 確認 `db_ready` 始終為 `true`

3. **錯誤率**
   - 監控 4xx/5xx 錯誤比例
   - 特別注意 503 錯誤

4. **回應時間**
   - 首次請求（冷啟動）: < 3 秒
   - 後續請求: < 500ms

## 技術債務與改進建議

### 已解決
- ✓ 異步/同步相容性問題
- ✓ 環境變數動態載入
- ✓ 錯誤診斷和日誌

### 未來可改進
- [ ] 新增自動化測試（單元測試、整合測試）
- [ ] 實施 API 速率限制
- [ ] 新增 Sentry 或類似的錯誤追蹤服務
- [ ] 優化冷啟動時間
- [ ] 新增 API 文件（OpenAPI/Swagger）

## 參考資料

- [Vercel Python Runtime](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Flask WSGI](https://flask.palletsprojects.com/en/3.0.x/deploying/)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

## 版本資訊

- **修復日期**: 2025-10-18
- **Python 版本**: 3.11+ (Vercel 預設)
- **Flask 版本**: 3.0+
- **Supabase Client**: 2.10.0

---

**修復狀態**: ✅ 完成
**測試狀態**: ✅ 通過
**部署狀態**: ⏳ 待部署

部署後請執行 `python verify_api.py https://your-app.vercel.app` 進行最終驗證。
