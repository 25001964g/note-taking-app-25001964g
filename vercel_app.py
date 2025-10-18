"""
Alternative Vercel entrypoint at project root
This can be used if api/index.py has path issues
"""
from api.index import app

# Vercel will use this app object
__all__ = ['app']
