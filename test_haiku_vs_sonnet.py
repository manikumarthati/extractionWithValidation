#!/usr/bin/env python3
"""
Test Haiku vs Sonnet model performance for PDF data extraction
Compares accuracy, speed, and cost-effectiveness
"""

import json
import os
import time
from services.advanced_pipeline import AdvancedPDFExtractionPipeline

def test_model_comparison():
    """Test both Haiku and Sonnet models with the same document"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # PDF path
    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_1.pdf"

    # Schema path
    schema_path = "D:/learning/stepwisePdfParsing/employee_profile_hierarchical_schema.json"

    try:
        # Load the schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        results = {}

        # Test configurations to compare
        configs_to_test = [
            ('budget', 'Claude Haiku Only - Maximum Cost Savings'),
            ('current', 'Balanced Config - Haiku + Sonnet'),
            ('claude', 'Claude Sonnet Only - Superior Accuracy')
        ]

        for config_name, config_desc in configs_to_test:
            print(f"\n{'='*60}")
            print(f"TESTING: {config_desc}")
            print(f"Config: {config_name}")
            print('='*60)

            # Create pipeline with specific config
            pipeline = AdvancedPDFExtractionPipeline(api_key, model_config_name=config_name)

            # Time the extraction
            start_time = time.time()

            # Run extraction
            result = pipeline.process_document(
                pdf_path=pdf_path,
                schema=schema,
                page_num=0,  # First page
                max_rounds=2,  # Limit rounds for comparison
                target_accuracy=0.90
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Store results
            results[config_name] = {
                'config_desc': config_desc,
                'success': result.get('success', False),
                'processing_time': processing_time,
                'workflow_summary': result.get('workflow_summary', {}),
                'final_data': result.get('final_data', {}),
                'error': result.get('error') if not result.get('success') else None
            }

            # Print immediate results
            print(f"Success: {result.get('success')}")
            print(f"Processing Time: {processing_time:.2f} seconds")

            if result.get('success'):
                workflow = result.get('workflow_summary', {})
                print(f"Text Extraction Success: {workflow.get('text_extraction_success')}")
                print(f"Validation Success: {workflow.get('validation_success')}")
                print(f"Final Accuracy: {workflow.get('final_accuracy')}")
                print(f"Validation Rounds: {workflow.get('validation_rounds_completed')}")
                print(f"Corrections Applied: {workflow.get('total_corrections_applied')}")

                # Check specific field extraction quality
                final_data = result.get('final_data', {})
                if "Employee_Profile" in final_data:
                    basic_info = final_data["Employee_Profile"].get("Basic_Information", {})
                    employment = basic_info.get("Employment_Details", {})

                    # Test blank field handling
                    blank_fields = ["Position", "Employee_Type", "Title"]
                    blank_field_score = 0
                    for field in blank_fields:
                        if field in employment:
                            if employment[field] == "":
                                blank_field_score += 1
                                print(f"[PASS] {field}: Correctly blank")
                            else:
                                print(f"[FAIL] {field}: '{employment[field]}' (should be blank)")

                    print(f"Blank Field Accuracy: {blank_field_score}/{len(blank_fields)} ({(blank_field_score/len(blank_fields)*100):.1f}%)")

                    # Test complete text extraction
                    tax_info = final_data["Employee_Profile"].get("Tax_Information", {})
                    employer_taxes = tax_info.get("Employer_Taxes", [])
                    complete_text_found = False

                    for tax in employer_taxes:
                        if tax.get("Tax_Code") == "MNDW":
                            description = tax.get("Tax_Description", "")
                            if "Workforce Enhancement Fee" in description:
                                print(f"[PASS] Complete text: '{description}'")
                                complete_text_found = True
                            else:
                                print(f"[FAIL] Incomplete text: '{description}'")
                            break

                    if not complete_text_found:
                        print("[FAIL] MNDW tax record not found")

            else:
                print(f"[ERROR] Failed: {result.get('error')}")

        # Generate comparison report
        print(f"\n{'='*80}")
        print("PERFORMANCE COMPARISON REPORT")
        print('='*80)

        # Performance metrics comparison
        print("\n[METRICS] PERFORMANCE METRICS:")
        print("-" * 40)
        for config_name, data in results.items():
            print(f"{data['config_desc']}:")
            print(f"  Success: {'[PASS]' if data['success'] else '[FAIL]'}")
            print(f"  Time: {data['processing_time']:.2f}s")
            if data['success']:
                workflow = data['workflow_summary']
                print(f"  Final Accuracy: {workflow.get('final_accuracy', 'N/A')}")
                print(f"  Validation Rounds: {workflow.get('validation_rounds_completed', 'N/A')}")
            print()

        # Speed comparison
        print("[SPEED] SPEED RANKING:")
        print("-" * 20)
        speed_ranking = sorted(
            [(name, data['processing_time']) for name, data in results.items() if data['success']],
            key=lambda x: x[1]
        )

        for i, (config_name, time_taken) in enumerate(speed_ranking, 1):
            config_desc = results[config_name]['config_desc']
            print(f"{i}. {config_desc}: {time_taken:.2f}s")

        # Cost estimation
        print("\n[COST] ESTIMATED COSTS (per document):")
        print("-" * 35)
        cost_estimates = {
            'budget': '$0.05-0.12',
            'current': '$0.08-0.15',
            'claude': '$0.12-0.25'
        }

        for config_name, data in results.items():
            if config_name in cost_estimates:
                print(f"{data['config_desc']}: {cost_estimates[config_name]}")

        # Recommendations
        print(f"\n[RECOMMENDATIONS] RECOMMENDATIONS:")
        print("-" * 20)

        # Find fastest successful config
        fastest_config = min(
            [(name, data) for name, data in results.items() if data['success']],
            key=lambda x: x[1]['processing_time']
        )[0] if any(data['success'] for data in results.values()) else None

        if fastest_config:
            print(f"Fastest: {results[fastest_config]['config_desc']}")

        # Find most accurate
        most_accurate = None
        highest_accuracy = 0
        for name, data in results.items():
            if data['success']:
                accuracy = data['workflow_summary'].get('final_accuracy', 0)
                if isinstance(accuracy, (int, float)) and accuracy > highest_accuracy:
                    highest_accuracy = accuracy
                    most_accurate = name

        if most_accurate:
            print(f"Most Accurate: {results[most_accurate]['config_desc']} ({highest_accuracy})")

        # Best value recommendation
        if results.get('budget', {}).get('success'):
            print(f"Best Value: Budget Config - Good performance at lowest cost")
        elif results.get('current', {}).get('success'):
            print(f"Best Value: Current Config - Balanced performance and cost")

        return True

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Claude Model Performance Comparison")
    print("Testing Haiku vs Sonnet for PDF Data Extraction")
    print("=" * 60)

    success = test_model_comparison()

    if success:
        print(f"\n[SUCCESS] Model comparison completed!")
        print("Check the performance metrics above to choose the best configuration.")
    else:
        print(f"\n[ERROR] Model comparison failed")