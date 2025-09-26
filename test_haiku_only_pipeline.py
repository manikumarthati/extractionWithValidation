#!/usr/bin/env python3
"""
Test the pipeline using Haiku for all tasks
"""

import json
import os
from services.advanced_pipeline import AdvancedPDFExtractionPipeline

def test_haiku_only_pipeline():
    """Test pipeline with Haiku-only configuration"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # PDF path and schema
    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_1.pdf"
    schema_path = "D:/learning/stepwisePdfParsing/employee_profile_hierarchical_schema.json"

    try:
        # Load schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        print("Testing Pipeline with HAIKU-ONLY Configuration")
        print("=" * 55)
        print("All tasks will use: claude-3-5-haiku-20241022")
        print("Expected cost savings: 60-80% compared to Sonnet")
        print()

        # Create pipeline with budget config (Haiku-only)
        pipeline = AdvancedPDFExtractionPipeline(api_key, model_config_name='budget')

        # Show which models will be used
        from model_configs import get_model_for_task
        print("Model assignments:")
        tasks = ['classification', 'field_identification', 'data_extraction', 'vision_validation', 'reasoning']
        for task in tasks:
            model = get_model_for_task(task, 'budget')
            print(f"  {task}: {model}")
        print()

        # Run the pipeline
        print("Running extraction...")
        result = pipeline.process_document(
            pdf_path=pdf_path,
            schema=schema,
            page_num=0,
            max_rounds=2,
            target_accuracy=0.85
        )

        # Show results
        if result.get('success'):
            workflow = result.get('workflow_summary', {})
            print("\n[SUCCESS] Haiku-only pipeline results:")
            print(f"Text Extraction Success: {workflow.get('text_extraction_success')}")
            print(f"Validation Success: {workflow.get('validation_success')}")
            print(f"Final Accuracy: {workflow.get('final_accuracy')}")
            print(f"Validation Rounds: {workflow.get('validation_rounds_completed', 0)}")
            print(f"Corrections Applied: {workflow.get('total_corrections_applied', 0)}")

            # Cost estimate
            print(f"\nEstimated cost: $0.05-0.12 per document")
            print(f"Cost savings vs Sonnet: 60-80%")

            return True
        else:
            print(f"\n[FAILED] Pipeline error: {result.get('error')}")
            return False

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_haiku_only_pipeline()
    if success:
        print("\n[SUCCESS] Haiku-only pipeline test completed!")
    else:
        print("\n[FAILED] Haiku-only pipeline test failed")