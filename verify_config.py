#!/usr/bin/env python3
"""
Verify the current model configuration
"""

import os
from model_configs import get_model_config, list_available_configs, get_model_for_task

def verify_current_config():
    """Show the actual current configuration"""

    print("=" * 60)
    print("CURRENT MODEL CONFIGURATION VERIFICATION")
    print("=" * 60)

    # Check API keys
    print("\n[API] API Key Status:")
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')

    print(f"  Anthropic API: {'[OK] Configured' if anthropic_key else '[MISSING] Not found'}")
    print(f"  OpenAI API: {'[OK] Configured' if openai_key else '[MISSING] Not found'}")

    # Current config details
    print(f"\n[CONFIG] Current Configuration Details:")
    current_config = get_model_config('current')

    print(f"  Name: {current_config['description']}")
    print(f"  Cost: {current_config['estimated_cost_per_doc']}")
    print(f"  Features: {', '.join(current_config['features'])}")

    print(f"\n[MODELS] Model Assignments:")
    tasks = ['classification', 'field_identification', 'data_extraction', 'vision_validation', 'reasoning']

    for task in tasks:
        model = get_model_for_task(task, 'current')
        print(f"  {task:<20}: {model}")

    # Show all available configs
    print(f"\n[ALL] All Available Configurations:")
    configs = list_available_configs()

    for name, details in configs.items():
        print(f"\n  {name.upper()}:")
        print(f"    Description: {details['description']}")
        print(f"    Cost: {details['estimated_cost']}")

        # Show model breakdown for this config
        config_detail = get_model_config(name)
        data_model = config_detail.get('data_extraction', 'Unknown')
        vision_model = config_detail.get('vision_validation', 'Unknown')

        if 'haiku' in data_model.lower():
            print(f"    Primary Model: Claude Haiku (Cost-effective)")
        elif 'sonnet' in data_model.lower():
            print(f"    Primary Model: Claude Sonnet (High-accuracy)")
        elif 'opus' in data_model.lower():
            print(f"    Primary Model: Claude Opus (Premium)")
        else:
            print(f"    Primary Model: {data_model}")

    # Recommendations
    print(f"\n[TIPS] Recommendations:")
    print(f"  - For maximum cost savings: Use 'budget' or 'haiku' config")
    print(f"  - For balanced performance: Use 'current' config (recommended)")
    print(f"  - For maximum accuracy: Use 'claude' config")
    print(f"  - For premium quality: Use 'premium' config")

    # How to switch
    print(f"\n[USAGE] How to Switch Configurations:")
    print(f"  pipeline = AdvancedPDFExtractionPipeline(api_key, 'budget')     # Haiku only")
    print(f"  pipeline = AdvancedPDFExtractionPipeline(api_key, 'current')    # Balanced")
    print(f"  pipeline = AdvancedPDFExtractionPipeline(api_key, 'claude')     # Sonnet only")

if __name__ == "__main__":
    verify_current_config()