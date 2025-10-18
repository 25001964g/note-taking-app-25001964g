"""
Vercel Python entrypoint

This file exposes the Flask WSGI app for Vercel by importing it from src/main_flask.py
"""
import sys
import os

# Ensure the parent directory is in the path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app - Vercel looks for a module-level `app`
from src.main_flask import app

# For Vercel serverless functions, we need to ensure the app is properly configured
# The app object is automatically used by Vercel's Python runtime
