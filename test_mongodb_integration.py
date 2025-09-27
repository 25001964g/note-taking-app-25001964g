"""
Comprehensive Test Suite for MongoDB Atlas Note-Taking App
Tests all API endpoints, AI features, and database operations
"""
import os
import sys
import json
import requests
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_mongodb_atlas_integration():
    """Test MongoDB Atlas connection and basic operations"""
    print("🔗 Testing MongoDB Atlas Integration...")
    
    try:
        from src.models.mongo_atlas_note import MongoNote
        
        # Test connection
        mongo_model = MongoNote()
        stats = mongo_model.get_database_stats()
        
        print(f"✅ MongoDB Atlas connected successfully")
        print(f"   Database: {stats.get('database_name', 'notetaker')}")
        print(f"   Total Notes: {stats.get('total_notes', 0)}")
        
        # Test basic CRUD operations
        test_note_data = {
            'title': 'Test Note for MongoDB Atlas',
            'content': 'This is a test note to verify MongoDB Atlas integration',
            'tags': ['test', 'mongodb', 'atlas'],
            'event_date': '2024-01-15',
            'event_time': '10:30:00'
        }
        
        # Create a test note
        print("\n📝 Testing note creation...")
        note_id = mongo_model.create_note(test_note_data)
        print(f"✅ Note created with ID: {note_id}")
        
        # Retrieve the note
        print("\n📖 Testing note retrieval...")
        retrieved_note = mongo_model.get_note(note_id)
        print(f"✅ Note retrieved: {retrieved_note['title']}")
        
        # Update the note
        print("\n✏️  Testing note update...")
        updated_data = {
            'title': 'Updated Test Note',
            'content': 'This note has been updated to test MongoDB Atlas functionality',
            'tags': ['test', 'mongodb', 'atlas', 'updated']
        }
        mongo_model.update_note(note_id, updated_data)
        updated_note = mongo_model.get_note(note_id)
        print(f"✅ Note updated: {updated_note['title']}")
        
        # Search functionality
        print("\n🔍 Testing search functionality...")
        search_results = mongo_model.search_notes('updated')
        print(f"✅ Search found {len(search_results)} results")
        
        # Clean up test note
        print("\n🗑️  Cleaning up test note...")
        mongo_model.delete_note(note_id)
        print("✅ Test note deleted")
        
        mongo_model.close_connection()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB Atlas test failed: {str(e)}")
        return False

def test_ai_features():
    """Test AI note generation features"""
    print("\n🤖 Testing AI Features...")
    
    try:
        from src.llm import extract_notes
        
        # Test AI note generation
        test_text = """
        Yesterday I attended a team meeting about the new project. 
        We discussed the timeline, which should be completed by March 15th, 2024.
        Key participants included John Smith (Project Manager) and Sarah Wilson (Lead Developer).
        The main deliverables are: mobile app design, backend API development, and database setup.
        Next meeting is scheduled for January 20th at 2:00 PM.
        """
        
        print("📝 Testing AI note generation...")
        generated_note = extract_notes(test_text, 'english')
        
        if generated_note and 'title' in generated_note:
            print(f"✅ AI generated note: {generated_note['title']}")
            print(f"   Tags: {', '.join(generated_note.get('tags', []))}")
            print(f"   Event Date: {generated_note.get('event_date', 'Not specified')}")
            return True
        else:
            print("❌ AI note generation failed - no valid response")
            return False
            
    except Exception as e:
        print(f"❌ AI features test failed: {str(e)}")
        return False

def test_api_endpoints(base_url='http://127.0.0.1:5002'):
    """Test all Flask API endpoints"""
    print(f"\n🌐 Testing API Endpoints at {base_url}...")
    
    try:
        # Test health endpoint
        print("🏥 Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data['status']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test API info endpoint
        print("\n📚 Testing API info endpoint...")
        response = requests.get(f"{base_url}/api/info", timeout=10)
        if response.status_code == 200:
            api_info = response.json()
            print(f"✅ API info retrieved: {api_info['application']}")
        else:
            print(f"❌ API info failed: {response.status_code}")
        
        # Test get all notes
        print("\n📋 Testing get all notes...")
        response = requests.get(f"{base_url}/api/notes", timeout=10)
        if response.status_code == 200:
            notes = response.json()
            print(f"✅ Retrieved {len(notes)} notes")
        else:
            print(f"❌ Get notes failed: {response.status_code}")
        
        # Test create note
        print("\n📝 Testing create note endpoint...")
        test_note = {
            'title': 'API Test Note',
            'content': 'This note was created via API test',
            'tags': ['api', 'test', 'automation'],
            'event_date': '2024-01-16',
            'event_time': '14:30:00'
        }
        
        response = requests.post(f"{base_url}/api/notes", 
                               json=test_note, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 201:
            created_note = response.json()
            note_id = created_note['_id']
            print(f"✅ Note created via API: {created_note['title']}")
            
            # Test update note
            print("\n✏️  Testing update note endpoint...")
            updated_data = {
                'title': 'Updated API Test Note',
                'content': 'This note was updated via API test'
            }
            
            response = requests.put(f"{base_url}/api/notes/{note_id}",
                                  json=updated_data,
                                  headers={'Content-Type': 'application/json'},
                                  timeout=10)
            
            if response.status_code == 200:
                print("✅ Note updated via API")
            else:
                print(f"❌ Note update failed: {response.status_code}")
            
            # Test AI generation endpoint
            print("\n🤖 Testing AI generation endpoint...")
            ai_request = {
                'text': 'I need to prepare for a client presentation on February 1st. Meeting with ABC Corp at 3 PM. Need to create slides, prepare demo, and review contract.',
                'language': 'english'
            }
            
            response = requests.post(f"{base_url}/api/notes/generate",
                                   json=ai_request,
                                   headers={'Content-Type': 'application/json'},
                                   timeout=30)
            
            if response.status_code == 200:
                ai_note = response.json()
                print(f"✅ AI note generated: {ai_note.get('title', 'No title')}")
            else:
                print(f"❌ AI generation failed: {response.status_code}")
            
            # Clean up test note
            print("\n🗑️  Cleaning up API test note...")
            response = requests.delete(f"{base_url}/api/notes/{note_id}", timeout=10)
            if response.status_code == 200:
                print("✅ Test note deleted via API")
            else:
                print(f"❌ Note deletion failed: {response.status_code}")
                
        else:
            print(f"❌ Note creation failed: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API test failed - Connection error: {str(e)}")
        print("   Make sure the Flask server is running on port 5002")
        return False
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

def run_comprehensive_tests():
    """Run all tests and provide a summary"""
    print("🧪 Starting Comprehensive Test Suite for Note-Taking App")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: MongoDB Atlas Integration
    test_results['mongodb'] = test_mongodb_atlas_integration()
    
    # Test 2: AI Features
    test_results['ai'] = test_ai_features()
    
    # Test 3: API Endpoints (optional - requires server to be running)
    print("\n" + "=" * 60)
    print("📋 API Endpoint Tests (requires server to be running)")
    server_test = input("Do you want to test API endpoints? Server must be running on port 5002 (y/n): ").lower()
    
    if server_test == 'y':
        test_results['api'] = test_api_endpoints()
    else:
        test_results['api'] = None
        print("⏭️  Skipping API endpoint tests")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = 0
    
    for test_name, result in test_results.items():
        if result is not None:
            total += 1
            if result:
                passed += 1
                print(f"✅ {test_name.upper()} Tests: PASSED")
            else:
                print(f"❌ {test_name.upper()} Tests: FAILED")
        else:
            print(f"⏭️  {test_name.upper()} Tests: SKIPPED")
    
    print(f"\n🎯 Overall Results: {passed}/{total} test suites passed")
    
    if passed == total and total > 0:
        print("🎉 All tests passed! Your MongoDB Atlas integration is working perfectly!")
        print("\n🚀 Ready to start your application:")
        print("   ./start_dev_server.sh")
        print("\n🌐 Then visit: http://127.0.0.1:5002")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    print("=" * 60)

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    run_comprehensive_tests()