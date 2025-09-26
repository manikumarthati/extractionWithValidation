"""
Model configuration presets for easy switching between different Claude models
Allows for cost optimization and performance tuning based on task requirements
"""

# Current configuration: Claude 3.5 Haiku for cost-effective tasks, Sonnet for accuracy
CLAUDE_BALANCED_CONFIG = {
    'classification': 'claude-3-5-haiku-20241022',
    'field_identification': 'claude-3-5-sonnet-20241022',
    'data_extraction': 'claude-3-5-sonnet-20241022',
    'vision_validation': 'claude-3-5-sonnet-20241022',
    'reasoning': 'claude-3-5-sonnet-20241022',
    'description': 'Balanced configuration using Claude 3.5 Haiku and Sonnet',
    'estimated_cost_per_doc': '$0.08-0.15',
    'features': ['Vision capabilities', 'Cost-effective', 'Excellent performance', 'Better reasoning']
}

# Claude 3.5 Sonnet configuration: Superior document processing
CLAUDE_SONNET_CONFIG = {
    'classification': 'claude-3-5-sonnet-20241022',
    'field_identification': 'claude-3-5-sonnet-20241022',
    'data_extraction': 'claude-3-5-sonnet-20241022',
    'vision_validation': 'claude-3-5-sonnet-20241022',
    'reasoning': 'claude-3-5-sonnet-20241022',
    'description': 'Claude 3.5 Sonnet for superior document accuracy',
    'estimated_cost_per_doc': '$0.12-0.25',
    'features': ['Superior accuracy', 'Better table reasoning', 'Excellent schema compliance', 'Vision + text']
}

# Budget configuration: Claude 3.5 Haiku only
CLAUDE_HAIKU_CONFIG = {
    'classification': 'claude-3-5-haiku-20241022',
    'field_identification': 'claude-3-5-haiku-20241022',
    'data_extraction': 'claude-3-5-haiku-20241022',
    'vision_validation': 'claude-3-5-haiku-20241022',
    'reasoning': 'claude-3-5-haiku-20241022',
    'description': 'Budget configuration using only Claude 3.5 Haiku',
    'estimated_cost_per_doc': '$0.05-0.12',
    'features': ['Maximum cost savings', 'Fast processing', 'Good performance', 'Vision capabilities']
}

# Premium configuration: Claude Opus for maximum accuracy
CLAUDE_OPUS_CONFIG = {
    'classification': 'claude-3-5-haiku-20241022',      # Still cost-effective for simple tasks
    'field_identification': 'claude-3-5-sonnet-20241022', # Good balance for medium complexity
    'data_extraction': 'claude-3-opus-20240229',       # Best for critical extraction
    'vision_validation': 'claude-3-opus-20240229',     # Best vision + reasoning
    'reasoning': 'claude-3-opus-20240229',             # Maximum reasoning power
    'description': 'Premium configuration for maximum accuracy with Claude Opus',
    'estimated_cost_per_doc': '$0.25-0.50',
    'features': ['Maximum accuracy', 'Best reasoning', 'Premium vision', 'Higher cost']
}

# Available configurations
AVAILABLE_CONFIGS = {
    'budget': CLAUDE_HAIKU_CONFIG,
    'haiku': CLAUDE_HAIKU_CONFIG,  # Alias for budget
    'haiku_only': CLAUDE_HAIKU_CONFIG,  # Clear naming
    'current': CLAUDE_BALANCED_CONFIG,
    'claude': CLAUDE_SONNET_CONFIG,
    'balanced': CLAUDE_BALANCED_CONFIG,
    'premium': CLAUDE_OPUS_CONFIG
}

def get_model_config(config_name: str = 'current') -> dict:
    """Get model configuration by name"""
    return AVAILABLE_CONFIGS.get(config_name, CLAUDE_BALANCED_CONFIG)

def get_model_for_task(task: str, config_name: str = 'current') -> str:
    """Get specific model for a task"""
    config = get_model_config(config_name)
    return config.get(task, 'claude-3-5-sonnet-20241022')

def list_available_configs() -> dict:
    """List all available configurations with details"""
    result = {}
    for name, config in AVAILABLE_CONFIGS.items():
        result[name] = {
            'description': config['description'],
            'estimated_cost': config['estimated_cost_per_doc'],
            'features': config['features']
        }
    return result

def switch_to_claude_sonnet():
    """Easy function to switch to Claude 3.5 Sonnet configuration"""
    return CLAUDE_SONNET_CONFIG

def get_cost_comparison():
    """Get cost comparison between configurations"""
    return {
        'Budget (Claude Haiku only)': '$0.05-0.12 per document',
        'Current (Claude Balanced)': '$0.08-0.15 per document',
        'Claude (Sonnet all tasks)': '$0.12-0.25 per document',
        'Premium (Opus for critical)': '$0.25-0.50 per document'
    }

# Easy upgrade path
def create_upgrade_config(current_config: str, target_config: str) -> dict:
    """Create an upgrade path between configurations"""
    current = get_model_config(current_config)
    target = get_model_config(target_config)

    changes = {}
    for task in current:
        if task in target and current[task] != target[task]:
            changes[task] = {
                'from': current[task],
                'to': target[task]
            }

    return {
        'changes_needed': changes,
        'upgrade_path': f"{current_config} -> {target_config}",
        'cost_impact': f"{current['estimated_cost_per_doc']} -> {target['estimated_cost_per_doc']}"
    }

if __name__ == "__main__":
    # Demo the configurations
    print("Available Claude Model Configurations:")
    print("=" * 50)

    for name, details in list_available_configs().items():
        print(f"\n{name.upper()}:")
        print(f"  Description: {details['description']}")
        print(f"  Cost: {details['estimated_cost']}")
        print(f"  Features: {', '.join(details['features'])}")

    print("\n" + "=" * 50)
    print("Cost Comparison:")
    for config, cost in get_cost_comparison().items():
        print(f"  {config}: {cost}")

    print("\n" + "=" * 50)
    print("Upgrade Path (current -> claude):")
    upgrade = create_upgrade_config('current', 'claude')
    print(f"  Path: {upgrade['upgrade_path']}")
    print(f"  Cost: {upgrade['cost_impact']}")
    print("  Changes needed:")
    for task, change in upgrade['changes_needed'].items():
        print(f"    {task}: {change['from']} -> {change['to']}")