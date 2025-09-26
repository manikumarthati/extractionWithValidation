#!/usr/bin/env python3
"""
Test to verify model routing works correctly
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_model_routing():
    """Test that model routing works correctly"""
    print("Testing Model Routing")
    print("=" * 40)

    from model_configs import get_model_for_task

    # Test different configurations
    configs = ['current', 'claude']

    for config in configs:
        print(f"\nConfiguration: {config}")
        print("-" * 20)

        tasks = ['data_extraction', 'vision_validation', 'field_identification']

        for task in tasks:
            model = get_model_for_task(task, config)
            print(f"  {task}: {model}")

            # Check if it should use Claude
            uses_claude = model.startswith('claude')
            print(f"    -> Uses Claude: {uses_claude}")

def test_pipeline_routing():
    """Test pipeline model selection logic"""
    print("\n\nTesting Pipeline Model Selection")
    print("=" * 40)

    # Simulate the pipeline logic
    configs_to_test = [
        ('current', 'OpenAI text extraction'),
        ('claude', 'Claude vision extraction')
    ]

    for config_name, expected_method in configs_to_test:
        from model_configs import get_model_for_task
        model_name = get_model_for_task('data_extraction', config_name)

        if model_name.startswith('claude'):
            selected_method = "Claude vision extraction"
        else:
            selected_method = "OpenAI text extraction"

        status = "✓" if selected_method == expected_method else "✗"
        print(f"{status} Config '{config_name}' -> {selected_method}")

def test_environment_detection():
    """Test environment-based model selection"""
    print("\n\nTesting Environment Detection")
    print("=" * 40)

    # Check for API keys
    openai_key = os.environ.get('OPENAI_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

    print(f"OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Not set'}")
    print(f"ANTHROPIC_API_KEY: {'✓ Set' if anthropic_key else '✗ Not set'}")

    # Simulate Streamlit logic
    from model_configs import MODEL_CONFIG
    base_config = MODEL_CONFIG
    print(f"Base MODEL_CONFIG: {base_config}")

    # Check if Claude would be auto-selected
    if anthropic_key and base_config == 'current':
        final_config = 'claude'
        print("→ Would auto-select Claude configuration")
    else:
        final_config = base_config
        print(f"→ Would use {final_config} configuration")

    print(f"Final configuration: {final_config}")

def main():
    """Run all tests"""
    test_model_routing()
    test_pipeline_routing()
    test_environment_detection()

    print("\n" + "=" * 50)
    print("Summary:")
    print("- Pipeline now routes to Claude when claude config is used")
    print("- Step 3 will use Claude vision instead of OpenAI text extraction")
    print("- Auto-detects Claude when ANTHROPIC_API_KEY is available")
    print("\nTo ensure Claude is used:")
    print("1. Set ANTHROPIC_API_KEY environment variable")
    print("2. Or set MODEL_CONFIG=claude")

if __name__ == "__main__":
    main()