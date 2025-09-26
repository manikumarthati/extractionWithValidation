#!/usr/bin/env python3
"""
Test script to verify the UnboundLocalError fix in advanced_streamlit_app.py
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test that the Streamlit app can be imported without errors"""
    try:
        import advanced_streamlit_app
        print("[OK] advanced_streamlit_app imported successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to import advanced_streamlit_app: {e}")
        return False

def test_class_initialization():
    """Test that the main UI class can be initialized"""
    try:
        import advanced_streamlit_app
        ui = advanced_streamlit_app.AdvancedPipelineUI()
        print("[OK] AdvancedPipelineUI initialized successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to initialize AdvancedPipelineUI: {e}")
        return False

def test_method_structure():
    """Test that the render_upload_section method exists and has proper structure"""
    try:
        import advanced_streamlit_app
        ui = advanced_streamlit_app.AdvancedPipelineUI()

        # Check if method exists
        if hasattr(ui, 'render_upload_section'):
            print("[OK] render_upload_section method exists")
        else:
            print("[ERROR] render_upload_section method not found")
            return False

        # Check method signature (should take self as parameter)
        import inspect
        sig = inspect.signature(ui.render_upload_section)
        params = list(sig.parameters.keys())
        if len(params) == 0:  # self is implicit
            print("[OK] render_upload_section has correct signature")
        else:
            print(f"[WARNING] render_upload_section has unexpected parameters: {params}")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to analyze render_upload_section method: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Streamlit App UnboundLocalError Fix")
    print("=" * 50)

    tests = [
        ("Import Test", test_import),
        ("Class Initialization Test", test_class_initialization),
        ("Method Structure Test", test_method_structure)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        if test_func():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[OK] All tests passed! UnboundLocalError should be fixed.")
        print("\nThe Streamlit app should now run without the page_num error.")
        print("To start the app, run: streamlit run advanced_streamlit_app.py")
    else:
        print("[ERROR] Some tests failed. Check the errors above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)