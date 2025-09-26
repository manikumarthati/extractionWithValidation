#!/usr/bin/env python3
"""
Test Claude environment variable loading
"""

import os
from dotenv import load_dotenv

def test_env_loading():
    """Test that environment variables are loaded correctly"""
    print("Testing Environment Variable Loading")
    print("=" * 50)

    # Load .env file
    load_dotenv()

    # Check for required environment variables
    openai_key = os.environ.get('OPENAI_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

    print(f"OPENAI_API_KEY:")
    print(f"  Present: {bool(openai_key)}")
    if openai_key:
        print(f"  Starts with: {openai_key[:10]}...")
        print(f"  Length: {len(openai_key)}")

    print(f"\nANTHROPIC_API_KEY:")
    print(f"  Present: {bool(anthropic_key)}")
    if anthropic_key:
        print(f"  Starts with: {anthropic_key[:10]}...")
        print(f"  Length: {len(anthropic_key)}")

    return bool(openai_key), bool(anthropic_key)

def test_claude_client_init():
    """Test Claude client initialization"""
    print("\n\nTesting Claude Client Initialization")
    print("=" * 50)

    try:
        from claude_client import ClaudeClient

        # Try to initialize Claude client
        client = ClaudeClient()
        print("✓ Claude client initialized successfully")
        print(f"  Model: {client.default_model}")
        return True

    except Exception as e:
        print(f"✗ Claude client initialization failed: {e}")
        return False

def test_model_client_manager():
    """Test model client manager initialization"""
    print("\n\nTesting Model Client Manager")
    print("=" * 50)

    try:
        from services.model_client_manager import ModelClientManager

        # Initialize with Claude config
        manager = ModelClientManager(config_name='claude')
        print("✓ ModelClientManager initialized")

        # Test Claude client initialization
        manager._ensure_claude_client()

        if manager.claude_client:
            print("✓ Claude client successfully initialized in manager")
            return True
        else:
            print("✗ Claude client failed to initialize in manager")
            return False

    except Exception as e:
        print(f"✗ ModelClientManager test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Claude Environment & Initialization Test")
    print("=" * 60)

    # Test environment loading
    has_openai, has_anthropic = test_env_loading()

    # Test Claude client
    claude_works = False
    if has_anthropic:
        claude_works = test_claude_client_init()

    # Test model client manager
    manager_works = False
    if has_anthropic:
        manager_works = test_model_client_manager()

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  OpenAI Key: {'✓' if has_openai else '✗'}")
    print(f"  Anthropic Key: {'✓' if has_anthropic else '✗'}")
    print(f"  Claude Client: {'✓' if claude_works else '✗'}")
    print(f"  Model Manager: {'✓' if manager_works else '✗'}")

    if has_anthropic and claude_works and manager_works:
        print("\n🎉 All tests passed! Claude should work in the pipeline.")
    elif not has_anthropic:
        print("\n❌ ANTHROPIC_API_KEY not found - check .env file")
    else:
        print("\n❌ Claude initialization failed - check logs above")

if __name__ == "__main__":
    main()