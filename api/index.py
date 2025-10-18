"""
Vercel Python entrypoint

This file exposes the Flask WSGI app for Vercel by importing it from src/main_flask.py
"""

from src.main_flask import app  # noqa: F401  (Vercel looks for a module-level `app`)
