#!/usr/bin/env python3
"""
Test the fixed _extract_clean_schema_structure method with the real genericSchemaFull.json
"""

import json
import os
from services.schema_text_extractor import SchemaTextExtractor

def test_real_schema_array_structure():
    """Test that arrays are properly recognized in the real schema"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # Create extractor
    extractor = SchemaTextExtractor(api_key)

    try:
        # Load the real schema
        with open('genericSchemaFull.json', 'r') as f:
            real_schema = json.load(f)

        print("Testing real schema array structure extraction...")

        # Test the fixed method
        clean_schema = extractor._extract_clean_schema_structure(real_schema)

        print("Clean schema structure (first 20 entries):")
        count = 0
        for key, value in clean_schema.items():
            if count < 20:
                print(f"  {key}: {type(value).__name__}")
                if isinstance(value, list) and len(value) > 0:
                    print(f"    Array structure: {list(value[0].keys())}")
                count += 1

        # Check specifically for Employer_Tax
        if "Employer_Tax" in clean_schema:
            employer_tax = clean_schema["Employer_Tax"]
            print(f"\nEmployer_Tax structure: {type(employer_tax).__name__}")
            if isinstance(employer_tax, list):
                print("SUCCESS: Employer_Tax is correctly identified as an array")
                if len(employer_tax) > 0:
                    print(f"Array item fields: {list(employer_tax[0].keys())}")
                else:
                    print("WARNING: Array structure is empty")
            else:
                print("ERROR: Employer_Tax should be an array")
                return False

        # Check for other arrays that should be detected
        array_entities = [key for key, value in clean_schema.items() if isinstance(value, list)]
        print(f"\nTotal array entities found: {len(array_entities)}")
        print(f"Array entities: {array_entities[:10]}")  # Show first 10

        return True

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Real Schema Array Structure Fix")
    print("=" * 45)

    success = test_real_schema_array_structure()

    if success:
        print("\nReal schema test passed!")
        print("The fix correctly handles the complex real-world schema")
    else:
        print("\nReal schema test failed")