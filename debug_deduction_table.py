#!/usr/bin/env python3
"""
Debug script specifically for the Deduction Information table column shifting issue
where frequency was classified as calcode in obfuscated_fake_cbiz_prof_10_pages_5.pdf
"""

import os
import json
import time
from services.advanced_pipeline import AdvancedPDFExtractionPipeline

def debug_deduction_table():
    """Debug the deduction table column shifting issue"""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_5.pdf"

    print("[DEBUG] Debugging Deduction Table Column Shifting")
    print("=" * 50)
    print(f"PDF: {os.path.basename(pdf_path)}")
    print("Issue: frequency was classified as calcode in deduction table")
    print()

    # Define schema specifically for deduction information table
    deduction_schema = {
        "form_fields": [],
        "tables": [
            {
                "name": "deduction_information",
                "columns": [
                    {"name": "code", "type": "string"},
                    {"name": "deduction", "type": "string"},
                    {"name": "rate", "type": "number"},
                    {"name": "calcode", "type": "string"},
                    {"name": "frequency", "type": "string"},
                    {"name": "goal_paid", "type": "string"},
                    {"name": "min_max_annual", "type": "string"},
                    {"name": "arrears", "type": "string"},
                    {"name": "agency", "type": "string"},
                    {"name": "effective_dates", "type": "string"}
                ]
            }
        ]
    }

    try:
        # Initialize pipeline with debug enabled
        print("Initializing pipeline with debug logging enabled...")
        pipeline = AdvancedPDFExtractionPipeline(api_key, model_config_name='current', enable_debug=True)

        # Process document
        print("Processing document...")
        result = pipeline.process_document(
            pdf_path=pdf_path,
            schema=deduction_schema,
            page_num=0,
            max_rounds=3,
            target_accuracy=0.95,
            progress_callback=None
        )

        if result["success"]:
            final_data = result["final_data"]
            print("[SUCCESS] Extraction completed successfully!")
            print()

            # Analyze the deduction table specifically
            if "tables" in final_data and len(final_data["tables"]) > 0:
                deduction_table = None
                for table in final_data["tables"]:
                    table_name = table.get("name", "").lower()
                    if "deduction" in table_name:
                        deduction_table = table
                        break

                if deduction_table:
                    print("[ANALYSIS] DEDUCTION TABLE ANALYSIS:")
                    print("-" * 40)

                    rows = deduction_table.get("rows", []) or deduction_table.get("data", [])
                    print(f"Extracted {len(rows)} deduction rows:")
                    print()

                    for i, row in enumerate(rows):
                        print(f"Row {i + 1}:")
                        for col, value in row.items():
                            print(f"  {col}: {value}")
                        print()

                    # Specific analysis for frequency/calcode confusion
                    print("[ANALYSIS] COLUMN SHIFTING DETECTION:")
                    print("-" * 35)

                    for i, row in enumerate(rows):
                        calcode_value = row.get("calcode") or row.get("CalcCode")
                        frequency_value = row.get("frequency") or row.get("Frequency")

                        # Check if calcode contains frequency values
                        if calcode_value and isinstance(calcode_value, str):
                            frequency_words = ["monthly", "weekly", "quarterly", "annually", "biweekly", "daily", "per pay"]
                            if any(freq in calcode_value.lower() for freq in frequency_words):
                                print(f"[ERROR] COLUMN SHIFT DETECTED in Row {i + 1}:")
                                print(f"    calcode = '{calcode_value}' (contains frequency data)")
                                print(f"    frequency = '{frequency_value}' (may be wrong data)")
                                print(f"    LIKELY FIX: Move '{calcode_value}' to frequency column")
                                print()

                        # Check if frequency contains non-frequency data
                        if frequency_value and isinstance(frequency_value, str):
                            # If frequency contains % symbols, codes, or numbers, it's likely shifted
                            if "%" in frequency_value or len(frequency_value) <= 6:
                                print(f"[ERROR] REVERSE SHIFT DETECTED in Row {i + 1}:")
                                print(f"    frequency = '{frequency_value}' (doesn't look like frequency)")
                                print(f"    calcode = '{calcode_value}' (may be correct)")
                                print()

                        # Check for 401K specific case
                        code_value = row.get("code") or row.get("Code")
                        if code_value and "401" in str(code_value):
                            print(f"[401K ANALYSIS] Row {i + 1}:")
                            print(f"    code: {code_value}")
                            print(f"    calcode: {calcode_value}")
                            print(f"    frequency: {frequency_value}")
                            if calcode_value == "Monthly" or frequency_value == "%401K":
                                print(f"    [ISSUE] Expected: calcode='%401K', frequency='Monthly'")
                            print()

                else:
                    print("[ERROR] No deduction table found in extracted data")
                    print(f"Available tables: {[t.get('name', 'unnamed') for t in final_data.get('tables', [])]}")

                    # Show all tables to help identify the issue
                    print()
                    print("[DEBUG] ALL EXTRACTED TABLES:")
                    for i, table in enumerate(final_data.get('tables', [])):
                        print(f"  Table {i+1}: {table.get('name', 'unnamed')}")
                        rows = table.get('rows', []) or table.get('data', [])
                        if rows and len(rows) > 0:
                            print(f"    Sample row keys: {list(rows[0].keys())}")
                        print()

            # Show validation results
            validation_step = result["pipeline_steps"].get("step4_validation", {})
            if validation_step.get("success"):
                print(f"[SUMMARY] VALIDATION SUMMARY:")
                print(f"   Rounds performed: {validation_step.get('validation_rounds', 0)}")
                print(f"   Corrections applied: {validation_step.get('corrections_applied', 0)}")
                print(f"   Final accuracy: {validation_step.get('accuracy_estimate', 0):.1%}")
                print()

                if validation_step.get('corrections_applied', 0) > 0:
                    print("[OK] Visual validation made corrections")
                else:
                    print("[WARNING] Visual validation made no corrections for column shifting")
            else:
                print(f"[ERROR] Validation failed: {validation_step.get('error', 'Unknown error')}")

        else:
            print(f"[ERROR] Extraction failed: {result.get('error')}")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Debug analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_deduction_table()
    if success:
        print("\n[SUCCESS] Deduction table debug analysis completed!")
    else:
        print("\n[FAILED] Deduction table debug analysis failed")