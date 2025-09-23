# 筆記生成功能文檔

## 功能概述

已成功實作筆記生成功能，使用 `llm.py` 中的 `extract_notes` 函數來將用戶輸入轉換為結構化筆記。

## API 端點

### 1. 生成筆記 (不儲存)
```http
POST /api/notes/generate
Content-Type: application/json

{
  "text": "用戶輸入的文字",
  "language": "輸出語言 (English, Chinese, Japanese 等)"
}
```

**回應:**
```json
{
  "title": "生成的標題",
  "content": "結構化的筆記內容",
  "tags": ["標籤1", "標籤2"],
  "original_text": "原始輸入文字",
  "language": "輸出語言"
}
```

### 2. 生成並儲存筆記
```http
POST /api/notes/generate-and-save
Content-Type: application/json

{
  "text": "用戶輸入的文字",
  "language": "輸出語言 (選擇性，預設為 English)",
  "event_date": "事件日期 (選擇性，YYYY-MM-DD)",
  "event_time": "事件時間 (選擇性，HH:MM:SS)"
}
```

**回應:**
```json
{
  "note": {
    "id": 1,
    "title": "生成的標題",
    "content": "結構化的筆記內容",
    "tags": ["標籤1", "標籤2"],
    "created_at": "2025-09-23T03:45:00",
    "updated_at": "2025-09-23T03:45:00"
  },
  "original_text": "原始輸入文字",
  "language": "輸出語言"
}
```

## 使用範例

### 英文輸入
```json
{
  "text": "Meeting with John at 3pm on Friday to discuss the project updates",
  "language": "English"
}
```

**生成結果:**
```json
{
  "title": "Meeting with John",
  "content": "There is a meeting scheduled with John at 3pm on Friday to discuss the project updates.",
  "tags": ["meeting", "project", "updates"]
}
```

### 中文輸入
```json
{
  "text": "明天下午3點和John開會討論專案進度",
  "language": "Chinese"
}
```

**生成結果:**
```json
{
  "title": "明天下午會議",
  "content": "明天下午3點和John開會討論專案進度。",
  "tags": ["會議", "專案", "時間管理"]
}
```

### 日文輸入
```json
{
  "text": "買い物リスト: 牛乳、パン、卵、野菜を買う必要がある",
  "language": "Japanese"
}
```

## 功能特色

1. **多語言支援**: 支援多種輸出語言，包括英文、中文、日文等
2. **智能提取**: 自動從非結構化文字中提取標題、內容和標籤
3. **彈性選擇**: 可以選擇只生成或生成後直接儲存到資料庫
4. **錯誤處理**: 完善的JSON解析和錯誤處理機制
5. **標籤自動生成**: 自動生成最多3個相關標籤

## 測試

使用提供的 `test_api.py` 腳本來測試功能：

```bash
python3 test_api.py
```

或使用 `demo.http` 文件中的範例請求進行測試。