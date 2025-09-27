"""
Real-time MongoDB Data Monitor
Watch data being sent to MongoDB Atlas in real-time
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from threading import Thread

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

class MongoDBDataMonitor:
    def __init__(self):
        self.monitoring = False
        self.last_count = 0
        
    def get_current_data_count(self):
        """Get current number of documents in MongoDB"""
        try:
            from src.models.mongo_atlas_note import MongoNote
            from dotenv import load_dotenv
            load_dotenv()
            
            mongo_model = MongoNote()
            stats = mongo_model.get_database_stats()
            count = stats.get('total_notes', 0)
            mongo_model.close_connection()
            return count
            
        except Exception as e:
            print(f"❌ Error getting data count: {e}")
            return -1
    
    def get_latest_notes(self, limit=3):
        """Get the latest notes from MongoDB"""
        try:
            from src.models.mongo_atlas_note import MongoNote
            from dotenv import load_dotenv
            load_dotenv()
            
            mongo_model = MongoNote()
            notes = mongo_model.get_all_notes()
            mongo_model.close_connection()
            
            # Return the latest notes (they're already sorted by updated_at DESC)
            return notes[:limit] if notes else []
            
        except Exception as e:
            print(f"❌ Error getting latest notes: {e}")
            return []
    
    def monitor_data_changes(self):
        """Monitor MongoDB for data changes"""
        print("🔍 Starting MongoDB Atlas Data Monitor...")
        print("   Watching for new data being added...")
        print("   Press Ctrl+C to stop monitoring\n")
        
        self.last_count = self.get_current_data_count()
        print(f"📊 Initial count: {self.last_count} notes")
        
        self.monitoring = True
        
        try:
            while self.monitoring:
                current_count = self.get_current_data_count()
                
                if current_count != self.last_count and current_count != -1:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if current_count > self.last_count:
                        new_notes = current_count - self.last_count
                        print(f"\n🆕 [{timestamp}] NEW DATA DETECTED!")
                        print(f"   📈 Count changed: {self.last_count} → {current_count} (+{new_notes})")
                        
                        # Show the latest notes
                        latest_notes = self.get_latest_notes(new_notes)
                        for i, note in enumerate(latest_notes):
                            print(f"\n   📝 New Note #{i+1}:")
                            print(f"      ID: {note['id']}")
                            print(f"      Title: {note['title']}")
                            print(f"      Content: {note['content'][:80]}{'...' if len(note['content']) > 80 else ''}")
                            print(f"      Tags: {note.get('tags', [])}")
                            print(f"      Created: {note.get('created_at', 'Unknown')}")
                    
                    elif current_count < self.last_count:
                        deleted_notes = self.last_count - current_count
                        print(f"\n🗑️  [{timestamp}] DATA DELETED!")
                        print(f"   📉 Count changed: {self.last_count} → {current_count} (-{deleted_notes})")
                    
                    self.last_count = current_count
                
                time.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
            self.monitoring = False

    def test_data_creation(self):
        """Test creating data via API to see monitoring in action"""
        print("\n🧪 Testing Data Creation (to demonstrate monitoring)...")
        
        test_data = [
            {
                "title": "Monitor Test 1",
                "content": "This note is created to test the MongoDB monitor",
                "tags": ["monitor", "test"]
            },
            {
                "title": "Monitor Test 2", 
                "content": "Another test note to see real-time monitoring",
                "tags": ["monitor", "demo"]
            }
        ]
        
        for i, note_data in enumerate(test_data, 1):
            print(f"   Creating test note {i}...")
            try:
                response = requests.post(
                    "http://127.0.0.1:5002/api/notes",
                    json=note_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 201:
                    print(f"   ✅ Test note {i} created successfully")
                else:
                    print(f"   ❌ Failed to create test note {i}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error creating test note {i}: {e}")
            
            time.sleep(3)  # Wait 3 seconds between creations
    
    def show_api_monitoring_commands(self):
        """Show commands for monitoring API requests"""
        print("\n📡 API Request Monitoring Commands:")
        print("=" * 50)
        
        commands = [
            {
                "name": "Create a test note",
                "command": """curl -X POST http://127.0.0.1:5002/api/notes \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Live Test", "content": "Testing live monitoring", "tags": ["live", "test"]}'"""
            },
            {
                "name": "Generate AI note",
                "command": """curl -X POST http://127.0.0.1:5002/api/notes/generate-and-save \\
  -H "Content-Type: application/json" \\
  -d '{"text": "I need to buy groceries tomorrow morning", "language": "english"}'"""
            },
            {
                "name": "Get all current notes",
                "command": "curl -X GET http://127.0.0.1:5002/api/notes"
            },
            {
                "name": "Check database health",
                "command": "curl -X GET http://127.0.0.1:5002/health"
            }
        ]
        
        for cmd_info in commands:
            print(f"\n🔸 {cmd_info['name']}:")
            print(f"   {cmd_info['command']}")

def main():
    print("🔍 MongoDB Atlas Real-time Data Monitor")
    print("=" * 60)
    
    monitor = MongoDBDataMonitor()
    
    print("\nChoose monitoring option:")
    print("1. Real-time data monitoring (watch for changes)")
    print("2. Test data creation (create test notes)")
    print("3. Show API monitoring commands")
    print("4. Current database status")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            monitor.monitor_data_changes()
            
        elif choice == "2":
            monitor.test_data_creation()
            
        elif choice == "3":
            monitor.show_api_monitoring_commands()
            
        elif choice == "4":
            print("\n📊 Current Database Status:")
            count = monitor.get_current_data_count()
            print(f"   Total Notes: {count}")
            
            if count > 0:
                latest = monitor.get_latest_notes(5)
                print(f"\n📝 Latest {len(latest)} Notes:")
                for i, note in enumerate(latest, 1):
                    print(f"   {i}. {note['title']} (ID: {note['id'][:8]}...)")
                    
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

if __name__ == "__main__":
    main()