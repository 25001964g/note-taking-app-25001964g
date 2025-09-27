"""
Main Flask Application with MongoDB Atlas Integration
Note-Taking App using MongoDB Atlas cloud database
"""
import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.routes.note_atlas import note_atlas_bp
from src.routes.user import user_bp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create Flask application
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes (Cross-Origin Resource Sharing)
CORS(app)

# Verify MongoDB Atlas connection from environment variables
mongodb_uri = os.getenv('MONGODB_URI')
github_token = os.getenv('GITHUB_TOKEN')

if not mongodb_uri:
    print("❌ ERROR: MONGODB_URI not found in environment variables")
    print("   Please check your .env file and ensure MONGODB_URI is set")
    sys.exit(1)

if not github_token:
    print("❌ WARNING: GITHUB_TOKEN not found in environment variables")
    print("   AI features may not work properly")

print("✅ Environment variables loaded successfully")
print(f"🔗 MongoDB Atlas URI configured: {mongodb_uri[:50]}...")
print(f"🤖 GitHub Token configured: {github_token[:20] if github_token else 'Not set'}...")

# Register blueprints with API prefix
app.register_blueprint(user_bp, url_prefix='/api')  # User routes (if needed)
app.register_blueprint(note_atlas_bp, url_prefix='/api')  # MongoDB Atlas note routes

# Static file serving routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serve static files and handle client-side routing
    Returns index.html for client-side routes, or specific static files
    """
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

# Application health check endpoint
@app.route('/health')
def health_check():
    """
    Application health check endpoint
    Verifies MongoDB Atlas connection and overall application status
    """
    try:
        # Import MongoDB model to test connection
        from src.models.mongo_atlas_note import MongoNote
        
        # Test MongoDB Atlas connection
        mongo_model = MongoNote()
        stats = mongo_model.get_database_stats()
        mongo_model.close_connection()
        
        return jsonify({
            'status': 'healthy',
            'application': 'Note-Taking App',
            'database': 'MongoDB Atlas',
            'connection': 'active',
            'total_notes': stats.get('total_notes', 0),
            'version': '2.0.0',
            'features': [
                'CRUD Operations',
                'AI Note Generation',
                'Note Translation',
                'Full-text Search',
                'MongoDB Atlas Cloud Storage'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'application': 'Note-Taking App',
            'database': 'MongoDB Atlas',
            'connection': 'failed',
            'error': str(e),
            'version': '2.0.0'
        }), 503

# API information endpoint
@app.route('/api/info')
def api_info():
    """
    API information endpoint
    Returns available API endpoints and their descriptions
    """
    return jsonify({
        'application': 'Note-Taking App API',
        'version': '2.0.0',
        'database': 'MongoDB Atlas',
        'endpoints': {
            'notes': {
                'GET /api/notes': 'Get all notes (supports ?q=search_term)',
                'POST /api/notes': 'Create a new note',
                'GET /api/notes/<id>': 'Get a specific note',
                'PUT /api/notes/<id>': 'Update a specific note',
                'DELETE /api/notes/<id>': 'Delete a specific note'
            },
            'search': {
                'GET /api/notes/search?q=<term>': 'Search notes by title, content, or tags'
            },
            'ai_features': {
                'POST /api/notes/generate': 'Generate note structure from text using AI',
                'POST /api/notes/generate-and-save': 'Generate and save note using AI',
                'POST /api/notes/<id>/translate': 'Translate note to target language'
            },
            'utilities': {
                'GET /api/notes/stats': 'Get database statistics',
                'GET /health': 'Application health check',
                'GET /api/info': 'This API information page'
            }
        },
        'note_structure': {
            'title': 'string (required)',
            'content': 'string (required)',
            'tags': 'array of strings (optional)',
            'event_date': 'string (YYYY-MM-DD, optional)',
            'event_time': 'string (HH:MM:SS, optional)',
            'created_at': 'datetime (auto-generated)',
            'updated_at': 'datetime (auto-updated)'
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(503)
def service_unavailable(error):
    """Handle 503 errors"""
    return jsonify({'error': 'Service temporarily unavailable'}), 503

# Application startup
if __name__ == '__main__':
    print("🚀 Starting Note-Taking Application with MongoDB Atlas...")
    print("=" * 60)
    print("🏠 Application: http://127.0.0.1:5002")
    print("🔍 Health Check: http://127.0.0.1:5002/health")
    print("📚 API Info: http://127.0.0.1:5002/api/info")
    print("=" * 60)
    print("\n📋 Available API Endpoints:")
    print("   GET    /api/notes - Get all notes")
    print("   POST   /api/notes - Create new note")
    print("   GET    /api/notes/<id> - Get specific note")
    print("   PUT    /api/notes/<id> - Update note")
    print("   DELETE /api/notes/<id> - Delete note")
    print("   GET    /api/notes/search?q=<term> - Search notes")
    print("   POST   /api/notes/generate - AI generate note (no save)")
    print("   POST   /api/notes/generate-and-save - AI generate and save")
    print("   POST   /api/notes/<id>/translate - Translate note")
    print("   GET    /api/notes/stats - Database statistics")
    print("\n🤖 AI Features:")
    print("   • Intelligent note generation from unstructured text")
    print("   • Multi-language support (English, Chinese, Japanese, etc.)")
    print("   • Automatic tag extraction and content structuring")
    print("   • Note translation to any language")
    print("\n☁️ Database: MongoDB Atlas Cloud")
    print("🔒 Features: CORS enabled, Error handling, Health monitoring")
    print("=" * 60)
    
    # Start the Flask development server
    app.run(host='0.0.0.0', port=5002, debug=True)