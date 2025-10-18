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


# ------------------ Date/Time Inference Helpers (no external deps) ------------------
from datetime import datetime, timedelta
import re

WEEKDAYS = {
    'monday': 0, 'mon': 0,
    'tuesday': 1, 'tue': 1, 'tues': 1,
    'wednesday': 2, 'wed': 2,
    'thursday': 3, 'thu': 3, 'thurs': 3,
    'friday': 4, 'fri': 4,
    'saturday': 5, 'sat': 5,
    'sunday': 6, 'sun': 6,
}

MONTHS = {
    'january': 1, 'jan': 1,
    'february': 2, 'feb': 2,
    'march': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'may': 5,
    'june': 6, 'jun': 6,
    'july': 7, 'jul': 7,
    'august': 8, 'aug': 8,
    'september': 9, 'sep': 9, 'sept': 9,
    'october': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'december': 12, 'dec': 12,
}

def _next_weekday(target_weekday: int, ref: datetime) -> datetime:
    days_ahead = (target_weekday - ref.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return ref + timedelta(days=days_ahead)

def _this_or_next_weekday(target_weekday: int, ref: datetime, force_next: bool) -> datetime:
    if force_next:
        return _next_weekday(target_weekday, ref)
    # upcoming occurrence including today
    days_ahead = (target_weekday - ref.weekday()) % 7
    return ref + timedelta(days=days_ahead)

def infer_time(text: str) -> str or None:
    s = (text or '').lower()
    # Prefer explicit 24-hour times like 18:00 or 09:30 first
    m0 = re.search(r'(?:\bat\s*)?\b([01]?\d|2[0-3]):([0-5]\d)\b', s)
    if m0:
        h = int(m0.group(1)); mi = int(m0.group(2))
        return f"{h:02d}:{mi:02d}"
    # hh:mm[:ss] with optional am/pm (fallback)
    m = re.search(r'(?:at\s*)?(\d{1,2})(?::(\d{2}))?(?::(\d{2}))?\s*(am|pm)\b', s)
    if m:
        h = int(m.group(1)); mi = int(m.group(2) or 0)
        ampm = m.group(4)
        if ampm == 'pm' and h != 12:
            h += 12
        if ampm == 'am' and h == 12:
            h = 0
        h = max(0, min(23, h)); mi = max(0, min(59, mi))
        return f"{h:02d}:{mi:02d}"
    # 5pm / 1130am compact
    m2 = re.search(r'\b(\d{1,2})(\d{2})?\s*(am|pm)\b', s)
    if m2:
        h = int(m2.group(1)); mi = int(m2.group(2) or 0)
        ampm = m2.group(3)
        if ampm == 'pm' and h != 12:
            h += 12
        if ampm == 'am' and h == 12:
            h = 0
        return f"{h:02d}:{mi:02d}"
    # Named periods
    if any(w in s for w in ['noon', 'midday']):
        return '12:00'
    if 'midnight' in s:
        return '00:00'
    if 'morning' in s:
        return '09:00'
    if 'afternoon' in s:
        return '15:00'
    if 'evening' in s:
        return '19:00'
    if 'night' in s:
        return '21:00'
    return None

def _parse_numeric_date(token: str) -> datetime or None:
    token = token.replace('.', '/').replace('-', '/').strip()
    parts = token.split('/')
    try:
        if len(parts) == 3:
            a, b, c = parts
            if len(a) == 4:  # YYYY/MM/DD
                return datetime(int(a), int(b), int(c))
            d1, m1, y1 = int(a), int(b), int(c)
            if 1 <= d1 <= 31 and 1 <= m1 <= 12 and len(c) == 4:
                if d1 > 12:
                    return datetime(y1, m1, d1)
                if m1 > 12:
                    return datetime(y1, d1, m1)
                return datetime(y1, m1, d1)
    except Exception:
        return None
    return None

def infer_date(text: str, now: datetime = None) -> str or None:
    if not text:
        return None
    now = now or datetime.now()
    s = text.lower()
    # Relative
    if any(k in s for k in ['tomorrow', 'tmr', 'tmrw']):
        return (now + timedelta(days=1)).date().isoformat()
    if 'today' in s:
        return now.date().isoformat()
    # Weekdays
    m = re.search(r'\b(next|this)?\s*(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thurs|fri|sat|sun)\b', s)
    if m:
        modifier = (m.group(1) or '').strip()
        wd = WEEKDAYS[m.group(2)]
        dt = _this_or_next_weekday(wd, now, force_next=(modifier == 'next'))
        return dt.date().isoformat()
    # Month name forms
    m2 = re.search(r'\b(\d{1,2})\s+(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s*(\d{4})?\b', s)
    if m2:
        day = int(m2.group(1)); month = MONTHS[m2.group(2)]; year = int(m2.group(3) or now.year)
        try:
            return datetime(year, month, day).date().isoformat()
        except Exception:
            pass
    m3 = re.search(r'\b(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+(\d{1,2})(?:,\s*(\d{4}))?\b', s)
    if m3:
        month = MONTHS[m3.group(1)]; day = int(m3.group(2)); year = int(m3.group(3) or now.year)
        try:
            return datetime(year, month, day).date().isoformat()
        except Exception:
            pass
    # Numeric
    for tok in re.findall(r'\b\d{1,4}[\-/\.]\d{1,2}[\-/\.]\d{1,4}\b', s):
        dt = _parse_numeric_date(tok)
        if dt:
            return dt.date().isoformat()
    return None

def infer_event_datetime(*texts: str) -> tuple:
    merged = ' \n '.join(t for t in texts if t)
    return infer_date(merged), infer_time(merged)


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

@app.route('/api/notes/infer-datetime-preview', methods=['POST'])
def infer_datetime_preview():
    """Infer event_date and event_time from provided text/content without DB access."""
    try:
        data = request.json or {}
        text = data.get('text', '') or ''
        content = data.get('content', '') or ''
        event_date, event_time = infer_event_datetime(text, content)
        return jsonify({
            'input_text': text,
            'input_content': content,
            'inferred_event_date': event_date,
            'inferred_event_time': event_time
        })
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
        from datetime import datetime
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
        
        # Infer event date/time using both the raw text and LLM content
        content = structured_note.get('content', '') or ''
        event_date, event_time = infer_event_datetime(text, content)
        print(f"Inferred event_date: {event_date}, event_time: {event_time}")

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