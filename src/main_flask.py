import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from src.db_config import DB_READY, init_supabase_if_needed
from src.models.note_supabase import Note

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Enable CORS for all routes
CORS(app)

# Configure JSON encoder for better datetime handling
app.json_encoder = json.JSONEncoder

# Add error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

def _run_async(coro):
    """Run an async coroutine in a safe event loop context for WSGI servers."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(new_loop)
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
                asyncio.set_event_loop(loop)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No current event loop
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)


@app.route('/api/notes', methods=['GET'])
def get_notes():
    try:
        if not init_supabase_if_needed():
            return jsonify({"error": "Database not configured. Set SUPABASE_URL and SUPABASE_KEY."}), 503
        notes = _run_async(Note.get_all())
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        print(f"Error in get_notes: {str(e)}")
        return jsonify({"error": "Failed to retrieve notes"}), 500

@app.route('/api/notes', methods=['POST'])
def create_note():
    try:
        print("Received create note request")
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.json
        print(f"Received note data: {data}")
        
        # Validate required fields: allow either title or content (match frontend UX)
        if not (data.get('title') or data.get('content')):
            return jsonify({"error": "Title or content is required"}), 400
        
        # Handle tags if present
        tags = data.get('tags', [])
        if isinstance(tags, list):
            tags = ','.join(str(tag).strip() for tag in tags if tag)
        
        try:
            if not init_supabase_if_needed():
                return jsonify({"error": "Database not configured. Set SUPABASE_URL and SUPABASE_KEY."}), 503
            print(f"Creating note with title: {data.get('title')} and content length: {len(data.get('content') or '')}")
            note = _run_async(Note.create(
                title=(data.get('title') or 'Untitled'),
                content=(data.get('content') or ''),
                tags=tags if tags else None,
                event_date=data.get('event_date'),
                event_time=data.get('event_time')
            ))
            
            result = note.to_dict()
            print(f"Successfully created note: {result}")
            return jsonify(result), 201
            
        except ValueError as ve:
            error_msg = str(ve)
            print(f"Validation error: {error_msg}")
            return jsonify({"error": error_msg}), 400
            
        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Failed to save note to database"}), 500
            
    except Exception as e:
        error_msg = f"Request processing error: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to process note creation request"}), 500

@app.route('/api/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    try:
        if not init_supabase_if_needed():
            return jsonify({"error": "Database not configured. Set SUPABASE_URL and SUPABASE_KEY."}), 503
        note = _run_async(Note.get_by_id(note_id))
        if note is None:
            return jsonify({"error": "Note not found"}), 404
        return jsonify(note.to_dict())
    except Exception as e:
        print(f"Error in get_note: {str(e)}")
        return jsonify({"error": "Failed to retrieve note"}), 500

@app.route('/api/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    if not init_supabase_if_needed():
        return jsonify({"error": "Database not configured. Set SUPABASE_URL and SUPABASE_KEY."}), 503
    note = _run_async(Note.get_by_id(note_id))
    if note is None:
        return jsonify({"error": "Note not found"}), 404
    
    data = request.json
    # Handle tags: convert list to comma-separated string if present
    tags = data.get('tags', [])
    if isinstance(tags, list):
        tags = ','.join(tags)
    
    # Also pass through date/time so the model can normalize them
    updated_note = _run_async(note.update(
        title=data.get('title'),
        content=data.get('content'),
        tags=tags,
        event_date=data.get('event_date'),
        event_time=data.get('event_time')
    ))
    return jsonify(updated_note.to_dict())

@app.route('/api/notes/normalize-preview', methods=['POST'])
def normalize_preview():
    """Return normalized date/time strings without touching the database (debug helper)."""
    try:
        data = request.json or {}
        d = data.get('event_date')
        t = data.get('event_time')
        normalized = {
            'input_event_date': d,
            'input_event_time': t,
            'normalized_event_date': Note.format_date_str(d),
            'normalized_event_time': Note.format_time_str(t)
        }
        return jsonify(normalized)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    if not init_supabase_if_needed():
        return jsonify({"error": "Database not configured. Set SUPABASE_URL and SUPABASE_KEY."}), 503
    note = _run_async(Note.get_by_id(note_id))
    if note is None:
        return jsonify({"error": "Note not found"}), 404
    
    _run_async(note.delete())
    return jsonify({"message": "Note deleted successfully"})

@app.route('/api/notes/generate-and-save', methods=['POST'])
def generate_and_save_note():
    """Generate a structured note from user input using LLM and save it"""
    try:
        print("Starting AI note generation")
        from src.llm import extract_notes
        from datetime import datetime, timedelta
        import re
        
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'text is required'}), 400
            
        text = data['text']
        language = data.get('language', 'English')
        
        print(f"Generating note for text: {text} in {language}")
        
        # Extract structured notes using LLM
        structured_note = extract_notes(text, lang=language)
        print(f"LLM response: {structured_note}")
        
        # Get content for parsing date/time
        content = structured_note.get('content', text)
        event_date = None
        event_time = None
        
        # Look for time patterns like "Xpm", "X:YY pm", "X:YY"
        time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(?:am|pm|AM|PM)?'
        time_matches = re.findall(time_pattern, content.lower())
        if time_matches:
            hour = int(time_matches[0][0])
            minute = int(time_matches[0][1]) if time_matches[0][1] else 0
            # If pm is mentioned and hour is less than 12, add 12 hours
            if 'pm' in content.lower() and hour < 12:
                hour += 12
            event_time = f"{hour:02d}:{minute:02d}"

        # Look for today/tomorrow/date patterns
        today = datetime.now()
        if 'tomorrow' in content.lower():
            tomorrow = today + timedelta(days=1)
            event_date = tomorrow.date().isoformat()  # Convert to YYYY-MM-DD string
            print(f"Setting tomorrow's date: {event_date}")
        elif 'today' in content.lower():
            event_date = today.date().isoformat()  # Convert to YYYY-MM-DD string
            print(f"Setting today's date: {event_date}")
        
        print(f"Extracted event_date: {event_date}, event_time: {event_time}")

        # Get tags from LLM response and convert to string
        tags = structured_note.get('tags', [])
        if isinstance(tags, list):
            tags = ','.join(tags)
            
        try:
            note = _run_async(Note.create(
                title=structured_note.get('title', 'AI Generated Note'),
                content=structured_note.get('content', text),
                tags=tags,
                event_date=event_date,
                event_time=event_time
            ))
            
            result = {
                'note': note.to_dict(),
                'original_text': text,
                'language': language,
                'event_date': event_date,
                'event_time': event_time
            }
            print(f"Generated note: {result}")
            return jsonify(result), 201
            
        except Exception as e:
            print(f"Error creating note: {str(e)}")
            raise
        
    except Exception as e:
        print(f"Error generating AI note: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<note_id>/translate', methods=['POST'])
async def translate_note(note_id):
    """Translate a note to the target language"""
    try:
        print(f"Starting translation for note {note_id}")
        from src.llm import translate
        
        note = await Note.get_by_id(note_id)
        if note is None:
            print(f"Note {note_id} not found")
            return jsonify({"error": "Note not found"}), 404

        data = request.json
        print(f"Received translation request data: {data}")
        
        if not data or 'target_language' not in data:
            print("Missing target_language in request")
            return jsonify({"error": "target_language is required"}), 400

        target_language = data['target_language']
        print(f"Translating to {target_language}")

        # Get current title, content and tags
        title = data.get('title', note.title) or ''
        content = data.get('content', note.content) or ''
        tags = data.get('tags', note.tags) or ''
        print(f"Original title: {title}")
        print(f"Original content: {content}")
        print(f"Original tags: {tags}")

        # Translate title, content and tags
        try:
            translated_title = translate(title, target_language) if title.strip() else ''
            print(f"Translated title: {translated_title}")
            
            translated_content = translate(content, target_language) if content.strip() else ''
            print(f"Translated content: {translated_content}")
            
            # Handle tags translation
            translated_tags = []
            if tags:
                # Convert string tags to list if needed
                tag_list = tags.split(',') if isinstance(tags, str) else tags
                
                # Translate each tag individually
                for tag in tag_list:
                    tag = tag.strip()
                    if tag:
                        try:
                            translated_tag = translate(tag, target_language)
                            # Clean up the translated tag (remove quotes if present)
                            translated_tag = translated_tag.strip().strip('"\'')
                            translated_tags.append(translated_tag)
                            print(f"Translated tag '{tag}' to '{translated_tag}'")
                        except Exception as e:
                            print(f"Error translating tag '{tag}': {e}")
                            # Keep original tag if translation fails
                            translated_tags.append(tag)
            
            print(f"All translated tags: {translated_tags}")

            response = {
                'translated_title': translated_title.strip() if translated_title else '',
                'translated_content': translated_content.strip() if translated_content else '',
                'translated_tags': translated_tags,  # Now it's an array
                'original_title': title,
                'original_content': content,
                'original_tags': tag_list if isinstance(tags, list) else (tags.split(',') if tags else []),
                'target_language': target_language
            }
            print(f"Sending response: {response}")
            return jsonify(response)
            
        except Exception as e:
            print(f"Translation failed: {str(e)}")
            raise

    except Exception as e:
        print(f"Translation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5002))
    app.run(host='0.0.0.0', port=port, debug=True)