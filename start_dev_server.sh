#!/bin/bash

# Note-Taking App with MongoDB Atlas - Development Server
# This script starts the Flask application with all dependencies configured

echo "🚀 Starting Note-Taking App with MongoDB Atlas..."
echo "=================================================="

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    echo "❌ ERROR: .env file not found!"
    echo "   Please create a .env file with your MongoDB Atlas credentials"
    echo "   Example:"
    echo "   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database"
    echo "   GITHUB_TOKEN=your_github_token_here"
    exit 1
fi

# Verify environment variables
echo "🔍 Checking environment variables..."
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
mongodb_uri = os.getenv('MONGODB_URI')
github_token = os.getenv('GITHUB_TOKEN')
if not mongodb_uri:
    print('❌ MONGODB_URI not found in .env file')
    exit(1)
if not github_token:
    print('⚠️  GITHUB_TOKEN not found in .env file (AI features may not work)')
print('✅ Environment variables configured')
"

if [[ $? -ne 0 ]]; then
    echo "❌ Environment configuration failed"
    exit 1
fi

# Test MongoDB connection
echo "🔗 Testing MongoDB Atlas connection..."
python -c "
from src.models.mongo_atlas_note import MongoNote
try:
    mongo_model = MongoNote()
    stats = mongo_model.get_database_stats()
    mongo_model.close_connection()
    print(f'✅ MongoDB Atlas connected - {stats.get(\"total_notes\", 0)} notes in database')
except Exception as e:
    print(f'❌ MongoDB connection failed: {str(e)}')
    exit(1)
"

if [[ $? -ne 0 ]]; then
    echo "❌ MongoDB Atlas connection failed"
    exit 1
fi

# Start the Flask application
echo "🌐 Starting Flask development server..."
echo "=================================================="
echo "🏠 Application URL: http://127.0.0.1:5002"
echo "🔍 Health Check: http://127.0.0.1:5002/health"
echo "📚 API Documentation: http://127.0.0.1:5002/api/info"
echo "=================================================="
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask application
python src/main_atlas.py