#!/usr/bin/env python3
"""
Set environment variables to use Haiku for all tasks
"""

import os

# Set all Claude models to Haiku
os.environ['CLASSIFICATION_MODEL'] = 'claude-3-5-haiku-20241022'
os.environ['FIELD_IDENTIFICATION_MODEL'] = 'claude-3-5-haiku-20241022'
os.environ['DATA_EXTRACTION_MODEL'] = 'claude-3-5-haiku-20241022'
os.environ['VISION_VALIDATION_MODEL'] = 'claude-3-5-haiku-20241022'
os.environ['CLAUDE_DEFAULT_MODEL'] = 'claude-3-5-haiku-20241022'

print("Environment variables set to use Haiku for all tasks:")
print(f"CLASSIFICATION_MODEL: {os.environ['CLASSIFICATION_MODEL']}")
print(f"FIELD_IDENTIFICATION_MODEL: {os.environ['FIELD_IDENTIFICATION_MODEL']}")
print(f"DATA_EXTRACTION_MODEL: {os.environ['DATA_EXTRACTION_MODEL']}")
print(f"VISION_VALIDATION_MODEL: {os.environ['VISION_VALIDATION_MODEL']}")
print(f"CLAUDE_DEFAULT_MODEL: {os.environ['CLAUDE_DEFAULT_MODEL']}")

# Test that it works
from services.schema_text_extractor import SchemaTextExtractor
api_key = os.environ.get('ANTHROPIC_API_KEY')
if api_key:
    extractor = SchemaTextExtractor(api_key, 'budget')
    print("\nHaiku-only extractor created successfully!")