"""
MongoDB Atlas Data Verification Guide
Instructions for checking data in MongoDB Atlas dashboard and via code
"""

# =====================================
# METHOD 1: MongoDB Atlas Web Dashboard
# =====================================

"""
1. Go to https://cloud.mongodb.com/
2. Log in with your MongoDB Atlas credentials
3. Navigate to your cluster
4. Click "Browse Collections"
5. Select database: "notetaker"
6. Select collection: "notes"
7. View all documents and their structure
"""

# =====================================
# METHOD 2: Direct Database Query Script
# =====================================

import os
import sys
from datetime import datetime
from pprint import pprint

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def check_mongodb_data():
    """Check all data in MongoDB Atlas"""
    print("🔍 Checking MongoDB Atlas Data...")
    print("=" * 50)
    
    try:
        from src.models.mongo_atlas_note import MongoNote
        from dotenv import load_dotenv
        load_dotenv()
        
        # Connect to MongoDB
        mongo_model = MongoNote()
        
        # Get database statistics
        print("📊 Database Statistics:")
        stats = mongo_model.get_database_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n📋 All Notes in Database:")
        print("-" * 50)
        
        # Get all notes
        notes = mongo_model.get_all_notes()
        
        if not notes:
            print("   No notes found in database")
        else:
            for i, note in enumerate(notes, 1):
                print(f"\n📝 Note #{i}:")
                print(f"   ID: {note['id']}")
                print(f"   Title: {note['title']}")
                print(f"   Content: {note['content'][:100]}{'...' if len(note['content']) > 100 else ''}")
                print(f"   Tags: {note.get('tags', [])}")
                print(f"   Event Date: {note.get('event_date', 'None')}")
                print(f"   Event Time: {note.get('event_time', 'None')}")
                print(f"   Created: {note.get('created_at', 'Unknown')}")
                print(f"   Updated: {note.get('updated_at', 'Unknown')}")
                print("-" * 30)
        
        # Close connection
        mongo_model.close_connection()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking MongoDB data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# =====================================
# METHOD 3: Real-time Data Monitoring
# =====================================

def monitor_api_requests():
    """Monitor API requests and data being sent"""
    print("\n🔍 API Request Monitoring Guide:")
    print("=" * 50)
    
    print("""
    1. Check server logs:
       tail -f server.log
    
    2. Monitor API calls with curl:
       # Get all notes
       curl -X GET http://127.0.0.1:5002/api/notes
       
       # Create a test note
       curl -X POST http://127.0.0.1:5002/api/notes \\
         -H "Content-Type: application/json" \\
         -d '{"title": "Test Note", "content": "Testing data flow", "tags": ["test"]}'
    
    3. Check specific note by ID:
       curl -X GET http://127.0.0.1:5002/api/notes/<note_id>
    
    4. Test AI generation:
       curl -X POST http://127.0.0.1:5002/api/notes/generate-and-save \\
         -H "Content-Type: application/json" \\
         -d '{"text": "Meeting tomorrow at 2 PM", "language": "english"}'
    """)

# =====================================
# METHOD 4: Database Connection Test
# =====================================

def test_database_connection():
    """Test database connection and show connection details"""
    print("\n🔗 Database Connection Test:")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        import pymongo
        load_dotenv()
        
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            print("❌ MONGODB_URI not found in environment variables")
            return False
        
        print(f"🔗 Connecting to: {mongodb_uri[:50]}...")
        
        # Create client and test connection
        client = pymongo.MongoClient(mongodb_uri)
        
        # Test ping
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # Get database and collection info
        db = client['notetaker']
        collection = db['notes']
        
        # Count documents
        count = collection.count_documents({})
        print(f"📊 Total documents in 'notes' collection: {count}")
        
        # Show collection indexes
        indexes = list(collection.list_indexes())
        print(f"📋 Database indexes: {len(indexes)}")
        for idx in indexes:
            print(f"   - {idx['name']}: {idx.get('key', {})}")
        
        # Show sample document structure
        sample = collection.find_one()
        if sample:
            print("\n📝 Sample Document Structure:")
            for key, value in sample.items():
                print(f"   {key}: {type(value).__name__} - {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 MongoDB Atlas Data Verification Tool")
    print("=" * 60)
    
    # Run all checks
    check_mongodb_data()
    test_database_connection()
    monitor_api_requests()
    
    print("\n" + "=" * 60)
    print("✅ Data verification complete!")
    print("\nFor real-time monitoring:")
    print("1. Keep server running: python src/main_atlas.py")
    print("2. Monitor logs: tail -f server.log")
    print("3. Test APIs with curl commands above")
    print("4. Check MongoDB Atlas dashboard online")