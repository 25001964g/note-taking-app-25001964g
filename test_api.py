#!/usr/bin/env python3
"""
Test script for the note generation API endpoints
"""
import requests
import json
import os

# Set up the environment
with open('token.txt', 'r') as f:
    token = f.read().strip()
os.environ['GITHUB_TOKEN'] = token

BASE_URL = 'http://127.0.0.1:5005'

def test_generate_note():
    """Test the /api/notes/generate endpoint"""
    print("測試 /api/notes/generate 端點...")
    
    # Test English
    data = {
        "text": "Meeting with John at 3pm on Friday to discuss the project updates",
        "language": "English"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/notes/generate", 
                               headers={'Content-Type': 'application/json'},
                               json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 英文測試成功:")
            print(f"  標題: {result['title']}")
            print(f"  內容: {result['content']}")
            print(f"  標籤: {result['tags']}")
        else:
            print(f"❌ 英文測試失敗: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 英文測試錯誤: {e}")
    
    # Test Chinese
    data_cn = {
        "text": "明天下午3點和John開會討論專案進度",
        "language": "Chinese"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/notes/generate", 
                               headers={'Content-Type': 'application/json'},
                               json=data_cn)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 中文測試成功:")
            print(f"  標題: {result['title']}")
            print(f"  內容: {result['content']}")
            print(f"  標籤: {result['tags']}")
        else:
            print(f"❌ 中文測試失敗: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 中文測試錯誤: {e}")

def test_generate_and_save_note():
    """Test the /api/notes/generate-and-save endpoint"""
    print("\n\n測試 /api/notes/generate-and-save 端點...")
    
    data = {
        "text": "Badminton match tomorrow 5pm at PolyU sports center",
        "language": "English"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/notes/generate-and-save", 
                               headers={'Content-Type': 'application/json'},
                               json=data)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ 生成並儲存測試成功:")
            print(f"  筆記ID: {result['note']['id']}")
            print(f"  標題: {result['note']['title']}")
            print(f"  內容: {result['note']['content']}")
            print(f"  標籤: {result['note']['tags']}")
        else:
            print(f"❌ 生成並儲存測試失敗: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 生成並儲存測試錯誤: {e}")

def test_get_notes():
    """Test getting all notes to verify the saved note"""
    print("\n\n驗證已儲存的筆記...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/notes")
        
        if response.status_code == 200:
            notes = response.json()
            print(f"✅ 成功取得 {len(notes)} 條筆記")
            for note in notes[:3]:  # Show first 3 notes
                print(f"  - {note['title']}: {note['content'][:50]}...")
        else:
            print(f"❌ 取得筆記失敗: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 取得筆記錯誤: {e}")

if __name__ == "__main__":
    print("🚀 開始測試筆記生成API端點\n")
    
    test_generate_note()
    test_generate_and_save_note()
    test_get_notes()
    
    print("\n✨ 測試完成!")