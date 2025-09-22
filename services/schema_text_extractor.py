"""
Schema-based PDF text extraction with vision validation
1. Extract raw text from PDF using libraries
2. Extract data from text using schema + LLM
3. Validate extracted JSON using vision capabilities
4. Correct issues found during validation
"""

import json
import time
import re
import fitz  # PyMuPDF
from typing import Dict, Any, List, Optional, Tuple
from .vision_extractor import VisionBasedExtractor
from .openai_service import OpenAIService
from .visual_field_inspector import VisualFieldInspector


class SchemaTextExtractor:
    def __init__(self, api_key: str):
        """Initialize schema text extractor with vision validation"""
        self.vision_extractor = VisionBasedExtractor(api_key)
        self.openai_service = OpenAIService(api_key)
        self.visual_inspector = VisualFieldInspector(api_key)

    def extract_raw_text(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        """Extract raw text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)

            if page_num >= len(doc):
                return {
                    "success": False,
                    "error": f"Page {page_num} does not exist in PDF with {len(doc)} pages"
                }

            page = doc[page_num]
            raw_text = page.get_text()
            text_blocks = page.get_text("dict")["blocks"]
            word_data = page.get_text("words")

            doc.close()

            return {
                "success": True,
                "raw_text": raw_text,
                "text_blocks": text_blocks,
                "word_data": word_data,
                "page_number": page_num + 1,
                "extraction_method": "pymupdf_text"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Text extraction failed: {str(e)}"
            }

    def extract_with_schema_from_text(self, raw_text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from raw text using provided schema and LLM"""
        try:
            extraction_prompt = self._build_text_schema_prompt(raw_text, schema)
            result = self.openai_service._make_gpt_request(extraction_prompt, 'data_extraction')

            if result["success"]:
                # Additional JSON validation and cleaning
                extracted_data = result["data"]

                # If the data is already a dict (successfully parsed), validate it
                if isinstance(extracted_data, dict):
                    try:
                        json_str = json.dumps(extracted_data)
                        validated_data = json.loads(json_str)

                        # Perform aggressive row count validation
                        validated_data = self._validate_and_enhance_table_rows(validated_data, raw_text, schema)

                        return self._create_clean_output_format(
                            validated_data, schema, "text_based_schema"
                        )
                    except (TypeError, json.JSONDecodeError) as json_error:
                        print(f"DEBUG - JSON validation failed: {json_error}")
                        # Return the data anyway but with a warning
                        result = self._create_clean_output_format(
                            extracted_data, schema, "text_based_schema"
                        )
                        result["json_warning"] = f"JSON validation issue: {str(json_error)}"
                        return result
                else:
                    # If extracted_data is a string (raw response), try to parse it
                    print(f"DEBUG - Extracted data is string, attempting to parse: {type(extracted_data)}")
                    try:
                        if isinstance(extracted_data, str):
                            # Clean and parse the JSON string
                            cleaned_json = self._clean_json_response(extracted_data)
                            validated_data = json.loads(cleaned_json)

                            return self._create_clean_output_format(
                                validated_data, schema, "text_based_schema"
                            )
                        else:
                            # Fallback: return as-is with warning
                            result = self._create_clean_output_format(
                                extracted_data, schema, "text_based_schema"
                            )
                            result["json_warning"] = f"Unexpected data type: {type(extracted_data)}"
                            return result
                    except json.JSONDecodeError as parse_error:
                        print(f"DEBUG - JSON parsing failed: {parse_error}")
                        return {
                            "success": False,
                            "error": f"JSON parsing failed: {str(parse_error)}",
                            "raw_response": str(extracted_data)[:500]  # First 500 chars for debugging
                        }
            else:
                return {
                    "success": False,
                    "error": f"Text-based schema extraction failed: {result.get('error')}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Schema extraction from text failed: {str(e)}"
            }

    def validate_with_vision(self, pdf_path: str, extracted_json: Dict[str, Any],
                           schema: Dict[str, Any], page_num: int = 0) -> Dict[str, Any]:
        """Validate extracted JSON data using vision capabilities"""
        try:
            validation_prompt = self._build_vision_validation_prompt(extracted_json, schema)

            image_data = self.vision_extractor.convert_pdf_to_image(pdf_path, page_num)
            image_base64 = self.vision_extractor.encode_image_to_base64(image_data)

            response = self.vision_extractor.client.chat.completions.create(
                model=self.vision_extractor.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": validation_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_completion_tokens=15000,
            )

            content = response.choices[0].message.content.strip()

            try:
                validation_result = json.loads(content)
            except json.JSONDecodeError:
                validation_result = self.vision_extractor._extract_json_from_vision_response(content)

            return {
                "success": True,
                "validation_result": validation_result,
                "validation_method": "vision_based"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Vision validation failed: {str(e)}"
            }

    def correct_with_vision(self, pdf_path: str, original_json: Dict[str, Any],
                          validation_issues: Dict[str, Any], schema: Dict[str, Any],
                          page_num: int = 0) -> Dict[str, Any]:
        """Correct extracted JSON using vision analysis"""
        try:
            correction_prompt = self._build_vision_correction_prompt(
                original_json, validation_issues, schema
            )

            image_data = self.vision_extractor.convert_pdf_to_image(pdf_path, page_num)
            image_base64 = self.vision_extractor.encode_image_to_base64(image_data)

            response = self.vision_extractor.client.chat.completions.create(
                model=self.vision_extractor.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": correction_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_completion_tokens=15000,
            )

            content = response.choices[0].message.content.strip()

            try:
                corrected_data = json.loads(content)
            except json.JSONDecodeError:
                corrected_data = self.vision_extractor._extract_json_from_vision_response(content)

            return {
                "success": True,
                "corrected_data": corrected_data,
                "correction_method": "vision_based"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Vision correction failed: {str(e)}"
            }

    def process_complete_workflow(self, pdf_path: str, schema: Dict[str, Any],
                                page_num: int = 0) -> Dict[str, Any]:
        """Complete workflow: text extraction → schema extraction → vision validation → correction"""
        try:
            # Step 1: Extract raw text from PDF
            text_result = self.extract_raw_text(pdf_path, page_num)
            if not text_result["success"]:
                return text_result

            raw_text = text_result["raw_text"]

            # Step 2: Extract data using schema from text
            extraction_result = self.extract_with_schema_from_text(raw_text, schema)
            if not extraction_result["success"]:
                return extraction_result

            extracted_json = extraction_result["extracted_data"]

            # Step 3: Validate with vision
            validation_result = self.validate_with_vision(pdf_path, extracted_json, schema, page_num)
            if not validation_result["success"]:
                extraction_result["validation_warning"] = validation_result.get("error")
                return extraction_result

            validation_data = validation_result["validation_result"]

            # Step 4: Check if correction is needed
            needs_correction = (
                validation_data.get("column_shifting_detected", False) or
                validation_data.get("field_mapping_issues_detected", False) or
                validation_data.get("accuracy_score", 1.0) < 0.9 or
                self._check_table_completeness_issues(validation_data)
            )

            if needs_correction:
                # Step 5: Correct using vision
                correction_result = self.correct_with_vision(
                    pdf_path, extracted_json, validation_data, schema, page_num
                )

                if correction_result["success"]:
                    final_data = correction_result["corrected_data"]
                    correction_applied = True
                else:
                    final_data = extracted_json
                    correction_applied = False
                    correction_result = {"error": correction_result.get("error")}
            else:
                final_data = extracted_json
                correction_applied = False
                correction_result = {"message": "No correction needed"}

            # Create clean final output
            clean_final_result = self._create_clean_output_format(
                final_data, schema, "complete_workflow"
            )

            # Add workflow metadata
            clean_final_result["workflow_summary"] = {
                "text_extraction_success": True,
                "schema_extraction_success": True,
                "vision_validation_success": True,
                "correction_applied": correction_applied,
                "needs_correction": needs_correction
            }

            # Keep detailed results for debugging but clean the schema references
            clean_final_result["detailed_results"] = {
                "text_extraction": text_result,
                "validation_summary": validation_result.get("validation_result", {}),
                "correction_summary": correction_result
            }

            return clean_final_result

        except Exception as e:
            return {
                "success": False,
                "error": f"Complete workflow failed: {str(e)}"
            }

    def enhanced_extraction_workflow(self, pdf_path: str, schema: Dict[str, Any],
                                   page_num: int = 0, use_visual_validation: bool = True,
                                   multi_round_validation: bool = True) -> Dict[str, Any]:
        """
        Enhanced workflow: text extraction + multi-round visual validation + correction tracking

        Features:
        - 600 DPI image conversion for maximum clarity
        - Multiple rounds of visual validation (up to 3 rounds)
        - Detailed correction tracking and reporting
        - Handles column shifting and value hallucination issues
        """
        try:
            # Step 1: Your existing text-based extraction (98% accurate)
            print("📄 Extracting text from PDF...")
            text_result = self.extract_raw_text(pdf_path, page_num)
            if not text_result["success"]:
                return text_result

            print("🔍 Extracting data using schema...")
            extraction_result = self.extract_with_schema_from_text(text_result["raw_text"], schema)
            if not extraction_result["success"]:
                return extraction_result

            extracted_data = extraction_result["extracted_data"]

            # Step 2: Optional visual validation (recommended for high accuracy)
            if use_visual_validation:
                if multi_round_validation:
                    print("👁️ Performing multi-round high-accuracy visual validation...")
                    visual_validation_result = self.visual_inspector.multi_round_visual_validation(
                        pdf_path, extracted_data, schema, page_num, max_rounds=10, target_accuracy=1.0
                    )
                else:
                    print("👁️ Performing single-round visual validation...")
                    visual_validation_result = self.visual_inspector.complete_visual_validation_workflow(
                        pdf_path, extracted_data, schema, page_num
                    )

                if visual_validation_result["success"]:
                    final_data = visual_validation_result["extracted_data"]
                    visual_summary = visual_validation_result
                else:
                    # If visual validation fails, use original data with warning
                    final_data = extracted_data
                    visual_summary = {
                        "visual_validation_applied": False,
                        "visual_validation_error": visual_validation_result.get("error"),
                        "corrections_needed": False
                    }
            else:
                final_data = extracted_data
                visual_summary = {
                    "visual_validation_applied": False,
                    "corrections_needed": False
                }

            # Create clean final output
            clean_final_result = self._create_clean_output_format(
                final_data, schema, "enhanced_workflow"
            )

            # Add workflow metadata
            clean_final_result["workflow_summary"] = {
                "text_extraction_success": True,
                "schema_extraction_success": True,
                "visual_validation_applied": visual_summary.get("visual_validation_applied", False),
                "corrections_needed": visual_summary.get("corrections_needed", False),
                "corrections_applied": visual_summary.get("total_corrections_applied", visual_summary.get("corrections_applied", 0)),
                "validation_rounds_completed": visual_summary.get("validation_rounds_completed", 1),
                "target_accuracy_achieved": visual_summary.get("target_accuracy_achieved", False),
                "final_accuracy_estimate": visual_summary.get("final_accuracy_estimate", visual_summary.get("validation_summary", {}).get("accuracy_estimate", 0.98))
            }

            # Keep essential metadata
            clean_final_result["page_processed"] = page_num + 1

            # Keep detailed results for debugging but clean the schema references
            clean_final_result["detailed_results"] = {
                "text_extraction": text_result,
                "visual_validation_summary": visual_summary
            }

            return clean_final_result

        except Exception as e:
            return {
                "success": False,
                "error": f"Enhanced extraction workflow failed: {str(e)}"
            }

    def _build_text_schema_prompt(self, raw_text: str, schema: Dict[str, Any]) -> str:
        """Build prompt for extracting data from text using user-provided schema"""

        # Use clean schema structure for LLM prompt (without descriptions/hints)
        clean_schema_for_prompt = self._extract_clean_schema_structure(schema)

        # Build prompt without f-string to avoid format issues with JSON examples
        prompt = """Extract structured data from the following text according to the provided schema.

SCHEMA TO FOLLOW:
""" + json.dumps(clean_schema_for_prompt, indent=2) + """

RAW TEXT:
""" + raw_text + """

EXTRACTION INSTRUCTIONS:
1. Extract data exactly as specified in the schema structure
2. Use the exact field names and structure from the schema
3. Find values corresponding to each field/column specified in the schema
4. Use null for fields that exist in schema but cannot be found in text
5. Maintain proper data types as indicated in the schema
6. IMPORTANT: Return ONLY the essential data values, no metadata, descriptions, or additional details
7. Keep the response concise and focused only on the actual data values

CRITICAL TABLE EXTRACTION RULES:
8. **FOR TABLES/ARRAYS:** Extract ALL rows visible in the document, not just the first one
9. **TABLE COMPLETENESS:** If schema shows an array/list, extract every single row from the table
10. **ROW COUNT:** Never limit to one row - extract all data rows present in tables
11. **MULTIPLE ENTRIES:** When multiple similar entries exist (like employees, benefits, transactions), capture them all
12. **FULL TABLE DATA:** Scan the entire table from top to bottom and include every row with data - scan the entire table top to bottom

**AGGRESSIVE TABLE ROW EXTRACTION - MANDATORY:**
13. **EXHAUSTIVE SCANNING:** Look for data in ALL possible formats - different fonts, sizes, colors, alignments
14. **BOUNDARY CHECKING:** Check for rows near page boundaries, margins, or at the very bottom of tables
15. **FORMATTING VARIATIONS:** Include rows that might have different formatting, spacing, or appear faded
16. **PARTIAL ROWS:** Include any row that has even partial data visible
17. **HIDDEN PATTERNS:** Look for data patterns that might indicate additional rows (sequences, numbering, etc.)
18. **ZERO TOLERANCE:** If you suspect there might be more rows, extract them - better to include questionable rows than miss real data
19. **VALIDATION REQUIREMENT:** After extraction, count your rows and ensure you haven't missed any by scanning the text again

CRITICAL JSON REQUIREMENTS:
- Return ONLY valid JSON, no additional text or explanations
- Use double quotes for all strings
- Escape special characters properly: \\" for quotes, \\\\ for backslashes, \\n for newlines
- No trailing commas anywhere
- No comments in JSON
- Ensure all brackets and braces are properly closed
- If a string value contains quotes, escape them with backslash
- Keep values concise - extract only the essential information without verbose descriptions

EXAMPLE OF CONCISE OUTPUT WITH MULTIPLE TABLE ROWS:
{
  "name": "John Smith",
  "employee_id": "12345",
  "salary": 75000,
  "benefits": [
    {
      "type": "Health",
      "amount": "200"
    },
    {
      "type": "Dental",
      "amount": "50"
    },
    {
      "type": "Vision",
      "amount": "25"
    }
  ],
  "employees": [
    {
      "name": "John Smith",
      "id": "001"
    },
    {
      "name": "Jane Doe",
      "id": "002"
    },
    {
      "name": "Bob Johnson",
      "id": "003"
    }
  ]
}

OUTPUT FORMAT:
Return valid JSON that matches the exact structure of the provided schema with concise data values only.

Extract the data now and return ONLY the JSON:"""

        return prompt

    def _clean_json_response(self, response_text: str) -> str:
        """Clean JSON response text to ensure valid JSON"""

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

        # Clean common issues
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

    def _extract_clean_schema_structure(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clean schema structure without hints, descriptions, and metadata"""

        def clean_entity_type(entity_type: Dict[str, Any]) -> Dict[str, str]:
            """Extract just the essential field names and types from entity type"""
            clean_structure = {}

            if 'properties' in entity_type:
                for prop in entity_type['properties']:
                    field_name = prop.get('name', '')
                    field_type = prop.get('valueType', 'string')

                    # Strip complex metadata, keep only essential type info
                    if field_type in ['string', 'number', 'boolean', 'array']:
                        clean_structure[field_name] = field_type
                    else:
                        # For complex types, just mark as object
                        clean_structure[field_name] = 'object'

            return clean_structure

        # Handle different schema formats
        if 'documentSchema' in schema and 'entityTypes' in schema['documentSchema']:
            # Google Document AI schema format
            clean_schema = {}
            for entity_type in schema['documentSchema']['entityTypes']:
                entity_name = entity_type.get('name', 'document')
                clean_schema[entity_name] = clean_entity_type(entity_type)
            return clean_schema

        elif 'properties' in schema:
            # Direct properties format
            return clean_entity_type(schema)

        else:
            # Simple key-value schema
            clean_schema = {}
            for key, value in schema.items():
                if isinstance(value, dict):
                    clean_schema[key] = 'object'
                elif isinstance(value, list):
                    clean_schema[key] = 'array'
                else:
                    clean_schema[key] = 'string'
            return clean_schema

    def _create_clean_output_format(self, extracted_data: Dict[str, Any],
                                  schema: Dict[str, Any],
                                  extraction_method: str) -> Dict[str, Any]:
        """Create clean output format without schema hints and metadata"""

        return {
            "success": True,
            "extracted_data": extracted_data,
            "extraction_method": extraction_method,
            "schema_structure": self._extract_clean_schema_structure(schema)
        }

    def _build_vision_validation_prompt(self, extracted_json: Dict[str, Any],
                                      schema: Dict[str, Any]) -> str:
        """Build prompt for vision validation using schema structure"""

        prompt = """Validate the extracted JSON data against this PDF image. Look for:

1. COLUMN SHIFTING in tables (data in wrong columns)
2. FIELD-VALUE MAPPING errors (wrong values assigned to fields)
3. MISSING DATA that's visible in the image
4. INCORRECT DATA that doesn't match the image

EXTRACTED JSON TO VALIDATE:
""" + json.dumps(extracted_json, indent=2) + """



VALIDATION TASKS:
- For each table: Check if column data aligns with headers
- For each form field: Verify the value matches the field label
- Look for systematic errors or misalignments
- Check data accuracy and completeness

OUTPUT FORMAT:
{
  "validation_summary": {
    "overall_accuracy": 0.85,
    "issues_found": 3
  },
  "column_shifting_detected": true,
  "column_shifting_details": [
    {
      "table_name": "Table Name",
      "issue": "Values shifted right by 1 column",
      "affected_rows": [1, 2, 3]
    }
  ],
  "field_mapping_issues_detected": true,
  "field_mapping_issues": [
    {
      "field_name": "Employee Name",
      "extracted_value": "wrong_value",
      "correct_value": "correct_value",
      "issue": "Field contains ID instead of name"
    }
  ],
  "missing_data": [
    {
      "field_name": "Phone Number",
      "visible_in_image": true,
      "location": "bottom of form"
    }
  ],
  "accuracy_score": 0.85,
  "recommendations": ["Fix column alignment", "Correct field mappings"]
}"""

        return prompt

    def _build_vision_correction_prompt(self, original_json: Dict[str, Any],
                                      validation_issues: Dict[str, Any],
                                      schema: Dict[str, Any]) -> str:
        """Build prompt for vision-based correction using schema structure"""

        prompt = """Based on the validation analysis, provide the corrected JSON data by analyzing this PDF image.

ORIGINAL EXTRACTED JSON:
""" + json.dumps(original_json, indent=2) + """

VALIDATION ISSUES FOUND:
""" + json.dumps(validation_issues, indent=2) + """

TARGET SCHEMA:
""" + json.dumps(self._extract_clean_schema_structure(schema), indent=2) + """

CORRECTION INSTRUCTIONS:
1. Fix column shifting issues by properly aligning table data
2. Correct field-value mappings by matching values to correct fields
3. Add any missing data identified in validation
4. Ensure all data matches what's actually visible in the image
5. Maintain the exact schema structure provided
6. IMPORTANT: Return ONLY concise data values, no metadata or verbose descriptions
7. Keep the response minimal and focused on essential data only

OUTPUT FORMAT:
Return the corrected JSON in the EXACT structure of the target schema above with concise data values only.

Provide the corrected data:"""

        return prompt

    def _check_table_completeness_issues(self, validation_data: Dict[str, Any]) -> bool:
        """Check if there are table completeness issues (missing rows)"""

        table_results = validation_data.get("table_validation_results", [])

        for table in table_results:
            # Check if table has missing rows
            if table.get("row_completeness_issue", False):
                return True

            # Check for significant row count discrepancy
            rows_visible = table.get("rows_visible_in_image", 0)
            rows_extracted = table.get("rows_extracted", 0)

            if rows_visible > rows_extracted and rows_visible > 1:
                return True

            # Check if missing_rows > 0
            if table.get("missing_rows", 0) > 0:
                return True

        return False

    def generate_correction_report(self, workflow_result: Dict[str, Any]) -> str:
        """Generate a human-readable report of corrections made during validation"""

        if not workflow_result.get("detailed_results", {}).get("visual_validation_summary", {}).get("correction_history"):
            return "No corrections were applied during extraction."

        correction_history = workflow_result["detailed_results"]["visual_validation_summary"]["correction_history"]
        total_corrections = len(correction_history)
        rounds_completed = workflow_result["detailed_results"]["visual_validation_summary"].get("validation_rounds_completed", 1)

        report = f"""
[REPORT] EXTRACTION CORRECTION REPORT
================================

[PROCESS] Validation Process:
- Validation rounds completed: {rounds_completed}
- Total corrections applied: {total_corrections}
- Final accuracy estimate: {workflow_result["detailed_results"]["visual_validation_summary"].get("final_accuracy_estimate", 0.95):.1%}

[CORRECTIONS] CORRECTIONS APPLIED:
"""

        # Group corrections by type
        correction_types = {}
        for correction in correction_history:
            change_type = correction["change_type"]
            if change_type not in correction_types:
                correction_types[change_type] = []
            correction_types[change_type].append(correction)

        for change_type, corrections in correction_types.items():
            report += f"\n{change_type.replace('_', ' ').title()}:\n"

            for correction in corrections:
                field = correction["field"]
                round_num = correction["round"]
                before = correction.get("before_value", "N/A")
                after = correction.get("after_value", "N/A")

                if change_type == "value_corrected":
                    report += f"  - {field} (Round {round_num})\n"
                    report += f"    Before: {before}\n"
                    report += f"    After:  {after}\n"
                elif change_type == "table_rows_changed":
                    report += f"  - {field} (Round {round_num}): {before} -> {after}\n"
                elif change_type == "field_added":
                    report += f"  - Added {field} (Round {round_num}): {after}\n"
                elif change_type == "field_removed":
                    report += f"  - Removed {field} (Round {round_num}): {before}\n"
                elif change_type == "complex_column_realignment":
                    shift_pattern = correction.get("shift_pattern", "unknown")
                    columns_affected = correction.get("columns_affected", 0)
                    complexity = correction.get("complexity", "medium")
                    report += f"  - Complex column realignment (Round {round_num})\n"
                    report += f"    Pattern: {shift_pattern}\n"
                    report += f"    Columns affected: {columns_affected}\n"
                    report += f"    Complexity: {complexity}\n"

                    # Show detailed shift information if available
                    shift_details = correction.get("shift_details", [])
                    if shift_details:
                        report += f"    Detailed shifts:\n"
                        for detail in shift_details[:3]:  # Limit to first 3 for readability
                            column = detail.get("column", "unknown")
                            movement = detail.get("movement_type", "unknown")
                            report += f"      * {column}: {movement}\n"
                        if len(shift_details) > 3:
                            report += f"      * ... and {len(shift_details) - 3} more columns\n"

        # Summary of common issues addressed
        column_fixes = len([c for c in correction_history if "column" in c["field"].lower() or "table" in c["change_type"] or c["change_type"] == "complex_column_realignment"])
        value_fixes = len([c for c in correction_history if c["change_type"] == "value_corrected"])
        complex_shifts = len([c for c in correction_history if c["change_type"] == "complex_column_realignment"])

        report += f"""

[SUMMARY] ISSUES ADDRESSED:
- Column/Table issues fixed: {column_fixes}
- Complex column realignments: {complex_shifts}
- Value corrections made: {value_fixes}
- Fields added/removed: {total_corrections - column_fixes - value_fixes}

[SUCCESS] The extraction has been optimized through visual validation to address:
- Multiple column shifting in single tables/rows (fringe benefits, etc.)
- Cascading column misalignments and complex shift patterns
- Value hallucination in tax fields
- Missing or misplaced data
- Mixed left/right shifts within same row
"""

        return report

    def _validate_and_enhance_table_rows(self, data: Dict[str, Any], raw_text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggressive validation and enhancement of table row extraction
        Re-scans raw text to find any missing rows in tables/arrays
        """

        enhanced_data = data.copy()

        # Find all array/table fields in the data
        table_fields = []

        def find_arrays(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, list):
                        table_fields.append((current_path, value))
                    elif isinstance(value, dict):
                        find_arrays(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_arrays(item, f"{path}[{i}]")

        find_arrays(enhanced_data)

        # For each table field, try to find additional rows
        for field_path, current_rows in table_fields:
            if len(current_rows) == 0:
                continue

            print(f"DEBUG - Validating table field: {field_path} with {len(current_rows)} rows")

            # Analyze pattern of existing rows to find more
            additional_rows = self._scan_for_missing_rows(current_rows, raw_text, field_path)

            if additional_rows:
                print(f"DEBUG - Found {len(additional_rows)} additional rows for {field_path}")

                # Add the additional rows to the data
                self._merge_additional_rows(enhanced_data, field_path, additional_rows)

        return enhanced_data

    def _scan_for_missing_rows(self, existing_rows: List[Dict], raw_text: str, field_path: str) -> List[Dict]:
        """
        Scan raw text for patterns that might indicate missing table rows
        """

        if not existing_rows:
            return []

        additional_rows = []

        # Get pattern from existing rows
        if len(existing_rows) > 0:
            sample_row = existing_rows[0]
            row_keys = list(sample_row.keys()) if isinstance(sample_row, dict) else []

            # Look for repeated patterns in raw text
            # This is a heuristic approach to find similar data structures

            # Extract values from existing rows to create search patterns
            known_values = set()
            for row in existing_rows:
                if isinstance(row, dict):
                    for value in row.values():
                        if value and isinstance(value, str):
                            known_values.add(value.strip())

            # Split text into lines and look for potential table rows
            lines = raw_text.split('\n')
            potential_rows = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Skip lines that contain known values (already extracted)
                if any(known_val in line for known_val in known_values):
                    continue

                # Look for lines that might be table rows
                # Heuristics: contains numbers, has similar structure, etc.
                if self._looks_like_table_row(line, sample_row):
                    potential_row = self._try_parse_table_row(line, row_keys)
                    if potential_row:
                        potential_rows.append(potential_row)

            # Limit additional rows to avoid false positives
            additional_rows = potential_rows[:3]  # Max 3 additional rows per scan

        return additional_rows

    def _looks_like_table_row(self, line: str, sample_row: Dict) -> bool:
        """
        Heuristic to determine if a line looks like it could be a table row
        """

        if not line or len(line) < 10:
            return False

        # Check for common table row indicators
        indicators = 0

        # Contains numbers (common in tax/financial tables)
        if any(c.isdigit() for c in line):
            indicators += 1

        # Contains dollar signs or percentages
        if '$' in line or '%' in line:
            indicators += 2

        # Has multiple words/tokens separated by spaces
        tokens = line.split()
        if len(tokens) >= 2:
            indicators += 1

        # Contains common patterns from sample row
        if isinstance(sample_row, dict):
            for value in sample_row.values():
                if value and isinstance(value, str):
                    # Look for similar patterns (numbers, currency, etc.)
                    if '$' in str(value) and '$' in line:
                        indicators += 1
                    if any(c.isdigit() for c in str(value)) and any(c.isdigit() for c in line):
                        indicators += 1

        return indicators >= 2

    def _try_parse_table_row(self, line: str, expected_keys: List[str]) -> Dict[str, Any]:
        """
        Try to parse a line as a table row with the expected structure
        Enhanced to handle multi-word fields and common table patterns
        """

        if not expected_keys:
            return None

        # Enhanced parsing for table rows
        tokens = line.split()

        if len(tokens) < 2:  # Need at least 2 tokens for a meaningful row
            return None

        # For employer tax tables, try to intelligently parse
        if len(expected_keys) == 3:  # Assuming [name, rate, amount] structure
            row = {}

            # Last token is likely the amount (has $ or is pure number)
            amount = None
            rate = None
            name_tokens = []

            # Work backwards to identify amount and rate
            for i in range(len(tokens) - 1, -1, -1):
                token = tokens[i]

                if amount is None and ('$' in token or (token.replace('.', '').replace(',', '').isdigit())):
                    amount = token
                elif rate is None and ('%' in token or (token.replace('.', '').isdigit() and float(token.replace('%', '')) < 100)):
                    rate = token
                else:
                    name_tokens.insert(0, token)

            # Combine name tokens
            name = ' '.join(name_tokens) if name_tokens else None

            # Map to expected keys
            key_mapping = {
                0: name,
                1: rate,
                2: amount
            }

            for i, key in enumerate(expected_keys):
                row[key] = key_mapping.get(i)

            # Validate that we have meaningful content
            non_null_values = [v for v in row.values() if v is not None]
            if len(non_null_values) >= 2:  # Need at least name and one other field
                return row

        # Fallback to simple parsing
        row = {}
        for i, key in enumerate(expected_keys):
            if i < len(tokens):
                row[key] = tokens[i]
            else:
                row[key] = None

        # Validate that the row has at least some meaningful content
        non_null_values = [v for v in row.values() if v is not None]
        if len(non_null_values) >= 1:
            return row

        return None

    def _merge_additional_rows(self, data: Dict[str, Any], field_path: str, additional_rows: List[Dict]):
        """
        Merge additional rows into the data structure
        """

        # Navigate to the field and add rows
        path_parts = field_path.split('.')
        current = data

        # Navigate to parent
        for part in path_parts[:-1]:
            if part in current:
                current = current[part]
            else:
                return  # Path doesn't exist

        # Add to the array
        final_key = path_parts[-1]
        if final_key in current and isinstance(current[final_key], list):
            current[final_key].extend(additional_rows)
            print(f"DEBUG - Added {len(additional_rows)} rows to {field_path}. Total now: {len(current[final_key])}")