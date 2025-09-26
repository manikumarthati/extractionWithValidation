"""
Unified client manager for Claude models (OpenAI support removed)
"""

import os
import json
from typing import Dict, Any, Optional, Union
# from openai import OpenAI  # Removed - using Claude only
from anthropic import Anthropic
import base64
import logging

import sys
import os
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_configs import get_model_config, get_model_for_task
from claude_client import ClaudeClient

logger = logging.getLogger(__name__)

class ModelClientManager:
    """Claude-only client manager (OpenAI support removed)"""

    def __init__(self,
                 anthropic_api_key: Optional[str] = None,
                 config_name: str = 'current'):
        """Initialize Claude client only - OpenAI support removed"""

        self.anthropic_key = anthropic_api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.config_name = config_name

        # Debug logging
        print(f"ModelClientManager Debug:")
        print(f"  - Anthropic key present: {bool(self.anthropic_key)}")
        print(f"  - Config: {config_name}")
        if self.anthropic_key:
            print(f"  - Anthropic key starts with: {self.anthropic_key[:10]}...")

        # OpenAI support removed - Claude only
        self.openai_client = None

        # Initialize Claude client lazily to avoid initialization conflicts
        self.claude_client = None
        self._claude_initialized = False

    def _ensure_claude_client(self):
        """Initialize Claude client if needed"""
        if not self._claude_initialized:
            print(f"_ensure_claude_client Debug:")
            print(f"  - Anthropic key present: {bool(self.anthropic_key)}")

            if self.anthropic_key:
                try:
                    print(f"  - Attempting to initialize Claude client...")
                    self.claude_client = ClaudeClient(self.anthropic_key)
                    print(f"  - SUCCESS: Claude 3.5 Sonnet client initialized successfully")
                    logger.info("SUCCESS: Claude 3.5 Sonnet client initialized successfully")
                except Exception as e:
                    print(f"  - ERROR: Failed to initialize Claude client: {e}")
                    logger.error(f"ERROR: Failed to initialize Claude client: {e}")
                    self.claude_client = None
            else:
                print(f"  - ⚠️ No ANTHROPIC_API_KEY found - Claude not available")
                logger.warning("⚠️ No ANTHROPIC_API_KEY found - Claude not available")
            self._claude_initialized = True

    def extract_with_vision(self,
                          image_data: bytes,
                          schema: Dict,
                          task: str = 'data_extraction') -> Dict:
        """Extract data using Claude vision model only"""

        model_name = get_model_for_task(task, self.config_name)

        self._ensure_claude_client()
        if not self.claude_client:
            raise ValueError("Claude API key required or Claude client failed to initialize")
        return self.claude_client.extract_data_with_schema(
            image_data=image_data,
            schema=schema,
            model=model_name
        )

    def validate_and_fix(self,
                        extracted_data: Dict,
                        schema: Dict,
                        image_data: bytes,
                        focus_area: str = "general",
                        task: str = 'vision_validation') -> Dict:
        """Validate and fix data using Claude vision model only"""

        model_name = get_model_for_task(task, self.config_name)

        self._ensure_claude_client()
        if not self.claude_client:
            raise ValueError("Claude API key required or Claude client failed to initialize")
        return self.claude_client.validate_and_fix_data(
            extracted_data=extracted_data,
            schema=schema,
            image_data=image_data,
            focus_area=focus_area,
            model=model_name
        )

    # OpenAI methods removed - Claude only support

    def get_current_config(self) -> Dict:
        """Get current model configuration"""
        return get_model_config(self.config_name)

    def switch_config(self, config_name: str):
        """Switch to a different model configuration"""
        self.config_name = config_name
        logger.info(f"Switched to model configuration: {config_name}")

def get_model_client_manager(config_name: str = 'current') -> ModelClientManager:
    """Get a configured model client manager"""
    return ModelClientManager(config_name=config_name)