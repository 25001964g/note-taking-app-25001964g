"""
MongoDB Atlas Routes for Note-Taking Application
Handles all API endpoints for notes using MongoDB Atlas cloud database
"""
from flask import Blueprint, jsonify, request
from src.models.mongo_atlas_note import MongoNote
import json
import sys
import os

# Create Blueprint for MongoDB Atlas routes
note_atlas_bp = Blueprint('note_atlas', __name__)

# Initialize MongoDB Atlas connection
try:
    mongo_note_model = MongoNote()
    print("🚀 MongoDB Atlas routes initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize MongoDB Atlas routes: {e}")
    mongo_note_model = None

@note_atlas_bp.route('/notes', methods=['GET'])
def get_notes():
    """
    Get all notes from MongoDB Atlas, ordered by most recently updated
    Supports optional search query parameter 'q'
    """
    if not mongo_note_model:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Get optional search query parameter
        search_query = request.args.get('q', None)
        
        # Retrieve notes from MongoDB Atlas
        notes = mongo_note_model.get_all_notes(search_query=search_query)
        
        return jsonify(notes)
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve notes: {str(e)}'}), 500

@note_atlas_bp.route('/notes', methods=['POST'])
def create_note():
    """
    Create a new note in MongoDB Atlas
    Expects JSON payload with title, content, and optional fields
    """
    if not mongo_note_model:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        # Process tags - handle both list and comma-separated string formats
        tags = data.get('tags')
        if isinstance(tags, list):
            processed_tags = [t.strip() for t in tags if t is not None and str(t).strip()]
        elif isinstance(tags, str) and tags.strip():
            processed_tags = [t.strip() for t in tags.split(',') if t.strip()]
        else:
            processed_tags = []

        # Create note in MongoDB Atlas
        note = mongo_note_model.create_note(
            title=data['title'],
            content=data['content'],
            tags=processed_tags,
            event_date=data.get('event_date'),
            event_time=data.get('event_time')
        )
        
        return jsonify(note), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create note: {str(e)}'}), 500

@note_atlas_bp.route('/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    """
    Get a specific note by ID from MongoDB Atlas
    """
    if not mongo_note_model:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        note = mongo_note_model.get_note_by_id(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        return jsonify(note)
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve note: {str(e)}'}), 500

@note_atlas_bp.route('/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    """
    Update a specific note in MongoDB Atlas
    """
    if not mongo_note_model:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Process tags if provided
        tags = None
        if 'tags' in data:
            tags_data = data.get('tags')
            if isinstance(tags_data, list):
                tags = [t.strip() for t in tags_data if t is not None and str(t).strip()]
            elif isinstance(tags_data, str) and tags_data.strip():
                tags = [t.strip() for t in tags_data.split(',') if t.strip()]
            else:
                tags = []

        # Update note in MongoDB Atlas
        success = mongo_note_model.update_note(
            note_id=note_id,
            title=data.get('title'),
            content=data.get('content'),
            tags=tags,
            event_date=data.get('event_date'),
            event_time=data.get('event_time')
        )
        
        if success:
            # Return updated note
            updated_note = mongo_note_model.get_note_by_id(note_id)
            return jsonify(updated_note)
        else:
            return jsonify({'error': 'Note not found or no changes made'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Failed to update note: {str(e)}'}), 500

@note_atlas_bp.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """
    Delete a specific note from MongoDB Atlas
    """
    if not mongo_note_model:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        success = mongo_note_model.delete_note(note_id)
        if success:
            return '', 204  # No content response for successful deletion
        else:
            return jsonify({'error': 'Note not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to delete note: {str(e)}'}), 500

@note_atlas_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """
    Search notes by title, content, or tags in MongoDB Atlas
    """
    if not mongo_note_model:
        return jsonify({'error': 'Database connection failed'}), 500
    
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    try:
        notes = mongo_note_model.search_notes(query)
        return jsonify(notes)
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@note_atlas_bp.route('/notes/generate', methods=['POST'])
def generate_note():
    """
    Generate a structured note from user input using LLM (without saving)
    """
    try:
        # Import the extract_notes function from llm.py
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
        from llm import extract_notes
        
        data = request.json
        
        if not data or 'text' not in data:
            return jsonify({'error': 'text is required'}), 400
        
        text = data['text']
        language = data.get('language', 'English')
        
        if not text.strip():
            return jsonify({'error': 'text cannot be empty'}), 400
        
        print(f"🤖 Generating note from text: '{text}' in {language}")
        
        # Extract structured notes using LLM
        llm_response = extract_notes(text, lang=language)
        
        # Parse the JSON response from LLM
        try:
            structured_note = json.loads(llm_response)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                structured_note = json.loads(json_match.group())
            else:
                return jsonify({'error': 'Failed to parse LLM response'}), 500
        
        # Validate required fields
        if 'Title' not in structured_note or 'Notes' not in structured_note:
            return jsonify({'error': 'LLM response missing required fields'}), 500
        
        # Format the response
        response = {
            'title': structured_note.get('Title', ''),
            'content': structured_note.get('Notes', ''),
            'tags': structured_note.get('Tags', []),
            'original_text': text,
            'language': language
        }
        
        print(f"✅ Generated note: {response['title']}")
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate note: {str(e)}'}), 500

@note_atlas_bp.route('/notes/generate-and-save', methods=['POST'])
def generate_and_save_note():
    """
    Generate a structured note from user input using LLM and save to MongoDB Atlas
    """
    if not mongo_note_model:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Import the extract_notes function from llm.py
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
        from llm import extract_notes
        
        data = request.json
        
        if not data or 'text' not in data:
            return jsonify({'error': 'text is required'}), 400
        
        text = data['text']
        language = data.get('language', 'English')
        
        if not text.strip():
            return jsonify({'error': 'text cannot be empty'}), 400
        
        print(f"🤖 Generating and saving note from: '{text}' in {language}")
        
        # Extract structured notes using LLM
        llm_response = extract_notes(text, lang=language)
        
        # Parse the JSON response from LLM
        try:
            structured_note = json.loads(llm_response)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                structured_note = json.loads(json_match.group())
            else:
                return jsonify({'error': 'Failed to parse LLM response'}), 500
        
        # Validate required fields
        if 'Title' not in structured_note or 'Notes' not in structured_note:
            return jsonify({'error': 'LLM response missing required fields'}), 500
        
        # Prepare tags
        tags = structured_note.get('Tags', [])
        if not isinstance(tags, list):
            tags = []
        
        # Create and save the note to MongoDB Atlas
        note = mongo_note_model.create_note(
            title=structured_note.get('Title', ''),
            content=structured_note.get('Notes', ''),
            tags=tags,
            event_date=data.get('event_date'),
            event_time=data.get('event_time')
        )
        
        print(f"✅ Generated note saved to MongoDB Atlas: {note['title']}")
        
        return jsonify({
            'note': note,
            'original_text': text,
            'language': language,
            'message': 'Note generated and saved to MongoDB Atlas successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate and save note: {str(e)}'}), 500

@note_atlas_bp.route('/notes/<note_id>/translate', methods=['POST'])
def translate_note(note_id):
    """
    Translate a note to the target language using llm.py translate function
    """
    if not mongo_note_model:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Import the translate function from llm.py
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
        from llm import translate
        
        note = mongo_note_model.get_note_by_id(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        data = request.json
        
        if not data or 'target_language' not in data:
            return jsonify({'error': 'target_language is required'}), 400
        
        target_language = data['target_language']
        
        # Get current title and content from request or use note data
        current_title = data.get('title', note.get('title', ''))
        current_content = data.get('content', note.get('content', ''))
        
        # Translate both title and content if they exist
        translated_title = ''
        translated_content = ''
        
        if current_title.strip():
            translated_title = translate(current_title, target_language)
            print(f"🌐 Translated title to {target_language}")
            
        if current_content.strip():
            translated_content = translate(current_content, target_language)
            print(f"🌐 Translated content to {target_language}")
        
        return jsonify({
            'translated_title': translated_title,
            'translated_content': translated_content,
            'original_title': current_title,
            'original_content': current_content,
            'target_language': target_language
        })
        
    except Exception as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

@note_atlas_bp.route('/notes/stats', methods=['GET'])
def get_database_stats():
    """
    Get database statistics from MongoDB Atlas
    """
    if not mongo_note_model:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        stats = mongo_note_model.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

# Health check endpoint
@note_atlas_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify MongoDB Atlas connection
    """
    try:
        if mongo_note_model:
            # Test connection by getting database stats
            stats = mongo_note_model.get_database_stats()
            return jsonify({
                'status': 'healthy',
                'database': 'MongoDB Atlas',
                'total_notes': stats.get('total_notes', 0),
                'connection': 'active'
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'database': 'MongoDB Atlas',
                'connection': 'failed'
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'MongoDB Atlas',
            'error': str(e)
        }), 503