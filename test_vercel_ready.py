#!/usr/bin/env python3
"""
Quick test to verify the app is ready for Vercel deployment
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from src.main_flask import app
        print("✓ Flask app imported successfully")
        
        from src.db_config import init_supabase_if_needed, DB_READY
        print("✓ DB config imported successfully")
        
        from src.models.note_supabase import Note
        print("✓ Note model imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env():
    """Test environment variable handling"""
    print("\nTesting environment variables...")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    print(f"SUPABASE_URL: {'SET' if url else 'NOT SET'}")
    print(f"SUPABASE_KEY: {'SET' if key else 'NOT SET'}")
    
    if url and key:
        print("✓ Environment variables configured")
        return True
    else:
        print("⚠ Environment variables not configured (OK for initial deploy)")
        return None  # Not a failure, just a warning

def test_app_creation():
    """Test that the Flask app can be created"""
    print("\nTesting Flask app creation...")
    try:
        from src.main_flask import app
        
        # Test that routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"✓ App created with {len(routes)} routes")
        
        # Check for critical routes
        critical_routes = ['/api/notes', '/api/health']
        for route in critical_routes:
            if route in routes:
                print(f"  ✓ {route} registered")
            else:
                print(f"  ✗ {route} NOT registered")
                return False
        
        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_helper():
    """Test the async helper function"""
    print("\nTesting async helper...")
    try:
        from src.main_flask import _run_async
        import asyncio
        
        async def dummy():
            return "success"
        
        result = _run_async(dummy())
        if result == "success":
            print("✓ Async helper working")
            return True
        else:
            print(f"✗ Async helper returned unexpected result: {result}")
            return False
    except Exception as e:
        print(f"✗ Async helper failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Vercel Readiness Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Environment", test_env()))
    results.append(("App Creation", test_app_creation()))
    results.append(("Async Helper", test_async_helper()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for test_name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is None:
            status = "⚠ WARNING"
        else:
            status = "✗ FAIL"
        print(f"{test_name:20s} {status}")
    
    # Check if any critical tests failed
    failures = [name for name, result in results if result is False]
    
    print("\n" + "=" * 60)
    if failures:
        print(f"✗ {len(failures)} test(s) failed: {', '.join(failures)}")
        print("Please fix these issues before deploying to Vercel")
        return 1
    else:
        print("✓ All critical tests passed!")
        print("The app is ready for Vercel deployment")
        return 0

if __name__ == "__main__":
    sys.exit(main())
