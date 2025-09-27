"""
MongoDB Atlas Note Model
Enhanced note-taking application using MongoDB Atlas cloud database

This module provides comprehensive MongoDB Atlas integration with:
- CRUD operations for notes
- Full-text search capabilities
- Database statistics and monitoring
- Connection management and error handling
"""

import os
from datetime import datetime
from pymongo import MongoClient, ASCENDING, TEXT
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoNote:
    """
    MongoDB Atlas Note Model
    
    Manages note storage and retrieval operations using MongoDB Atlas cloud database.
    Provides methods for creating, reading, updating, deleting, and searching notes.
    """
    
    def __init__(self):
        """
        Initialize MongoDB Atlas connection
        
        Connects to MongoDB Atlas using environment variables and creates
        necessary database indexes for optimal performance.
        """
        # Get MongoDB Atlas connection string from environment
        self.mongodb_uri = os.getenv('MONGODB_URI')
        
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable is required")
        
        try:
            print("🔗 Connecting to MongoDB Atlas...")
            
            # Create MongoDB Atlas client
            self.client = MongoClient(self.mongodb_uri)
            
            # Connect to database and collection
            self.db = self.client['notetaker']  # Database name
            self.collection = self.db['notes']  # Collection name
            
            # Test connection with ping
            self.client.admin.command('ping')
            
            # Create indexes for better search performance
            self._create_indexes()
            
            print("✅ Successfully connected to MongoDB Atlas!")
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB Atlas: {e}")
            raise
    
    def _create_indexes(self):
        """
        Create database indexes for optimal query performance
        
        Creates text indexes for search functionality and regular indexes
        for common query patterns.
        """
        try:
            # Create text index for full-text search
            self.collection.create_index([
                ("title", TEXT),
                ("content", TEXT),
                ("tags", TEXT)
            ])
            
            # Create regular indexes for common queries
            self.collection.create_index("created_at")
            self.collection.create_index("updated_at")
            self.collection.create_index("tags")
            
            print("📋 Database indexes created for optimal performance")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create database indexes: {e}")
    
    def create_note(self, note_data):
        """
        Create a new note in MongoDB Atlas
        
        Args:
            note_data (dict): Dictionary containing note data with keys:
                - title (str): Note title (required)
                - content (str): Note content (required)
                - tags (list): Optional list of tags
                - event_date (str): Optional event date
                - event_time (str): Optional event time
            
        Returns:
            str: Created note's MongoDB _id as string
        """
        try:
            # Prepare note document
            note = {
                'title': note_data.get('title'),
                'content': note_data.get('content'),
                'tags': note_data.get('tags', []),
                'event_date': note_data.get('event_date'),
                'event_time': note_data.get('event_time'),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert document into MongoDB Atlas
            result = self.collection.insert_one(note)
            
            print(f"✅ Note created successfully with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Failed to save note: {e}")
            raise
    
    def get_all_notes(self, search_query=None):
        """
        Retrieve all notes from MongoDB Atlas, optionally filtered by search query
        
        Args:
            search_query (str): Optional search string to filter notes
            
        Returns:
            list: List of notes sorted by update time (newest first)
        """
        try:
            # Build search filter if query provided
            if search_query:
                filter_query = {
                    '$or': [
                        {'title': {'$regex': search_query, '$options': 'i'}},
                        {'content': {'$regex': search_query, '$options': 'i'}},
                        {'tags': {'$regex': search_query, '$options': 'i'}}
                    ]
                }
            else:
                filter_query = {}
            
            # Query notes from MongoDB Atlas, sorted by update time
            notes = []
            cursor = self.collection.find(filter_query).sort("updated_at", -1)
            
            for note in cursor:
                # Convert MongoDB _id to string and format dates
                note['id'] = str(note['_id'])
                del note['_id']  # Remove the ObjectId for clean JSON response
                
                # Format datetime objects to strings
                if 'created_at' in note and note['created_at']:
                    note['created_at'] = note['created_at'].isoformat()
                if 'updated_at' in note and note['updated_at']:
                    note['updated_at'] = note['updated_at'].isoformat()
                
                notes.append(note)
            
            print(f"📖 Retrieved {len(notes)} notes from MongoDB Atlas")
            return notes
            
        except Exception as e:
            print(f"❌ Failed to retrieve notes: {e}")
            raise
    
    def get_note(self, note_id):
        """
        Retrieve a single note by ID from MongoDB Atlas
        
        Args:
            note_id (str): MongoDB ObjectId as string
            
        Returns:
            dict: Note document or None if not found
        """
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(note_id)
            
            # Find note in MongoDB Atlas
            note = self.collection.find_one({'_id': object_id})
            
            if note:
                # Convert MongoDB _id to string
                note['id'] = str(note['_id'])
                del note['_id']
                
                # Format datetime objects
                if 'created_at' in note and note['created_at']:
                    note['created_at'] = note['created_at'].isoformat()
                if 'updated_at' in note and note['updated_at']:
                    note['updated_at'] = note['updated_at'].isoformat()
                
                print(f"📖 Retrieved note: {note['title']}")
                return note
            else:
                print(f"❌ Note not found with ID: {note_id}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to retrieve note: {e}")
            raise
    
    def update_note(self, note_id, update_data):
        """
        Update an existing note in MongoDB Atlas
        
        Args:
            note_id (str): MongoDB ObjectId as string
            update_data (dict): Dictionary containing fields to update
            
        Returns:
            bool: True if note was updated successfully
        """
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(note_id)
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Update note in MongoDB Atlas
            result = self.collection.update_one(
                {'_id': object_id},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                print(f"✅ Note updated successfully: {note_id}")
                return True
            else:
                print(f"❌ No note found to update with ID: {note_id}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to update note: {e}")
            raise
    
    def delete_note(self, note_id):
        """
        Delete a note from MongoDB Atlas
        
        Args:
            note_id (str): MongoDB ObjectId as string
            
        Returns:
            bool: True if note was deleted successfully
        """
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(note_id)
            
            # Delete note from MongoDB Atlas
            result = self.collection.delete_one({'_id': object_id})
            
            if result.deleted_count > 0:
                print(f"✅ Note deleted successfully: {note_id}")
                return True
            else:
                print(f"❌ No note found to delete with ID: {note_id}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to delete note: {e}")
            raise
    
    def search_notes(self, search_term):
        """
        Search notes using full-text search
        
        Args:
            search_term (str): Search term to find in notes
            
        Returns:
            list: List of matching notes sorted by relevance
        """
        try:
            # Use MongoDB text search
            results = []
            cursor = self.collection.find(
                {'$text': {'$search': search_term}},
                {'score': {'$meta': 'textScore'}}
            ).sort([('score', {'$meta': 'textScore'})])
            
            for note in cursor:
                # Convert MongoDB _id to string
                note['id'] = str(note['_id'])
                del note['_id']
                
                # Format datetime objects
                if 'created_at' in note:
                    note['created_at'] = note['created_at'].isoformat()
                if 'updated_at' in note:
                    note['updated_at'] = note['updated_at'].isoformat()
                
                results.append(note)
            
            print(f"🔍 Found {len(results)} notes matching '{search_term}'")
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            # Fallback to regex search if text search fails
            return self.get_all_notes(search_term)
    
    def get_database_stats(self):
        """
        Get database statistics and information
        
        Returns:
            dict: Database statistics including note count and database info
        """
        try:
            # Get collection statistics
            total_notes = self.collection.count_documents({})
            
            # Get database information
            db_stats = self.db.command("dbstats")
            
            print(f"📊 Database stats: {total_notes} total notes")
            
            return {
                'total_notes': total_notes,
                'database_name': self.db.name,
                'collection_name': self.collection.name,
                'storage_size': db_stats.get('storageSize', 0),
                'data_size': db_stats.get('dataSize', 0),
                'index_count': db_stats.get('indexes', 0)
            }
            
        except Exception as e:
            print(f"❌ Failed to get database stats: {e}")
            return {
                'total_notes': 0,
                'database_name': self.db.name,
                'error': str(e)
            }
    
    def close_connection(self):
        """
        Close MongoDB Atlas connection
        
        Should be called when done with database operations to free resources.
        """
        try:
            if hasattr(self, 'client'):
                self.client.close()
                print("🔌 MongoDB Atlas connection closed")
        except Exception as e:
            print(f"⚠️ Warning: Could not close connection properly: {e}")