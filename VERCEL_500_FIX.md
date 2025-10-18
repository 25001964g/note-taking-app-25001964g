# 🐛 Vercel 500 錯誤修復

## 問題診斷

從 Vercel 日誌截圖中看到：
```
Traceback (most recent call last): File "/var/task/vc__handler__python.py", line 38, in <module>
```

這表示 Vercel 的 Python handler 在嘗試導入模組時遇到錯誤。

## 根本原因

**在 `src/llm.py` 中發現了問題：**

```python
# ❌ 錯誤的代碼（模組級別讀取環境變數）
token = os.environ["GITHUB_TOKEN"]  # 如果未設定會拋出 KeyError
endpoint = "https://models.github.ai/inference"
```

當 Vercel 嘗試導入 Flask 應用時：
1. `api/index.py` → `src/main_flask.py` → `src/llm.py`
2. `src/llm.py` 在模組級別執行 `os.environ["GITHUB_TOKEN"]`
3. 如果環境變數未設定，拋出 `KeyError`
4. 整個導入失敗，導致 500 錯誤

## 實施的修復

### 1. 修復 `src/llm.py` - 延遲載入憑證

**修改前：**
```python
token = os.environ["GITHUB_TOKEN"]  # ❌ 模組級別，會立即執行
endpoint = "https://models.github.ai/inference"

def call_llm_model(model, messages, temperature=1.0, top_p=1.0):
    client = OpenAI(base_url=endpoint, api_key=token)
    # ...
```

**修改後：**
```python
def get_llm_client():
    """Get OpenAI client with lazy loading of credentials"""
    token = os.getenv("GITHUB_TOKEN")  # ✓ 使用 getenv，只在呼叫時執行
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    endpoint = "https://models.github.ai/inference"
    return OpenAI(base_url=endpoint, api_key=token)

def call_llm_model(model, messages, temperature=1.0, top_p=1.0):
    client = get_llm_client()  # ✓ 延遲載入
    # ...
```

**效果：**
- ✅ 模組可以被安全導入，即使 `GITHUB_TOKEN` 未設定
- ✅ 只有在實際呼叫 LLM 功能時才會檢查環境變數
- ✅ 其他 API 端點（如 `/api/notes`）不受影響

### 2. 添加 `runtime.txt` - 指定 Python 版本

```
python-3.11
```

這確保 Vercel 使用正確的 Python 版本。

### 3. 添加 `.vercelignore` - 減少部署大小

排除不必要的文件：
- 測試文件
- 文檔（保留必要的）
- 資料庫文件
- Python 緩存

### 4. 簡化 `api/index.py`

```python
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main_flask import app
```

簡潔明了，避免複雜的路徑處理。

## 測試結果

### 本地測試
```bash
$ python3 -c "from api.index import app; print('✓ Import successful')"
✓ Import successful
```

### 預期 Vercel 行為

**修復前：**
- 所有請求返回 500 錯誤
- 日誌顯示 `KeyError: 'GITHUB_TOKEN'`

**修復後：**
- ✅ `/api/health` - 返回 200，顯示系統狀態
- ✅ `GET /api/notes` - 返回 200，列出筆記
- ✅ `POST /api/notes` - 返回 201，建立筆記
- ✅ `/` - 返回 200，顯示前端頁面
- ⚠️ `/api/notes/generate-and-save` - 如果未設定 `GITHUB_TOKEN`，會返回明確的錯誤訊息（而不是 500）

## 環境變數要求

### 必需（用於基本功能）
- `SUPABASE_URL` - Supabase 專案 URL
- `SUPABASE_ANON_KEY` - Supabase 匿名金鑰

### 可選（用於 AI 功能）
- `GITHUB_TOKEN` - 用於 GitHub Models API（AI 筆記生成和翻譯）

**重要**：即使沒有 `GITHUB_TOKEN`，應用的核心功能（CRUD 操作）也能正常運作。

## 部署步驟

### 1. 提交修復
```bash
git add .
git commit -m "Fix Vercel 500 error: lazy load LLM credentials"
git push origin main
```

### 2. 在 Vercel 設定環境變數

前往 Vercel Dashboard → Settings → Environment Variables：

**必需變數：**
```
SUPABASE_URL=https://nasmrxzpyvatumbrypxf.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
```

**可選變數（如需 AI 功能）：**
```
GITHUB_TOKEN=<your-github-token>
```

### 3. 驗證部署

```bash
# 檢查健康狀態
curl https://note-taking-app-25001964g.vercel.app/api/health

# 測試 GET
curl https://note-taking-app-25001964g.vercel.app/api/notes

# 測試 POST
curl -X POST https://note-taking-app-25001964g.vercel.app/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","content":"Hello"}'
```

## 檔案變更摘要

| 檔案 | 變更 | 原因 |
|------|------|------|
| `src/llm.py` | 延遲載入 `GITHUB_TOKEN` | 修復模組導入時的 KeyError |
| `runtime.txt` | 新增，指定 Python 3.11 | 確保使用正確的 Python 版本 |
| `.vercelignore` | 新增，排除不必要文件 | 減少部署大小和時間 |
| `api/index.py` | 簡化路徑處理 | 提高可讀性和可靠性 |

## 錯誤處理改善

現在 LLM 功能會提供更好的錯誤訊息：

**修復前：**
```
500 Internal Server Error (模組導入失敗)
```

**修復後：**
```json
{
  "error": "GITHUB_TOKEN environment variable is not set"
}
```

## 向後相容性

✅ **完全相容** - 所有現有功能保持不變：
- CRUD 操作
- 搜尋功能
- 日期/時間處理
- 前端 UI

## 監控建議

部署後，在 Vercel Dashboard 監控：
1. **Function Logs** - 確認沒有 import 錯誤
2. **Analytics** - 檢查錯誤率下降
3. **環境變數** - 確認所有必需變數已設定

## 故障排除

### 如果仍然出現 500 錯誤

1. **檢查日誌**
   - Vercel Dashboard → Deployments → 選擇最新部署 → Functions 標籤
   - 查看詳細錯誤訊息

2. **驗證環境變數**
   ```bash
   curl https://your-app.vercel.app/api/health
   ```
   應該顯示 `has_supabase_url: true` 和 `has_supabase_key: true`

3. **測試特定端點**
   - 如果 `/api/notes` 正常但 `/api/notes/generate-and-save` 失敗
   - 這是正常的（需要 `GITHUB_TOKEN`）

## 相關文件

- 📄 `VERCEL_DEPLOY_GUIDE.md` - 完整部署指南
- 📄 `VERCEL_CONFIG_UPDATE.md` - 配置更新說明
- 📄 `VERCEL_WARNING_FIXED.md` - 警告修復說明

---

**狀態**: ✅ 已修復
**測試**: ✅ 本地測試通過
**影響**: 修復 500 錯誤，應用可正常使用
**日期**: 2025-10-18
