#!/usr/bin/env python3
"""
Direct model comparison using ClaudeService
Tests Haiku vs Sonnet performance on extraction tasks
"""

import json
import os
import time
from services.claude_service import ClaudeService
from model_configs import get_model_for_task

def test_direct_model_comparison():
    """Direct comparison of Claude models for data extraction"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # Test prompt for extraction
    test_prompt = """
Extract the following information from this employee profile text:
- Employee_Name: The person's full name
- Position: Job position (may be blank)
- Employee_Type: Employment type (may be blank)
- Title: Job title (may be blank)

**IMPORTANT**: If a field appears in the document but is blank/empty, return an empty string "" for that field.

Text to extract from:
Employee Profile
Caroline Jones
Emp Id 4632 Status A Emp Type Home # 509-121-3247
Position Statutory 0.00 Work #
Title Seasonal 0.00 Ext.

Return the result as valid JSON only:
"""

    # Test different models
    models_to_test = [
        ('claude-3-5-haiku-20241022', 'Claude 3.5 Haiku'),
        ('claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet')
    ]

    results = {}

    for model_id, model_name in models_to_test:
        print(f"\n{'='*50}")
        print(f"Testing: {model_name}")
        print(f"Model ID: {model_id}")
        print('='*50)

        try:
            # Create Claude service
            claude_service = ClaudeService(api_key)

            # Time the extraction
            start_time = time.time()

            # Make direct API call
            response = claude_service.extract_data_with_claude(
                extraction_prompt=test_prompt,
                model_name=model_id
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Parse response
            success = response.get('success', False)
            extracted_data = response.get('extracted_data', {})
            error = response.get('error')

            # Store results
            results[model_id] = {
                'model_name': model_name,
                'success': success,
                'processing_time': processing_time,
                'extracted_data': extracted_data,
                'error': error
            }

            # Print results
            print(f"Success: {success}")
            print(f"Processing Time: {processing_time:.2f} seconds")

            if success and extracted_data:
                print(f"Extracted Data: {json.dumps(extracted_data, indent=2)}")

                # Check blank field handling
                position = extracted_data.get('Position', 'NOT_FOUND')
                emp_type = extracted_data.get('Employee_Type', 'NOT_FOUND')
                title = extracted_data.get('Title', 'NOT_FOUND')

                print(f"\nBlank Field Analysis:")
                print(f"  Position: '{position}' {'[CORRECT]' if position == '' else '[NEEDS_FIX]'}")
                print(f"  Employee_Type: '{emp_type}' {'[CORRECT]' if emp_type == '' else '[NEEDS_FIX]'}")
                print(f"  Title: '{title}' {'[CORRECT]' if title == '' else '[NEEDS_FIX]'}")

                # Score blank field handling
                blank_score = 0
                if position == "": blank_score += 1
                if emp_type == "": blank_score += 1
                if title == "": blank_score += 1

                print(f"  Blank field accuracy: {blank_score}/3 ({blank_score/3*100:.1f}%)")

                # Check if name extraction works
                name = extracted_data.get('Employee_Name', '')
                print(f"  Employee_Name: '{name}' {'[CORRECT]' if 'Caroline Jones' in name else '[NEEDS_FIX]'}")

            else:
                print(f"Error: {error}")

        except Exception as e:
            print(f"Test failed: {e}")
            results[model_id] = {
                'model_name': model_name,
                'success': False,
                'processing_time': 0,
                'extracted_data': {},
                'error': str(e)
            }

    # Generate comparison report
    print(f"\n{'='*60}")
    print("CLAUDE MODEL PERFORMANCE COMPARISON")
    print('='*60)

    print("\n[PERFORMANCE SUMMARY]:")
    print("-" * 25)
    for model_id, data in results.items():
        print(f"{data['model_name']}:")
        print(f"  Model ID: {model_id}")
        print(f"  Success: {'YES' if data['success'] else 'NO'}")
        print(f"  Time: {data['processing_time']:.2f}s")
        if data['success'] and data['extracted_data']:
            # Calculate accuracy
            extracted = data['extracted_data']
            accuracy_score = 0
            total_checks = 4

            if extracted.get('Employee_Name') and 'Caroline Jones' in extracted.get('Employee_Name', ''):
                accuracy_score += 1
            if extracted.get('Position') == '':
                accuracy_score += 1
            if extracted.get('Employee_Type') == '':
                accuracy_score += 1
            if extracted.get('Title') == '':
                accuracy_score += 1

            print(f"  Accuracy: {accuracy_score}/{total_checks} ({accuracy_score/total_checks*100:.1f}%)")
        elif not data['success']:
            print(f"  Error: {data['error']}")
        print()

    # Speed comparison
    successful_results = [(model_id, data) for model_id, data in results.items() if data['success']]
    if successful_results:
        print("[SPEED RANKING]:")
        print("-" * 15)
        speed_ranking = sorted(successful_results, key=lambda x: x[1]['processing_time'])
        for i, (model_id, data) in enumerate(speed_ranking, 1):
            print(f"{i}. {data['model_name']}: {data['processing_time']:.2f}s")

    # Accuracy comparison
    if successful_results:
        print(f"\n[ACCURACY RANKING]:")
        print("-" * 18)
        accuracy_ranking = []
        for model_id, data in successful_results:
            extracted = data['extracted_data']
            accuracy_score = 0
            if extracted.get('Employee_Name') and 'Caroline Jones' in extracted.get('Employee_Name', ''):
                accuracy_score += 1
            if extracted.get('Position') == '':
                accuracy_score += 1
            if extracted.get('Employee_Type') == '':
                accuracy_score += 1
            if extracted.get('Title') == '':
                accuracy_score += 1
            accuracy_ranking.append((model_id, data, accuracy_score))

        accuracy_ranking.sort(key=lambda x: x[2], reverse=True)
        for i, (model_id, data, score) in enumerate(accuracy_ranking, 1):
            print(f"{i}. {data['model_name']}: {score}/4 ({score/4*100:.1f}%)")

    # Cost analysis
    print(f"\n[COST ANALYSIS]:")
    print("-" * 15)
    print("Haiku: Lower cost (~60% cheaper than Sonnet)")
    print("Sonnet: Higher accuracy, better reasoning")
    print("For high-volume processing: Haiku can provide significant cost savings")
    print("For critical accuracy: Sonnet is recommended")

    return any(data['success'] for data in results.values())

if __name__ == "__main__":
    print("Direct Claude Model Performance Test")
    print("Testing: Haiku vs Sonnet for text extraction")
    print("=" * 50)

    success = test_direct_model_comparison()

    if success:
        print(f"\n[SUCCESS] Model comparison completed!")
        print("Use the results above to choose the best model for your use case.")
    else:
        print(f"\n[FAILED] All models failed")