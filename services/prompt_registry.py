"""
Centralized Prompt Registry for All LLM Providers
Maintains provider-specific prompts without modification
Provides unified access pattern for all extraction tasks
"""

import json
from typing import Dict, Any


class PromptRegistry:
    """Centralized prompt management for Claude and Gemini providers"""

    # ==== CLAUDE PROMPTS (Existing sophisticated prompts) ====

    CLAUDE_STRUCTURE_CLASSIFICATION = """
    Analyze this PDF page and classify its structure.

    Document Info:
    - Total text length: {text_length} characters
    - Total text blocks: {total_blocks}

    Sample text content:
    {sample_text}

    Classify this page as one of:
    1. "form" - Contains form fields with labels and values (like applications, invoices)
    2. "table" - Contains tabular data with rows and columns
    3. "mixed" - Contains both form elements and tables

    Also identify the main regions and provide confidence score.

    You MUST respond with valid JSON only. No additional text or explanation.

    {{
        "classification": "form|table|mixed",
        "confidence": 0.85,
        "reasoning": "Brief explanation of classification",
        "regions": [
            {{
                "type": "form|table",
                "description": "Description of this region",
                "estimated_bounds": "top|middle|bottom"
            }}
        ]
    }}
    """

    CLAUDE_COMPREHENSIVE_FIELD_EXTRACTION = """
    You are a document structure specialist. Follow these very specific rules to identify and extract FORM FIELDS and TABLE HEADERS from the provided text.
    *** CRITICAL RULES - READ FIRST ***
    1. DO NOT include table headers in form_fields - they go ONLY in the tables section!
    2. DO NOT include actual data values like "John Doe" or "12/26/2001" in field names!
    3. Extract ONLY field labels like "Employee Name", "Birth Date", NOT their values!
    4. Extract ONLY table column headers like "Rate", "Description", NOT table data!
    5. Think Harder while extracting form fields. DO not miss any field though they do not have value.

    You are identifying document STRUCTURE ONLY - field labels and table headers.

    Text to analyze:
    {text}

    User feedback and instructions: {user_feedback}

    ## EXTRACTION GUIDELINES

    **FORM FIELDS (individual labeled data points):**
    - Look for patterns like "Label:" followed by values
    - Extract the LABEL part only (e.g., "Employee Name", "SSN", "DOB")
    - NEVER extract the actual values (e.g., "Caroline Jones", "088-39-6286")
    - These are typically scattered throughout the document as individual items

    **TABLE HEADERS (column names in tabular data):**
    - Look for column headers that appear above rows of data
    - Extract headers like "Rate", "Description", "Effective Dates"
    - These appear in organized tables with multiple rows of data below them
    - DO NOT include these in form_fields - they go in tables section only!

    **WHAT TO IGNORE:**
    - Actual data values (names, numbers, dates)
    - Section titles like "Employee Information"
    - Page headers/footers
    - Table row data

    ## User Feedback Integration
    If user feedback is provided:
    - Apply their corrections exactly as specified
    - Add missing fields they mention
    - Remove incorrectly identified items they highlight
    - Follow their guidance on field vs table header classification

    **REQUIRED JSON FORMAT:**
    {{
        "form_fields": [
            {{
                "field_name": "Employee Name"
            }},
            {{
                "field_name": "Birth Date"
            }}
        ],
        "tables": [
            {{
                "table_name": "Rate/Salary Information",
                "headers": ["RateCode", "Description", "Rate", "Effective Dates"]
            }}
        ],
        "extraction_summary": {{
            "total_form_fields": 2,
            "total_tables": 1,
            "refinement_iteration": 1
        }},
        "feedback_response": "Brief note on how user feedback was incorporated"
    }}

    *** FINAL REMINDER ***
    - form_fields = individual field LABELS only (not table headers!)
    - tables = table names with their column headers
    - NO actual data values in either section!
    """

    CLAUDE_UNIFIED_SCHEMA_EXTRACTION = """
    You are a comprehensive data extraction specialist with enhanced intelligence from user feedback analysis.

    **SCHEMA PROVIDED:**
    Form Fields: {form_fields_schema}
    Tables: {tables_schema}

    **CORE EXTRACTION RULES:**
    1. **Form Fields**: Extract exact values for each field name. Use null if field exists but has no value.
    2. **Tables**: For each table, extract ALL rows with data for the specified headers. SCAN ENTIRE DOCUMENT for multiple rows - do not stop at first row!
    3. **Precision**: Preserve original formatting, dates, numbers, and compound values exactly.
    4. **Completeness**: Extract everything in one pass - do not separate forms and tables.

    **ENHANCED EXTRACTION INTELLIGENCE:**
    {enhanced_instructions}

    **VALIDATION REQUIREMENTS:**
    {validation_rules}

    **DETECTION IMPROVEMENTS:**
    {detection_improvements}

    **FORMAT HANDLING:**
    {format_handling}

    **Document Text:**
    {text}

    **META-INSTRUCTION:**
    These enhancements are derived from actual user feedback and corrections. Apply them carefully to achieve maximum extraction accuracy while maintaining the core extraction rules above.

    **Required JSON Response:**
    {{
        "form_data": {{
            "Field Name 1": "exact value or null",
            "Field Name 2": "exact value or null"
        }},
        "table_data": [
            {{
                "table_name": "Table Name 1",
                "headers": ["Header1", "Header2", "Header3"],
                "rows": [
                    {{"Header1": "value1", "Header2": "value2", "Header3": null}},
                    {{"Header1": "value3", "Header2": null, "Header3": "value4"}}
                ]
            }}
        ],
        "extraction_summary": {{
            "total_form_fields_extracted": 0,
            "total_tables_extracted": 0,
            "total_table_rows_extracted": 0,
            "extraction_confidence": 0.95,
            "enhancements_applied": true
        }}
    }}
    """

    CLAUDE_TEXT_SCHEMA_EXTRACTION = """You are an expert data extraction specialist. Your task is to extract ALL structured data from the provided text using systematic chain-of-thought reasoning.

**CRITICAL MISSION**: Extract EVERY table row and EVERY data element. Missing data is unacceptable.

SCHEMA TO FOLLOW:
{schema}

RAW TEXT TO ANALYZE:
{raw_text}

## CHAIN OF THOUGHT EXTRACTION PROCESS:

**STEP 1: DOCUMENT STRUCTURE ANALYSIS**
Before extracting, analyze and explain:
- What type of document is this? (employee profile, tax document, benefit summary, etc.)
- What are the main sections? (personal info, tables, lists, etc.)
- How many tables/arrays do I see in the text?
- Where are the table headers and how can I identify table boundaries?

**STEP 2: SYSTEMATIC TABLE IDENTIFICATION**
For each array/list in the schema, think step by step:
- What table does this array represent?
- Where does this table start in the raw text?
- What are the column headers for this table?
- Where does this table end?
- How many rows can I count?

**STEP 3: COMPLETE TABLE SCANNING METHODOLOGY**
For EACH table/array field, use this process:

**3A: BOUNDARY DETECTION**
- Identify table start: Look for headers, section titles, or repeated patterns
- Identify table end: Look for next section, blank lines, or different content type
- Mark the entire table region for systematic scanning

**3B: ROW-BY-ROW SYSTEMATIC EXTRACTION**
- Start from first data row after headers
- Extract each row completely, maintaining column alignment
- Continue row by row until table boundary
- Count total rows as you go: "Row 1: [data], Row 2: [data], Row 3: [data]..."
- Verify against raw text: "I see X rows in the table"

**3C: COMPLETENESS VERIFICATION**
- Did I reach the end of the table?
- Are there any rows I might have missed?
- Do the row counts match what I can see in the text?
- Let me re-scan one more time to ensure completeness

## ENHANCED EXTRACTION INSTRUCTIONS:
1. Extract data exactly as specified in the schema structure
2. Use the exact field names and structure from the schema
3. Find values corresponding to each field/column specified in the schema
4. **BLANK FIELD HANDLING:** If a field exists in the schema but appears blank/empty in the document (not missing), extract it as empty string "" - DO NOT use null
5. **COMPLETE TEXT EXTRACTION:** Always use the complete, untruncated text from the raw text - if you see partial text, find the complete version in the raw text
6. Maintain proper data types as indicated in the schema
7. IMPORTANT: Return ONLY the essential data values, no metadata, descriptions, or additional details
8. Keep the response concise and focused only on the actual data values

**CRITICAL BLANK FIELD RULES:**
9. **BLANK vs NULL:** If a field label exists but has no value (blank), use empty string "". Only use null if the field is completely absent from the document
10. **EMPTY FIELDS MATTER:** Fields like "Position:", "Emp Type:", "Title:" may be blank in documents but should be extracted as "" not omitted
11. **VISUAL BLANKS:** If you see a field label followed by blank space, extract as empty string ""

**CRITICAL TEXT COMPLETENESS RULES:**
12. **PARTIAL TEXT MATCHING:** If you encounter truncated/partial text, search the raw text for the complete version
13. **TRUNCATION EXAMPLES:** "Workforce Enhanc..." should become "Workforce Enhancement Fee" by finding complete text in raw
14. **ABBREVIATION EXPANSION:** Use the most complete form available in the raw text
15. **TEXT PRIORITY:** Raw text completeness takes priority over partial visual representations

Return ONLY valid JSON matching the schema structure exactly. No explanations or additional text."""

    CLAUDE_VISION_VALIDATION = """Validate the extracted JSON data against this PDF image. Look for:

1. COLUMN SHIFTING in tables (data in wrong columns)
2. FIELD-VALUE MAPPING errors (wrong values assigned to fields)
3. MISSING DATA that's visible in the image
4. INCORRECT DATA that doesn't match the image

EXTRACTED JSON TO VALIDATE:
{extracted_json}

VALIDATION TASKS:
- For each table: Check if column data aligns with headers
- For each form field: Verify the value matches the field label
- Look for systematic errors or misalignments
- Check data accuracy and completeness

OUTPUT FORMAT:
{{
  "validation_summary": {{
    "overall_accuracy": 0.85,
    "issues_found": 3
  }},
  "column_shifting_detected": true,
  "column_shifting_details": [
    {{
      "table_name": "Table Name",
      "issue": "Values shifted right by 1 column",
      "affected_rows": [1, 2, 3]
    }}
  ],
  "field_mapping_issues_detected": true,
  "field_mapping_issues": [
    {{
      "field_name": "Employee Name",
      "extracted_value": "wrong_value",
      "correct_value": "correct_value",
      "issue": "Field contains ID instead of name"
    }}
  ],
  "missing_data": [
    {{
      "field_name": "Phone Number",
      "visible_in_image": true,
      "location": "bottom of form"
    }}
  ]
}}"""

    CLAUDE_COMPREHENSIVE_VISUAL_VALIDATION = """**CRITICAL: You are viewing the uploaded document image for PAGE {page_num}.** Perform TRUE VISUAL INSPECTION by examining the actual document layout and spatial positioning in the image.

**VISUAL LAYOUT INSPECTION APPROACH**:
1. **IGNORE semantic assumptions** - don't guess based on what values "should" go where
2. **LOOK at actual visual positioning** - examine where text appears in the document image
3. **IDENTIFY layout type** - distinguish between tabular data vs form fields
4. **APPLY appropriate spatial validation** based on layout type

**FOR TABULAR DATA (tables with columns and rows):**
- Look at column headers and trace vertically down to see which values align under each header
- Check for column misalignment where values appear shifted left/right from intended columns
- Identify empty cells that should contain data vs cells incorrectly containing shifted data
- Pay attention to visual grid lines, borders, and column spacing

**FOR FORM FIELDS (label-value pairs):**
- Look at spatial relationships between labels and their associated values
- Check horizontal positioning - values should be near their corresponding labels
- Verify labels are correctly matched to nearby values (not distant ones)
- Look for visual cues like colons, spacing, and alignment that indicate field relationships

**EXAMPLE MISALIGNMENT DETECTION:**
For deduction table with columns [DeductionCode, CalCode, Frequency]:
- If you see "DNTL" under DeductionCode, look directly right to see what's under CalCode
- If CalCode column appears empty but contains "B5", and Frequency column is empty but should contain "B5"
- This indicates a LEFT-SHIFT: "B5" moved one column left from Frequency to CalCode

CURRENT EXTRACTED DATA TO VERIFY AND CROSS-REFERENCE:
{extracted_data}

EXPECTED SCHEMA:
{schema}

**CRITICAL VISUAL INSPECTION INSTRUCTIONS:**
You are looking at page {page_num}. USE THE ACTUAL VISUAL LAYOUT to verify the extracted data above:
- Where is each value positioned in the image relative to its intended field/column?
- Are there empty spaces where values should be?
- Are values positioned under wrong columns or next to wrong labels?
- What do the visual alignment cues (lines, spacing, borders) tell you?

**COMMON VALIDATION ISSUES TO PREVENT:**
1. **FALSE FREQUENCY DETECTION**: Some deduction codes have NO frequency value
   - If a field appears empty in the image, mark it as empty (not "B" or partial text)
   - Don't assume truncated single letters are valid frequency codes

2. **TEXT TRUNCATION HANDLING**: Visual extraction may truncate values
   - If you see partial text in the image (like "B" instead of "B5"), use the complete value from the extracted data above
   - Example: Visual shows "B", extracted data above has "B5" → use "B5" as the correct value
   - Cross-reference with the extracted data when visual text appears incomplete
   - **CRITICAL**: If text in extracted data is truncated (like "Minnesota Federal Lo" instead of "Minnesota Federal Loan Assessment"), flag this as an ERROR even if positioning is correct

## CHAIN OF THOUGHT VALIDATION PROCESS:

**STEP 1: DOCUMENT UNDERSTANDING & CONTEXT ANALYSIS**
First, let me understand what I'm looking at:
- What type of document is this? (employee profile, financial statement, etc.)
- What are the main sections I can see?
- How is the information organized visually (forms, tables, lists)?
- What is the overall layout and structure?

Reasoning: Understanding the document context helps me set proper expectations for field locations and data relationships.

**STEP 2: SYSTEMATIC FIELD-BY-FIELD ANALYSIS**
For each extracted field, I will reason through:

*For each field, think step by step:*
1. "I'm looking for field [FIELD_NAME] with extracted value [VALUE]"
2. "Let me scan the document for the field label..."
3. "I found/didn't find the label at [LOCATION]"
4. "The value near this label appears to be [ACTUAL_VALUE]"
5. "Comparing extracted vs actual: [MATCH/MISMATCH/EMPTY]"
6. "My confidence in this assessment: [CONFIDENCE_SCORE] because [REASONING]"

**STEP 3: TABLE STRUCTURE ANALYSIS WITH EXPLICIT COUNTING**
For each table, I will explicitly reason:

*Table Analysis Process:*
1. "I'm examining table: [TABLE_NAME]"
2. "Let me identify the column headers: [LIST_HEADERS]"
3. "Now I'll count the data rows systematically:"
   - "Row 1: I can see data: [ROW_1_DATA]"
   - "Row 2: I can see data: [ROW_2_DATA]"
   - "Row 3: I can see data: [ROW_3_DATA]"
   - "[Continue for all visible rows...]"
4. "Total rows I counted visually: [VISUAL_COUNT]"
5. "Total rows in extracted data: [EXTRACTED_COUNT]"
6. "Comparison: [MATCH/MISMATCH] - [EXPLANATION]"

**STEP 4: COLUMN ALIGNMENT VERIFICATION WITH DETAILED REASONING**
For tables with potential alignment issues:

*Column Alignment Analysis:*
1. "Looking at row [N]: [ROW_DATA]"
2. "For each column, let me verify the semantic match:"
   - "Column [NAME]: Expected type [TYPE], actual value [VALUE]"
   - "Does '[VALUE]' make sense for '[COLUMN_NAME]'? [YES/NO] because [REASONING]"
3. "**CRITICAL: Empty Column Skip Analysis:**"
   - "Are there empty columns that should contain the shifted data?"
   - "If [COLUMN_A] is empty and [COLUMN_B] contains data that semantically belongs in [COLUMN_A], this indicates a column shift"

**STEP 5: COMPREHENSIVE ACCURACY ASSESSMENT**
Final reasoning synthesis:
1. "Based on my visual inspection, here are the key findings:"
2. "Overall accuracy estimate: [PERCENTAGE] because [REASONING]"
3. "Major issues identified: [LIST_ISSUES]"
4. "Fields that need correction: [LIST_FIELDS]"
5. "Tables that need realignment: [LIST_TABLES]"

Return detailed JSON validation results focusing on visual accuracy."""

    CLAUDE_VISUAL_CORRECTION = """**CRITICAL: You are viewing the uploaded document image for PAGE {page_num}.** Use VISUAL LAYOUT ANALYSIS to correct the extracted data based on actual document positioning.

**LAYOUT-AWARE CORRECTION APPROACH:**
1. **EXAMINE the visual layout** - identify whether data is in tables or form fields
2. **APPLY layout-specific correction methods** based on document structure
3. **USE spatial positioning** to determine correct field/column assignments
4. **IGNORE semantic guessing** - rely only on visual positioning cues

**FOR TABULAR DATA CORRECTIONS:**
- Look at column headers and trace down to see actual data positioning
- For column misalignment: move values to the column they visually align with
- For empty cells: check if values shifted from neighboring columns
- Use grid lines, borders, and spacing as alignment guides

**FOR FORM FIELD CORRECTIONS:**
- Follow spatial relationships between labels and values
- Match values to the nearest appropriate labels based on visual proximity
- Use visual cues (colons, indentation, spacing) to determine field associations
- Consider horizontal and vertical positioning relative to field labels

**SPECIFIC CORRECTION EXAMPLE:**
If validation found B5 in CalCode but it should be in Frequency:
- Look at the deduction table in the image
- Find where "B5" actually appears visually
- Check which column header it aligns under
- Move it to the correct column based on visual alignment

ORIGINAL EXTRACTED DATA FROM PAGE {page_num}:
{extracted_data}

VISUAL INSPECTION FINDINGS FOR PAGE {page_num}:
{validation_result}

TARGET SCHEMA:
{schema}

**CORRECTION INSTRUCTIONS:**
Look at page {page_num} image and make corrections based on ACTUAL VISUAL POSITIONING:
- Where do you see each value positioned relative to headers/labels?
- What does the visual layout tell you about correct field/column assignments?
- Use spacing, alignment, and visual structure to guide corrections.

**CRITICAL CORRECTION GUIDELINES:**
1. **EMPTY FREQUENCY FIELDS**: If frequency column appears empty in image, keep it empty
   - Don't add "B" or single letters unless you clearly see complete text
   - Some deduction codes legitimately have no frequency value

2. **MANDATORY TEXT PRESERVATION**: ALWAYS preserve complete text from original extracted data
   - NEVER truncate text during corrections - visual inspection may show partial text due to image resolution
   - If original data has "Minnesota Federal Loan Assessment", keep it as "Minnesota Federal Loan Assessment"
   - If visual shows "Minnesota Federal Lo", use complete text from original data above
   - CRITICAL: Only fix POSITIONING and COLUMN ASSIGNMENT - never shorten text descriptions

3. **CORRECTION PRIORITY ORDER**:
   - FIRST: Fix column misalignment (move values to correct columns)
   - SECOND: Use complete text values from original extracted data
   - THIRD: Only change values if they are completely wrong (not just truncated)

4. **SPECIFIC CORRECTION EXAMPLES**:
   - Column shift: Move "B5" from CalCode to Frequency (preserve "B5")
   - Text preservation: Keep "Minnesota Federal Loan Assessment" complete, don't truncate to "Minnesota Federal Lo"
   - Empty field: If CalCode appears empty in image, keep it empty ("")

**FINAL TEXT PRESERVATION REMINDER:**
Before outputting your correction, verify that ALL text descriptions match the complete versions from the original extracted data above. Do not truncate any text - if visual appears truncated, use the complete original text.

CORRECTION INSTRUCTIONS:

1. **FOR FIELDS WITH ISSUES:**
   - Look at the document image carefully
   - Find the correct field labels and their corresponding values
   - Extract the actual values you see in the document
   - If a field is truly empty, use null

2. **FOR COMPLEX TABLE ALIGNMENT & MULTIPLE COLUMN SHIFTS:**
   - Look at the table structure in the image with extreme care
   - Count ALL rows with data and extract every single one

   **ADVANCED COLUMN CORRECTION PROCESS:**
   - Examine each table cell individually against its column header
   - For rows with multiple column shifts, fix each cell independently
   - Look for cascading shifts where one error causes subsequent errors
   - Identify the root cause (missing separators, merged cells, OCR errors)

   **SPECIFIC CORRECTION STRATEGIES:**
   - Mixed shifts: Some data shifted left, some right in same row - correct each individually
   - Cascade shifts: One wrong placement affects all subsequent columns - rebuild the entire row
   - Partial shifts: Only some rows affected - compare with correctly aligned rows as reference
   - Header misalignment: Verify each data value semantically matches its intended column

   **COLUMN-BY-COLUMN VERIFICATION:**
   - For each column header, scan down and verify all values make semantic sense
   - Names should contain text, amounts should contain numbers, dates should be date-formatted
   - If a "Name" column contains "$200", that's clearly shifted data
   - If an "Amount" column contains "John Doe", that's clearly shifted data

   **ROW COMPLETION - ZERO TOLERANCE FOR MISSING ROWS:**
   - Document MUST be inspected completely for ALL table rows
   - Empty rows in output indicate extraction failure
   - Small font, overlapping text, or faint lines are NOT excuses for missing data
   - If you see a row in the image, it MUST be in the corrected output

Return corrected JSON data maintaining the original schema structure."""

    # ==== GEMINI PROMPTS (Existing simple prompts) ====

    GEMINI_STRUCTURE_CLASSIFICATION = """
You are a data extraction specialist. Analyze the provided PDF text and classify its structure.

CLASSIFICATION OPTIONS:
- "form": Contains form fields with labels and values
- "table": Contains tabular data with rows and columns
- "mixed": Contains both form elements and tables

TEXT:
{sample_text}

Return JSON with this structure:
{{
    "classification": "form|table|mixed",
    "confidence": 0.85,
    "reasoning": "Brief explanation"
}}
"""

    GEMINI_FIELD_EXTRACTION = """
You are a data extraction specialist. Extract field names and table headers from the provided text.

TEXT:
{text}

INSTRUCTIONS:
1. Identify form field labels (not values)
2. Identify table column headers
3. Return structured field information
4. Do not include actual data values

Return JSON with this structure:
{{
    "form_fields": [
        {{"field_name": "Employee Name"}},
        {{"field_name": "Birth Date"}}
    ],
    "tables": [
        {{
            "table_name": "Employee Information",
            "headers": ["Name", "ID", "Department"]
        }}
    ]
}}
"""

    GEMINI_DATA_EXTRACTION = """
You are a data extraction specialist. Extract structured data from the provided PDF text according to the given JSON schema.

SCHEMA:
{schema}

PDF TEXT:
{text}

INSTRUCTIONS:
1. Extract data that matches the schema structure exactly
2. Return ONLY valid JSON that conforms to the schema
3. If a field is not found, use null
4. For arrays/tables, extract all available rows
5. Ensure proper data types (strings, numbers, booleans)
6. Do not add any additional fields not in the schema

Return the extracted data as valid JSON:
"""

    GEMINI_VISION_VALIDATION = """
You are a data validation specialist. Compare the extracted data against the actual PDF image to verify accuracy.

SCHEMA:
{schema}

EXTRACTED DATA:
{extracted_data}

INSTRUCTIONS:
1. Examine the PDF image carefully
2. Compare each extracted field with what you see in the image
3. Identify any missing, incorrect, or misaligned data
4. For tables, check row counts and column alignments
5. Return validation results as JSON

Return JSON with this structure:
{{
    "validation_passed": true,
    "accuracy_estimate": 0.95,
    "issues_found": [
        {{
            "field": "field_name",
            "issue": "description of issue",
            "suggested_correction": "corrected value"
        }}
    ],
    "corrected_data": {{}}
}}
"""

    GEMINI_VISUAL_CORRECTION = """
You are a data correction specialist. Fix the extracted data based on what you see in the PDF image.

ORIGINAL EXTRACTED DATA:
{extracted_data}

VALIDATION ISSUES FOUND:
{validation_result}

TARGET SCHEMA:
{schema}

INSTRUCTIONS:
1. Look at the PDF image carefully
2. Identify the specific issues mentioned in the validation
3. Correct the data based on what you actually see in the image
4. For tables, ensure proper column alignment
5. For forms, verify field-value relationships
6. Return corrected data in the same schema format

Return the corrected JSON data:
"""

    # ==== PROMPT REGISTRY METHODS ====

    @classmethod
    def get_prompt(cls, provider: str, task_type: str, **kwargs) -> str:
        """
        Get provider-specific prompt for a task

        Args:
            provider: 'claude' or 'gemini'
            task_type: 'classification', 'field_extraction', 'data_extraction', etc.
            **kwargs: Template variables for prompt formatting

        Returns:
            Formatted prompt string
        """
        prompt_map = {
            'claude': {
                'classification': cls.CLAUDE_STRUCTURE_CLASSIFICATION,
                'field_extraction': cls.CLAUDE_COMPREHENSIVE_FIELD_EXTRACTION,
                'data_extraction': cls.CLAUDE_UNIFIED_SCHEMA_EXTRACTION,
                'text_schema_extraction': cls.CLAUDE_TEXT_SCHEMA_EXTRACTION,
                'vision_validation': cls.CLAUDE_VISION_VALIDATION,
                'comprehensive_visual_validation': cls.CLAUDE_COMPREHENSIVE_VISUAL_VALIDATION,
                'visual_correction': cls.CLAUDE_VISUAL_CORRECTION
            },
            'gemini': {
                'classification': cls.GEMINI_STRUCTURE_CLASSIFICATION,
                'field_extraction': cls.GEMINI_FIELD_EXTRACTION,
                'data_extraction': cls.GEMINI_DATA_EXTRACTION,
                'text_schema_extraction': cls.GEMINI_DATA_EXTRACTION,  # Reuse for now
                'vision_validation': cls.GEMINI_VISION_VALIDATION,
                'comprehensive_visual_validation': cls.GEMINI_VISION_VALIDATION,  # Reuse for now
                'visual_correction': cls.GEMINI_VISUAL_CORRECTION
            }
        }

        provider_prompts = prompt_map.get(provider.lower())
        if not provider_prompts:
            raise ValueError(f"Unknown provider: {provider}")

        prompt_template = provider_prompts.get(task_type)
        if not prompt_template:
            raise ValueError(f"Unknown task type '{task_type}' for provider '{provider}'")

        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable {e} for {provider} {task_type} prompt")

    @classmethod
    def list_available_prompts(cls) -> Dict[str, Dict[str, str]]:
        """List all available prompts by provider and task"""
        return {
            'claude': {
                'classification': 'Structure classification with detailed analysis',
                'field_extraction': 'Comprehensive field and table header extraction',
                'data_extraction': 'Unified schema-based data extraction with enhancements',
                'text_schema_extraction': 'Chain-of-thought text extraction with completeness verification',
                'vision_validation': 'Basic vision validation for accuracy checking',
                'comprehensive_visual_validation': 'Advanced chain-of-thought visual validation',
                'visual_correction': 'Sophisticated visual correction with layout awareness'
            },
            'gemini': {
                'classification': 'Simple structure classification',
                'field_extraction': 'Basic field and header extraction',
                'data_extraction': 'Schema-based data extraction',
                'text_schema_extraction': 'Schema-based data extraction (reused)',
                'vision_validation': 'Basic validation against PDF image',
                'comprehensive_visual_validation': 'Basic validation (reused)',
                'visual_correction': 'Simple correction based on validation findings'
            }
        }

    @classmethod
    def validate_prompt_requirements(cls, provider: str, task_type: str, **kwargs) -> bool:
        """Validate that all required template variables are provided"""
        try:
            cls.get_prompt(provider, task_type, **kwargs)
            return True
        except ValueError:
            return False

    @classmethod
    def get_required_variables(cls, provider: str, task_type: str) -> list:
        """Get list of required template variables for a prompt"""
        import re
        prompt_map = {
            'claude': {
                'classification': cls.CLAUDE_STRUCTURE_CLASSIFICATION,
                'field_extraction': cls.CLAUDE_COMPREHENSIVE_FIELD_EXTRACTION,
                'data_extraction': cls.CLAUDE_UNIFIED_SCHEMA_EXTRACTION,
                'text_schema_extraction': cls.CLAUDE_TEXT_SCHEMA_EXTRACTION,
                'vision_validation': cls.CLAUDE_VISION_VALIDATION,
                'comprehensive_visual_validation': cls.CLAUDE_COMPREHENSIVE_VISUAL_VALIDATION,
                'visual_correction': cls.CLAUDE_VISUAL_CORRECTION
            },
            'gemini': {
                'classification': cls.GEMINI_STRUCTURE_CLASSIFICATION,
                'field_extraction': cls.GEMINI_FIELD_EXTRACTION,
                'data_extraction': cls.GEMINI_DATA_EXTRACTION,
                'text_schema_extraction': cls.GEMINI_DATA_EXTRACTION,
                'vision_validation': cls.GEMINI_VISION_VALIDATION,
                'comprehensive_visual_validation': cls.GEMINI_VISION_VALIDATION,
                'visual_correction': cls.GEMINI_VISUAL_CORRECTION
            }
        }

        provider_prompts = prompt_map.get(provider.lower(), {})
        template = provider_prompts.get(task_type, "")

        # Extract variables like {variable_name} from template
        variables = re.findall(r'\{([^}]+)\}', template)
        return list(set(variables))


# Convenience functions for backward compatibility
def get_claude_prompt(task_type: str, **kwargs) -> str:
    """Get Claude-specific prompt"""
    return PromptRegistry.get_prompt('claude', task_type, **kwargs)


def get_gemini_prompt(task_type: str, **kwargs) -> str:
    """Get Gemini-specific prompt"""
    return PromptRegistry.get_prompt('gemini', task_type, **kwargs)


if __name__ == "__main__":
    # Demo the prompt registry
    print("=== Centralized Prompt Registry ===")
    print("\nAvailable prompts:")
    for provider, tasks in PromptRegistry.list_available_prompts().items():
        print(f"\n{provider.upper()}:")
        for task, desc in tasks.items():
            required_vars = PromptRegistry.get_required_variables(provider, task)
            print(f"  {task}: {desc}")
            print(f"    Required vars: {required_vars}")

    # Test prompt retrieval
    print("\n=== Test Prompt Retrieval ===")
    try:
        claude_classification = PromptRegistry.get_prompt(
            'claude', 'classification',
            text_length=1000,
            total_blocks=5,
            sample_text="Employee Name: John Doe"
        )
        print(f"✓ Claude classification prompt generated ({len(claude_classification)} chars)")

        gemini_validation = PromptRegistry.get_prompt(
            'gemini', 'vision_validation',
            schema='{"name": "string"}',
            extracted_data='{"name": "John Smith"}'
        )
        print(f"✓ Gemini validation prompt generated ({len(gemini_validation)} chars)")

        claude_correction = PromptRegistry.get_prompt(
            'claude', 'visual_correction',
            page_num=0,
            extracted_data='{"name": "John"}',
            validation_result='{"issues": []}',
            schema='{"name": "string"}'
        )
        print(f"✓ Claude correction prompt generated ({len(claude_correction)} chars)")

    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n=== Prompt Registry Successfully Created ===")
    print("✓ All Claude prompts preserved (sophisticated)")
    print("✓ All Gemini prompts preserved (simple)")
    print("✓ All validation and correction prompts included")
    print("✓ Unified interface for all providers")