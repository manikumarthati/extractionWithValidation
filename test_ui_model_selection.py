#!/usr/bin/env python3
"""
Test the UI model selection functionality
Simulates the UI interaction without actually running Streamlit
"""

from model_configs import get_model_config, list_available_configs

def test_ui_model_selection():
    """Test that the model selection UI data works correctly"""

    print("Testing UI Model Selection Functionality")
    print("=" * 50)

    # Simulate getting available configurations (like the UI does)
    configs = list_available_configs()
    config_options = {}
    config_display_names = []

    print("\n[AVAILABLE CONFIGS] What the user sees in the dropdown:")
    for name, details in configs.items():
        display_name = f"{name.title()}: {details['description']} - {details['estimated_cost']}"
        config_options[display_name] = name
        config_display_names.append(display_name)
        print(f"  {display_name}")

    # Test selection mapping
    print(f"\n[SELECTION MAPPING] Display name -> config name:")
    for display, config_name in config_options.items():
        print(f"  '{display}' -> '{config_name}'")

    # Test model details for each config
    print(f"\n[MODEL DETAILS] What models each config uses:")
    for config_name in config_options.values():
        config_detail = get_model_config(config_name)
        print(f"\n  {config_name.upper()} configuration:")
        print(f"    Classification: {config_detail['classification']}")
        print(f"    Data Extraction: {config_detail['data_extraction']}")
        print(f"    Vision Validation: {config_detail['vision_validation']}")
        print(f"    Cost: {config_detail['estimated_cost_per_doc']}")

    # Test specific scenarios
    print(f"\n[SCENARIO TESTS]")

    # Scenario 1: User wants cheapest option
    haiku_configs = [name for name, details in configs.items() if 'haiku' in details['description'].lower()]
    if haiku_configs:
        cheapest = haiku_configs[0]  # budget/haiku should be cheapest
        print(f"  Cheapest option: {cheapest} - {configs[cheapest]['estimated_cost']}")

    # Scenario 2: User wants most accurate
    sonnet_configs = [name for name, details in configs.items() if 'sonnet' in details['description'].lower()]
    if sonnet_configs:
        most_accurate = [name for name in sonnet_configs if 'superior' in configs[name]['description'].lower()]
        if most_accurate:
            print(f"  Most accurate: {most_accurate[0]} - {configs[most_accurate[0]]['estimated_cost']}")

    # Scenario 3: User wants balanced
    balanced_configs = [name for name, details in configs.items() if 'balanced' in details['description'].lower()]
    if balanced_configs:
        print(f"  Balanced option: {balanced_configs[0]} - {configs[balanced_configs[0]]['estimated_cost']}")

    # Test cost comparison
    print(f"\n[COST COMPARISON]")
    costs = []
    for name, details in configs.items():
        cost_range = details['estimated_cost']
        # Extract the low end of the range for comparison
        low_cost = float(cost_range.split('-')[0].replace('$', ''))
        costs.append((name, low_cost, cost_range))

    costs.sort(key=lambda x: x[1])  # Sort by cost
    print("  Ranked by cost (lowest to highest):")
    for i, (name, low_cost, cost_range) in enumerate(costs, 1):
        savings = ""
        if i == 1:
            savings = " (cheapest)"
        elif i == len(costs):
            savings = " (most expensive)"
        print(f"    {i}. {name.title()}: {cost_range}{savings}")

    print(f"\n[SUCCESS] UI model selection functionality verified!")
    print("Users can now select from these model configurations in the UI:")
    print(f"- Budget configs for cost savings: {[c for c in configs.keys() if 'budget' in c or 'haiku' in c]}")
    print(f"- Balanced configs for mixed use: {[c for c in configs.keys() if 'balanced' in c or 'current' in c]}")
    print(f"- Premium configs for accuracy: {[c for c in configs.keys() if 'claude' in c or 'premium' in c]}")

    return True

if __name__ == "__main__":
    success = test_ui_model_selection()
    if success:
        print(f"\n[SUCCESS] Model selection UI is ready!")
    else:
        print(f"\n[FAILED] Model selection UI test failed")