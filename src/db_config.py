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

print(f"Initializing Supabase client with URL: {supabase_url}")
supabase = create_client(supabase_url, supabase_key)

# Test database connection
try:
    print("Testing database connection...")
    test = supabase.table('notes').select("*").limit(1).execute()
    print("Successfully connected to database")
except Exception as e:
    print(f"Failed to connect to database: {str(e)}")
    raise