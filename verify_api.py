#!/usr/bin/env python3
"""
快速驗證腳本 - 測試 API 端點是否正常工作
可以用於本地開發和 Vercel 部署後的驗證
"""
import urllib.request
import json
import sys
from datetime import datetime

def test_endpoint(base_url, verbose=True):
    """測試所有關鍵端點"""
    results = []
    
    # 測試 1: Health Check
    if verbose:
        print("\n" + "="*60)
        print("測試 1: Health Check")
        print("="*60)
    
    try:
        url = f"{base_url}/api/health"
        if verbose:
            print(f"GET {url}")
        
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode())
        
        if verbose:
            print(f"Status: {response.status}")
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data.get('db_ready'):
            results.append(("Health Check", True, "✓ DB ready"))
        else:
            results.append(("Health Check", False, "✗ DB not ready - check environment variables"))
    except Exception as e:
        results.append(("Health Check", False, f"✗ Error: {e}"))
        if verbose:
            print(f"Error: {e}")
    
    # 測試 2: GET Notes
    if verbose:
        print("\n" + "="*60)
        print("測試 2: GET /api/notes")
        print("="*60)
    
    try:
        url = f"{base_url}/api/notes"
        if verbose:
            print(f"GET {url}")
        
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode())
        
        if verbose:
            print(f"Status: {response.status}")
            print(f"Found {len(data)} note(s)")
        
        if response.status == 200:
            results.append(("GET Notes", True, f"✓ Retrieved {len(data)} notes"))
        else:
            results.append(("GET Notes", False, f"✗ Unexpected status: {response.status}"))
    except Exception as e:
        results.append(("GET Notes", False, f"✗ Error: {e}"))
        if verbose:
            print(f"Error: {e}")
    
    # 測試 3: POST Note
    if verbose:
        print("\n" + "="*60)
        print("測試 3: POST /api/notes")
        print("="*60)
    
    try:
        url = f"{base_url}/api/notes"
        
        # 建立測試資料
        test_note = {
            "title": f"測試筆記 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": "這是一個自動測試建立的筆記",
            "event_date": "2025-10-18",
            "event_time": "14:30",
            "tags": "測試,自動化"
        }
        
        if verbose:
            print(f"POST {url}")
            print(f"Payload: {json.dumps(test_note, indent=2, ensure_ascii=False)}")
        
        req = urllib.request.Request(
            url,
            data=json.dumps(test_note).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        if verbose:
            print(f"Status: {response.status}")
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if response.status == 201 and data.get('id'):
            results.append(("POST Note", True, f"✓ Created note with ID: {data['id']}"))
            created_id = data['id']
        else:
            results.append(("POST Note", False, f"✗ Unexpected response"))
            created_id = None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        results.append(("POST Note", False, f"✗ HTTP {e.code}: {error_body}"))
        if verbose:
            print(f"HTTP Error {e.code}")
            print(f"Response: {error_body}")
        created_id = None
    except Exception as e:
        results.append(("POST Note", False, f"✗ Error: {e}"))
        if verbose:
            print(f"Error: {e}")
        created_id = None
    
    # 測試 4: GET Single Note (如果建立成功)
    if created_id:
        if verbose:
            print("\n" + "="*60)
            print(f"測試 4: GET /api/notes/{created_id}")
            print("="*60)
        
        try:
            url = f"{base_url}/api/notes/{created_id}"
            if verbose:
                print(f"GET {url}")
            
            response = urllib.request.urlopen(url)
            data = json.loads(response.read().decode())
            
            if verbose:
                print(f"Status: {response.status}")
                print(f"Retrieved note: {data.get('title')}")
            
            if response.status == 200 and data.get('id') == created_id:
                results.append(("GET Single Note", True, "✓ Retrieved note successfully"))
            else:
                results.append(("GET Single Note", False, "✗ Unexpected response"))
        except Exception as e:
            results.append(("GET Single Note", False, f"✗ Error: {e}"))
            if verbose:
                print(f"Error: {e}")
        
        # 測試 5: DELETE Note (清理測試資料)
        if verbose:
            print("\n" + "="*60)
            print(f"測試 5: DELETE /api/notes/{created_id}")
            print("="*60)
        
        try:
            url = f"{base_url}/api/notes/{created_id}"
            if verbose:
                print(f"DELETE {url}")
            
            req = urllib.request.Request(url, method='DELETE')
            response = urllib.request.urlopen(req)
            
            if verbose:
                print(f"Status: {response.status}")
                print("✓ Test note deleted")
            
            results.append(("DELETE Note", True, "✓ Deleted test note"))
        except Exception as e:
            results.append(("DELETE Note", False, f"✗ Error: {e}"))
            if verbose:
                print(f"Error: {e}")
    
    return results

def print_summary(results):
    """印出測試摘要"""
    print("\n" + "="*60)
    print("測試摘要")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, message in results:
        status = "✓" if success else "✗"
        print(f"{status} {test_name:20s} {message}")
    
    print("\n" + "="*60)
    print(f"結果: {passed}/{total} 測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！應用已準備好使用")
        return 0
    else:
        print("⚠️  部分測試失敗，請檢查錯誤訊息")
        return 1

def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        # 預設使用本地開發伺服器
        base_url = "http://127.0.0.1:5000"
    
    print("="*60)
    print("API 端點驗證工具")
    print("="*60)
    print(f"測試目標: {base_url}")
    
    # 詢問是否顯示詳細輸出
    verbose = True
    if len(sys.argv) > 2 and sys.argv[2] == '--quiet':
        verbose = False
    
    try:
        results = test_endpoint(base_url, verbose)
        return print_summary(results)
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
        return 1
    except Exception as e:
        print(f"\n\n測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # 使用範例:
    # python verify_api.py                                    # 測試本地 (127.0.0.1:5000)
    # python verify_api.py http://127.0.0.1:5002             # 測試本地指定埠
    # python verify_api.py https://your-app.vercel.app       # 測試 Vercel 部署
    # python verify_api.py https://your-app.vercel.app --quiet  # 安靜模式
    
    sys.exit(main())
