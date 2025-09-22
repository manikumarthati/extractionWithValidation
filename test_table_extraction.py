#!/usr/bin/env python3
"""
Test table extraction improvements
"""

import json
from services.schema_text_extractor import SchemaTextExtractor

def test_table_extraction_instructions():
    """Test that the table extraction instructions are properly included"""

    test_schema = {
        "documentSchema": {
            "entityTypes": [
                {
                    "name": "document",
                    "properties": [
                        {
                            "name": "employees",
                            "valueType": "array"
                        },
                        {
                            "name": "benefits",
                            "valueType": "array"
                        }
                    ]
                }
            ]
        }
    }

    extractor = SchemaTextExtractor("")

    # Test that the prompt includes table instructions
    sample_text = """
    Employee Table:
    Name        ID      Department
    John Doe    001     Engineering
    Jane Smith  002     Marketing
    Bob Wilson  003     Sales

    Benefits Table:
    Type        Amount
    Health      $200
    Dental      $50
    Vision      $25
    """

    prompt = extractor._build_text_schema_prompt(sample_text, test_schema)

    print("[TEST] Checking if table extraction rules are in prompt...")

    # Check for key table extraction instructions
    table_keywords = [
        "FOR TABLES/ARRAYS",
        "Extract ALL rows visible",
        "not just the first one",
        "TABLE COMPLETENESS",
        "every single row from the table",
        "ROW COUNT",
        "Never limit to one row",
        "MULTIPLE ENTRIES",
        "capture them all",
        "FULL TABLE DATA",
        "scan the entire table top to bottom"
    ]

    found_keywords = []
    missing_keywords = []

    for keyword in table_keywords:
        if keyword in prompt:
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    print(f"[RESULT] Found {len(found_keywords)}/{len(table_keywords)} table extraction keywords")

    if missing_keywords:
        print(f"[WARNING] Missing keywords: {missing_keywords}")

    # Check if example shows multiple rows
    example_checks = [
        '"type": "Health"',
        '"type": "Dental"',
        '"type": "Vision"',
        '"name": "John Smith"',
        '"name": "Jane Doe"',
        '"name": "Bob Johnson"'
    ]

    found_examples = []
    for check in example_checks:
        if check in prompt:
            found_examples.append(check)

    print(f"[RESULT] Found {len(found_examples)}/{len(example_checks)} multi-row examples")

    success = len(missing_keywords) == 0 and len(found_examples) >= 4

    if success:
        print("[SUCCESS] Table extraction instructions properly integrated!")
    else:
        print("[FAILED] Table extraction instructions need improvement")

    return success

def test_table_completeness_checker():
    """Test the table completeness checking logic"""

    extractor = SchemaTextExtractor("")

    # Test case 1: Missing rows detected
    validation_data_with_missing = {
        "table_validation_results": [
            {
                "table_name": "employees",
                "rows_visible_in_image": 5,
                "rows_extracted": 1,
                "missing_rows": 4,
                "row_completeness_issue": True
            }
        ]
    }

    result1 = extractor._check_table_completeness_issues(validation_data_with_missing)
    print(f"[TEST] Missing rows detection: {result1}")

    # Test case 2: Complete table
    validation_data_complete = {
        "table_validation_results": [
            {
                "table_name": "employees",
                "rows_visible_in_image": 3,
                "rows_extracted": 3,
                "missing_rows": 0,
                "row_completeness_issue": False
            }
        ]
    }

    result2 = extractor._check_table_completeness_issues(validation_data_complete)
    print(f"[TEST] Complete table detection: {not result2}")

    # Test case 3: Empty validation data
    result3 = extractor._check_table_completeness_issues({})
    print(f"[TEST] Empty data handling: {not result3}")

    success = result1 and not result2 and not result3

    if success:
        print("[SUCCESS] Table completeness checker working correctly!")
    else:
        print("[FAILED] Table completeness checker needs fixes")

    return success

if __name__ == "__main__":
    print("Testing Table Extraction Improvements...")

    test1 = test_table_extraction_instructions()
    print()
    test2 = test_table_completeness_checker()

    if test1 and test2:
        print("\n[SUCCESS] All table extraction improvements working!")
    else:
        print("\n[FAILED] Some table extraction improvements need work")