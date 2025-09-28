"""
Advanced PDF Extraction Pipeline Implementation
Complete 4-step pipeline: Preprocess -> Upload Vision Image -> Extract -> Validate/Correct
Optimized to save tokens by removing unnecessary PDF uploads to Claude
"""

import json
import time
import os
import io
import cv2
import numpy as np
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, Any, List, Optional, Tuple
# OpenAI import removed - using Claude only
import tempfile
import re
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

from .schema_text_extractor import SchemaTextExtractor
from .claude_service import ClaudeService
from .gemini_service import GeminiService
from .table_alignment_fixer import EnhancedValidationEngine

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.model_client_manager import ModelClientManager

class DebugLogger:
    """Centralized debug logging for all pipeline steps"""

    def __init__(self, debug_dir: str = "debug_pipeline"):
        self.debug_dir = debug_dir
        os.makedirs(debug_dir, exist_ok=True)
        self.session_id = int(time.time())

    def save_step(self, step_name: str, data: Any, data_type: str = "json"):
        """Save intermediate step data"""
        try:
            filename = f"step_{step_name}_{self.session_id}.{data_type}"
            filepath = os.path.join(self.debug_dir, filename)

            if data_type == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    if isinstance(data, (dict, list)):
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    else:
                        json.dump({"data": str(data)}, f, indent=2, ensure_ascii=False)
            elif data_type == "txt":
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(data))

            print(f"[DEBUG] Saved {step_name} to {filepath}")
            return filepath

        except Exception as e:
            print(f"[DEBUG] Failed to save {step_name}: {e}")
            return None

    def save_validation_round(self, round_num: int, validation_data: dict):
        """Save validation round results"""
        try:
            filename = f"validation_round_{round_num}_{self.session_id}.json"
            filepath = os.path.join(self.debug_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(validation_data, f, indent=2, ensure_ascii=False)

            print(f"[DEBUG] Saved validation round {round_num} to {filepath}")
            return filepath

        except Exception as e:
            print(f"[DEBUG] Failed to save validation round {round_num}: {e}")
            return None

class HighResImagePreprocessor:
    """600 DPI image preprocessing with advanced enhancements"""

    def __init__(self):
        self.target_dpi = 600
        self.max_file_size_mb = 20

    def pdf_to_high_res_image(self, pdf_path: str, page_num: int) -> str:
        """Convert PDF page to 600 DPI image with preprocessing"""

        print(f"[CONVERT] Converting PDF page {page_num} to 600 DPI...")

        doc = fitz.open(pdf_path)
        page = doc[page_num]

        # Calculate matrix for 600 DPI (scale factor = 600/72 = 8.33)
        zoom_factor = self.target_dpi / 72.0
        matrix = fitz.Matrix(zoom_factor, zoom_factor)

        # Render at high resolution
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))

        doc.close()

        print(f"[OK] Original 600 DPI image size: {image.size}")

        # Apply preprocessing
        processed_image = self._preprocess_high_res_image(image)

        # Save with optimization
        output_path = f"temp_600dpi_{page_num}_{int(time.time())}.png"
        self._optimize_for_upload(processed_image, output_path)

        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[OK] Preprocessed image saved: {file_size_mb:.1f}MB")

        return output_path

    def _preprocess_high_res_image(self, image: Image.Image) -> Image.Image:
        """Complete preprocessing pipeline for 600 DPI image"""

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Check size limits for Claude
        max_pixels = 2048 * 2048
        current_pixels = image.size[0] * image.size[1]

        if current_pixels > max_pixels:
            scale_factor = (max_pixels / current_pixels) ** 0.5
            new_width = int(image.size[0] * scale_factor)
            new_height = int(image.size[1] * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            effective_dpi = int(scale_factor * 600)
            print(f"[RESIZE] Resized to: {image.size} (~{effective_dpi} effective DPI)")

        # Enhance image quality
        image = self._enhance_quality(image)

        # Correct skew
        image = self._correct_skew(image)

        # Add visual guides
        image = self._add_visual_guides(image)

        return image

    def _enhance_quality(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better vision model performance"""

        # Check minimum image dimensions
        if image.size[0] < 10 or image.size[1] < 10:
            print(f"[WARNING] Image too small for processing: {image.size}")
            return image

        # Sharpness enhancement
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)

        # Contrast enhancement
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.15)

        # Noise reduction (MedianFilter requires odd size and minimum dimensions)
        if image.size[0] >= 3 and image.size[1] >= 3:
            image = image.filter(ImageFilter.MedianFilter(size=3))

        return image

    def _correct_skew(self, image: Image.Image) -> Image.Image:
        """Detect and correct document skew"""

        # Check minimum image dimensions for OpenCV operations
        if image.size[0] < 50 or image.size[1] < 50:
            print(f"[WARNING] Image too small for skew correction: {image.size}")
            return image

        try:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            print(f"[WARNING] Error in image conversion for skew correction: {e}")
            return image

        try:
            # Edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Line detection
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)

            if lines is not None:
                angles = []
                for rho, theta in lines[:10]:
                    angle = theta * 180 / np.pi
                    if 85 <= angle <= 95:  # Near horizontal lines
                        angles.append(angle - 90)

                if angles:
                    skew_angle = np.median(angles)

                    if abs(skew_angle) > 0.5:
                        print(f"[FIX] Correcting skew: {skew_angle:.2f}°")
                        center = tuple(np.array(cv_image.shape[1::-1]) / 2)
                        rot_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
                        cv_image = cv2.warpAffine(cv_image, rot_matrix, cv_image.shape[1::-1])

            return Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

        except Exception as e:
            print(f"[WARNING] Error in skew correction: {e}")
            return image

    def _add_visual_guides(self, image: Image.Image) -> Image.Image:
        """Add visual guides to help vision model detect fields"""

        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Adaptive threshold for better text detection
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 11, 2)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        line_thickness = 2

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Scale thresholds for 600 DPI
            min_width, max_width = 100, 4000
            min_height, max_height = 30, 800

            if min_width < w < max_width and min_height < h < max_height:
                # Draw field boundaries
                cv2.rectangle(cv_image, (x-3, y-3), (x+w+3, y+h+3), (200, 200, 255), line_thickness)

                # Add type indicators
                aspect_ratio = w / h
                if aspect_ratio > 5:
                    cv2.putText(cv_image, "ROW", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX,
                               0.6, (0, 150, 0), line_thickness)
                elif 1 < aspect_ratio < 5:
                    cv2.putText(cv_image, "FIELD", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX,
                               0.6, (150, 0, 0), line_thickness)

        return Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

    def _optimize_for_upload(self, image: Image.Image, output_path: str) -> None:
        """Optimize image for upload while maintaining quality"""

        # Try different quality levels
        for quality in [95, 90, 85, 80, 75]:
            temp_path = f"temp_{quality}_{output_path}"
            image.save(temp_path, "PNG", optimize=True, quality=quality, dpi=(600, 600))

            file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)

            if file_size_mb <= self.max_file_size_mb:
                os.rename(temp_path, output_path)
                return
            else:
                os.unlink(temp_path)

        # If still too large, use basic compression
        image.save(output_path, "PNG", optimize=True, dpi=(600, 600))

class OptimizedFileManager:
    """File upload manager for both Claude and Gemini APIs - Vision images only"""

    def __init__(self, api_key: str, provider: str = 'anthropic', model_config_name: str = 'claude_sonnet'):
        self.provider = provider
        self.model_config_name = model_config_name
        self.uploaded_files = {}

        if provider == 'google':
            # Initialize Gemini service
            from services.gemini_service import GeminiService
            from model_configs import GOOGLE_API_KEY
            self.ai_service = GeminiService(GOOGLE_API_KEY, model_config_name)
        else:
            # Initialize Claude service
            from services.claude_service import ClaudeService
            self.ai_service = ClaudeService(api_key, model_config_name)

    # Removed upload_original_pdf method - PDF uploads to Claude were unnecessary
    # Pipeline now uses only vision images for validation, saving significant tokens

    def upload_processed_image(self, image_path: str) -> str:
        """Upload preprocessed image to AI service (Claude or Gemini)"""

        # Check if already cached to avoid rate limits
        cached_file_id = self.get_cached_file_id(image_path)
        if cached_file_id:
            print(f"[OK] Using cached image file ID: {cached_file_id}")
            return cached_file_id

        provider_name = "Gemini" if self.provider == 'google' else "Claude"
        print(f"[UPLOAD] Uploading image to {provider_name} Files API...")

        # Add small delay to help with rate limiting
        time.sleep(2)  # 2 second delay before upload

        try:
            # Use unified AI service upload method
            upload_result = self.ai_service.upload_image(image_path)

            if upload_result['success']:
                file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
                file_id = upload_result['file_id']
                print(f"[OK] Upload complete: {file_size_mb:.1f}MB, File ID: {file_id}")

                # Cache the file ID
                self.uploaded_files[image_path] = file_id
                return file_id
            else:
                raise Exception(upload_result.get('error', 'Upload failed'))

        except Exception as e:
            print(f"ERROR: {provider_name} Files API upload failed: {str(e)}")
            raise e

    def get_cached_file_id(self, image_path: str) -> str:
        """Get cached file ID if available"""
        return self.uploaded_files.get(image_path)

    def list_uploaded_files(self):
        """List all uploaded files from AI service (Claude or Gemini)"""
        try:
            if self.provider == 'google':
                # For Gemini, use genai.list_files()
                import google.generativeai as genai
                files = list(genai.list_files())
                return files
            else:
                # For Claude, use existing method
                response = self.ai_service.client.beta.files.list(
                    extra_headers={
                        "anthropic-beta": "files-api-2025-04-14"
                    }
                )
                return response.data
        except Exception as e:
            print(f"ERROR: Failed to list files: {str(e)}")
            return []

    def get_file_metadata(self, file_id: str):
        """Get metadata for a specific file from AI service (Claude or Gemini)"""
        try:
            if self.provider == 'google':
                # For Gemini, use genai.get_file()
                import google.generativeai as genai
                file_info = genai.get_file(file_id)
                return file_info
            else:
                # For Claude, use existing method
                metadata = self.ai_service.client.beta.files.retrieve_metadata(
                    file_id=file_id,
                    extra_headers={
                        "anthropic-beta": "files-api-2025-04-14"
                    }
                )
                return metadata
        except Exception as e:
            print(f"ERROR: Failed to get file metadata: {str(e)}")
            return None

    def delete_file(self, file_id: str):
        """Delete a specific file from AI service (Claude or Gemini)"""
        try:
            if self.provider == 'google':
                # Use Gemini service delete method
                result = self.ai_service.delete_file(file_id)
                return result['success']
            else:
                # Use Claude service delete method
                result = self.ai_service.delete_file(file_id)
                return result['success']
        except Exception as e:
            print(f"ERROR: Failed to delete file {file_id}: {str(e)}")
            return False

    def delete_all_files(self):
        """Delete all files from AI service (Claude or Gemini)"""
        try:
            if self.provider == 'google':
                # Use Gemini service delete all method
                result = self.ai_service.delete_all_files()
            else:
                # Use Claude service delete all method
                result = self.ai_service.delete_all_files()

            # Clear local cache if available
            if hasattr(self, 'uploaded_files'):
                self.uploaded_files.clear()

            return result

        except Exception as e:
            print(f"ERROR: Failed to delete all files: {str(e)}")
            return {
                "success": False,
                "deleted_count": 0,
                "message": f"Delete operation failed: {str(e)}"
            }

class ValidationCorrectionEngine:
    """Combined validation and correction engine with Claude and Claude support"""

    def __init__(self, api_key: str, model_config_name: str = 'claude_sonnet'):
        from model_configs import get_provider

        self.config_name = model_config_name
        self.provider = get_provider(model_config_name)

        if self.provider == 'google':
            # Initialize Gemini service
            gemini_api_key = os.environ.get('GOOGLE_API_KEY')
            if not gemini_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini")
            self.ai_service = GeminiService(gemini_api_key, model_config_name)
        else:
            # Initialize Claude service (default)
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))
            self.model_client_manager = ModelClientManager(
                anthropic_api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'),
                config_name=model_config_name
            )

        self.max_rounds = 10
        self.target_accuracy = 1.0

        # Set model config for validation
        from model_configs import get_model_for_task
        self.model_config = {
            'vision_model': get_model_for_task('vision_validation', model_config_name)
        }

    def _clean_json_response(self, response_text: str) -> str:
        """Clean JSON response using the same method as schema_text_extractor"""

        # Remove any text before the first {
        start_idx = response_text.find('{')
        if start_idx == -1:
            raise json.JSONDecodeError("No JSON object found in response", response_text, 0)

        # Find the last }
        end_idx = response_text.rfind('}')
        if end_idx == -1:
            raise json.JSONDecodeError("No closing brace found in response", response_text, 0)

        # Extract JSON part
        json_part = response_text[start_idx:end_idx + 1]

        # Clean common issues - same as schema_text_extractor
        # Remove trailing commas
        json_part = re.sub(r',(\s*[}\]])', r'\1', json_part)

        # Fix unescaped quotes in string values
        lines = json_part.split('\n')
        fixed_lines = []

        for line in lines:
            if not line.strip():
                fixed_lines.append(line)
                continue

            # Count quotes to detect string boundaries
            quote_count = line.count('"')
            escaped_quote_count = line.count('\\"')
            actual_quote_count = quote_count - escaped_quote_count

            # If we have unescaped quotes in values, try to fix them
            if ':' in line and actual_quote_count > 2:
                # Split on the first colon to separate key from value
                if line.count(':') >= 1:
                    colon_idx = line.find(':')
                    key_part = line[:colon_idx + 1]
                    value_part = line[colon_idx + 1:].strip()

                    # If value part has unescaped quotes, fix them
                    if value_part.startswith('"') and value_part.endswith('"'):
                        # Extract the content between quotes
                        content = value_part[1:-1]
                        # Escape any unescaped quotes in the content
                        content = content.replace('"', '\\"')
                        value_part = f'"{content}"'

                    line = key_part + ' ' + value_part

            fixed_lines.append(line)

        cleaned_json = '\n'.join(fixed_lines)

        # Ensure proper closure
        open_braces = cleaned_json.count('{') - cleaned_json.count('}')
        open_brackets = cleaned_json.count('[') - cleaned_json.count(']')

        if open_braces > 0:
            cleaned_json += '}' * open_braces
        if open_brackets > 0:
            cleaned_json += ']' * open_brackets

        return cleaned_json

    def validate_and_correct_iteratively(self, file_id: str, extracted_data: dict,
                                       schema: dict, max_rounds: int = 10,
                                       target_accuracy: float = 1.0,
                                       progress_callback=None) -> dict:
        """Iterative validation and correction"""

        def log_progress(message):
            if progress_callback:
                progress_callback(message)
            else:
                print(message)

        self.max_rounds = max_rounds
        self.target_accuracy = target_accuracy

        current_data = extracted_data.copy()
        correction_history = []
        round_results = []

        log_progress(f"[VALIDATE] Starting validation/correction (max {max_rounds} rounds, target {target_accuracy:.0%})")

        for round_num in range(1, self.max_rounds + 1):
            log_progress(f"[ROUND] Round {round_num}/{self.max_rounds}")

            round_start = time.time()

            # Combined validation + correction
            round_result = self._validate_and_correct_round(
                file_id, current_data, schema, round_num, correction_history
            )

            round_result["round_number"] = round_num
            round_result["round_duration"] = time.time() - round_start
            round_results.append(round_result)

            if not round_result["success"]:
                log_progress(f"ERROR: Round {round_num} failed: {round_result.get('error')}")
                break

            # Update data if corrections were made
            if round_result["corrections_made"]:
                current_data = round_result["corrected_data"]
                new_corrections = round_result["corrections_applied"]
                correction_history.extend(new_corrections)

                log_progress(f"[OK] Round {round_num}: {len(new_corrections)} corrections applied")
            else:
                log_progress(f"[OK] Round {round_num}: No corrections needed")

            # Check if target accuracy reached
            accuracy = round_result["accuracy_estimate"]
            if accuracy >= self.target_accuracy:
                print(f"🎯 Target accuracy {self.target_accuracy:.0%} reached!")
                break

        return self._compile_validation_results(round_results, current_data, correction_history)

    def _validate_and_correct_round(self, file_id: str, current_data: dict,
                                  schema: dict, round_num: int,
                                  correction_history: list) -> dict:
        """Single round of validation and correction"""

        # DEBUG: Save validation input data
        if self.debug_logger:
            validation_input = {
                "round_number": round_num,
                "current_data": current_data,
                "schema": schema,
                "correction_history": correction_history,
                "file_id": file_id
            }
            self.debug_logger.save_step(f"06_validation_input_round_{round_num}", validation_input, "json")

        # Build validation prompt with JSON requirements (same style as schema_text_extractor)
        prompt = self._build_validation_correction_prompt(
            current_data, schema, round_num, correction_history
        )

        # DEBUG: Save validation prompt
        if self.debug_logger:
            self.debug_logger.save_step(f"07_validation_prompt_round_{round_num}", prompt, "txt")

        try:
            # Use Claude messages API with Files API beta header
            response = self.client.messages.create(
                model=self.model_config['vision_model'],
                max_tokens=16000,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "source": {"type": "file", "file_id": file_id}}
                    ]
                }],
                extra_headers={
                    "anthropic-beta": "files-api-2025-04-14"
                }
            )

            content = response.content[0].text

            # DEBUG: Save validation response
            if self.debug_logger:
                validation_response = {
                    "round_number": round_num,
                    "response_content": content,
                    "response_object": {
                        "model": response.model,
                        "usage": response.usage.model_dump() if hasattr(response, 'usage') else None
                    }
                }
                self.debug_logger.save_step(f"08_validation_response_round_{round_num}", validation_response, "json")

            # Use the same JSON parsing approach as schema_text_extractor
            parsed_result = self._parse_validation_correction_response(response, current_data)

            # DEBUG: Save parsed validation result
            if self.debug_logger:
                self.debug_logger.save_step(f"09_validation_result_round_{round_num}", parsed_result, "json")

            return parsed_result

        except Exception as e:
            return {
                "success": False,
                "error": f"API call failed: {str(e)}",
                "corrections_made": False,
                "accuracy_estimate": 0.5
            }

    def _ensure_schema_compliance(self, data: dict, schema: dict) -> dict:
        """Ensure data complies with the provided schema structure"""

        # Use the JSON validator's schema compliance functionality
        return self.json_validator._ensure_schema_compliance(data, schema)

    def _build_validation_correction_prompt(self, current_data: dict, schema: dict,
                                          round_num: int, correction_history: list) -> str:
        """Build comprehensive validation + correction prompt"""

        history_context = ""
        if correction_history:
            recent_corrections = correction_history[-3:]
            history_context = f"""
            PREVIOUS CORRECTIONS (for context):
            {json.dumps(recent_corrections, indent=2)}
            """

        prompt = f"""
        DOCUMENT VALIDATION AND CORRECTION - Round {round_num}

        TASK: Analyze this 600 DPI preprocessed document image and BOTH validate AND correct the extracted data.

        IMAGE FEATURES:
        - 600 DPI resolution for maximum clarity
        - Skew-corrected and contrast-enhanced
        - Light blue boxes highlight detected form fields
        - "FIELD" and "ROW" labels show field types

        CURRENT EXTRACTED DATA:
        {json.dumps(current_data, indent=2)}

        REQUIRED SCHEMA:
        {json.dumps(schema, indent=2)}

        {history_context}

        CRITICAL VALIDATION FOCUS - COLUMN SHIFTS & KEY-VALUE ISSUES:

        ** COLUMN SHIFTING DETECTION:**
        1. **Visual Table Analysis**: Look at each table in the image carefully
           - Check if column headers align with their data values
           - Identify if data has shifted left/right into wrong columns
           - Look for pattern: "Rate: 50000" but extracted as "Description: 50000"

        2. **Header-Data Alignment**: For each table row:
           - Trace vertically from header down to data values
           - Verify each value is under its correct column header
           - Look for off-by-one shifts where data moves one column over

        ** KEY-VALUE ASSOCIATION ERRORS:**
        1. **Field Label Mapping**: For each form field:
           - Find the visual label text (e.g., "Employee Name:")
           - Trace to the adjacent value in the document
           - Check if extracted field name matches the visual label

        2. **Proximity Analysis**: Values should be:
           - Immediately after their labels (same line or next line)
           - Spatially close to their field names
           - Not confused with other nearby values

        3. **Common Patterns to Check**:
           - "Birth Date: 01/15/1985" → correct association
           - "Birth Date: SSN" → WRONG (grabbed wrong value)
           - Missing employer tax table rows entirely

        **VALIDATION INSTRUCTIONS:**
        1. Use 600 DPI vision to read precise spatial relationships
        2. Map each extracted value back to its visual location in document
        3. Verify table data is under correct column headers
        4. Ensure form values match their adjacent labels
        5. Check for completely missing table sections
        6. If errors found, provide corrected data with proper alignment

        RESPONSE FORMAT (strict JSON):
        {{
            "validation_status": "corrections_needed" | "no_corrections_needed",
            "accuracy_estimate": 0.95,
            "corrections_made": true | false,
            "corrected_data": {{...}},
            "corrections_applied": [
                {{
                    "field": "field_name",
                    "change_type": "value_corrected" | "field_added" | "column_realigned" | "row_added" | "column_shift_fix" | "key_value_reassociation" | "missing_table_extracted",
                    "before_value": "...",
                    "after_value": "...",
                    "reason": "Clear explanation of why this correction was needed"
                }}
            ],
            "validation_details": {{
                "fields_checked": 25,
                "errors_found": 3,
                "confidence_level": "high" | "medium" | "low"
            }}
        }}

        CRITICAL RULES:
        - If accuracy_estimate >= {self.target_accuracy}, set corrections_made to false
        - Always provide corrected_data if corrections_made is true
        - Be extremely precise due to high image resolution
        - Focus on the visual guides to understand field boundaries
        """

        return prompt

    def _parse_validation_correction_response(self, response, current_data: dict) -> dict:
        """Parse validation + correction response using same cleaning as schema_text_extractor"""

        try:
            content = response.content[0].text

            # Use the same JSON cleaning approach as schema_text_extractor
            cleaned_json = self._clean_json_response(content)
            result = json.loads(cleaned_json)

            # Validate structure
            required_fields = ["validation_status", "accuracy_estimate", "corrections_made"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Handle corrected data
            if result["corrections_made"]:
                if "corrected_data" not in result:
                    raise ValueError("corrections_made=true but no corrected_data provided")
            else:
                result["corrected_data"] = current_data
                result["corrections_applied"] = result.get("corrections_applied", [])

            result["success"] = True
            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse response: {str(e)}",
                "corrections_made": False,
                "corrected_data": current_data,
                "corrections_applied": [],
                "accuracy_estimate": 0.5
            }

    def _compile_validation_results(self, round_results: list, final_data: dict,
                                  correction_history: list) -> dict:
        """Compile final validation results"""

        # DEBUG: Save final compilation input
        if self.debug_logger:
            compilation_input = {
                "round_results": round_results,
                "final_data": final_data,
                "correction_history": correction_history,
                "timestamp": time.time()
            }
            self.debug_logger.save_step("10_final_compilation_input", compilation_input, "json")

        successful_rounds = [r for r in round_results if r["success"]]

        if not successful_rounds:
            return {
                "success": False,
                "error": "No successful validation rounds",
                "final_data": final_data
            }

        final_round = successful_rounds[-1]
        total_corrections = len(correction_history)

        final_results = {
            "success": True,
            "final_data": final_data,
            "validation_rounds_completed": len(successful_rounds),
            "total_corrections_applied": total_corrections,
            "final_accuracy_estimate": final_round["accuracy_estimate"],
            "target_accuracy_achieved": final_round["accuracy_estimate"] >= self.target_accuracy,
            "round_details": round_results,
            "correction_history": correction_history,
            "validation_summary": {
                "rounds_needed": len(successful_rounds),
                "corrections_per_round": [len(r.get("corrections_applied", [])) for r in successful_rounds],
                "accuracy_progression": [r.get("accuracy_estimate", 0) for r in successful_rounds]
            }
        }

        # DEBUG: Save final compiled results
        if self.debug_logger:
            self.debug_logger.save_step("11_final_compiled_results", final_results, "json")

        return final_results

class AdvancedPDFExtractionPipeline:
    """Main pipeline controller with Claude and Claude support"""

    def __init__(self, api_key: str, model_config_name: str = 'claude_sonnet', enable_debug: bool = True):
        self.api_key = api_key
        self.model_config_name = model_config_name

        from model_configs import get_provider
        self.provider = get_provider(model_config_name)

        if self.provider == 'google':
            # For Gemini, we need GOOGLE_API_KEY
            from model_configs import GOOGLE_API_KEY
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini")
            self.ai_service = GeminiService(GOOGLE_API_KEY, model_config_name)
        else:
            # For Claude (default)
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))

        # Always initialize text extractor for both providers
        self.text_extractor = SchemaTextExtractor(api_key, model_config_name)

        self.preprocessor = HighResImagePreprocessor()
        # Initialize file manager for both providers
        self.file_manager = OptimizedFileManager(api_key, self.provider, model_config_name)
        self.validator_corrector = ValidationCorrectionEngine(api_key, model_config_name)
        self.enhanced_validator = EnhancedValidationEngine(api_key, model_config_name)
        self.model_client_manager = ModelClientManager(
            anthropic_api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'),
            config_name=model_config_name
        )

        # Debug logging
        self.debug_logger = DebugLogger() if enable_debug else None
        self.enable_debug = enable_debug

    def process_document(self, pdf_path: str, schema: dict, page_num: int = 0,
                        max_rounds: int = 10, target_accuracy: float = 1.0,
                        progress_callback=None, selected_file_id: str = None) -> dict:
        """Complete 4-step pipeline execution"""

        pipeline_start = time.time()

        # DEBUG: Save pipeline input parameters
        if self.debug_logger:
            pipeline_input = {
                "pdf_path": pdf_path,
                "schema": schema,
                "page_num": page_num,
                "max_rounds": max_rounds,
                "target_accuracy": target_accuracy,
                "selected_file_id": selected_file_id,
                "model_config": self.model_config_name,
                "pipeline_start_time": pipeline_start
            }
            self.debug_logger.save_step("00_pipeline_input", pipeline_input, "json")

        result = {
            "success": False,
            "pipeline_steps": {},
            "final_data": None,
            "workflow_summary": {},
            "processing_log": []
        }

        def log_progress(message):
            result["processing_log"].append(f"[{time.time() - pipeline_start:.1f}s] {message}")
            if progress_callback:
                progress_callback(message)

        try:
            log_progress("🚀 Starting advanced PDF extraction pipeline")

            # STEP 1 & 2: Handle file input with optimized image upload for validation
            if selected_file_id:
                # Skip preprocessing for selected files
                log_progress(f"📎 Using selected file ID: {selected_file_id}")
                step1_result = {
                    "success": True,
                    "processed_image_path": None,
                    "source": "selected_file"
                }
                result["pipeline_steps"]["step1_preprocess"] = step1_result

                step2_result = {
                    "success": True,
                    "file_id": selected_file_id,
                    "upload_time": 0,
                    "source": "selected_file"
                }

                # Also create and upload high-res image for vision validation
                log_progress("[UPLOAD] Creating high-res image for token-efficient validation...")
                vision_image_result = self._create_and_upload_vision_image(pdf_path, page_num, log_progress)
                step2_result["vision_image_file_id"] = vision_image_result.get("file_id")
            else:
                # Preprocess and upload both PDF and high-res image
                log_progress("[STEP] Step 1: Preprocessing PDF to 600 DPI...")
                step1_result = self._step1_preprocess(pdf_path, page_num, log_progress)
                result["pipeline_steps"]["step1_preprocess"] = step1_result

                if not step1_result["success"]:
                    result["error"] = f"Step 1 failed: {step1_result.get('error')}"
                    return result

                log_progress("[UPLOAD] Step 2: Uploading vision image for validation (PDF upload removed to save tokens)...")
                step2_result = self._step2_upload_vision_image_only(pdf_path, page_num, log_progress)

            result["pipeline_steps"]["step2_upload"] = step2_result

            if not step2_result["success"]:
                result["error"] = f"Step 2 failed: {step2_result.get('error')}"
                return result

            # STEP 3: Schema-based text extraction using proven SchemaTextExtractor
            log_progress("📝 Step 3: Schema-based text extraction...")
            step3_result = self._step3_text_extraction(pdf_path, schema, page_num, log_progress)
            result["pipeline_steps"]["step3_text_extraction"] = step3_result

            if not step3_result["success"]:
                result["error"] = f"Step 3 failed: {step3_result.get('error')}"
                return result

            # STEP 4: Token-efficient multi-round vision validation using uploaded image
            log_progress("[VALIDATE] Step 4: Multi-round vision validation with uploaded image...")
            vision_image_file_id = step2_result.get("vision_image_file_id")

            # Debug: Log step2_result and extracted file_id
            log_progress(f"DEBUG: step2_result keys: {list(step2_result.keys())}")
            log_progress(f"DEBUG: vision_image_file_id extracted: {vision_image_file_id}")

            step4_result = self._step4_token_efficient_validation(
                pdf_path,
                step3_result["extracted_data"],
                schema,
                page_num,
                max_rounds,
                target_accuracy,
                vision_image_file_id,
                log_progress
            )
            result["pipeline_steps"]["step4_validation"] = step4_result

            # DEBUG: Log step4 result contents
            print(f"\nDEBUG: Step4 Result Contents:")
            print(f"  step4_result keys: {list(step4_result.keys())}")
            print(f"  final_accuracy_estimate: {step4_result.get('final_accuracy_estimate')}")
            print(f"  validation_rounds_completed: {step4_result.get('validation_rounds_completed')}")
            print(f"  total_corrections_applied: {step4_result.get('total_corrections_applied')}")

            # Compile final results
            result["success"] = step4_result["success"]
            result["final_data"] = step4_result["final_data"]
            result["workflow_summary"] = self._compile_workflow_summary(result["pipeline_steps"])

            # DEBUG: Log workflow summary contents after compilation
            print(f"\nDEBUG: Compiled Workflow Summary:")
            print(f"  workflow_summary keys: {list(result['workflow_summary'].keys())}")
            print(f"  final_accuracy: {result['workflow_summary'].get('final_accuracy')}")
            print(f"  validation_rounds_completed: {result['workflow_summary'].get('validation_rounds_completed')}")
            print(f"  total_corrections_applied: {result['workflow_summary'].get('total_corrections_applied')}")

            # Cleanup
            self._cleanup_temp_files(step1_result.get("processed_image_path"))

            total_time = time.time() - pipeline_start
            result["workflow_summary"]["total_processing_time"] = total_time

            log_progress(f"[OK] Pipeline complete in {total_time:.1f}s")

            # DEBUG: Save final pipeline result
            if self.debug_logger:
                self.debug_logger.save_step("12_final_pipeline_result", result, "json")

            return result

        except Exception as e:
            log_progress(f"ERROR: Pipeline failed: {str(e)}")
            result["error"] = str(e)
            return result

    def _step1_preprocess(self, pdf_path: str, page_num: int, log_progress) -> dict:
        """Step 1: PDF preprocessing"""

        step_start = time.time()

        try:
            processed_image_path = self.preprocessor.pdf_to_high_res_image(pdf_path, page_num)

            with Image.open(processed_image_path) as img:
                file_size_mb = os.path.getsize(processed_image_path) / (1024 * 1024)

            log_progress(f"[OK] Preprocessing complete: {img.size}, {file_size_mb:.1f}MB")

            return {
                "success": True,
                "processed_image_path": processed_image_path,
                "image_size": img.size,
                "file_size_mb": file_size_mb,
                "processing_time": time.time() - step_start
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - step_start
            }

    def _step2_upload(self, image_path: str, log_progress) -> dict:
        """Step 2: Upload to Claude"""

        step_start = time.time()

        try:
            file_id = self.file_manager.upload_processed_image(image_path)

            log_progress(f"[OK] Upload complete: {file_id}")

            return {
                "success": True,
                "file_id": file_id,
                "upload_time": time.time() - step_start
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "upload_time": time.time() - step_start
            }

    # Removed _step2_upload_pdf method - PDF upload to Claude was unnecessary
    # Text extraction uses local PyMuPDF, validation uses vision images only

    def _create_and_upload_vision_image(self, pdf_path: str, page_num: int, log_progress) -> dict:
        """Create high-res image and upload to Claude for token-efficient vision validation"""

        import os
        import hashlib

        step_start = time.time()

        try:
            # Create deterministic cache key for this PDF + page combination
            pdf_name = os.path.basename(pdf_path)
            cache_key = f"{pdf_name}_page_{page_num}_vision"

            # Check if we already have this image uploaded
            for cached_path, file_id in self.file_manager.uploaded_files.items():
                if cache_key in cached_path:
                    log_progress(f"[OK] Using cached vision image: {file_id}")
                    return {
                        "success": True,
                        "file_id": file_id,
                        "upload_time": time.time() - step_start,
                        "file_type": "vision_image_cached"
                    }

            # Create high-resolution image
            image_path = self.preprocessor.pdf_to_high_res_image(pdf_path, page_num)

            # Upload image to Claude Files API
            vision_file_id = self.file_manager.upload_processed_image(image_path)

            log_progress(f"[OK] Vision image uploaded: {vision_file_id}")

            # Cache with deterministic key instead of temp path
            self.file_manager.uploaded_files[f"{cache_key}_{image_path}"] = vision_file_id

            # Clean up temporary image
            os.unlink(image_path)

            return {
                "success": True,
                "file_id": vision_file_id,
                "upload_time": time.time() - step_start,
                "file_type": "vision_image"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "upload_time": time.time() - step_start
            }

    def _step2_upload_vision_image_only(self, pdf_path: str, page_num: int, log_progress) -> dict:
        """Upload only high-res image for token-efficient validation (PDF upload removed to save tokens)"""

        step_start = time.time()

        try:
            # Create and upload high-res image for vision validation only
            vision_result = self._create_and_upload_vision_image(pdf_path, page_num, log_progress)

            # Debug: Check vision result
            vision_file_id = vision_result.get("file_id")
            if not vision_file_id:
                log_progress(f"WARNING: Vision image upload failed or returned no file_id")
                log_progress(f"DEBUG: Vision result: {vision_result}")

            log_progress(f"[OK] Vision image uploaded (PDF upload skipped to save tokens): Vision={vision_file_id}")

            return {
                "success": True,
                "vision_image_file_id": vision_file_id,
                "upload_time": time.time() - step_start,
                "file_type": "vision_only",
                "tokens_saved": "PDF upload removed to save tokens"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "upload_time": time.time() - step_start
            }

    def _step3_text_extraction(self, pdf_path: str, schema: dict, page_num: int, log_progress, file_id: str = None) -> dict:
        """Step 3: Text-based extraction - routes to Claude or Claude based on config"""

        step_start = time.time()

        try:
            # Check if we should use Claude for data extraction
            from model_configs import get_model_for_task
            model_name = get_model_for_task('data_extraction', self.model_config_name)

            if model_name.startswith('claude'):
                # Use Claude-based extraction with vision
                log_progress("[VALIDATE] Using Claude 3.5 Sonnet for data extraction...")
                return self._step3_claude_extraction(pdf_path, schema, page_num, log_progress, step_start, file_id)
            else:
                # Use traditional text-based extraction with Claude
                log_progress("[STEP] Using Claude text extraction...")
                return self._step3_claude_text_extraction(pdf_path, schema, page_num, log_progress, step_start, file_id)

        except Exception as e:
            return {
                "success": False,
                "error": f"Text-based schema extraction failed: {str(e)}",
                "extraction_time": time.time() - step_start
            }

    def _step3_claude_text_extraction(self, pdf_path: str, schema: dict, page_num: int, log_progress, step_start: float, file_id: str = None) -> dict:
        """Step 3: Claude text-based extraction"""

        try:
            # Extract raw text
            text_result = self.text_extractor.extract_raw_text(pdf_path, page_num)

            if not text_result["success"]:
                return text_result

            # Extract with schema
            extraction_result = self.text_extractor.extract_with_schema_from_text(
                text_result["raw_text"], schema
            )

            if extraction_result["success"]:
                log_progress("[OK] Claude text extraction complete")

                return {
                    "success": True,
                    "extracted_data": extraction_result["extracted_data"],
                    "extraction_time": time.time() - step_start
                }
            else:
                return extraction_result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extraction_time": time.time() - step_start
            }

    def _step3_claude_extraction(self, pdf_path: str, schema: dict, page_num: int, log_progress, step_start: float, file_id: str = None) -> dict:
        """Step 3: Claude text-based extraction using PDF parsed text with schema prompt"""

        try:
            # Extract raw text from PDF first
            log_progress("[STEP] Extracting text from PDF...")
            text_result = self.text_extractor.extract_raw_text(pdf_path, page_num)

            if not text_result["success"]:
                return {
                    "success": False,
                    "error": f"Text extraction failed: {text_result.get('error')}",
                    "extraction_time": time.time() - step_start
                }

            raw_text = text_result["raw_text"]

            # DEBUG: Save extracted raw text
            if self.debug_logger:
                self.debug_logger.save_step("01_extracted_raw_text", raw_text, "txt")
                self.debug_logger.save_step("01_text_extraction_result", text_result, "json")

            log_progress("🤖 Extracting data from PDF text using Claude 3.5 Sonnet...")

            # Use the existing _build_text_schema_prompt from schema_text_extractor
            extraction_prompt = self.text_extractor._build_text_schema_prompt(raw_text, schema)

            # DEBUG: Save the extraction prompt
            if self.debug_logger:
                self.debug_logger.save_step("02_extraction_prompt", extraction_prompt, "txt")

            # Make request to Claude using the text-based prompt
            result = self.text_extractor.claude_service._make_claude_request(extraction_prompt, 'data_extraction')

            # DEBUG: Save Claude response
            if self.debug_logger:
                self.debug_logger.save_step("03_claude_response", result, "json")

            if result["success"]:
                extracted_data = result["data"]

                # DEBUG: Save raw extracted data
                if self.debug_logger:
                    self.debug_logger.save_step("04_raw_extracted_data_of_LLM_Response", extracted_data, "json")

                # If the data is already a dict (successfully parsed), validate it
                if isinstance(extracted_data, dict):
                    try:
                        # Validate JSON structure
                        json_str = json.dumps(extracted_data)
                        validated_data = json.loads(json_str)

                        # DEBUG: Save validated data
                        if self.debug_logger:
                            self.debug_logger.save_step("05_validated_json_extracted_data", validated_data, "json")

                        # Perform aggressive row count validation
                        #validated_data = self.text_extractor._validate_and_enhance_table_rows(validated_data, raw_text, schema)

                        log_progress("[OK] Claude text-based extraction complete")

                        return {
                            "success": True,
                            "extracted_data": validated_data,
                            "extraction_time": time.time() - step_start,
                            "extraction_method": "claude_text_with_schema"
                        }
                    except (TypeError, json.JSONDecodeError) as json_error:
                        log_progress(f"[WARNING] JSON validation issue: {json_error}")
                        return {
                            "success": True,
                            "extracted_data": extracted_data,
                            "extraction_time": time.time() - step_start,
                            "json_warning": f"JSON validation issue: {str(json_error)}"
                        }
                else:
                    # If extracted_data is a string (raw response), try to parse it
                    try:
                        if isinstance(extracted_data, str):
                            # Clean and parse the JSON string
                            cleaned_json = self.text_extractor._clean_json_response(extracted_data)
                            validated_data = json.loads(cleaned_json)

                            log_progress("[OK] Claude text-based extraction complete")

                            return {
                                "success": True,
                                "extracted_data": validated_data,
                                "extraction_time": time.time() - step_start,
                                "extraction_method": "claude_text_with_schema_parsed"
                            }
                        else:
                            # Return as-is with warning
                            return {
                                "success": True,
                                "extracted_data": extracted_data,
                                "extraction_time": time.time() - step_start,
                                "json_warning": f"Unexpected data type: {type(extracted_data)}"
                            }
                    except json.JSONDecodeError as parse_error:
                        return {
                            "success": False,
                            "error": f"JSON parsing failed: {str(parse_error)}",
                            "raw_response": str(extracted_data)[:500],  # First 500 chars for debugging
                            "extraction_time": time.time() - step_start
                        }
            else:
                return {
                    "success": False,
                    "error": f"Claude text-based extraction failed: {result.get('error')}",
                    "extraction_time": time.time() - step_start
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Claude extraction failed: {str(e)}",
                "extraction_time": time.time() - step_start
            }

    # Removed _extract_from_uploaded_file method - PDF upload to Claude was unnecessary
    # Only vision images are used for validation, saving significant tokens

    def _step3_schema_text_extraction(self, pdf_path: str, schema: dict, page_num: int, log_progress) -> dict:
        """Step 3: Use SchemaTextExtractor for proven text-based extraction"""

        step_start = time.time()

        try:
            # Use SchemaTextExtractor's extract_with_schema_from_text method
            text_result = self.text_extractor.extract_raw_text(pdf_path, page_num)

            if not text_result["success"]:
                return {
                    "success": False,
                    "error": f"Text extraction failed: {text_result.get('error')}",
                    "extraction_time": time.time() - step_start
                }

            # Extract structured data using schema
            extraction_result = self.text_extractor.extract_with_schema_from_text(
                text_result["raw_text"], schema
            )

            if extraction_result["success"]:
                log_progress("[OK] Schema text extraction complete")

                return {
                    "success": True,
                    "extracted_data": extraction_result["extracted_data"],
                    "extraction_time": time.time() - step_start,
                    "extraction_method": "schema_text_extractor"
                }
            else:
                return {
                    "success": False,
                    "error": f"Schema extraction failed: {extraction_result.get('error')}",
                    "extraction_time": time.time() - step_start
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Schema text extraction failed: {str(e)}",
                "extraction_time": time.time() - step_start
            }

    def _step4_token_efficient_validation(self, pdf_path: str, extracted_data: dict, schema: dict,
                                        page_num: int, max_rounds: int, target_accuracy: float,
                                        vision_image_file_id: str, log_progress) -> dict:
        """Step 4: Use SchemaTextExtractor's multi-round validation with uploaded image for token efficiency"""

        step_start = time.time()

        try:
            # Debug: Log what file_id we received
            log_progress(f"DEBUG: Received vision_image_file_id: {vision_image_file_id}")

            if not vision_image_file_id:
                log_progress("[WARNING] No vision image uploaded, using standard validation...")
                # Fallback to basic validation if no image
                return {
                    "success": True,
                    "final_data": extracted_data,
                    "validation_rounds_completed": 0,
                    "final_accuracy_estimate": 0.85,
                    "total_corrections_applied": 0,
                    "validation_time": time.time() - step_start,
                    "token_efficient": False,
                    # Keep old names for backward compatibility
                    "validation_rounds": 0,
                    "accuracy_estimate": 0.85,
                    "corrections_applied": 0
                }

            log_progress(f"[VALIDATE] Using token-efficient validation with image file: {vision_image_file_id}")

            # Use provider-specific validation logic
            if hasattr(self.text_extractor, 'provider') and self.text_extractor.provider == 'google':
                # Use Gemini's multi-round validation with simple prompts
                log_progress(f"[VALIDATE] Using Gemini-optimized multi-round validation")

                validation_result = self._gemini_multi_round_validation(
                    pdf_path, extracted_data, schema, page_num, max_rounds, target_accuracy, vision_image_file_id
                )
            else:
                # Use Claude's detailed visual inspector
                # This is more token efficient as it reuses the uploaded image
                # Create page-specific file ID mapping for this page
                page_file_ids = {page_num: vision_image_file_id} if vision_image_file_id else None

                validation_result = self.text_extractor.visual_inspector.multi_round_visual_validation(
                    pdf_path, extracted_data, schema, page_num, max_rounds, target_accuracy,
                    vision_image_file_id, page_file_ids
                )

            # DEBUG: Log validation_result contents
            print(f"\nDEBUG: Validation Result from multi_round_visual_validation:")
            print(f"  validation_result keys: {list(validation_result.keys())}")
            print(f"  rounds_performed: {validation_result.get('rounds_performed')}")
            print(f"  validation_rounds_completed: {validation_result.get('validation_rounds_completed')}")
            print(f"  accuracy_estimate: {validation_result.get('accuracy_estimate')}")
            print(f"  final_accuracy_estimate: {validation_result.get('final_accuracy_estimate')}")
            print(f"  total_corrections: {validation_result.get('total_corrections')}")
            print(f"  total_corrections_applied: {validation_result.get('total_corrections_applied')}")

            if validation_result["success"]:
                # Use the correct field names from the multi_round_visual_validation result
                rounds_completed = validation_result.get("validation_rounds_completed", 0)
                final_accuracy = validation_result.get("final_accuracy_estimate", 0.9)
                total_corrections = validation_result.get("total_corrections_applied", 0)

                log_progress(f"[OK] Token-efficient validation complete: {final_accuracy:.0%} accuracy")

                return {
                    "success": True,
                    "final_data": validation_result["extracted_data"],
                    "validation_rounds_completed": rounds_completed,
                    "final_accuracy_estimate": final_accuracy,
                    "total_corrections_applied": total_corrections,
                    "validation_time": time.time() - step_start,
                    "token_efficient": True,
                    # Keep old names for backward compatibility
                    "validation_rounds": rounds_completed,
                    "accuracy_estimate": final_accuracy,
                    "corrections_applied": total_corrections
                }
            else:
                return {
                    "success": False,
                    "error": f"Token-efficient validation failed: {validation_result.get('error')}",
                    "final_data": extracted_data,
                    "validation_time": time.time() - step_start
                }

        except Exception as e:
            log_progress(f"ERROR: Token-efficient validation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Token-efficient validation failed: {str(e)}",
                "final_data": extracted_data,
                "validation_time": time.time() - step_start
            }

    def _step4_enhanced_validate_correct(self, file_id: str, extracted_data: dict, schema: dict,
                                        max_rounds: int, target_accuracy: float, log_progress) -> dict:
        """Step 4: Enhanced validation and correction with specialized fixes"""

        step_start = time.time()

        try:
            log_progress("[FIX] Running specialized table and key-value fixes...")

            # Use enhanced validation with specialized fixes for column shifts and key-value issues
            validation_result = self.enhanced_validator.enhanced_validate_and_correct(
                file_id, extracted_data, schema, max_rounds, log_progress
            )

            validation_result["total_validation_time"] = time.time() - step_start

            if validation_result["success"]:
                accuracy = validation_result.get('accuracy_estimate', 0.95)
                total_fixes = validation_result.get('total_fixes', 0)
                specialized_fixes = validation_result.get('specialized_fixes', {})

                log_progress(f"[OK] Enhanced validation complete: {accuracy:.0%} accuracy")
                log_progress(f"[FIX] Applied {total_fixes} total fixes")

                if specialized_fixes:
                    table_fixes = specialized_fixes.get('table_fixes', 0)
                    kv_fixes = specialized_fixes.get('key_value_fixes', 0)
                    if table_fixes > 0:
                        log_progress(f"📊 Fixed {table_fixes} table column alignment issues")
                    if kv_fixes > 0:
                        log_progress(f"🔑 Fixed {kv_fixes} key-value association issues")

            return validation_result

        except Exception as e:
            log_progress(f"ERROR: Enhanced validation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "final_data": extracted_data,
                "total_validation_time": time.time() - step_start
            }

    def _gemini_multi_round_validation(self, pdf_path: str, extracted_data: dict, schema: dict,
                                     page_num: int, max_rounds: int, target_accuracy: float,
                                     vision_image_file_id: str = None) -> dict:
        """Multi-round validation for Gemini using simple prompts"""
        import json
        import time

        validation_history = []
        rounds_performed = 0
        current_data = extracted_data.copy()
        final_accuracy = 0.85  # Default starting accuracy
        total_corrections = 0

        for round_num in range(1, max_rounds + 1):
            rounds_performed = round_num

            # Build simple validation prompt
            schema_str = json.dumps(schema, indent=2)
            data_str = json.dumps(current_data, indent=2)
            prompt = f"""
You are a data validation specialist. Compare the extracted data against the actual PDF image to verify accuracy.

ROUND {round_num} of {max_rounds} - VALIDATION WITH CORRECTIONS:

EXTRACTED DATA:
{data_str}

CRITICAL VALIDATION RULES:

1. **TEXT TRUNCATION HANDLING - CRITICAL RULE:**
   - **ALWAYS PRESERVE the longer extracted text over shorter visual text**
   - If extracted data = "Dental Insurance S125" but image shows = "Dental Insurance", KEEP "Dental Insurance S125"
   - If extracted data = "Minnesota Federal Loan Assessment" but image shows = "Minnesota Federal Lo...", KEEP the full text
   - **NEVER truncate good extracted data to match visually truncated image text**
   - Only change if extracted text is completely wrong (different meaning entirely)

0. **DATE FORMAT STANDARDIZATION:**
   - Convert dates to clean format: "YYYY-MM-DD" (e.g., "2024-12-17")
   - Remove time components: "2024-12-17T00:00:00" should become "2024-12-17"
   - Apply to ALL date fields consistently

2. **TABLE ROW COUNT ACCURACY:**
   - Count EXACTLY how many rows you see in each table in the PDF
   - Do NOT add extra rows that don't exist in the PDF
   - Flag if extracted data has more rows than visually present

3. **COLUMN ALIGNMENT VALIDATION:**
   - For deduction tables: Check if values are in correct columns
   - Look for shifts: "B5" appearing in CalCode instead of Frequency column
   - Verify each value is under the correct column header

4. **COMPLETE DATA PRESERVATION:**
   - In corrected_data, include the ENTIRE JSON structure
   - Only modify the specific fields that have errors
   - Keep all other data unchanged from the original extraction

INSTRUCTIONS:
1. **PRESERVE FULL TEXT**: Never shorten extracted text to match truncated visual text
2. Count table rows precisely - never add rows that don't exist
3. Check column alignment carefully for deduction information
4. Clean all date formats to YYYY-MM-DD (remove time components)
5. Return complete JSON structure in corrected_data (not just the problem section)
6. Only set accuracy_estimate to 1.0 (100%) if NO issues are found in this round
7. Return VALIDATION RESULTS in JSON format ONLY - no extra commentary
Return JSON with this structure:
{{
    "validation_passed": true/false,
    "accuracy_estimate": 0.95,
    "issues_found": [
        {{
            "field": "field_name",
            "issue": "description of issue",
            "suggested_correction": "corrected value"
        }}
    ],
    "corrected_data": {{}} // COMPLETE JSON with all fields, only corrections applied
}}
"""

            # Perform validation round
            if vision_image_file_id:
                result = self.text_extractor.ai_service.validate_with_vision_file(
                    vision_image_file_id, prompt
                )
            else:
                image_data = self.text_extractor.vision_extractor.convert_pdf_to_image(pdf_path, page_num)
                result = self.text_extractor.ai_service.validate_with_vision(image_data, current_data, schema)

            if not result.get('success'):
                break

            # Extract validation data
            if vision_image_file_id:
                validation_data = result.get('data', {})
            else:
                validation_data = result.get('validation_result', {})

            validation_history.append({
                'round': round_num,
                'accuracy_estimate': validation_data.get('accuracy_estimate', 0.85),
                'issues_found': validation_data.get('issues_found', []),
                'validation_passed': validation_data.get('validation_passed', False)
            })

            final_accuracy = validation_data.get('accuracy_estimate', 0.85)
            issues_found = validation_data.get('issues_found', [])
            total_corrections += len(issues_found)

            # Apply corrections if available
            corrected_data = validation_data.get('corrected_data')
            if corrected_data:
                print(f"[DEBUG] Round {round_num}: Applying corrections to data")
                print(f"[DEBUG] Corrected data keys: {list(corrected_data.keys()) if isinstance(corrected_data, dict) else 'Not a dict'}")
                current_data = corrected_data
            else:
                print(f"[DEBUG] Round {round_num}: No corrected_data found in validation response")
                print(f"[DEBUG] validation_data keys: {list(validation_data.keys()) if isinstance(validation_data, dict) else 'Not a dict'}")

            # Only stop if no issues found (true 100% accuracy)
            if not issues_found and validation_data.get('validation_passed', False):
                break

            # Check if target accuracy reached (but continue if we just applied corrections)
            if final_accuracy >= target_accuracy and not issues_found:
                break

        return {
            'success': True,
            'validation_rounds_completed': rounds_performed,
            'rounds_performed': rounds_performed,
            'accuracy_estimate': final_accuracy,
            'final_accuracy_estimate': final_accuracy,
            'total_corrections': total_corrections,
            'extracted_data': current_data,
            'validation_history': validation_history,
            'target_accuracy_reached': final_accuracy >= target_accuracy
        }

    def _step4_validate_correct(self, file_id: str, extracted_data: dict, schema: dict,
                               max_rounds: int, target_accuracy: float, log_progress) -> dict:
        """Step 4: Standard validation and correction (fallback)"""

        step_start = time.time()

        try:
            validation_result = self.validator_corrector.validate_and_correct_iteratively(
                file_id, extracted_data, schema, max_rounds, target_accuracy, log_progress
            )

            validation_result["total_validation_time"] = time.time() - step_start

            if validation_result["success"]:
                log_progress(f"[OK] Validation complete: {validation_result['final_accuracy_estimate']:.0%} accuracy")

            return validation_result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "final_data": extracted_data,
                "total_validation_time": time.time() - step_start
            }

    def _compile_workflow_summary(self, pipeline_steps: dict) -> dict:
        """Compile comprehensive workflow summary"""

        step4 = pipeline_steps.get("step4_validation", {})

        return {
            "preprocessing_success": pipeline_steps.get("step1_preprocess", {}).get("success", False),
            "upload_success": pipeline_steps.get("step2_upload", {}).get("success", False),
            "text_extraction_success": pipeline_steps.get("step3_text_extraction", {}).get("success", False),
            "validation_success": step4.get("success", False),
            "final_accuracy": step4.get("final_accuracy_estimate", 0),
            "validation_rounds_completed": step4.get("validation_rounds_completed", 0),
            "total_corrections_applied": step4.get("total_corrections_applied", 0),
            "target_accuracy_achieved": step4.get("target_accuracy_achieved", False),
            "processing_times": {
                "preprocessing": pipeline_steps.get("step1_preprocess", {}).get("processing_time", 0),
                "upload": pipeline_steps.get("step2_upload", {}).get("upload_time", 0),
                "text_extraction": pipeline_steps.get("step3_text_extraction", {}).get("extraction_time", 0),
                "validation": step4.get("total_validation_time", 0)
            }
        }

    def _cleanup_temp_files(self, *file_paths):
        """Clean up temporary files"""

        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete {file_path}: {e}")