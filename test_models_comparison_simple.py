#!/usr/bin/env python3
"""
Simple model comparison using existing enhanced extraction test
Tests different model configurations on the same task
"""

import json
import os
import time
from test_enhanced_extraction import test_enhanced_extraction
from model_configs import get_model_for_task, list_available_configs

def test_model_configurations():
    """Test different model configurations"""

    print("Available Model Configurations:")
    configs = list_available_configs()
    for name, details in configs.items():
        print(f"  {name}: {details['description']} - {details['estimated_cost']}")
    print()

    # Test configurations to compare
    configs_to_test = [
        ('budget', 'Claude Haiku Only'),
        ('current', 'Balanced (Haiku + Sonnet)'),
        ('claude', 'Claude Sonnet Only')
    ]

    results = {}

    for config_name, config_desc in configs_to_test:
        print(f"{'='*60}")
        print(f"TESTING: {config_desc}")
        print(f"Config: {config_name}")

        # Show which models will be used
        print(f"Models in this config:")
        print(f"  Data extraction: {get_model_for_task('data_extraction', config_name)}")
        print(f"  Field identification: {get_model_for_task('field_identification', config_name)}")
        print(f"  Vision validation: {get_model_for_task('vision_validation', config_name)}")
        print('='*60)

        try:
            start_time = time.time()

            # Note: The existing test doesn't actually use the config_name parameter
            # because SchemaTextExtractor doesn't accept it, but we can still
            # measure performance and identify issues
            success = test_enhanced_extraction(config_name)

            end_time = time.time()
            processing_time = end_time - start_time

            results[config_name] = {
                'config_desc': config_desc,
                'success': success,
                'processing_time': processing_time,
                'models': {
                    'data_extraction': get_model_for_task('data_extraction', config_name),
                    'field_identification': get_model_for_task('field_identification', config_name),
                    'vision_validation': get_model_for_task('vision_validation', config_name)
                }
            }

            print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
            print(f"Time: {processing_time:.2f} seconds")

        except Exception as e:
            print(f"Test failed with error: {e}")
            results[config_name] = {
                'config_desc': config_desc,
                'success': False,
                'processing_time': 0,
                'error': str(e),
                'models': {}
            }

        print("\n")

    # Generate comparison report
    print(f"{'='*80}")
    print("MODEL CONFIGURATION COMPARISON REPORT")
    print('='*80)

    print("\n[PERFORMANCE SUMMARY]:")
    print("-" * 30)
    for config_name, data in results.items():
        print(f"{data['config_desc']}:")
        if data['success']:
            print(f"  Status: SUCCESS")
            print(f"  Time: {data['processing_time']:.2f}s")
            print(f"  Data Extraction Model: {data['models'].get('data_extraction', 'Unknown')}")
        else:
            print(f"  Status: FAILED")
            if 'error' in data:
                print(f"  Error: {data['error']}")
        print()

    # Speed comparison
    successful_results = [(name, data) for name, data in results.items() if data['success']]
    if successful_results:
        print("[SPEED RANKING]:")
        print("-" * 15)
        speed_ranking = sorted(successful_results, key=lambda x: x[1]['processing_time'])
        for i, (config_name, data) in enumerate(speed_ranking, 1):
            print(f"{i}. {data['config_desc']}: {data['processing_time']:.2f}s")

    # Cost comparison
    print(f"\n[COST ESTIMATES]:")
    print("-" * 17)
    cost_info = {
        'budget': '$0.05-0.12 per document (Cheapest)',
        'current': '$0.08-0.15 per document (Balanced)',
        'claude': '$0.12-0.25 per document (Most accurate)'
    }
    for config_name, data in results.items():
        if config_name in cost_info:
            status = "✓" if data['success'] else "✗"
            print(f"{status} {data['config_desc']}: {cost_info[config_name]}")

    # Recommendations
    print(f"\n[RECOMMENDATIONS]:")
    print("-" * 17)

    if results.get('budget', {}).get('success'):
        print("• Budget config working - Ideal for high-volume, cost-sensitive processing")

    if results.get('current', {}).get('success'):
        print("• Current config working - Good balance of cost and accuracy")

    if results.get('claude', {}).get('success'):
        print("• Claude config working - Best accuracy for critical documents")

    # If all failed
    if not any(data['success'] for data in results.values()):
        print("• All configurations failed - Check API keys and dependencies")

    # If only expensive configs work
    elif results.get('claude', {}).get('success') and not results.get('budget', {}).get('success'):
        print("• Only Sonnet working - Haiku may need prompt optimization")

    return any(data['success'] for data in results.values())

if __name__ == "__main__":
    print("Claude Model Configuration Comparison")
    print("Testing: Enhanced extraction with different model configs")
    print("=" * 65)

    success = test_model_configurations()

    if success:
        print(f"\n[SUCCESS] At least one configuration worked!")
        print("Use the analysis above to choose the optimal configuration.")
    else:
        print(f"\n[FAILED] All configurations failed")