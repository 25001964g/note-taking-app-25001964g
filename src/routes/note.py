from flask import Blueprint, jsonify, request
from src.models.note import Note, db

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    notes = Note.query.order_by(Note.updated_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        # accept optional fields: tags (list or comma string), event_date (YYYY-MM-DD), event_time (HH:MM:SS)
        tags = data.get('tags')
        if isinstance(tags, list):
            tags_str = ','.join([t.strip() for t in tags if t is not None])
        else:
            tags_str = tags.strip() if isinstance(tags, str) and tags.strip() != '' else None

        note = Note(
            title=data['title'],
            content=data['content'],
            tags=tags_str,
            event_date=data.get('event_date'),
            event_time=data.get('event_time')
        )
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        # Update optional fields
        if 'tags' in data:
            tags = data.get('tags')
            if isinstance(tags, list):
                note.tags = ','.join([t.strip() for t in tags if t is not None])
            else:
                note.tags = tags.strip() if isinstance(tags, str) and tags.strip() != '' else None

        if 'event_date' in data:
            note.event_date = data.get('event_date')

        if 'event_time' in data:
            note.event_time = data.get('event_time')
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    notes = Note.query.filter(
        (Note.title.contains(query)) | (Note.content.contains(query))
    ).order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])


@note_bp.route('/notes/generate', methods=['POST'])
def generate_note():
    """Generate a structured note from user input using LLM"""
    try:
        # Import the extract_notes function from llm.py
        import sys
        import os
        import json
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
        from llm import extract_notes
        
        data = request.json
        
        if not data or 'text' not in data:
            return jsonify({'error': 'text is required'}), 400
        
        text = data['text']
        language = data.get('language', 'English')
        
        if not text.strip():
            return jsonify({'error': 'text cannot be empty'}), 400
        
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
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/generate-and-save', methods=['POST'])
def generate_and_save_note():
    """Generate a structured note from user input using LLM and save it to database"""
    try:
        # Import the extract_notes function from llm.py
        import sys
        import os
        import json
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
        from llm import extract_notes
        
        data = request.json
        
        if not data or 'text' not in data:
            return jsonify({'error': 'text is required'}), 400
        
        text = data['text']
        language = data.get('language', 'English')
        
        if not text.strip():
            return jsonify({'error': 'text cannot be empty'}), 400
        
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
        tags_str = ','.join([t.strip() for t in tags if t is not None]) if tags else None
        
        # Create and save the note
        note = Note(
            title=structured_note.get('Title', ''),
            content=structured_note.get('Notes', ''),
            tags=tags_str,
            event_date=data.get('event_date'),
            event_time=data.get('event_time')
        )
        
        db.session.add(note)
        db.session.commit()
        
        return jsonify({
            'note': note.to_dict(),
            'original_text': text,
            'language': language
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/<int:note_id>/translate', methods=['POST'])
def translate_note(note_id):
    """Translate a note to the target language using llm.py translate function"""
    try:
        # Import the translate function from llm.py
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
        from llm import translate
        
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data or 'target_language' not in data:
            return jsonify({'error': 'target_language is required'}), 400
        
        target_language = data['target_language']
        
        # Get current title and content from request or use note data
        current_title = data.get('title', note.title or '')
        current_content = data.get('content', note.content or '')
        
        # Translate both title and content if they exist
        translated_title = ''
        translated_content = ''
        
        if current_title.strip():
            translated_title = translate(current_title, target_language)
            
        if current_content.strip():
            translated_content = translate(current_content, target_language)
        
        return jsonify({
            'translated_title': translated_title,
            'translated_content': translated_content,
            'original_title': current_title,
            'original_content': current_content,
            'target_language': target_language
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
