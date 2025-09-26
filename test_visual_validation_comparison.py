#!/usr/bin/env python3
"""
Test Haiku vs Sonnet for visual validation tasks
This tests the most complex reasoning task where model differences should be most apparent
"""

import json
import os
import time
from services.advanced_pipeline import AdvancedPDFExtractionPipeline

def test_visual_validation_comparison():
    """Test visual validation performance between different models"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # PDF path and schema
    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_1.pdf"
    schema_path = "D:/learning/stepwisePdfParsing/employee_profile_hierarchical_schema.json"

    try:
        # Load the schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        # Create custom configs for visual validation testing
        configs_to_test = [
            ('budget', 'Haiku for Vision Validation'),
            ('current', 'Sonnet for Vision Validation'),
            ('claude', 'Sonnet for Vision Validation')
        ]

        results = {}

        for config_name, config_desc in configs_to_test:
            print(f"\n{'='*70}")
            print(f"TESTING VISUAL VALIDATION: {config_desc}")
            print(f"Config: {config_name}")

            # Show which model will be used for vision validation
            from model_configs import get_model_for_task
            vision_model = get_model_for_task('vision_validation', config_name)
            data_model = get_model_for_task('data_extraction', config_name)

            print(f"Vision Validation Model: {vision_model}")
            print(f"Data Extraction Model: {data_model}")
            print('='*70)

            try:
                # Create pipeline with specific config
                pipeline = AdvancedPDFExtractionPipeline(api_key, model_config_name=config_name)

                # Time the full process including validation
                start_time = time.time()

                # Run the complete pipeline with visual validation
                result = pipeline.process_document(
                    pdf_path=pdf_path,
                    schema=schema,
                    page_num=0,  # First page
                    max_rounds=2,  # Allow validation rounds
                    target_accuracy=0.85  # Lower target to see validation behavior
                )

                end_time = time.time()
                processing_time = end_time - start_time

                # Store detailed results
                workflow_summary = result.get('workflow_summary', {})
                results[config_name] = {
                    'config_desc': config_desc,
                    'vision_model': vision_model,
                    'data_model': data_model,
                    'success': result.get('success', False),
                    'processing_time': processing_time,
                    'text_extraction_success': workflow_summary.get('text_extraction_success'),
                    'validation_success': workflow_summary.get('validation_success'),
                    'final_accuracy': workflow_summary.get('final_accuracy'),
                    'validation_rounds': workflow_summary.get('validation_rounds_completed', 0),
                    'corrections_applied': workflow_summary.get('total_corrections_applied', 0),
                    'final_data': result.get('final_data', {}),
                    'error': result.get('error') if not result.get('success') else None
                }

                # Print immediate results
                print(f"Overall Success: {result.get('success')}")
                print(f"Processing Time: {processing_time:.2f} seconds")
                print(f"Text Extraction: {workflow_summary.get('text_extraction_success')}")
                print(f"Validation Success: {workflow_summary.get('validation_success')}")
                print(f"Final Accuracy: {workflow_summary.get('final_accuracy', 'N/A')}")
                print(f"Validation Rounds: {workflow_summary.get('validation_rounds_completed', 0)}")
                print(f"Corrections Applied: {workflow_summary.get('total_corrections_applied', 0)}")

                # Analyze blank field handling specifically
                if result.get('success') and 'Employee_Profile' in result['final_data']:
                    final_data = result['final_data']
                    basic_info = final_data["Employee_Profile"].get("Basic_Information", {})
                    employment = basic_info.get("Employment_Details", {})

                    blank_fields = ["Position", "Employee_Type", "Title"]
                    blank_field_score = 0

                    print(f"\nBlank Field Analysis:")
                    for field in blank_fields:
                        value = employment.get(field, "MISSING")
                        if value == "":
                            blank_field_score += 1
                            print(f"  {field}: [CORRECT] Empty string")
                        elif value == "MISSING":
                            print(f"  {field}: [MISSING] Field not found")
                        else:
                            print(f"  {field}: [INCORRECT] '{value}' (should be empty)")

                    print(f"  Blank Field Accuracy: {blank_field_score}/{len(blank_fields)} ({blank_field_score/len(blank_fields)*100:.1f}%)")

            except Exception as e:
                print(f"Test failed: {e}")
                results[config_name] = {
                    'config_desc': config_desc,
                    'vision_model': vision_model,
                    'data_model': data_model,
                    'success': False,
                    'processing_time': 0,
                    'error': str(e)
                }

            print("\n" + "-"*50)

        # Generate comprehensive comparison report
        print(f"\n{'='*80}")
        print("VISUAL VALIDATION COMPARISON REPORT")
        print('='*80)

        print("\n[PERFORMANCE SUMMARY]:")
        print("-" * 30)
        for config_name, data in results.items():
            print(f"{data['config_desc']}:")
            print(f"  Vision Model: {data.get('vision_model', 'Unknown')}")
            print(f"  Data Model: {data.get('data_model', 'Unknown')}")
            print(f"  Success: {'YES' if data['success'] else 'NO'}")

            if data['success']:
                print(f"  Time: {data['processing_time']:.2f}s")
                print(f"  Final Accuracy: {data.get('final_accuracy', 'N/A')}")
                print(f"  Validation Rounds: {data.get('validation_rounds', 0)}")
                print(f"  Corrections Applied: {data.get('corrections_applied', 0)}")
                print(f"  Vision Validation Success: {data.get('validation_success', 'N/A')}")
            else:
                print(f"  Error: {data.get('error', 'Unknown')}")
            print()

        # Visual validation effectiveness comparison
        successful_results = [(name, data) for name, data in results.items() if data['success']]

        if successful_results:
            print("[VISUAL VALIDATION EFFECTIVENESS]:")
            print("-" * 35)

            for config_name, data in successful_results:
                rounds = data.get('validation_rounds', 0)
                corrections = data.get('corrections_applied', 0)
                accuracy = data.get('final_accuracy', 0)

                effectiveness_score = 0
                if isinstance(accuracy, (int, float)) and accuracy > 0.9:
                    effectiveness_score += 3
                elif isinstance(accuracy, (int, float)) and accuracy > 0.8:
                    effectiveness_score += 2
                elif isinstance(accuracy, (int, float)) and accuracy > 0.7:
                    effectiveness_score += 1

                if corrections > 0:
                    effectiveness_score += 1

                if rounds > 0 and data.get('validation_success'):
                    effectiveness_score += 1

                print(f"{data['config_desc']}:")
                print(f"  Accuracy: {accuracy}")
                print(f"  Corrections: {corrections}")
                print(f"  Validation Rounds: {rounds}")
                print(f"  Effectiveness Score: {effectiveness_score}/5")
                print()

        # Speed comparison
        if successful_results:
            print("[SPEED RANKING]:")
            print("-" * 15)
            speed_ranking = sorted(successful_results, key=lambda x: x[1]['processing_time'])
            for i, (config_name, data) in enumerate(speed_ranking, 1):
                print(f"{i}. {data['config_desc']}: {data['processing_time']:.2f}s")

        # Cost vs Quality Analysis
        print(f"\n[COST VS QUALITY ANALYSIS]:")
        print("-" * 27)

        haiku_result = results.get('budget', {})
        sonnet_result = results.get('current', {}) or results.get('claude', {})

        if haiku_result.get('success') and sonnet_result.get('success'):
            haiku_acc = haiku_result.get('final_accuracy', 0)
            sonnet_acc = sonnet_result.get('final_accuracy', 0)

            print(f"Haiku Vision Validation:")
            print(f"  Cost: ~60-80% cheaper than Sonnet")
            print(f"  Accuracy: {haiku_acc}")
            print(f"  Time: {haiku_result['processing_time']:.2f}s")
            print()
            print(f"Sonnet Vision Validation:")
            print(f"  Cost: Premium pricing")
            print(f"  Accuracy: {sonnet_acc}")
            print(f"  Time: {sonnet_result['processing_time']:.2f}s")
            print()

            if isinstance(haiku_acc, (int, float)) and isinstance(sonnet_acc, (int, float)):
                accuracy_diff = abs(sonnet_acc - haiku_acc)
                if accuracy_diff < 0.05:
                    print("Recommendation: Haiku provides similar accuracy at much lower cost")
                elif sonnet_acc > haiku_acc:
                    print(f"Recommendation: Sonnet provides {accuracy_diff:.1%} better accuracy - consider if worth the extra cost")
                else:
                    print("Recommendation: Haiku outperforms Sonnet - clear winner")

        return any(data['success'] for data in results.values())

    except Exception as e:
        print(f"Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Visual Validation Model Comparison")
    print("Testing: Haiku vs Sonnet for complex visual reasoning tasks")
    print("=" * 70)

    success = test_visual_validation_comparison()

    if success:
        print(f"\n[SUCCESS] Visual validation comparison completed!")
        print("This test shows which model is better for complex visual reasoning tasks.")
    else:
        print(f"\n[FAILED] Visual validation comparison failed")