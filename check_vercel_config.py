#!/usr/bin/env python3
"""
Pre-deployment check script
Verifies that the Vercel configuration is correct before deploying
"""
import json
import os
import sys

def check_vercel_json():
    """Check if vercel.json uses the new configuration format"""
    print("Checking vercel.json configuration...")
    
    if not os.path.exists('vercel.json'):
        print("❌ vercel.json not found")
        return False
    
    with open('vercel.json', 'r') as f:
        config = json.load(f)
    
    # Check for old configuration
    if 'builds' in config:
        print("❌ Old 'builds' configuration found")
        print("   Please remove 'builds' and use 'rewrites' instead")
        return False
    
    if 'routes' in config:
        print("❌ Old 'routes' configuration found")
        print("   Please use 'rewrites' instead of 'routes'")
        return False
    
    # Check for new configuration
    if 'rewrites' not in config:
        print("⚠️  No 'rewrites' configuration found")
        print("   This might be intentional, but typically you need rewrites for routing")
    
    # Validate rewrites structure
    if 'rewrites' in config:
        rewrites = config['rewrites']
        if not isinstance(rewrites, list):
            print("❌ 'rewrites' should be a list")
            return False
        
        required_keys = ['source', 'destination']
        for i, rewrite in enumerate(rewrites):
            for key in required_keys:
                if key not in rewrite:
                    print(f"❌ Rewrite #{i+1} missing required key: {key}")
                    return False
        
        print(f"✅ vercel.json is using new configuration format")
        print(f"   Found {len(rewrites)} rewrite rule(s)")
        return True
    
    return True

def check_api_structure():
    """Check if API structure is correct"""
    print("\nChecking API structure...")
    
    if not os.path.exists('api'):
        print("❌ 'api' directory not found")
        return False
    
    if not os.path.exists('api/index.py'):
        print("❌ 'api/index.py' not found")
        return False
    
    print("✅ API structure is correct")
    return True

def check_requirements():
    """Check if requirements.txt exists"""
    print("\nChecking requirements.txt...")
    
    if not os.path.exists('requirements.txt'):
        print("⚠️  requirements.txt not found")
        print("   Vercel needs this file to install dependencies")
        return False
    
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
        if 'Flask' not in requirements:
            print("⚠️  Flask not found in requirements.txt")
    
    print("✅ requirements.txt exists")
    return True

def check_env_template():
    """Check if there's guidance for environment variables"""
    print("\nChecking environment variable documentation...")
    
    docs_exist = (
        os.path.exists('VERCEL_DEPLOY_GUIDE.md') or
        os.path.exists('DEPLOY_CHECKLIST.md')
    )
    
    if docs_exist:
        print("✅ Deployment documentation found")
    else:
        print("⚠️  No deployment documentation found")
        print("   Consider creating a guide for setting environment variables")
    
    return True

def main():
    print("=" * 60)
    print("Vercel Configuration Pre-Deployment Check")
    print("=" * 60)
    print()
    
    checks = [
        ("Vercel Configuration", check_vercel_json),
        ("API Structure", check_api_structure),
        ("Requirements File", check_requirements),
        ("Documentation", check_env_template),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error checking {name}: {e}")
            results.append((name, False))
        print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = all(result for _, result in results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10s} {name}")
    
    print()
    if all_passed:
        print("✅ All checks passed! Ready to deploy to Vercel")
        print()
        print("Next steps:")
        print("1. Commit your changes: git add . && git commit -m 'Update Vercel config'")
        print("2. Push to deploy: git push origin main")
        print("3. Check deployment status on Vercel Dashboard")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())
