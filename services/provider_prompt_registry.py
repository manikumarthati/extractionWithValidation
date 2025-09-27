"""
Provider-Specific Prompt Registry
Elegant, maintainable system for managing prompts optimized for different AI providers
"""

import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class PromptType(Enum):
    """Types of prompts supported by the system"""
    VALIDATION = "validation"
    CORRECTION = "correction"
    EXTRACTION = "extraction"


class Provider(Enum):
    """Supported AI providers"""
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class PromptTemplate:
    """Container for prompt template with metadata"""
    template: str
    provider: Provider
    prompt_type: PromptType
    version: str = "1.0"
    description: str = ""

    def render(self, **kwargs) -> str:
        """Render the template with provided variables"""
        return self.template.format(**kwargs)


class BasePromptProvider(ABC):
    """Base class for provider-specific prompt implementations"""

    @property
    @abstractmethod
    def provider_name(self) -> Provider:
        """Return the provider this class handles"""
        pass

    @abstractmethod
    def get_validation_prompt(self, **context) -> str:
        """Generate validation prompt for this provider"""
        pass

    @abstractmethod
    def get_correction_prompt(self, **context) -> str:
        """Generate correction prompt for this provider"""
        pass

    @abstractmethod
    def get_extraction_prompt(self, **context) -> str:
        """Generate extraction prompt for this provider"""
        pass


class AnthropicPromptProvider(BasePromptProvider):
    """Claude-optimized prompts with detailed reasoning chains"""

    @property
    def provider_name(self) -> Provider:
        return Provider.ANTHROPIC

    def get_validation_prompt(self, extracted_data: Dict, schema: Dict, page_num: int = 0, **kwargs) -> str:
        """Claude excels at complex reasoning - use detailed chain-of-thought"""

        template = """**CRITICAL: You are viewing the uploaded document image for PAGE {page_num}.**

**CHAIN OF THOUGHT VALIDATION APPROACH:**

**STEP 1: DOCUMENT CONTEXT ANALYSIS**
First, understand the document structure:
- Identify document type and layout patterns
- Locate main sections and data organization
- Note visual hierarchy and spacing patterns

**STEP 2: SYSTEMATIC FIELD VALIDATION**
For each extracted field, reason through:
1. "Looking for field [FIELD_NAME] with extracted value [VALUE]"
2. "Scanning document for field label and spatial positioning..."
3. "Comparing extracted vs actual: [ANALYSIS]"
4. "Confidence assessment: [SCORE] because [REASONING]"

**STEP 3: TABLE STRUCTURE ANALYSIS**
For tabular data, perform detailed analysis:
- Count rows systematically with explicit verification
- Check column alignment using semantic reasoning
- Identify empty column skip patterns that cause shifts
- Validate data types match expected column headers

**STEP 4: COLUMN SHIFT DETECTION**
Critical spatial analysis:
- Look for values in wrong columns due to empty cell skipping
- Example: If "B5" appears in CalcCode but CalcCode should be empty, and Frequency is empty but should contain "B5", this indicates left-shift
- Trace value movement patterns across columns

**EXTRACTED DATA TO VERIFY:**
{extracted_data}

**EXPECTED SCHEMA:**
{schema}

**INSTRUCTIONS:**
Use your reasoning capabilities to perform comprehensive validation. Think step-by-step through each finding. Report ONLY issues found - skip correctly extracted items.

**REQUIRED RESPONSE FORMAT:**
Return valid JSON with this structure:
{{
  "field_validation_results": [
    {{
      "field_name": "field_with_issue",
      "extracted_value": "wrong_value",
      "visual_inspection": {{
        "actual_value_in_document": "correct_value",
        "issue": "description",
        "confidence": 0.95
      }}
    }}
  ],
  "table_validation_results": [
    {{
      "table_name": "table_name",
      "rows_visible_in_image": 6,
      "rows_extracted": 5,
      "row_completeness_issue": true,
      "cell_validation_results": [
        {{
          "row_index": 0,
          "column_name": "problematic_column",
          "extracted_value": "wrong_value",
          "visual_inspection": {{
            "actual_value_in_document": "correct_value",
            "belongs_in_column": "correct_column",
            "issue": "column_misalignment"
          }}
        }}
      ]
    }}
  ],
  "overall_assessment": {{
    "fields_with_issues": 0,
    "accuracy_estimate": 0.95,
    "major_issues": []
  }}
}}"""

        return template.format(
            page_num=page_num,
            extracted_data=json.dumps(extracted_data, indent=2),
            schema=json.dumps(schema, indent=2)
        )

    def get_correction_prompt(self, extracted_data: Dict, validation_result: Dict, schema: Dict, page_num: int = 0, **kwargs) -> str:
        """Claude correction with detailed reasoning and text preservation"""

        template = """**CRITICAL: You are viewing the uploaded document image for PAGE {page_num}.**

**CORRECTION REASONING APPROACH:**

**STEP 1: ANALYZE VALIDATION FINDINGS**
Review the validation results systematically:
- Understand what issues were identified
- Prioritize corrections by impact and confidence
- Plan correction strategy to avoid cascading errors

**STEP 2: TEXT PRESERVATION PROTOCOL**
MANDATORY: Preserve complete text from original extraction:
- If original data has "Dental Insurance S125", keep "Dental Insurance S125"
- If original data has "Minnesota Federal Loan Assessment", keep complete text
- ONLY extract new values if original field was null/empty or completely wrong
- Never truncate text during corrections

**STEP 3: SPATIAL CORRECTION METHODOLOGY**
For column shifts and misalignments:
- Use visual positioning to determine correct field/column assignments
- Move values to spatially correct locations while preserving text
- Fix empty column skip patterns (e.g., move "B5" from CalcCode to Frequency)

**STEP 4: SYSTEMATIC CORRECTION APPLICATION**
Apply corrections with reasoning:
- For each correction, explain the spatial logic
- Verify corrections don't create new misalignments
- Maintain schema structure integrity

**ORIGINAL EXTRACTED DATA:**
{extracted_data}

**VALIDATION FINDINGS:**
{validation_result}

**TARGET SCHEMA:**
{schema}

**CORRECTION PRIORITIES:**
1. Fix column misalignment (highest priority)
2. Preserve complete text from original data
3. Add missing data identified in validation
4. Correct field-value mappings

Return the corrected data in exact schema format with complete text preservation.
IMPORTANT: Return ONLY corrected JSON data, no explanations."""

        return template.format(
            page_num=page_num,
            extracted_data=json.dumps(extracted_data, indent=2),
            validation_result=json.dumps(validation_result, indent=2),
            schema=json.dumps(schema, indent=2)
        )

    def get_extraction_prompt(self, text: str, schema: Dict, **kwargs) -> str:
        """Claude extraction with detailed reasoning"""

        template = """You are a data extraction specialist. Extract structured data from the provided PDF text according to the given JSON schema.

**DETAILED EXTRACTION PROCESS:**

**STEP 1: SCHEMA ANALYSIS**
- Understand the required data structure
- Identify required vs optional fields
- Note data types and validation requirements

**STEP 2: TEXT ANALYSIS**
- Scan the text systematically for relevant information
- Identify table structures and field-value relationships
- Note spatial relationships and formatting patterns

**STEP 3: EXTRACTION WITH REASONING**
- Extract data that matches schema structure exactly
- For tables, ensure proper column alignment
- Preserve complete text values (don't truncate)
- Use null for truly missing fields

**SCHEMA:**
{schema}

**PDF TEXT:**
{text}

**EXTRACTION REQUIREMENTS:**
1. Return ONLY valid JSON conforming to schema
2. Preserve complete text values
3. Use proper data types (strings, numbers, booleans)
4. For arrays/tables, extract all available rows
5. Use null for missing fields
6. Ensure column alignment in tabular data

Return the extracted data as valid JSON:"""

        return template.format(
            schema=json.dumps(schema, indent=2),
            text=text
        )


class GooglePromptProvider(BasePromptProvider):
    """Gemini-optimized prompts with direct, action-oriented instructions"""

    @property
    def provider_name(self) -> Provider:
        return Provider.GOOGLE

    def get_validation_prompt(self, extracted_data: Dict, schema: Dict, page_num: int = 0, **kwargs) -> str:
        """Gemini works better with direct, concrete instructions"""

        template = """TASK: Validate extracted data by VISUALLY INSPECTING the document image (PAGE {page_num})

VISUAL INSPECTION PROCESS:
1. **EXAMINE THE IMAGE**: Look at the actual document image uploaded
2. **LOCATE EACH FIELD**: Find form fields, labels, and their values in the image
3. **TRACE TABLE STRUCTURE**: Identify table headers and follow columns down to data
4. **SPOT MISALIGNMENTS**: Look for data in wrong columns or incorrect field associations
5. **COMPARE EXTRACTION**: Check if extracted JSON matches what you visually see

FIELD INSPECTION - Look at the image and verify:
• **Form Fields**: Is each extracted value in the correct labeled field?
• **Label-Value Pairs**: Are values associated with the right labels?
• **Field Positioning**: Does the spatial layout match the extraction?

TABLE INSPECTION - Look at table structure and verify:
• **Column Headers**: Does each extracted value belong under the correct header?
• **Data Alignment**: Are values shifted left/right from their intended columns?
• **Empty vs Filled Cells**: Are null values actually empty in the image?
• **Row Completeness**: Are all visible table rows extracted?

EXTRACTED DATA:
{extracted_data}

SCHEMA:
{schema}

VALIDATION RULES:
✓ Report ONLY problems - skip correct items
✓ For tables: Check each cell is in correct column
✓ Count all visible rows - report if extraction missed any
✓ Check empty fields are actually empty in document

RESPONSE FORMAT (JSON only):
{{
  "field_validation_results": [
    {{
      "field_name": "problem_field",
      "extracted_value": "wrong_value",
      "visual_inspection": {{
        "actual_value_in_document": "correct_value",
        "issue": "description",
        "confidence": 0.95
      }}
    }}
  ],
  "table_validation_results": [
    {{
      "table_name": "table_name",
      "rows_visible_in_image": 6,
      "rows_extracted": 5,
      "row_completeness_issue": true,
      "cell_validation_results": [
        {{
          "row_index": 0,
          "column_name": "wrong_column",
          "extracted_value": "misplaced_value",
          "visual_inspection": {{
            "actual_value_in_document": "correct_value",
            "belongs_in_column": "correct_column",
            "issue": "column_shift"
          }}
        }}
      ]
    }}
  ],
  "overall_assessment": {{
    "fields_with_issues": 2,
    "accuracy_estimate": 0.90,
    "major_issues": ["column_shift_in_benefits_table"]
  }}
}}"""

        return template.format(
            page_num=page_num,
            extracted_data=json.dumps(extracted_data, indent=2),
            schema=json.dumps(schema, indent=2)
        )

    def get_correction_prompt(self, extracted_data: Dict, validation_result: Dict, schema: Dict, page_num: int = 0, **kwargs) -> str:
        """Gemini correction with direct, actionable instructions"""

        template = """TASK: Fix data extraction errors using document image (PAGE {page_num})

CORRECTION RULES:
1. **PRESERVE TEXT**: Keep complete text from original data
   - If original has "Dental Insurance S125" → keep "Dental Insurance S125"
   - If original has "Minnesota Federal Loan Assessment" → keep complete text
   - Only change if original was null or completely wrong

2. **FIX COLUMN SHIFTS**: Move values to correct columns
   - Example: Move "B5" from CalcCode to Frequency column
   - Use visual alignment in document to determine correct placement

3. **ADD MISSING DATA**: Extract any data validation found but extraction missed

4. **MAINTAIN STRUCTURE**: Keep exact schema format

ORIGINAL DATA:
{extracted_data}

VALIDATION FOUND THESE ISSUES:
{validation_result}

TARGET SCHEMA:
{schema}

CORRECTION PRIORITY:
• Column misalignment (highest priority)
• Missing data
• Field mapping errors
• Text preservation (always preserve complete text)

OUTPUT: Return corrected data in exact schema format (JSON only, no explanations)"""

        return template.format(
            page_num=page_num,
            extracted_data=json.dumps(extracted_data, indent=2),
            validation_result=json.dumps(validation_result, indent=2),
            schema=json.dumps(schema, indent=2)
        )

    def get_extraction_prompt(self, text: str, schema: Dict, **kwargs) -> str:
        """Gemini extraction with clear, direct instructions"""

        template = """TASK: Extract structured data from PDF text

EXTRACTION RULES:
• Follow schema structure exactly
• For tables: Keep values in correct columns (check data types match column headers)
• Preserve complete text (don't truncate)
• Use null for missing fields
• Extract ALL table rows

SCHEMA:
{schema}

PDF TEXT:
{text}

IMPORTANT TABLE ALIGNMENT:
- Text columns should contain names/descriptions
- Number columns should contain amounts/codes
- Date columns should contain dates
- If data type doesn't match column, check alignment

OUTPUT: Valid JSON matching schema (no extra text)"""

        return template.format(
            schema=json.dumps(schema, indent=2),
            text=text
        )


class PromptRegistry:
    """Central registry for managing provider-specific prompts"""

    def __init__(self):
        self._providers: Dict[Provider, BasePromptProvider] = {
            Provider.ANTHROPIC: AnthropicPromptProvider(),
            Provider.GOOGLE: GooglePromptProvider()
        }

    def get_provider(self, provider: Provider) -> BasePromptProvider:
        """Get prompt provider for specific AI provider"""
        if provider not in self._providers:
            raise ValueError(f"Unsupported provider: {provider}")
        return self._providers[provider]

    def get_prompt(self, provider: Provider, prompt_type: PromptType, **context) -> str:
        """Get optimized prompt for provider and task type"""
        prompt_provider = self.get_provider(provider)

        if prompt_type == PromptType.VALIDATION:
            return prompt_provider.get_validation_prompt(**context)
        elif prompt_type == PromptType.CORRECTION:
            return prompt_provider.get_correction_prompt(**context)
        elif prompt_type == PromptType.EXTRACTION:
            return prompt_provider.get_extraction_prompt(**context)
        else:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")

    def register_provider(self, provider_class: BasePromptProvider):
        """Register a new prompt provider"""
        self._providers[provider_class.provider_name] = provider_class

    def list_providers(self) -> list[Provider]:
        """List all registered providers"""
        return list(self._providers.keys())


# Global registry instance
prompt_registry = PromptRegistry()


# Convenience functions for easy access
def get_validation_prompt(provider: Provider, **context) -> str:
    """Get validation prompt for provider"""
    return prompt_registry.get_prompt(provider, PromptType.VALIDATION, **context)


def get_correction_prompt(provider: Provider, **context) -> str:
    """Get correction prompt for provider"""
    return prompt_registry.get_prompt(provider, PromptType.CORRECTION, **context)


def get_extraction_prompt(provider: Provider, **context) -> str:
    """Get extraction prompt for provider"""
    return prompt_registry.get_prompt(provider, PromptType.EXTRACTION, **context)