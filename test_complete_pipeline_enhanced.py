#!/usr/bin/env python3
"""
Test the complete pipeline with enhanced extraction to see if vision validation/correction fixes the issues
"""

import json
import os
from services.advanced_pipeline import AdvancedPDFExtractionPipeline

def test_complete_pipeline():
    """Test the complete pipeline with the Employee Profile PDF"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # PDF path
    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_1.pdf"

    # Use the hierarchical schema we created
    schema_path = "D:/learning/stepwisePdfParsing/employee_profile_hierarchical_schema.json"

    try:
        # Load the schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        # Create pipeline
        pipeline = AdvancedPDFExtractionPipeline(api_key, model_config_name='current')

        print("Testing complete pipeline with enhanced extraction...")
        print("This will test:")
        print("1. Enhanced text-based extraction (with our fixes)")
        print("2. Vision-based validation (existing)")
        print("3. Vision-based correction (existing)")
        print()

        # Run the complete pipeline
        result = pipeline.process_document(
            pdf_path=pdf_path,
            schema=schema,
            page_num=0,  # First page
            max_rounds=3,
            target_accuracy=0.95
        )

        if result["success"]:
            print("=== PIPELINE RESULTS ===")
            print(f"Success: {result['success']}")

            workflow_summary = result.get("workflow_summary", {})
            print(f"Text extraction success: {workflow_summary.get('text_extraction_success')}")
            print(f"Validation success: {workflow_summary.get('validation_success')}")
            print(f"Final accuracy: {workflow_summary.get('final_accuracy')}")
            print(f"Validation rounds: {workflow_summary.get('validation_rounds_completed')}")
            print(f"Corrections applied: {workflow_summary.get('total_corrections_applied')}")
            print()

            # Check specific fields we're concerned about
            final_data = result.get("final_data", {})

            print("=== BLANK FIELD ANALYSIS ===")
            if "Employee_Profile" in final_data and "Basic_Information" in final_data["Employee_Profile"]:
                basic_info = final_data["Employee_Profile"]["Basic_Information"]
                employment_details = basic_info.get("Employment_Details", {})

                # Check the problematic fields
                test_fields = {
                    "Position": employment_details.get("Position"),
                    "Employee_Type": employment_details.get("Employee_Type"),
                    "Title": employment_details.get("Title")
                }

                for field_name, field_value in test_fields.items():
                    if field_value == "":
                        print(f"[PASS] {field_name}: Correctly blank ('')")
                    elif field_value is None:
                        print(f"[INFO] {field_name}: Null (acceptable for missing)")
                    else:
                        print(f"[CHECK] {field_name}: '{field_value}' (should this be blank?)")

            print("\n=== COMPLETE TEXT ANALYSIS ===")
            # Check employer tax records for complete text
            if ("Employee_Profile" in final_data and
                "Tax_Information" in final_data["Employee_Profile"] and
                "Employer_Taxes" in final_data["Employee_Profile"]["Tax_Information"]):

                employer_taxes = final_data["Employee_Profile"]["Tax_Information"]["Employer_Taxes"]

                for tax_record in employer_taxes:
                    if tax_record.get("Tax_Code") == "MNDW":
                        description = tax_record.get("Tax_Description", "")
                        if "Workforce Enhancement Fee" in description:
                            print(f"[PASS] MNDW: Complete text '{description}'")
                        else:
                            print(f"[CHECK] MNDW: '{description}' (partial text?)")
                        break

            # Show a sample of the final data structure
            print("\n=== SAMPLE FINAL DATA ===")
            print(json.dumps(final_data, indent=2)[:1000] + "..." if len(json.dumps(final_data, indent=2)) > 1000 else json.dumps(final_data, indent=2))

            return True

        else:
            print(f"Pipeline failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Complete Pipeline with Enhanced Extraction")
    print("=" * 55)

    success = test_complete_pipeline()

    if success:
        print("\n[SUCCESS] Complete pipeline test completed!")
        print("Check the analysis above to see if vision validation/correction")
        print("fixed the blank field and text completeness issues.")
    else:
        print("\n[FAILED] Complete pipeline test failed")