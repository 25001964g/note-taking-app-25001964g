import sys
import os
import traceback
from typing import Callable

# Add parent directory to path so `src` becomes importable
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
	sys.path.insert(0, project_root)

def _make_error_app(exc: BaseException) -> Callable:
	"""Return a tiny WSGI app that exposes import errors clearly in Vercel logs/response."""
	error_text = f"Startup error: {exc}\n\nTraceback:\n{traceback.format_exc()}"
	def wsgi_app(environ, start_response):
		start_response('500 Internal Server Error', [('Content-Type', 'text/plain; charset=utf-8')])
		return [error_text.encode('utf-8')]
	# Also print to stdout so it shows in Function Logs
	print(error_text)
	return wsgi_app

try:
	from src.main_flask import app  # module-level WSGI app expected by Vercel
except Exception as e:
	# Construct a fallback WSGI app that returns diagnostics instead of opaque 500
	app = _make_error_app(e)
