"""
Google Gemini 2.0 Flash service for PDF data extraction
Provides text extraction and vision validation capabilities with provider-optimized prompts
"""
import google.generativeai as genai
import json
import os
import time
from typing import Dict, Any, List
from PIL import Image
from model_configs import get_model_for_task
from .provider_prompt_registry import prompt_registry, Provider, PromptType

class GeminiService:
    def __init__(self, api_key: str, model_config_name: str = 'gemini_flash'):
        """Initialize Gemini service"""
        genai.configure(api_key=api_key)
        self.model_config_name = model_config_name
        self.MAX_RETRIES = 3

    def _make_gemini_request(self, prompt: str, task_type: str, image_data=None) -> Dict[str, Any]:
        """Make a Gemini request with task-specific model selection"""

        # Get model from configuration
        model_name = get_model_for_task(task_type, self.model_config_name)

        print(f"[DEBUG] Using Gemini model: {model_name} for task: {task_type}")

        request_start = time.time()

        for attempt in range(self.MAX_RETRIES):
            try:
                # Initialize the model
                model = genai.GenerativeModel(model_name)

                # Prepare content
                if image_data:
                    # For vision tasks, include image
                    content = [prompt, image_data]
                else:
                    # For text-only tasks
                    content = [prompt]

                # Make the request
                response = model.generate_content(
                    content,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.0,
                        max_output_tokens=65536,
                    )
                )

                request_end = time.time()
                request_duration = request_end - request_start

                # Extract the response text
                if response.text:
                    return {
                        'success': True,
                        'content': response.text,
                        'model_used': model_name,
                        'request_duration': request_duration,
                        'usage': {
                            'input_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                            'output_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                            'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0) if hasattr(response, 'usage_metadata') else 0
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Empty response from Gemini',
                        'model_used': model_name
                    }

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    return {
                        'success': False,
                        'error': f"Request failed after {self.MAX_RETRIES} attempts: {str(e)}",
                        'model_used': model_name
                    }
                time.sleep(2 ** attempt)  # Exponential backoff

        return {
            'success': False,
            'error': 'Maximum retries exceeded',
            'model_used': model_name
        }

    def extract_data(self, text: str, schema: dict, page_num: int = 0) -> Dict[str, Any]:
        """Extract structured data from text using Gemini with provider-optimized prompts"""

        # Use provider-optimized extraction prompt
        prompt = prompt_registry.get_prompt(
            provider=Provider.GOOGLE,
            prompt_type=PromptType.EXTRACTION,
            text=text,
            schema=schema
        )

        print(f"[EXTRACTION] Using Gemini-optimized prompt for data extraction")

        result = self._make_gemini_request(prompt, 'data_extraction')

        if result['success']:
            try:
                # Parse the JSON response
                content = result['content'].strip()

                # Clean up response (remove any markdown formatting)
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

                extracted_data = json.loads(content)

                return {
                    'success': True,
                    'extracted_data': extracted_data,
                    'raw_content': result['content'],
                    'model_used': result['model_used'],
                    'usage': result.get('usage', {}),
                    'request_duration': result.get('request_duration', 0)
                }

            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f"Failed to parse JSON response: {str(e)}",
                    'raw_content': result['content'],
                    'model_used': result['model_used']
                }
        else:
            return result

    def validate_with_vision(self, image_path: str, extracted_data: dict, schema: dict, page_num: int = 0) -> Dict[str, Any]:
        """Validate extracted data against PDF image using Gemini Vision with optimized prompts"""

        try:
            # Load and prepare image
            image = Image.open(image_path)

            # Use provider-optimized validation prompt
            prompt = prompt_registry.get_prompt(
                provider=Provider.GOOGLE,
                prompt_type=PromptType.VALIDATION,
                extracted_data=extracted_data,
                schema=schema,
                page_num=page_num
            )

            print(f"[VALIDATION] Using Gemini-optimized validation prompt for page {page_num}")

            result = self._make_gemini_request(prompt, 'vision_validation', image)

            if result['success']:
                try:
                    content = result['content'].strip()

                    # Clean up response
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()

                    validation_result = json.loads(content)

                    return {
                        'success': True,
                        'validation_result': validation_result,
                        'raw_content': result['content'],
                        'model_used': result['model_used'],
                        'usage': result.get('usage', {}),
                        'request_duration': result.get('request_duration', 0)
                    }

                except json.JSONDecodeError as e:
                    return {
                        'success': False,
                        'error': f"Failed to parse validation JSON: {str(e)}",
                        'raw_content': result['content'],
                        'model_used': result['model_used']
                    }
            else:
                return result

        except Exception as e:
            return {
                'success': False,
                'error': f"Vision validation failed: {str(e)}"
            }

    def upload_image(self, image_path: str) -> Dict[str, Any]:
        """Upload image to Gemini File API and return file info"""
        try:
            # Upload file to Gemini
            uploaded_file = genai.upload_file(image_path)

            return {
                'success': True,
                'file_id': uploaded_file.name,
                'file_uri': uploaded_file.uri,
                'mime_type': uploaded_file.mime_type,
                'size_bytes': getattr(uploaded_file, 'size_bytes', 0)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to upload image to Gemini: {str(e)}"
            }

    def validate_with_vision_file(self, file_id: str, prompt: str) -> Dict[str, Any]:
        """Validate using uploaded file ID with Gemini (accepts pre-generated prompt)"""
        try:
            # Get the uploaded file
            uploaded_file = genai.get_file(file_id)

            print(f"[VALIDATION] Using Gemini file-based validation with file ID: {file_id[:12]}...")

            # Make request with file
            result = self._make_gemini_request(prompt, 'vision_validation', uploaded_file)

            if result['success']:
                try:
                    content = result['content'].strip()

                    # Clean up response
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()

                    validation_result = json.loads(content)

                    return {
                        'success': True,
                        'data': validation_result,
                        'raw_content': result['content'],
                        'model_used': result['model_used'],
                        'usage': result.get('usage', {}),
                        'request_duration': result.get('request_duration', 0)
                    }

                except json.JSONDecodeError as e:
                    return {
                        'success': False,
                        'error': f"Failed to parse validation JSON: {str(e)}",
                        'raw_content': result['content'],
                        'model_used': result['model_used']
                    }
            else:
                return result

        except Exception as e:
            return {
                'success': False,
                'error': f"File-based validation failed: {str(e)}"
            }

    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete a specific file from Gemini File API"""
        try:
            # Delete file from Gemini
            genai.delete_file(file_id)
            print(f"SUCCESS: Deleted Gemini file: {file_id}")
            return {
                'success': True,
                'file_id': file_id
            }

        except Exception as e:
            # Check if it's a "not found" error (file already deleted)
            if "not found" in str(e).lower() or "404" in str(e):
                print(f"DEBUG: Gemini file {file_id} already deleted or not found")
                return {'success': True, 'file_id': file_id}  # Consider this a success
            print(f"ERROR: Failed to delete Gemini file {file_id}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to delete file: {str(e)}",
                'file_id': file_id
            }

    def delete_all_files(self) -> Dict[str, Any]:
        """Delete all files from Gemini File API"""
        try:
            # List all files
            files = list(genai.list_files())

            if not files:
                return {
                    "success": True,
                    "deleted_count": 0,
                    "message": "No Gemini files found"
                }

            print(f"DEBUG: Attempting to delete {len(files)} Gemini files...")

            deleted_count = 0
            failed_files = []

            for file in files:
                result = self.delete_file(file.name)
                if result['success']:
                    deleted_count += 1
                else:
                    failed_files.append(file.name)

            message = f"Deleted {deleted_count} Gemini files"
            if failed_files:
                message += f", failed to delete {len(failed_files)} files"

            return {
                "success": len(failed_files) == 0,
                "deleted_count": deleted_count,
                "failed_files": failed_files,
                "message": message
            }

        except Exception as e:
            print(f"ERROR: Failed to delete all Gemini files: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to delete all files: {str(e)}",
                "deleted_count": 0
            }