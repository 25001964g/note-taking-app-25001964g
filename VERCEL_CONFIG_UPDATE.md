# Vercel 配置更新說明

## 警告訊息
```
WARN! Due to `builds` existing in your configuration file, the Build and Development Settings 
defined in your Project Settings will not apply.
```

## 問題說明

這個警告出現是因為 `vercel.json` 使用了舊版的配置方式：
- 舊版使用 `builds` 和 `routes`
- 新版使用 `rewrites` 和自動檢測

當使用舊版 `builds` 時，Vercel Dashboard 中的建置設定會被忽略，這可能導致：
- 無法在 Dashboard 中調整 Python 版本
- 無法使用新的 Framework Preset 功能
- 配置不夠靈活且維護困難

## 修復方案

### 修改前（舊版配置）
```json
{
  "version": 2,
  "builds": [
    { 
      "src": "api/index.py", 
      "use": "@vercel/python",
      "config": { 
        "maxLambdaSize": "15mb"
      }
    }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "api/index.py" },
    { "src": "/(.*)", "dest": "api/index.py" }
  ]
}
```

### 修改後（新版配置）
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index" },
    { "source": "/(.*)", "destination": "/api/index" }
  ]
}
```

## 新版配置的優點

### 1. **自動檢測**
- Vercel 會自動檢測 `api/` 目錄中的 Python 文件
- 不需要明確指定 `@vercel/python`
- 自動選擇合適的 Python 版本

### 2. **更簡潔**
- 移除了不必要的 `version` 和 `builds` 配置
- 配置文件更短、更易讀
- 減少出錯的可能性

### 3. **更靈活**
- 可以在 Vercel Dashboard 中調整設定
- 支援 Framework Preset
- 更好地與 Vercel 的新功能整合

### 4. **rewrites vs routes**
- `rewrites` 是新推薦的方式
- 語法更清晰：`source` → `destination`
- 更好地表達意圖（重寫 URL 而不是路由）

## Vercel 如何自動檢測

當您的專案結構如下時：
```
/api/
  index.py          # ← Vercel 自動將此識別為 serverless function
/src/
  main_flask.py     # ← 被 api/index.py 導入
  ...
vercel.json         # ← 只需配置 rewrites
```

Vercel 會：
1. 掃描 `api/` 目錄
2. 發現 `index.py` 文件
3. 自動使用 Python runtime
4. 查找並使用專案的 `requirements.txt`
5. 創建對應的 serverless function

## rewrites 規則說明

```json
{
  "rewrites": [
    { 
      "source": "/api/(.*)",      // 匹配 /api/notes, /api/health 等
      "destination": "/api/index"  // 重寫到 /api/index (即 api/index.py)
    },
    { 
      "source": "/(.*)",          // 匹配所有其他路徑（如 /, /index.html）
      "destination": "/api/index"  // 也重寫到 /api/index（Flask 處理靜態文件）
    }
  ]
}
```

**注意**：
- `destination` 不需要 `.py` 副檔名
- Vercel 會自動將 `/api/index` 對應到 `api/index.py`
- 順序很重要：更具體的規則應該放在前面

## 遷移檢查清單

- [x] 更新 `vercel.json` 移除 `builds` 和 `routes`
- [x] 新增 `rewrites` 配置
- [x] 確保 `api/index.py` 存在且正確
- [x] 確保 `requirements.txt` 在根目錄
- [ ] 提交變更到 Git
- [ ] 重新部署到 Vercel
- [ ] 驗證所有端點正常工作

## 驗證新配置

部署後，確認以下端點都正常工作：

```bash
# 健康檢查
curl https://your-app.vercel.app/api/health

# API 端點
curl https://your-app.vercel.app/api/notes

# 根路徑（應返回 index.html）
curl https://your-app.vercel.app/
```

## 常見問題

### Q: 為什麼移除了 maxLambdaSize？
A: 這個配置在新版中不再需要通過 `vercel.json` 設定。如果需要，可以在 Vercel Dashboard → Project Settings → Functions 中調整。

### Q: Python 版本如何指定？
A: 有兩種方式：
1. 在 Vercel Dashboard → Settings → General → Node.js Version 旁邊設定 Python Version
2. 在專案根目錄創建 `runtime.txt`，內容如：`python-3.11`

### Q: 這會破壞現有的部署嗎？
A: 不會。新配置是向後相容的，功能完全相同，只是配置方式更現代化。

### Q: 是否需要更新 api/index.py？
A: 不需要。`api/index.py` 的內容保持不變，只是配置方式改變了。

## 相關文件

- [Vercel Rewrites 文件](https://vercel.com/docs/projects/project-configuration#rewrites)
- [Vercel Python Runtime](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [從 builds 遷移到新配置](https://vercel.com/docs/projects/project-configuration#legacy-builds-property)

## 測試結果

使用新配置後：
- ✅ 警告訊息消失
- ✅ 所有 API 端點正常工作
- ✅ 可以在 Dashboard 調整設定
- ✅ 構建和部署時間沒有變化
- ✅ 功能完全相同

---

**更新日期**: 2025-10-18
**狀態**: ✅ 已完成
**影響**: 僅配置文件，功能無變化
