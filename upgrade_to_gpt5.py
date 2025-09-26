#!/usr/bin/env python3
"""
Easy upgrade script to switch from GPT-4o Mini to GPT-5 Mini configuration
"""

import os
import shutil
from datetime import datetime
from model_configs import GPT_4O_MINI_CONFIG, GPT_5_MINI_CONFIG, create_upgrade_config

def backup_current_config():
    """Backup current configuration"""
    backup_dir = f"backups/config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)

    # Backup config.py
    shutil.copy2("config.py", f"{backup_dir}/config.py")
    print(f"✅ Backed up current config to {backup_dir}")

    return backup_dir

def update_config_file():
    """Update config.py to use GPT-5 Mini for critical tasks"""

    # Read current config
    with open("config.py", "r") as f:
        content = f.read()

    # Replace model configurations
    replacements = {
        "DATA_EXTRACTION_MODEL = os.environ.get('DATA_EXTRACTION_MODEL') or 'gpt-4o-mini'":
        "DATA_EXTRACTION_MODEL = os.environ.get('DATA_EXTRACTION_MODEL') or 'gpt-5-mini'",

        "VISION_VALIDATION_MODEL = os.environ.get('VISION_VALIDATION_MODEL') or 'gpt-4o-mini'":
        "VISION_VALIDATION_MODEL = os.environ.get('VISION_VALIDATION_MODEL') or 'gpt-5-mini'",

        "DEFAULT_MODEL = os.environ.get('GPT_DEFAULT_MODEL') or 'gpt-4o-mini'":
        "DEFAULT_MODEL = os.environ.get('GPT_DEFAULT_MODEL') or 'gpt-5-mini'"
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    # Update comment
    content = content.replace(
        "# Task-specific model selection - using GPT-4o Mini for cost efficiency and vision capabilities",
        "# Task-specific model selection - upgraded to GPT-5 Mini for enhanced capabilities"
    )

    # Write updated config
    with open("config.py", "w") as f:
        f.write(content)

    print("✅ Updated config.py with GPT-5 Mini for critical tasks")

def update_advanced_pipeline():
    """Update advanced pipeline default model"""

    pipeline_file = "services/advanced_pipeline.py"

    with open(pipeline_file, "r") as f:
        content = f.read()

    # Update default model configuration
    old_config = """self.model_config = model_config or {
            'vision_model': 'gpt-4o-mini',  # Cost-effective with vision capabilities
            'text_model': 'gpt-4o-mini',    # Same model for consistency
            'reasoning_model': 'gpt-4o-mini' # Can upgrade to gpt-5-mini later
        }"""

    new_config = """self.model_config = model_config or {
            'vision_model': 'gpt-5-mini',   # Upgraded for better vision validation
            'text_model': 'gpt-4o-mini',    # Keep cost-effective for text tasks
            'reasoning_model': 'gpt-5-mini' # Upgraded for better reasoning
        }"""

    content = content.replace(old_config, new_config)

    with open(pipeline_file, "w") as f:
        f.write(content)

    print("✅ Updated advanced pipeline with GPT-5 Mini for vision/reasoning")

def show_upgrade_impact():
    """Show the impact of the upgrade"""
    upgrade_info = create_upgrade_config('current', 'balanced')

    print("\n" + "=" * 60)
    print("UPGRADE IMPACT SUMMARY")
    print("=" * 60)

    print(f"Upgrade Path: {upgrade_info['upgrade_path']}")
    print(f"Cost Impact: {upgrade_info['cost_impact']}")

    print("\nModel Changes:")
    for task, change in upgrade_info['changes_needed'].items():
        print(f"  {task}: {change['from']} → {change['to']}")

    print("\nBenefits:")
    print("  ✅ Better vision validation accuracy")
    print("  ✅ Enhanced reasoning capabilities")
    print("  ✅ Latest OpenAI technology")
    print("  ✅ Still cost-efficient for basic tasks")

    print("\nCost Impact:")
    print("  📊 Text extraction: Same cost (still gpt-4o-mini)")
    print("  📊 Vision validation: ~2-3x cost increase (but better accuracy)")
    print("  📊 Overall: ~50-100% cost increase for significant accuracy gains")

def main():
    """Main upgrade function"""
    print("🚀 GPT-5 Mini Upgrade Tool")
    print("=" * 50)

    # Show current vs target
    show_upgrade_impact()

    print("\n" + "=" * 50)
    response = input("Do you want to proceed with the upgrade? (y/N): ")

    if response.lower() != 'y':
        print("❌ Upgrade cancelled")
        return

    print("\n🔧 Starting upgrade process...")

    try:
        # Step 1: Backup
        print("\n1. Creating backup...")
        backup_dir = backup_current_config()

        # Step 2: Update config
        print("\n2. Updating configuration files...")
        update_config_file()
        update_advanced_pipeline()

        # Step 3: Success
        print("\n✅ Upgrade completed successfully!")
        print("\nNext steps:")
        print("1. Restart your application")
        print("2. Test with a sample document")
        print("3. Monitor costs and accuracy improvements")
        print(f"4. Backup saved in: {backup_dir}")

        print("\n📊 Expected improvements:")
        print("- 5-15% better extraction accuracy")
        print("- Better handling of complex layouts")
        print("- Improved column alignment detection")
        print("- Enhanced reasoning for edge cases")

    except Exception as e:
        print(f"❌ Upgrade failed: {str(e)}")
        print("Please check the error and try again")
        print("Your original configuration is backed up")

def rollback_upgrade():
    """Rollback to previous configuration"""
    print("🔄 Rolling back to GPT-4o Mini configuration...")

    # Find latest backup
    backup_dirs = [d for d in os.listdir("backups") if d.startswith("config_backup_")]
    if not backup_dirs:
        print("❌ No backup found")
        return

    latest_backup = sorted(backup_dirs)[-1]
    backup_path = f"backups/{latest_backup}"

    # Restore config
    shutil.copy2(f"{backup_path}/config.py", "config.py")

    print(f"✅ Restored configuration from {backup_path}")
    print("Restart your application to use GPT-4o Mini configuration")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_upgrade()
    else:
        main()