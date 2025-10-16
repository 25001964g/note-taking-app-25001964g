import os
import sys
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

@app.route('/api/notes', methods=['GET'])
async def get_notes():
    notes = await Note.get_all()
    return jsonify([note.to_dict() for note in notes])

@app.route('/api/notes', methods=['POST'])
async def create_note():
    data = request.json
    note = await Note.create(title=data['title'], content=data['content'])
    return jsonify(note.to_dict()), 201

@app.route('/api/notes/<note_id>', methods=['GET'])
async def get_note(note_id):
    note = await Note.get_by_id(note_id)
    if note is None:
        return jsonify({"error": "Note not found"}), 404
    return jsonify(note.to_dict())

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
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)