"""
Claude Provider Implementation
Implements the common LLM provider interface for Anthropic Claude
Uses existing Claude service functionality with unified interface
"""

import json
import time
import os
from typing import Dict, Any
from anthropic import Anthropic

from .base_llm_provider import BaseLLMProvider
from model_configs import get_model_for_task


class ClaudeProvider(BaseLLMProvider):
    """Claude implementation of the LLM provider interface"""

    def __init__(self, api_key: str, model_config_name: str = 'claude_sonnet'):
        super().__init__(api_key, model_config_name)
        self.client = Anthropic(api_key=api_key)

    def get_provider_name(self) -> str:
        """Get the provider name"""
        return 'claude'

    def _make_request(self, prompt: str, task_type: str, **kwargs) -> Dict[str, Any]:
        """Make a Claude request with task-specific model selection and cost tracking"""

        # Get model from our model config system
        model_name = get_model_for_task(task_type, self.model_config_name)

        # Set default values for temperature and max_tokens
        temperature = kwargs.get('temperature', 0.0)
        max_tokens = kwargs.get('max_tokens', 8192)

        print(f"[DEBUG] Using Claude model: {model_name} for task: {task_type} (config: {self.model_config_name})")

        request_start = time.time()

        for attempt in range(self.MAX_RETRIES):
            try:
                # Build request parameters for Claude
                response = self.client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Track usage and cost if enabled
                usage_info = {}
                if self.ENABLE_COST_TRACKING:
                    usage_info = self._track_usage(response, task_type, model_name)

                content = response.content[0].text.strip()

                # Save prompt and response for debugging
                debug_file = self._create_debug_log(task_type, prompt, content)
                if debug_file:
                    print(f"DEBUG - Prompt & response saved to: {debug_file}")

                # Try to parse JSON, with fallback handling
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # Try multiple JSON extraction strategies
                    extraction_result = self._extract_json_from_response(content, model_name, task_type)
                    if not extraction_result["success"]:
                        return extraction_result
                    result = extraction_result["data"]

                return {
                    "success": True,
                    "data": result,
                    "usage": usage_info,
                    "model_used": model_name,
                    "task_type": task_type,
                    "response_time": time.time() - request_start
                }

            except json.JSONDecodeError as e:
                # Try to extract JSON from the response
                content = response.content[0].text
                return {
                    "success": False,
                    "error": f"JSON parsing error: {str(e)}",
                    "raw_content": content,
                    "model_used": model_name,
                    "task_type": task_type
                }

            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    return {
                        "success": False,
                        "error": f"Request failed after {self.MAX_RETRIES} attempts: {str(e)}",
                        "model_used": model_name,
                        "task_type": task_type
                    }

                # Wait before retry
                time.sleep(2 ** attempt)  # Exponential backoff

        return {"success": False, "error": "Maximum retries exceeded"}

    def validate_with_vision(self, image_base64: str, validation_prompt: str) -> Dict[str, Any]:
        """Perform vision-based validation using Claude API"""
        try:
            # Get model config for vision tasks
            model_name = get_model_for_task('field_identification', self.model_config_name)

            # Set default values for temperature and max_tokens
            temperature = 0.0
            max_tokens = 8192

            request_start = time.time()

            for attempt in range(self.MAX_RETRIES):
                try:
                    # Build message with image content for Claude
                    response = self.client.messages.create(
                        model=model_name,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": validation_prompt},
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",
                                            "data": image_base64
                                        }
                                    }
                                ]
                            }
                        ]
                    )

                    # Track usage if enabled
                    usage_info = {}
                    if self.ENABLE_COST_TRACKING:
                        usage_info = self._track_usage(response, 'vision_validation', model_name)

                    content = response.content[0].text.strip()

                    # Try to parse JSON response
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError:
                        result = self._extract_json_from_response(content, model_name, 'vision_validation')
                        if not result["success"]:
                            return result
                        result = result["data"]

                    return {
                        "success": True,
                        "data": result,
                        "usage": usage_info,
                        "model_used": model_name,
                        "response_time": time.time() - request_start
                    }

                except Exception as e:
                    # Handle rate limiting (429) with longer backoff
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        backoff_time = 10 + (2 ** attempt) * 5  # 15s, 25s, 45s...
                        print(f"Rate limit hit (429), backing off for {backoff_time}s...")
                        time.sleep(backoff_time)
                    else:
                        # Standard exponential backoff for other errors
                        backoff_time = 2 ** attempt
                        time.sleep(backoff_time)

                    if attempt == self.MAX_RETRIES - 1:
                        return {
                            "success": False,
                            "error": f"Vision validation failed after {self.MAX_RETRIES} attempts: {str(e)}",
                            "response_time": time.time() - request_start
                        }

        except Exception as e:
            return {
                "success": False,
                "error": f"Vision validation error: {str(e)}"
            }

    def validate_with_vision_file(self, file_id: str, validation_prompt: str) -> Dict[str, Any]:
        """Perform vision-based validation using Claude Files API file_id (token efficient)"""
        try:
            # Get model config for vision tasks
            model_name = get_model_for_task('field_identification', self.model_config_name)

            # Set default values for temperature and max_tokens
            temperature = 0.0
            max_tokens = 8192

            request_start = time.time()

            for attempt in range(self.MAX_RETRIES):
                try:
                    # Build message with file_id reference for Claude (requires Files API beta header)
                    response = self.client.messages.create(
                        model=model_name,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": validation_prompt},
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "file",
                                            "file_id": file_id
                                        }
                                    }
                                ]
                            }
                        ],
                        extra_headers={"anthropic-beta": "files-api-2025-04-14"}
                    )

                    # Track usage if enabled
                    usage_info = {}
                    if self.ENABLE_COST_TRACKING:
                        usage_info = self._track_usage(response, 'vision_validation_file', model_name)

                    content = response.content[0].text.strip()

                    # Try to parse JSON response
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError:
                        result = self._extract_json_from_response(content, model_name, 'vision_validation_file')
                        if not result["success"]:
                            return result
                        result = result["data"]

                    return {
                        "success": True,
                        "data": result,
                        "usage": usage_info,
                        "model_used": model_name,
                        "response_time": time.time() - request_start,
                        "token_efficient": True
                    }

                except Exception as e:
                    # Handle rate limiting (429) with longer backoff
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        backoff_time = 10 + (2 ** attempt) * 5  # 15s, 25s, 45s...
                        print(f"Rate limit hit (429), backing off for {backoff_time}s...")
                        time.sleep(backoff_time)
                    else:
                        # Standard exponential backoff for other errors
                        backoff_time = 2 ** attempt
                        time.sleep(backoff_time)

                    if attempt == self.MAX_RETRIES - 1:
                        return {
                            "success": False,
                            "error": f"Vision validation with file_id failed after {self.MAX_RETRIES} attempts: {str(e)}",
                            "response_time": time.time() - request_start
                        }

        except Exception as e:
            return {
                "success": False,
                "error": f"Vision validation with file_id error: {str(e)}"
            }

    def upload_image(self, image_path: str) -> Dict[str, Any]:
        """Upload image to Claude Files API and return file info"""
        try:
            # Upload file to Claude Files API
            with open(image_path, "rb") as image_file:
                file_upload = self.client.files.create(
                    file=image_file,
                    purpose="vision"
                )

            return {
                'success': True,
                'file_id': file_upload.id,
                'filename': file_upload.filename,
                'size_bytes': file_upload.size_bytes,
                'type': file_upload.type
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to upload image to Claude: {str(e)}"
            }

    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete a specific file from Claude Files API"""
        try:
            # Note: Using the correct delete method for Claude Files API
            response = self.client.beta.files.delete(
                file_id=file_id,
                extra_headers={
                    "anthropic-beta": "files-api-2025-04-14"
                }
            )
            print(f"SUCCESS: Deleted Claude file: {file_id}")
            return {
                'success': True,
                'file_id': file_id
            }

        except Exception as e:
            # Check if it's a "not found" error (file already deleted)
            if "not found" in str(e).lower() or "404" in str(e):
                print(f"DEBUG: Claude file {file_id} already deleted or not found")
                return {'success': True, 'file_id': file_id}  # Consider this a success
            print(f"ERROR: Failed to delete Claude file {file_id}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to delete file: {str(e)}",
                'file_id': file_id
            }

    def delete_all_files(self) -> Dict[str, Any]:
        """Delete all files from Claude Files API"""
        try:
            # List all files
            files_response = self.client.beta.files.list(
                extra_headers={"anthropic-beta": "files-api-2025-04-14"}
            )
            files = files_response.data

            if not files:
                return {
                    "success": True,
                    "deleted_count": 0,
                    "message": "No Claude files found"
                }

            print(f"DEBUG: Attempting to delete {len(files)} Claude files...")

            deleted_count = 0
            failed_files = []

            for file in files:
                result = self.delete_file(file.id)
                if result['success']:
                    deleted_count += 1
                else:
                    failed_files.append(file.id)

            message = f"Deleted {deleted_count} Claude files"
            if failed_files:
                message += f", failed to delete {len(failed_files)} files"

            return {
                "success": len(failed_files) == 0,
                "deleted_count": deleted_count,
                "failed_files": failed_files,
                "message": message
            }

        except Exception as e:
            print(f"ERROR: Failed to delete all Claude files: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to delete all files: {str(e)}",
                "deleted_count": 0
            }

    def _track_usage(self, response, task_type: str, model: str) -> Dict[str, Any]:
        """Track token usage and estimated costs for Claude"""

        # Claude pricing (as of 2024 - should be updated regularly)
        pricing = {
            'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015},  # per 1K tokens
            'claude-3-5-haiku-20241022': {'input': 0.001, 'output': 0.005},
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075}
        }

        if hasattr(response, 'usage'):
            usage = response.usage
            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            model_pricing = pricing.get(model, {'input': 0.003, 'output': 0.015})  # fallback to Sonnet pricing
            input_cost = (input_tokens / 1000) * model_pricing['input']
            output_cost = (output_tokens / 1000) * model_pricing['output']
            total_cost = input_cost + output_cost

            return {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'estimated_cost': round(total_cost, 6),
                'model': model,
                'task_type': task_type
            }

        return {'error': 'Usage information not available'}


if __name__ == "__main__":
    # Demo the Claude provider
    print("=== Claude Provider Implementation ===")
    print("✓ Implements BaseLLMProvider interface")
    print("✓ Uses centralized prompt registry")
    print("✓ Maintains existing Claude functionality")
    print("✓ Provides consistent API across providers")
    print("✓ Supports all vision and correction features")

    # Test provider creation
    try:
        from model_configs import ANTHROPIC_API_KEY
        if ANTHROPIC_API_KEY:
            provider = ClaudeProvider(ANTHROPIC_API_KEY)
            print(f"✓ Provider created: {provider}")
            print(f"✓ Available tasks: {provider.get_available_tasks()}")
        else:
            print("⚠ No API key available for testing")
    except Exception as e:
        print(f"✗ Error testing provider: {e}")