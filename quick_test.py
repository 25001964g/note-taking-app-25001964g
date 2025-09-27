#!/usr/bin/env python3
"""
Quick MongoDB Connection and API Test
Tests MongoDB Atlas connection and basic API functionality
"""
import os
import sys
import requests
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_mongodb_connection():
    """Test direct MongoDB Atlas connection"""
    print("🔗 Testing MongoDB Atlas Connection...")
    
    try:
        from src.models.mongo_atlas_note import MongoNote
        from dotenv import load_dotenv
        load_dotenv()
        
        # Test connection
        mongo_model = MongoNote()
        stats = mongo_model.get_database_stats()
        
        print(f"✅ MongoDB Atlas connected successfully")
        print(f"   Database: {stats.get('database_name', 'notetaker')}")
        print(f"   Total Notes: {stats.get('total_notes', 0)}")
        
        # Test basic create operation
        test_note = {
            'title': 'Connection Test Note',
            'content': 'Testing MongoDB Atlas connection',
            'tags': ['test', 'connection'],
            'event_date': '2024-01-15'
        }
        
        note_id = mongo_model.create_note(test_note)
        print(f"✅ Created test note with ID: {note_id}")
        
        # Clean up
        mongo_model.delete_note(note_id)
        print("✅ Test note cleaned up")
        
        mongo_model.close_connection()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_server_running():
    """Test if Flask server is running"""
    print("\n🌐 Testing Flask Server Status...")
    
    try:
        response = requests.get("http://127.0.0.1:5002/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running: {data.get('status', 'unknown')}")
            print(f"   Database: {data.get('database', 'unknown')}")
            print(f"   Total Notes: {data.get('total_notes', 0)}")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - make sure Flask app is running on port 5002")
        return False
    except Exception as e:
        print(f"❌ Server test failed: {str(e)}")
        return False

def test_api_create_note():
    """Test API note creation"""
    print("\n📝 Testing API Note Creation...")
    
    try:
        test_note = {
            'title': 'API Test Note',
            'content': 'This note was created via API test',
            'tags': ['api', 'test'],
            'event_date': '2024-01-16'
        }
        
        response = requests.post(
            "http://127.0.0.1:5002/api/notes",
            json=test_note,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 201:
            data = response.json()
            note_id = data.get('_id')
            print(f"✅ Note created successfully with ID: {note_id}")
            
            # Test deletion
            delete_response = requests.delete(f"http://127.0.0.1:5002/api/notes/{note_id}", timeout=10)
            if delete_response.status_code == 200:
                print("✅ Test note deleted successfully")
            
            return True
            
        else:
            print(f"❌ Note creation failed")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API create test failed: {str(e)}")
        return False

def test_ai_generation():
    """Test AI note generation"""
    print("\n🤖 Testing AI Note Generation...")
    
    try:
        ai_request = {
            'text': 'Tomorrow I have a meeting with the client at 2 PM to discuss project requirements.',
            'language': 'english'
        }
        
        response = requests.post(
            "http://127.0.0.1:5002/api/notes/generate-and-save",
            json=ai_request,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            note_id = data.get('_id')
            print(f"✅ AI note generated: {data.get('title', 'No title')}")
            print(f"   ID: {note_id}")
            
            # Clean up AI note
            requests.delete(f"http://127.0.0.1:5002/api/notes/{note_id}", timeout=10)
            print("✅ AI note cleaned up")
            return True
            
        else:
            print(f"❌ AI generation failed")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ AI generation test failed: {str(e)}")
        return False

def main():
    print("🧪 Quick MongoDB Atlas and API Test")
    print("=" * 50)
    
    # Test 1: MongoDB Connection
    mongodb_ok = test_mongodb_connection()
    
    # Test 2: Server Status
    server_ok = test_server_running()
    
    if server_ok:
        # Test 3: API Note Creation
        api_ok = test_api_create_note()
        
        # Test 4: AI Generation
        ai_ok = test_ai_generation()
    else:
        print("\n⚠️  Skipping API tests - server not available")
        api_ok = False
        ai_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    tests = [
        ("MongoDB Connection", mongodb_ok),
        ("Flask Server", server_ok),
        ("API CRUD Operations", api_ok),
        ("AI Note Generation", ai_ok)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your application is working correctly!")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()