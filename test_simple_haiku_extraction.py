#!/usr/bin/env python3
"""
Simple test of Haiku vs Sonnet for text extraction only
Bypasses the full pipeline to focus on model comparison
"""

import json
import os
import time
from services.schema_text_extractor import SchemaTextExtractor
from model_configs import get_model_for_task

def test_simple_extraction():
    """Test both models with simple text extraction"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # Test schema
    test_schema = {
        "documentSchema": {
            "entityTypes": [
                {
                    "name": "employee_info",
                    "properties": [
                        {
                            "name": "Employee_Name",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Position",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Employee_Type",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Title",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        }
                    ]
                }
            ]
        }
    }

    # Test text - includes blank fields and complete text scenarios
    test_text = """
    Employee Profile
    Caroline Jones
    Emp Id 4632 Status A Emp Type Home # 509-121-3247
    Position Statutory 0.00 Work #
    Title Seasonal 0.00 Ext.
    """

    # Test both model configs
    configs = [
        ('budget', 'Haiku Only'),
        ('current', 'Balanced (Haiku + Sonnet)'),
        ('claude', 'Sonnet Only')
    ]

    results = {}

    for config_name, config_desc in configs:
        print(f"\n{'='*50}")
        print(f"Testing: {config_desc}")
        print(f"Config: {config_name}")
        print('='*50)

        try:
            # Create extractor with specific config
            extractor = SchemaTextExtractor(api_key, config_name)

            # Get the model being used for data extraction
            model_used = get_model_for_task('data_extraction', config_name)
            print(f"Model for data extraction: {model_used}")

            # Time the extraction
            start_time = time.time()

            # Extract with schema
            result = extractor.extract_with_schema_from_text(test_text, test_schema)

            end_time = time.time()
            processing_time = end_time - start_time

            # Store results
            results[config_name] = {
                'config_desc': config_desc,
                'model_used': model_used,
                'success': result.get('success', False),
                'processing_time': processing_time,
                'extracted_data': result.get('extracted_data', {}),
                'error': result.get('error') if not result.get('success') else None
            }

            # Print results
            print(f"Success: {result.get('success')}")
            print(f"Processing Time: {processing_time:.2f} seconds")

            if result.get('success'):
                extracted = result.get('extracted_data', {})
                print(f"Extracted Data: {json.dumps(extracted, indent=2)}")

                # Check blank field handling
                position = extracted.get('Position')
                emp_type = extracted.get('Employee_Type')
                title = extracted.get('Title')

                print(f"Position field: '{position}' (should be blank)")
                print(f"Employee_Type field: '{emp_type}' (should be blank)")
                print(f"Title field: '{title}' (should be blank)")

                # Score blank field handling
                blank_score = 0
                if position == "": blank_score += 1
                if emp_type == "": blank_score += 1
                if title == "": blank_score += 1

                print(f"Blank field accuracy: {blank_score}/3 ({blank_score/3*100:.1f}%)")

            else:
                print(f"Error: {result.get('error')}")

        except Exception as e:
            print(f"Test failed: {e}")
            results[config_name] = {
                'config_desc': config_desc,
                'model_used': 'unknown',
                'success': False,
                'processing_time': 0,
                'extracted_data': {},
                'error': str(e)
            }

    # Generate comparison report
    print(f"\n{'='*60}")
    print("MODEL PERFORMANCE COMPARISON")
    print('='*60)

    print("\n[PERFORMANCE SUMMARY]:")
    print("-" * 25)
    for config_name, data in results.items():
        print(f"{data['config_desc']}:")
        print(f"  Model: {data['model_used']}")
        print(f"  Success: {'YES' if data['success'] else 'NO'}")
        print(f"  Time: {data['processing_time']:.2f}s")
        if not data['success'] and data['error']:
            print(f"  Error: {data['error']}")
        print()

    # Speed ranking
    successful_results = [(name, data) for name, data in results.items() if data['success']]
    if successful_results:
        print("[SPEED RANKING]:")
        print("-" * 15)
        speed_ranking = sorted(successful_results, key=lambda x: x[1]['processing_time'])
        for i, (config_name, data) in enumerate(speed_ranking, 1):
            print(f"{i}. {data['config_desc']}: {data['processing_time']:.2f}s")

    # Cost comparison
    print(f"\n[COST ESTIMATES (per document)]:")
    print("-" * 32)
    cost_estimates = {
        'budget': '$0.05-0.12 (Haiku only)',
        'current': '$0.08-0.15 (Mixed)',
        'claude': '$0.12-0.25 (Sonnet only)'
    }
    for config_name, data in results.items():
        if config_name in cost_estimates:
            print(f"{data['config_desc']}: {cost_estimates[config_name]}")

    return any(data['success'] for data in results.values())

if __name__ == "__main__":
    print("Simple Claude Model Performance Test")
    print("Focus: Text extraction with blank field handling")
    print("=" * 50)

    success = test_simple_extraction()

    if success:
        print(f"\n[SUCCESS] At least one model configuration worked!")
    else:
        print(f"\n[FAILED] All model configurations failed")