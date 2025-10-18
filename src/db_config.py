import os
from typing import Optional
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables (reads from .env if present)
load_dotenv()

supabase = None  # type: Optional[object]
DB_READY = False

def _read_env() -> tuple[str | None, str | None]:
    """Read env vars at call time to avoid stale values on cold start.
    Supports common aliases used in some deployments.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return url, key

def init_supabase_if_needed() -> bool:
    """Lazy-init Supabase client. Returns True if ready, False otherwise.
    Avoids raising at import time on serverless cold start and after env changes.
    """
    global supabase, DB_READY
    if DB_READY and supabase is not None:
        return True

    url, key = _read_env()
    if not url or not key:
        if not url:
            print("SUPABASE_URL is not set; database features are disabled")
        if not key:
            print("SUPABASE_KEY/ANON_KEY is not set; database features are disabled")
        DB_READY = False
        return False
    try:
        print(f"Initializing Supabase client with URL: {url}")
        supabase = create_client(url, key)
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