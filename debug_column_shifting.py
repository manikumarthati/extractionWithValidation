#!/usr/bin/env python3
"""
Debug script to analyze why column shifting detection isn't working
for obfuscated_fake_cbiz_prof_10_pages_5.pdf where frequency was classified as calcode
"""

import os
import json
import time
from services.advanced_pipeline import AdvancedPDFExtractionPipeline

def debug_column_shifting():
    """Debug the column shifting issue in the specific PDF"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_5.pdf"

    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return False

    print("[DEBUG] Debugging Column Shifting Detection")
    print("=" * 50)
    print(f"PDF: {os.path.basename(pdf_path)}")
    print("Issue: frequency was classified as calcode")
    print()

    # Define a simple schema to test extraction
    test_schema = {
        "form_fields": [],
        "tables": [
            {
                "name": "employer_taxes",
                "columns": [
                    {"name": "calcode", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "rate", "type": "number"},
                    {"name": "wage_base", "type": "number"},
                    {"name": "frequency", "type": "string"},
                    {"name": "amount", "type": "number"}
                ]
            }
        ]
    }

    try:
        # Initialize pipeline with debug enabled
        print("Initializing pipeline with debug logging enabled...")
        pipeline = AdvancedPDFExtractionPipeline(api_key, model_config_name='current', enable_debug=True)

        # Process document with low target accuracy to see more validation rounds
        print("Processing document...")
        result = pipeline.process_document(
            pdf_path=pdf_path,
            schema=test_schema,
            page_num=0,
            max_rounds=3,  # Fewer rounds for faster debugging
            target_accuracy=0.95,  # Lower target to force validation
            progress_callback=None
        )

        if result["success"]:
            final_data = result["final_data"]

            print("[SUCCESS] Extraction completed successfully!")
            print()

            # Analyze the extracted employer_taxes table specifically
            if "tables" in final_data and len(final_data["tables"]) > 0:
                employer_taxes = None
                for table in final_data["tables"]:
                    if table.get("name") == "employer_taxes" or "employer" in table.get("name", "").lower():
                        employer_taxes = table
                        break

                if employer_taxes:
                    print("[ANALYSIS] EMPLOYER TAXES TABLE ANALYSIS:")
                    print("-" * 40)

                    rows = employer_taxes.get("rows", [])
                    print(f"Extracted {len(rows)} rows:")
                    print()

                    for i, row in enumerate(rows):
                        print(f"Row {i + 1}:")
                        for col, value in row.items():
                            print(f"  {col}: {value}")
                        print()

                    # Look for the specific issue: frequency classified as calcode
                    print("[ANALYSIS] COLUMN SHIFTING ANALYSIS:")
                    print("-" * 30)

                    frequency_in_calcode = False
                    calcode_has_frequency_values = False

                    for i, row in enumerate(rows):
                        calcode_value = row.get("calcode")
                        frequency_value = row.get("frequency")

                        # Check if calcode contains frequency-type values
                        if calcode_value and isinstance(calcode_value, str):
                            if calcode_value.lower() in ["monthly", "weekly", "quarterly", "annually", "biweekly", "daily"]:
                                frequency_in_calcode = True
                                print(f"[ERROR] COLUMN SHIFT DETECTED in Row {i + 1}:")
                                print(f"    calcode = '{calcode_value}' (should be frequency)")
                                print(f"    frequency = '{frequency_value}' (may be shifted)")
                                print()

                        # Check if frequency contains calcode-type values
                        if frequency_value and isinstance(frequency_value, str):
                            if len(frequency_value) <= 6 and frequency_value.isupper():
                                calcode_has_frequency_values = True
                                print(f"[ERROR] REVERSE SHIFT DETECTED in Row {i + 1}:")
                                print(f"    frequency = '{frequency_value}' (should be calcode)")
                                print(f"    calcode = '{calcode_value}' (may be shifted)")
                                print()

                    if not frequency_in_calcode and not calcode_has_frequency_values:
                        print("[OK] No obvious column shifting detected in final data")
                        print("   (This suggests the visual validation may have corrected the issue)")

                else:
                    print("[ERROR] No employer taxes table found in extracted data")
                    print(f"Available tables: {[t.get('name', 'unnamed') for t in final_data.get('tables', [])]}")

            else:
                print("[ERROR] No tables found in extracted data")

            # Show validation summary
            validation_step = result["pipeline_steps"].get("step4_validation", {})
            if validation_step.get("success"):
                rounds = validation_step.get("validation_rounds", 0)
                corrections = validation_step.get("corrections_applied", 0)
                accuracy = validation_step.get("accuracy_estimate", 0)

                print(f"[SUMMARY] VALIDATION SUMMARY:")
                print(f"   Rounds performed: {rounds}")
                print(f"   Corrections applied: {corrections}")
                print(f"   Final accuracy: {accuracy:.1%}")
                print()

                if corrections > 0:
                    print("[OK] Visual validation made corrections - check debug logs for details")
                else:
                    print("[WARNING] No corrections made by visual validation - this may be the issue")

        else:
            print(f"[ERROR] Extraction failed: {result.get('error')}")
            return False

        # Check debug files for more details
        print("[DEBUG] DEBUG FILES ANALYSIS:")
        print("-" * 25)

        debug_dir = "debug_pipeline"
        if os.path.exists(debug_dir):
            debug_files = os.listdir(debug_dir)
            recent_files = [f for f in debug_files if str(int(time.time()) - 300) in f]  # Last 5 minutes

            print(f"Recent debug files ({len(recent_files)} files):")
            for file in sorted(recent_files):
                print(f"  - {file}")

            # Look for validation files specifically
            validation_files = [f for f in recent_files if "validation" in f]
            if validation_files:
                print("\n[DEBUG] VALIDATION DEBUG FILES:")
                for file in validation_files:
                    print(f"  - {file}")
                print("Check these files to see what the visual validation detected")
            else:
                print("\n[WARNING] No validation debug files found - visual validation may not have run")

        return True

    except Exception as e:
        print(f"[ERROR] Debug analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_column_shifting()
    if success:
        print("\n[SUCCESS] Column shifting debug analysis completed!")
        print("Check the output above and debug files for insights.")
    else:
        print("\n[FAILED] Column shifting debug analysis failed")