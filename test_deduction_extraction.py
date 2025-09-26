#!/usr/bin/env python3
"""
Test what Claude extracts from the deduction table raw text
"""

import os
import json
from services.schema_text_extractor import SchemaTextExtractor

def test_deduction_extraction():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found")
        return

    # Raw text from the deduction section
    deduction_raw_text = """
Deduction Information
Code
Deduction
Rate
CalcCode
Frequency
Goal/Paid
Min/Max/Annual Max
Arrears
Agency
Effective
Dates
401KC
401K Contribution6.00
%401K
0.00/0.00
0.00/0.00/0.00
0.00
04/01/2016 to 12/31/2100
401kUM 401kUnmatch
14.00
%401K
0.00/0.00
0.00/0.00/0.00
0.00
08/01/2022 to 12/31/2100
DNTL
Dental Insurance S125
18.32
B5
0.00/0.00
0.00/0.00/0.00
0.00
09/01/2019 to 12/31/2100
"""

    # Schema for deduction table
    schema = {
        "tables": [
            {
                "name": "deduction_information",
                "columns": [
                    {"name": "code", "type": "string"},
                    {"name": "deduction", "type": "string"},
                    {"name": "rate", "type": "number"},
                    {"name": "calcode", "type": "string"},
                    {"name": "frequency", "type": "string"}
                ]
            }
        ]
    }

    print("TESTING DEDUCTION EXTRACTION")
    print("=" * 40)
    print("Raw text input:")
    print(deduction_raw_text)
    print("\nExpected extraction:")
    print("Row 1: code='401KC', deduction='401K Contribution', rate=6.00, calcode='%401K', frequency='Monthly'")
    print("Row 2: code='401kUM', deduction='401kUnmatch', rate=14.00, calcode='%401K', frequency='Monthly'")
    print()

    try:
        extractor = SchemaTextExtractor(api_key)
        result = extractor.extract_with_schema_from_text(deduction_raw_text, schema)

        if result["success"]:
            extracted_data = result["extracted_data"]
            print("ACTUAL EXTRACTION RESULT:")
            print("-" * 30)
            print(json.dumps(extracted_data, indent=2))
            print()

            # Analyze the extraction
            if "tables" in extracted_data and len(extracted_data["tables"]) > 0:
                table = extracted_data["tables"][0]
                rows = table.get("rows", []) or table.get("data", [])

                print("COLUMN SHIFT ANALYSIS:")
                print("-" * 25)
                for i, row in enumerate(rows):
                    print(f"Row {i+1}:")
                    calcode = row.get("calcode") or row.get("CalcCode", "")
                    frequency = row.get("frequency") or row.get("Frequency", "")

                    print(f"  calcode: '{calcode}'")
                    print(f"  frequency: '{frequency}'")

                    # Check if frequency data ended up in calcode
                    if calcode and frequency != "Monthly":
                        if any(word in calcode.lower() for word in ["monthly", "weekly", "per", "pay"]):
                            print(f"  [ISSUE] Frequency data in calcode column!")
                        elif calcode in ["B5", "%401K"] and not frequency:
                            print(f"  [ISSUE] Missing frequency - where is 'Monthly'?")
                    print()

        else:
            print(f"Extraction failed: {result.get('error')}")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deduction_extraction()