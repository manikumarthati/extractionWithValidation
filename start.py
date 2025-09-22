#!/usr/bin/env python3
"""
Startup script for PDF Processing System
Includes pre-flight checks and helpful messages
"""
import os
import sys
from pathlib import Path

def check_environment():
    """Check if environment is properly set up"""
    print("PDF Processing System Startup")
    print("=" * 40)
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("[ERROR] .env file not found")
        print("   Please copy .env.example to .env and configure your OpenAI API key")
        return False
    
    # Check OpenAI API key
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        print("[ERROR] OpenAI API key not configured")
        print("   Please set OPENAI_API_KEY in your .env file")
        return False
    
    print("[OK] Environment configuration OK")
    
    # Check directories
    upload_dir = Path("uploads")
    results_dir = Path("results")
    templates_dir = Path("templates")
    
    if not upload_dir.exists():
        upload_dir.mkdir(exist_ok=True)
        print("[OK] Created uploads directory")
    
    if not results_dir.exists():
        results_dir.mkdir(exist_ok=True)
        print("[OK] Created results directory")
    
    if not templates_dir.exists():
        print("[ERROR] Templates directory missing")
        return False
    
    print("[OK] Directory structure OK")
    
    return True

def main():
    """Main startup function"""
    if not check_environment():
        print("\n[ERROR] Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    print("\n[OK] All checks passed!")
    print("\nStarting Flask development server...")
    print("   Access the application at: http://localhost:5000")
    print("   Press Ctrl+C to stop the server")
    print("=" * 40)
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()