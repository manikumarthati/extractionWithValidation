#!/usr/bin/env python3
"""
Direct comparison of Haiku vs Sonnet for visual validation
Tests only the vision validation API calls without full pipeline
"""

import json
import os
import time
import base64
from services.claude_service import ClaudeService

def encode_image_to_base64(image_path: str) -> str:
    """Convert image to base64 for vision API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_vision_validation_direct():
    """Direct test of vision validation capabilities"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # Create a test image (use a temp file if available from previous runs)
    test_images = [
        "temp_600dpi_0_1758647068.png",  # Look for existing temp images
        "temp_600dpi_0_1758646404.png",
        "temp_600dpi_0_1758643205.png"
    ]

    image_path = None
    for img in test_images:
        if os.path.exists(img):
            image_path = img
            break

    if not image_path:
        print("No test image found. Please run the pipeline once to generate temp images.")
        return False

    print(f"Using test image: {image_path}")

    # Test data for validation
    test_data = {
        "Employee_Profile": {
            "Basic_Information": {
                "Employee_Details": {
                    "Employee_Name": "Caroline Jones",
                    "Employee_ID": "4632"
                },
                "Employment_Details": {
                    "Position": "Statutory",  # This should be blank
                    "Employee_Type": "Home",  # This should be blank
                    "Title": "Seasonal"       # This should be blank
                }
            }
        }
    }

    # Validation prompt
    validation_prompt = f"""
    You are validating extracted data against a PDF document image.

    Extracted Data:
    {json.dumps(test_data, indent=2)}

    Your task:
    1. Check if "Position", "Employee_Type", and "Title" fields should actually be blank/empty in the document
    2. Look at the visual layout - these fields often appear as labels with no values after them
    3. Identify any fields that appear to have incorrect values

    Look for patterns like:
    - "Position     Statutory 0.00" (Position field is blank, "Statutory" is a different field)
    - "Title       Seasonal 0.00" (Title field is blank, "Seasonal" is a different field)

    Return validation results in JSON format:
    {{
        "validation_results": [
            {{
                "field": "field_name",
                "current_value": "extracted_value",
                "should_be": "correct_value_or_blank",
                "confidence": 0.9,
                "reasoning": "why this correction is needed"
            }}
        ],
        "overall_accuracy": 0.85
    }}
    """

    # Models to test
    models_to_test = [
        ('claude-3-5-haiku-20241022', 'Claude 3.5 Haiku'),
        ('claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet')
    ]

    results = {}

    try:
        # Encode image
        image_base64 = encode_image_to_base64(image_path)

        for model_id, model_name in models_to_test:
            print(f"\n{'='*60}")
            print(f"TESTING VISION VALIDATION: {model_name}")
            print(f"Model: {model_id}")
            print('='*60)

            try:
                # Create Claude service with specific model config
                if 'haiku' in model_id.lower():
                    claude_service = ClaudeService(api_key, 'budget')
                else:
                    claude_service = ClaudeService(api_key, 'claude')

                # Time the validation
                start_time = time.time()

                # Call vision validation
                result = claude_service.validate_with_vision(image_base64, validation_prompt)

                end_time = time.time()
                processing_time = end_time - start_time

                # Parse results
                success = result.get('success', False)
                validation_data = result.get('validation_result', {})

                results[model_id] = {
                    'model_name': model_name,
                    'success': success,
                    'processing_time': processing_time,
                    'validation_data': validation_data,
                    'error': result.get('error') if not success else None
                }

                # Print results
                print(f"Success: {success}")
                print(f"Processing Time: {processing_time:.2f} seconds")

                if success:
                    print(f"Validation Results:")
                    if isinstance(validation_data, dict):
                        if 'validation_results' in validation_data:
                            for item in validation_data['validation_results']:
                                field = item.get('field', 'unknown')
                                current = item.get('current_value', 'unknown')
                                should_be = item.get('should_be', 'unknown')
                                confidence = item.get('confidence', 0)
                                reasoning = item.get('reasoning', 'no reasoning')

                                print(f"  Field: {field}")
                                print(f"    Current: '{current}'")
                                print(f"    Should be: '{should_be}'")
                                print(f"    Confidence: {confidence}")
                                print(f"    Reasoning: {reasoning}")
                                print()

                        overall_accuracy = validation_data.get('overall_accuracy', 'N/A')
                        print(f"  Overall Accuracy Assessment: {overall_accuracy}")
                    else:
                        print(f"  Raw validation data: {validation_data}")

                else:
                    print(f"Error: {result.get('error')}")

            except Exception as e:
                print(f"Test failed: {e}")
                results[model_id] = {
                    'model_name': model_name,
                    'success': False,
                    'processing_time': 0,
                    'error': str(e)
                }

        # Generate comparison report
        print(f"\n{'='*80}")
        print("VISION VALIDATION MODEL COMPARISON")
        print('='*80)

        print("\n[PERFORMANCE SUMMARY]:")
        print("-" * 25)
        for model_id, data in results.items():
            print(f"{data['model_name']}:")
            print(f"  Success: {'YES' if data['success'] else 'NO'}")
            print(f"  Time: {data['processing_time']:.2f}s")

            if data['success']:
                validation_data = data['validation_data']
                if isinstance(validation_data, dict):
                    accuracy = validation_data.get('overall_accuracy', 'N/A')
                    corrections = len(validation_data.get('validation_results', []))
                    print(f"  Accuracy Assessment: {accuracy}")
                    print(f"  Corrections Identified: {corrections}")

                    # Count blank field corrections
                    blank_corrections = 0
                    if 'validation_results' in validation_data:
                        for item in validation_data['validation_results']:
                            if item.get('should_be', '').strip() == '' or 'blank' in item.get('should_be', '').lower():
                                blank_corrections += 1

                    print(f"  Blank Field Corrections: {blank_corrections}")
            else:
                print(f"  Error: {data.get('error', 'Unknown')}")
            print()

        # Speed and accuracy comparison
        successful_results = [(model_id, data) for model_id, data in results.items() if data['success']]

        if len(successful_results) >= 2:
            print("[COMPARISON ANALYSIS]:")
            print("-" * 20)

            haiku_data = None
            sonnet_data = None

            for model_id, data in successful_results:
                if 'haiku' in model_id.lower():
                    haiku_data = data
                elif 'sonnet' in model_id.lower():
                    sonnet_data = data

            if haiku_data and sonnet_data:
                print("Speed Comparison:")
                print(f"  Haiku: {haiku_data['processing_time']:.2f}s")
                print(f"  Sonnet: {sonnet_data['processing_time']:.2f}s")

                speed_diff = haiku_data['processing_time'] - sonnet_data['processing_time']
                if speed_diff < 0:
                    print(f"  Winner: Haiku ({abs(speed_diff):.2f}s faster)")
                else:
                    print(f"  Winner: Sonnet ({speed_diff:.2f}s faster)")

                print("\nAccuracy Comparison:")
                haiku_acc = haiku_data.get('validation_data', {}).get('overall_accuracy', 'N/A')
                sonnet_acc = sonnet_data.get('validation_data', {}).get('overall_accuracy', 'N/A')
                print(f"  Haiku Assessment: {haiku_acc}")
                print(f"  Sonnet Assessment: {sonnet_acc}")

                print("\nCost Comparison:")
                print("  Haiku: ~60-80% cheaper for vision validation")
                print("  Sonnet: Premium pricing but potentially better reasoning")

        # Recommendations
        print(f"\n[RECOMMENDATIONS]:")
        print("-" * 17)

        haiku_success = any('haiku' in model_id.lower() and data['success'] for model_id, data in results.items())
        sonnet_success = any('sonnet' in model_id.lower() and data['success'] for model_id, data in results.items())

        if haiku_success and sonnet_success:
            print("Both models can handle vision validation tasks")
            print("Consider Haiku for cost-sensitive applications")
            print("Consider Sonnet for maximum accuracy requirements")
        elif haiku_success:
            print("Haiku successfully handles vision validation at lower cost")
        elif sonnet_success:
            print("Only Sonnet succeeded - may be needed for complex vision tasks")
        else:
            print("Both models failed - check image quality and prompts")

        return any(data['success'] for data in results.values())

    except Exception as e:
        print(f"Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Direct Vision Validation Model Comparison")
    print("Testing: Haiku vs Sonnet visual reasoning capabilities")
    print("=" * 60)

    success = test_vision_validation_direct()

    if success:
        print(f"\n[SUCCESS] Vision validation comparison completed!")
    else:
        print(f"\n[FAILED] Vision validation comparison failed")