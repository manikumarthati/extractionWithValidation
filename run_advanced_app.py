#!/usr/bin/env python3
"""
Launch script for the Advanced PDF Extraction Pipeline
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import streamlit
        import plotly
        import cv2
        import PIL
        import numpy
        import openai
        import fitz
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements: pip install -r requirements_advanced.txt")
        return False

def check_api_key():
    """Check if OpenAI API key is configured"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("Or add it to your .env file")
        return False
    else:
        print("✅ OpenAI API key configured")
        return True

def create_directories():
    """Create necessary directories"""
    dirs = ['uploads', 'results', 'temp']
    for directory in dirs:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")

def main():
    """Main launch function"""
    print("🚀 Advanced PDF Extraction Pipeline")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    # Check API key
    if not check_api_key():
        sys.exit(1)

    # Create directories
    create_directories()

    print("\n🌟 Starting Streamlit application...")
    print("📱 The app will open in your default browser")
    print("🔗 URL: http://localhost:8501")
    print("\n⚠️  Press Ctrl+C to stop the application")
    print("=" * 50)

    try:
        # Launch Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "advanced_streamlit_app.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error running application: {e}")

if __name__ == "__main__":
    main()