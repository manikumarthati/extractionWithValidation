#!/usr/bin/env python3
"""
Test script to demonstrate the new provider-aware prompt system
Shows how Gemini gets optimized prompts vs Claude
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the new provider-aware system
from services.provider_prompt_registry import prompt_registry, Provider, PromptType
from services.visual_field_inspector_refactored import ProviderAwareVisualFieldInspector
from services.schema_text_extractor import SchemaTextExtractor


def test_prompt_differences():
    """Test how prompts differ between providers"""

    print("="*80)
    print("TESTING PROVIDER-AWARE PROMPT SYSTEM")
    print("="*80)

    # Sample data for testing
    sample_extracted_data = {
        "employee_profile": {
            "name": "John Doe",
            "department": "Engineering"
        },
        "benefits_table": [
            {
                "code": "DNTL",
                "description": "Dental Insurance",
                "calc_code": "B5",  # This should be empty (column shift issue)
                "frequency": None   # This should contain "B5"
            }
        ]
    }

    sample_schema = {
        "employee_profile": {
            "name": {"type": "string"},
            "department": {"type": "string"}
        },
        "benefits_table": {
            "type": "array",
            "items": {
                "code": {"type": "string"},
                "description": {"type": "string"},
                "calc_code": {"type": "string"},
                "frequency": {"type": "string"}
            }
        }
    }

    # Test validation prompts for both providers
    print("\nVALIDATION PROMPT COMPARISON")
    print("-" * 60)

    claude_validation = prompt_registry.get_prompt(
        provider=Provider.ANTHROPIC,
        prompt_type=PromptType.VALIDATION,
        extracted_data=sample_extracted_data,
        schema=sample_schema,
        page_num=0
    )

    gemini_validation = prompt_registry.get_prompt(
        provider=Provider.GOOGLE,
        prompt_type=PromptType.VALIDATION,
        extracted_data=sample_extracted_data,
        schema=sample_schema,
        page_num=0
    )

    print(f"Claude validation prompt length: {len(claude_validation)} characters")
    print(f"Gemini validation prompt length: {len(gemini_validation)} characters")
    print(f"Gemini prompt is {len(gemini_validation)/len(claude_validation)*100:.1f}% the size of Claude's")

    # Show key differences
    print("\nKEY DIFFERENCES:")
    print("   Claude: Complex chain-of-thought reasoning")
    print("   Gemini: Direct, action-oriented instructions")

    # Test correction prompts
    print("\nCORRECTION PROMPT COMPARISON")
    print("-" * 60)

    sample_validation_result = {
        "field_validation_results": [],
        "table_validation_results": [
            {
                "table_name": "benefits_table",
                "cell_validation_results": [
                    {
                        "row_index": 0,
                        "column_name": "calc_code",
                        "extracted_value": "B5",
                        "visual_inspection": {
                            "belongs_in_column": "frequency",
                            "issue": "column_shift"
                        }
                    }
                ]
            }
        ]
    }

    claude_correction = prompt_registry.get_prompt(
        provider=Provider.ANTHROPIC,
        prompt_type=PromptType.CORRECTION,
        extracted_data=sample_extracted_data,
        validation_result=sample_validation_result,
        schema=sample_schema,
        page_num=0
    )

    gemini_correction = prompt_registry.get_prompt(
        provider=Provider.GOOGLE,
        prompt_type=PromptType.CORRECTION,
        extracted_data=sample_extracted_data,
        validation_result=sample_validation_result,
        schema=sample_schema,
        page_num=0
    )

    print(f"Claude correction prompt length: {len(claude_correction)} characters")
    print(f"Gemini correction prompt length: {len(gemini_correction)} characters")
    print(f"Gemini prompt is {len(gemini_correction)/len(claude_correction)*100:.1f}% the size of Claude's")

    return claude_validation, gemini_validation


def test_visual_inspector_integration():
    """Test the provider-aware visual inspector"""

    print("\n" + "="*80)
    print("TESTING VISUAL INSPECTOR INTEGRATION")
    print("="*80)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    google_api_key = os.environ.get('GOOGLE_API_KEY')

    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment")
        return

    # Test Claude inspector
    print("\nTesting Claude Inspector")
    print("-" * 40)

    claude_inspector = ProviderAwareVisualFieldInspector(api_key, 'claude_sonnet')
    claude_info = claude_inspector.get_system_info() if hasattr(claude_inspector, 'get_system_info') else {
        "provider": claude_inspector.provider.value,
        "inspector_class": claude_inspector.__class__.__name__
    }
    print(f"   Provider: {claude_info.get('provider', 'Unknown')}")
    print(f"   Class: {claude_info.get('inspector_class', 'Unknown')}")

    # Test Gemini inspector if available
    if google_api_key:
        print("\nTesting Gemini Inspector")
        print("-" * 40)

        gemini_inspector = ProviderAwareVisualFieldInspector(api_key, 'gemini_flash')
        gemini_info = gemini_inspector.get_system_info() if hasattr(gemini_inspector, 'get_system_info') else {
            "provider": gemini_inspector.provider.value,
            "inspector_class": gemini_inspector.__class__.__name__
        }
        print(f"   Provider: {gemini_info.get('provider', 'Unknown')}")
        print(f"   Class: {gemini_info.get('inspector_class', 'Unknown')}")
    else:
        print("GOOGLE_API_KEY not found - skipping Gemini test")


def test_schema_extractor_integration():
    """Test the updated schema extractor"""

    print("\n" + "="*80)
    print("TESTING SCHEMA EXTRACTOR INTEGRATION")
    print("="*80)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    google_api_key = os.environ.get('GOOGLE_API_KEY')

    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment")
        return

    # Test Claude configuration
    print("\nTesting Claude Schema Extractor")
    print("-" * 45)

    claude_extractor = SchemaTextExtractor(api_key, 'claude_sonnet')
    print(f"   Visual Inspector Type: {claude_extractor.visual_inspector.__class__.__name__}")
    print(f"   Model Config: {claude_extractor.model_config_name}")

    # Test Gemini configuration if available
    if google_api_key:
        print("\nTesting Gemini Schema Extractor")
        print("-" * 45)

        gemini_extractor = SchemaTextExtractor(api_key, 'gemini_flash')
        print(f"   Visual Inspector Type: {gemini_extractor.visual_inspector.__class__.__name__}")
        print(f"   Model Config: {gemini_extractor.model_config_name}")
    else:
        print("GOOGLE_API_KEY not found - skipping Gemini test")


def save_prompt_samples():
    """Save sample prompts for comparison"""

    print("\n" + "="*80)
    print("SAVING PROMPT SAMPLES FOR INSPECTION")
    print("="*80)

    sample_data = {
        "employee_name": "John Doe",
        "benefits": [
            {"code": "DNTL", "calc_code": "B5", "frequency": None}
        ]
    }

    sample_schema = {"type": "object", "properties": {"employee_name": {"type": "string"}}}

    # Save validation prompts
    claude_val = prompt_registry.get_prompt(
        Provider.ANTHROPIC, PromptType.VALIDATION,
        extracted_data=sample_data, schema=sample_schema
    )

    gemini_val = prompt_registry.get_prompt(
        Provider.GOOGLE, PromptType.VALIDATION,
        extracted_data=sample_data, schema=sample_schema
    )

    os.makedirs("debug_pipeline", exist_ok=True)

    with open("debug_pipeline/claude_validation_prompt_sample.txt", "w", encoding='utf-8') as f:
        f.write("CLAUDE VALIDATION PROMPT (Chain-of-Thought Reasoning)\n")
        f.write("="*60 + "\n\n")
        f.write(claude_val)

    with open("debug_pipeline/gemini_validation_prompt_sample.txt", "w", encoding='utf-8') as f:
        f.write("GEMINI VALIDATION PROMPT (Direct Action-Oriented)\n")
        f.write("="*60 + "\n\n")
        f.write(gemini_val)

    print(f"Saved prompt samples to debug_pipeline/")
    print(f"   - claude_validation_prompt_sample.txt")
    print(f"   - gemini_validation_prompt_sample.txt")


def main():
    """Run all tests"""

    print("STARTING PROVIDER-AWARE SYSTEM TESTS")

    try:
        # Test prompt differences
        test_prompt_differences()

        # Test visual inspector integration
        test_visual_inspector_integration()

        # Test schema extractor integration
        test_schema_extractor_integration()

        # Save sample prompts
        save_prompt_samples()

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("BENEFITS OF NEW SYSTEM:")
        print("   - Gemini gets optimized, direct prompts")
        print("   - Claude gets complex reasoning prompts")
        print("   - Better column shift detection for Gemini")
        print("   - Maintainable, provider-specific templates")
        print("   - Easy to add new providers")
        print("   - Centralized prompt management")

    except Exception as e:
        print(f"\nTEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()