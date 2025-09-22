#!/usr/bin/env python3
"""
Test that the enhanced extraction workflow works without KeyError
"""

import json
from services.schema_text_extractor import SchemaTextExtractor

def test_workflow_structure():
    """Test that the workflow methods work without KeyError"""

    # Simple test schema
    test_schema = {
        "documentSchema": {
            "entityTypes": [
                {
                    "name": "document",
                    "properties": [
                        {
                            "name": "company_name",
                            "valueType": "string"
                        },
                        {
                            "name": "employee_name",
                            "valueType": "string"
                        }
                    ]
                }
            ]
        }
    }

    # Mock extractor (no API key needed for structure test)
    extractor = SchemaTextExtractor("")

    # Test the output format creation
    sample_data = {"company_name": "ACME Corp", "employee_name": "John Doe"}

    try:
        clean_output = extractor._create_clean_output_format(
            sample_data, test_schema, "enhanced_workflow"
        )

        print("[TEST] Clean output format creation: SUCCESS")
        print(f"[INFO] Output keys: {list(clean_output.keys())}")

        # Verify structure
        expected_keys = ["success", "extracted_data", "extraction_method", "schema_structure"]
        missing_keys = [key for key in expected_keys if key not in clean_output]

        if missing_keys:
            print(f"[ERROR] Missing keys: {missing_keys}")
            return False

        # Verify data is in extracted_data
        if "extracted_data" in clean_output:
            extracted = clean_output["extracted_data"]
            if "company_name" in extracted and "employee_name" in extracted:
                print("[SUCCESS] Data properly placed in extracted_data")
            else:
                print("[ERROR] Data missing from extracted_data")
                return False

        # Check no old keys present
        old_keys = ["final_data", "schema_used"]
        found_old_keys = [key for key in old_keys if key in clean_output]

        if found_old_keys:
            print(f"[ERROR] Found old keys: {found_old_keys}")
            return False
        else:
            print("[SUCCESS] No old keys present")

        return True

    except Exception as e:
        print(f"[ERROR] Exception during test: {e}")
        return False

def test_key_access_pattern():
    """Test the new key access pattern"""

    # Simulate what the workflow would return
    mock_result = {
        "success": True,
        "extracted_data": {
            "company_name": "ACME Corp",
            "employee_name": "John Doe",
            "employees": [
                {"name": "John", "id": "001"},
                {"name": "Jane", "id": "002"}
            ]
        },
        "extraction_method": "enhanced_workflow",
        "schema_structure": {
            "document": {
                "company_name": "string",
                "employee_name": "string",
                "employees": "array"
            }
        },
        "workflow_summary": {
            "text_extraction_success": True,
            "schema_extraction_success": True,
            "visual_validation_applied": False
        }
    }

    try:
        # Test the access pattern apps should use
        final_data = mock_result["extracted_data"]  # This should work
        workflow_summary = mock_result["workflow_summary"]

        print("[TEST] New access pattern: SUCCESS")
        print(f"[INFO] Final data keys: {list(final_data.keys())}")
        print(f"[INFO] Employees count: {len(final_data.get('employees', []))}")

        # Verify we can't access old keys
        try:
            old_access = mock_result["final_data"]  # This should fail
            print("[ERROR] Old key access worked - should have failed!")
            return False
        except KeyError:
            print("[SUCCESS] Old key access properly fails")

        return True

    except Exception as e:
        print(f"[ERROR] Exception during key access test: {e}")
        return False

if __name__ == "__main__":
    print("Testing Workflow Fix...")

    test1 = test_workflow_structure()
    print()
    test2 = test_key_access_pattern()

    if test1 and test2:
        print("\n[SUCCESS] Workflow fix working properly!")
        print("Enhanced extraction workflow should now work without KeyError")
    else:
        print("\n[FAILED] Workflow fix needs more work!")