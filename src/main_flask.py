import os
import sys
import json
from dotenv import load_dotenv

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from src.db_config import supabase
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

@app.route('/api/notes', methods=['GET'])
async def get_notes():
    try:
        notes = await Note.get_all()
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        print(f"Error in get_notes: {str(e)}")
        return jsonify({"error": "Failed to retrieve notes"}), 500

@app.route('/api/notes', methods=['POST'])
async def create_note():
    try:
        data = request.json
        note = await Note.create(title=data['title'], content=data['content'])
        result = note.to_dict()
        print(f"Created note: {result}")  # Debug logging
        return jsonify(result), 201
    except Exception as e:
        print(f"Error in create_note: {str(e)}")
        return jsonify({"error": "Failed to create note"}), 500

@app.route('/api/notes/<note_id>', methods=['GET'])
async def get_note(note_id):
    try:
        note = await Note.get_by_id(note_id)
        if note is None:
            return jsonify({"error": "Note not found"}), 404
        return jsonify(note.to_dict())
    except Exception as e:
        print(f"Error in get_note: {str(e)}")
        return jsonify({"error": "Failed to retrieve note"}), 500

@app.route('/api/notes/<note_id>', methods=['PUT'])
async def update_note(note_id):
    note = await Note.get_by_id(note_id)
    if note is None:
        return jsonify({"error": "Note not found"}), 404
    
    data = request.json
    updated_note = await note.update(title=data.get('title'), content=data.get('content'))
    return jsonify(updated_note.to_dict())

@app.route('/api/notes/<note_id>', methods=['DELETE'])
async def delete_note(note_id):
    note = await Note.get_by_id(note_id)
    if note is None:
        return jsonify({"error": "Note not found"}), 404
    
    await note.delete()
    return jsonify({"message": "Note deleted successfully"})

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