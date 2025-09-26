#!/usr/bin/env python3
"""
Test extraction and validation of deduction table specifically
to ensure column shift detection works
"""

import os
import json
from services.advanced_pipeline import AdvancedPDFExtractionPipeline

def test_deduction_with_validation():
    """Test deduction table extraction with comprehensive schema and visual validation"""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found")
        return False

    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_5.pdf"

    print("[TEST] Testing Deduction Table Extraction + Visual Validation")
    print("=" * 60)
    print("Goal: Force extraction of deduction table and test column shift detection")
    print()

    # Comprehensive schema that explicitly asks for all tables including deductions
    comprehensive_schema = {
        "form_fields": [
            {"name": "employee_name", "type": "string"},
            {"name": "employee_id", "type": "string"}
        ],
        "tables": [
            {
                "name": "salary_information",
                "description": "Rate/Salary table with rate codes and effective dates",
                "columns": [
                    {"name": "rate_code", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "rate", "type": "number"},
                    {"name": "effective_dates", "type": "string"}
                ]
            },
            {
                "name": "employee_taxes",
                "description": "Employee tax information",
                "columns": [
                    {"name": "tax_code", "type": "string"},
                    {"name": "description", "type": "string"},
                    {"name": "status", "type": "string"},
                    {"name": "amount", "type": "number"},
                    {"name": "effective_dates", "type": "string"}
                ]
            },
            {
                "name": "deduction_information",
                "description": "CRITICAL: Deduction Information table with 401K contributions, dental, health insurance, etc.",
                "columns": [
                    {"name": "code", "type": "string", "description": "Deduction code like 401KC, DNTL, FH125"},
                    {"name": "deduction", "type": "string", "description": "Description like '401K Contribution', 'Dental Insurance'"},
                    {"name": "rate", "type": "number", "description": "Rate amount like 6.00, 14.00, 18.32"},
                    {"name": "calcode", "type": "string", "description": "Calculation code like %401K, B5 - can be blank"},
                    {"name": "frequency", "type": "string", "description": "Frequency like Monthly, Weekly - can be blank"},
                    {"name": "goal_paid", "type": "string", "description": "Goal/Paid amounts"},
                    {"name": "effective_dates", "type": "string", "description": "Date ranges"}
                ]
            }
        ]
    }

    try:
        print("Initializing pipeline...")
        pipeline = AdvancedPDFExtractionPipeline(api_key, 'current', enable_debug=True)

        # Process with visual validation enabled
        print("Processing document with comprehensive schema...")
        result = pipeline.process_document(
            pdf_path=pdf_path,
            schema=comprehensive_schema,
            page_num=0,
            max_rounds=2,  # Enable validation rounds
            target_accuracy=0.98,
            progress_callback=None
        )

        if result["success"]:
            final_data = result["final_data"]
            print("[SUCCESS] Extraction completed!")
            print()

            # Check if deduction table was extracted
            deduction_table = None
            all_tables = []

            if "tables" in final_data:
                for table in final_data["tables"]:
                    table_name = table.get("name", "").lower()
                    all_tables.append(table_name)
                    if "deduction" in table_name:
                        deduction_table = table
                        break

            print(f"[TABLES] Extracted tables: {all_tables}")
            print()

            if deduction_table:
                print("[FOUND] Deduction table extracted successfully!")
                print("-" * 40)

                rows = deduction_table.get("rows", []) or deduction_table.get("data", [])
                print(f"Deduction table has {len(rows)} rows:")
                print()

                # Analyze each row for column shifting
                column_shifts_detected = 0
                for i, row in enumerate(rows):
                    print(f"Row {i + 1}:")
                    code = row.get("code", "")
                    deduction_desc = row.get("deduction", "")
                    rate = row.get("rate", "")
                    calcode = row.get("calcode", "")
                    frequency = row.get("frequency", "")

                    print(f"  code: '{code}'")
                    print(f"  deduction: '{deduction_desc}'")
                    print(f"  rate: '{rate}'")
                    print(f"  calcode: '{calcode}'")
                    print(f"  frequency: '{frequency}'")

                    # Check for obvious column shifts
                    shift_detected = False

                    # Pattern 1: Frequency values in calcode column
                    if calcode and any(freq in str(calcode).lower() for freq in ["monthly", "weekly", "daily", "per"]):
                        print(f"  [SHIFT] Frequency value '{calcode}' in calcode column!")
                        shift_detected = True
                        column_shifts_detected += 1

                    # Pattern 2: CalcCode-like values in frequency column
                    if frequency and ("%" in str(frequency) or str(frequency) in ["B5", "ML"]):
                        print(f"  [SHIFT] CalcCode-like value '{frequency}' in frequency column!")
                        shift_detected = True
                        column_shifts_detected += 1

                    # Pattern 3: Numbers/amounts in wrong columns
                    if frequency and str(frequency).replace(".", "").replace("/", "").isdigit():
                        print(f"  [SHIFT] Numeric value '{frequency}' in frequency column!")
                        shift_detected = True
                        column_shifts_detected += 1

                    if not shift_detected:
                        print(f"  [OK] No obvious column shifts detected")

                    print()

                # Check validation results
                validation_step = result["pipeline_steps"].get("step4_validation", {})
                validation_success = validation_step.get("success", False)
                corrections_made = validation_step.get("corrections_applied", 0)

                print(f"[VALIDATION] Visual validation results:")
                print(f"  Success: {validation_success}")
                print(f"  Corrections made: {corrections_made}")
                print(f"  Manual shift detection: {column_shifts_detected} issues found")

                if column_shifts_detected > 0 and corrections_made == 0:
                    print(f"  [ISSUE] Manual analysis found {column_shifts_detected} shifts but visual validation made 0 corrections!")
                    print(f"  This indicates visual validation is not detecting column shifts properly.")
                elif column_shifts_detected > 0 and corrections_made > 0:
                    print(f"  [GOOD] Both manual analysis and visual validation detected issues")
                else:
                    print(f"  [OK] No column shifts detected by either method")

            else:
                print("[ERROR] Deduction table still not extracted!")
                print(f"Available tables: {all_tables}")
                print()
                print("This indicates the extraction step is still missing the deduction data.")

            return deduction_table is not None

        else:
            print(f"[ERROR] Processing failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_deduction_with_validation()
    if success:
        print("\n[SUCCESS] Deduction validation test completed!")
    else:
        print("\n[FAILED] Deduction validation test failed")