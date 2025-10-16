import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL", "https://nasmrxzpyvatumbrypxf.supabase.co")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_key:
    raise ValueError("SUPABASE_KEY environment variable is not set")

supabase = create_client(supabase_url, supabase_key)