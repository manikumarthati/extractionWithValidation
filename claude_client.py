"""
Claude API client configuration and utilities for document processing
"""

import os
import base64
import json
from typing import Dict, List, Optional, Union
from anthropic import Anthropic
import logging
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeClient:
    """Claude API client for document processing tasks"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude client"""
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")

        try:
            # Initialize Anthropic client with just the API key
            # Avoid potential proxy parameter conflicts
            self.client = Anthropic(api_key=self.api_key)
        except TypeError as e:
            if "proxies" in str(e):
                # Fallback: try initializing without any potential proxy parameters
                # Clear all possible proxy-related environment variables
                proxy_vars = [
                    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                    'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'
                ]
                old_values = {}

                print(f"WARNING: Proxy parameter conflict detected, clearing proxy environment variables...")

                for var in proxy_vars:
                    if var in os.environ:
                        old_values[var] = os.environ[var]
                        del os.environ[var]
                        print(f"   Cleared {var}")

                try:
                    # Try again without proxy environment variables
                    self.client = Anthropic(api_key=self.api_key)
                    print(f"SUCCESS: Claude client initialized successfully after clearing proxy vars")
                except Exception as e2:
                    print(f"ERROR: Claude initialization failed even after clearing proxies: {e2}")
                    raise e2
                finally:
                    # Restore proxy environment variables
                    for var, value in old_values.items():
                        os.environ[var] = value
            else:
                raise e

        self.default_model = "claude-3-5-sonnet-20241022"

    def extract_data_with_schema(self,
                                image_data: bytes,
                                schema: Dict,
                                model: str = None) -> Dict:
        """Extract structured data from image using Claude vision"""

        model = model or self.default_model

        # Encode image to base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        # Create the prompt with schema instructions
        prompt = f"""You are an expert document data extraction system. Extract information from this document image and return it as JSON that strictly follows the provided schema.

SCHEMA TO FOLLOW:
{json.dumps(schema, indent=2)}

CRITICAL JSON REQUIREMENTS:
- Return ONLY valid JSON, no additional text or explanations
- Use double quotes for all strings
- Escape special characters properly (\", \\, etc.)
- Use null for missing values, not empty strings unless specified
- Follow the exact field names and types in the schema
- For arrays, return empty array [] if no items found
- For objects, include all required fields even if null

ACCURACY REQUIREMENTS:
- Pay special attention to table column alignment
- When extracting tables, ensure values are in correct columns
- If a cell appears empty, do not shift subsequent values
- Validate that text values go to text fields, numbers to number fields
- For key-value associations, ensure proper field mapping

Extract the data now and return only the JSON response:"""

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_b64
                                }
                            }
                        ]
                    }
                ]
            )

            # Extract and clean the response
            response_text = response.content[0].text.strip()

            # Clean the response to ensure valid JSON
            cleaned_response = self._clean_json_response(response_text)

            # Parse JSON
            try:
                result = json.loads(cleaned_response)
                logger.info(f"Successfully extracted data using {model}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Response text: {cleaned_response}")
                return {"error": f"Failed to parse JSON: {str(e)}", "raw_response": cleaned_response}

        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            return {"error": f"Claude API error: {str(e)}"}

    def validate_and_fix_data(self,
                             extracted_data: Dict,
                             schema: Dict,
                             image_data: bytes,
                             focus_area: str = "general",
                             model: str = None) -> Dict:
        """Validate and fix extracted data with focus on specific issues"""

        model = model or self.default_model

        # Create focused prompts based on the focus area
        if focus_area == "table_alignment":
            focus_instructions = """
FOCUS ONLY ON TABLE COLUMN ALIGNMENT:
- Identify tables in the document
- Check if values appear in wrong columns due to empty cells
- Look for data type mismatches (text in number columns, numbers in text columns)
- Ensure proper column-to-field mapping
- Fix any column shifting issues
"""
        elif focus_area == "key_value_association":
            focus_instructions = """
FOCUS ONLY ON KEY-VALUE FIELD ASSOCIATIONS:
- Check form fields and their values
- When a field has no value, ensure subsequent values don't shift to wrong keys
- Validate data types match field expectations (numbers in numeric fields, text in text fields)
- Fix any field mapping errors
"""
        else:
            focus_instructions = "Perform general validation and correction of the extracted data."

        # Encode image to base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        prompt = f"""You are a document validation expert. Review the extracted data against the original document and fix any errors.

{focus_instructions}

ORIGINAL SCHEMA:
{json.dumps(schema, indent=2)}

EXTRACTED DATA TO VALIDATE:
{json.dumps(extracted_data, indent=2)}

VALIDATION INSTRUCTIONS:
1. Compare extracted data with the document image
2. Check for the specific issues mentioned in the focus area
3. Fix any errors found
4. Return corrected JSON that follows the schema exactly

CRITICAL JSON REQUIREMENTS:
- Return ONLY valid JSON, no additional text or explanations
- Use double quotes for all strings
- Maintain exact field names from schema
- Use null for truly missing values

Return the corrected JSON:"""

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_b64
                                }
                            }
                        ]
                    }
                ]
            )

            # Extract and clean the response
            response_text = response.content[0].text.strip()
            cleaned_response = self._clean_json_response(response_text)

            try:
                result = json.loads(cleaned_response)
                logger.info(f"Successfully validated data with focus: {focus_area}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in validation: {e}")
                return extracted_data  # Return original if validation fails

        except Exception as e:
            logger.error(f"Claude validation error: {str(e)}")
            return extracted_data  # Return original if validation fails

    def _clean_json_response(self, response_text: str) -> str:
        """Clean Claude response to ensure valid JSON"""

        # Remove any markdown formatting
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            if end != -1:
                response_text = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            if end != -1:
                response_text = response_text[start:end].strip()

        # Remove any leading/trailing text that's not JSON
        response_text = response_text.strip()

        # Find JSON start and end
        json_start = -1
        json_end = -1

        for i, char in enumerate(response_text):
            if char == '{':
                json_start = i
                break

        if json_start == -1:
            return response_text  # No JSON found, return as-is

        # Find matching closing brace
        brace_count = 0
        for i in range(json_start, len(response_text)):
            if response_text[i] == '{':
                brace_count += 1
            elif response_text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i
                    break

        if json_end != -1:
            response_text = response_text[json_start:json_end + 1]

        return response_text

def get_claude_client() -> ClaudeClient:
    """Get a configured Claude client instance"""
    return ClaudeClient()

# Test the client
if __name__ == "__main__":
    try:
        client = get_claude_client()
        print("✅ Claude client initialized successfully")
        print(f"Using model: {client.default_model}")
    except Exception as e:
        print(f"❌ Failed to initialize Claude client: {e}")
        print("Make sure ANTHROPIC_API_KEY environment variable is set")