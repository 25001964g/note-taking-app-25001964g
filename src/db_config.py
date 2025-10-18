import os
from typing import Optional
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables once at import time (safe for serverless)
load_dotenv()

_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None  # type: Optional[object]
DB_READY = False

def init_supabase_if_needed() -> bool:
    """Lazy-init Supabase client. Returns True if ready, False otherwise.
    Avoids raising at import time on serverless cold start.
    """
    global supabase, DB_READY
    if DB_READY and supabase is not None:
        return True
    if not _SUPABASE_URL or not _SUPABASE_KEY:
        if not _SUPABASE_URL:
            print("SUPABASE_URL is not set; database features are disabled")
        if not _SUPABASE_KEY:
            print("SUPABASE_KEY is not set; database features are disabled")
        DB_READY = False
        return False
    try:
        print(f"Initializing Supabase client with URL: {_SUPABASE_URL}")
        supabase = create_client(_SUPABASE_URL, _SUPABASE_KEY)
        # Do not run test queries at import/cold start to reduce latency/failures
        DB_READY = True
        return True
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        supabase = None
        DB_READY = False
        return False

# Try best-effort init (won't raise)
init_supabase_if_needed()