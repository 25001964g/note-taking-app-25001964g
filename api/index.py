"""
Vercel Python entrypoint (WSGI delegator)

We expose a WSGI callable named `app`. On first request, we lazily import
`src.main_flask.app`. If import fails (missing deps, path issues), we return
an HTML fallback page instead of a 500, and print the traceback to logs.
"""

import os
import sys
import traceback
from typing import Callable

THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)

_loaded_app = None  # type: ignore

def _load_real_app():
	global _loaded_app
	if _loaded_app is not None:
		return _loaded_app
	try:
		from src.main_flask import app as real_app  # type: ignore
		_loaded_app = real_app
	except Exception as e:
		print("[Vercel] Failed to import src.main_flask.app:", e)
		traceback.print_exc()
		_loaded_app = None
	return _loaded_app

def _fallback_response(start_response, status: str = '200 OK', body: str = ''):
	if not body:
		body = (
			"<!doctype html><html><body>"
			"<h1>NoteTaker</h1>"
			"<p>Application failed to start. See Vercel logs for details.</p>"
			"</body></html>"
		)
	start_response(status, [("Content-Type", "text/html; charset=utf-8")])
	return [body.encode("utf-8")]

def app(environ, start_response):  # WSGI callable expected by Vercel
	real = _load_real_app()
	if real is None:
		return _fallback_response(start_response, '200 OK')
	try:
		return real(environ, start_response)
	except Exception as e:
		print("[Vercel] Runtime error while handling request:", e)
		traceback.print_exc()
		return _fallback_response(start_response, '200 OK', f"<p>Error: {str(e)}</p>")
