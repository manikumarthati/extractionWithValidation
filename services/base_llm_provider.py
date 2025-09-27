"""
Base LLM Provider Interface
Defines common interface that all LLM providers must implement
Ensures consistent behavior across Claude, Gemini, and future providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import json
from .prompt_registry import PromptRegistry


class BaseLLMProvider(ABC):
    """Abstract base class defining the common interface for all LLM providers"""

    def __init__(self, api_key: str, model_config_name: str = 'default'):
        self.api_key = api_key
        self.model_config_name = model_config_name
        self.MAX_RETRIES = 3
        self.ENABLE_COST_TRACKING = True
        self.prompt_registry = PromptRegistry()

    # ==== ABSTRACT METHODS (must be implemented by each provider) ====

    @abstractmethod
    def _make_request(self, prompt: str, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        Make provider-specific API request

        Args:
            prompt: The prompt to send
            task_type: Type of task for model selection
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict with 'success', 'data'/'content', 'usage', 'model_used', etc.
        """
        pass

    @abstractmethod
    def validate_with_vision(self, image_data: Any, prompt: str) -> Dict[str, Any]:
        """
        Perform vision-based validation

        Args:
            image_data: Image data (base64, PIL Image, or file path)
            prompt: Validation prompt

        Returns:
            Dict with validation results
        """
        pass

    @abstractmethod
    def validate_with_vision_file(self, file_id: str, prompt: str) -> Dict[str, Any]:
        """
        Perform vision-based validation using uploaded file ID

        Args:
            file_id: Uploaded file identifier
            prompt: Validation prompt

        Returns:
            Dict with validation results
        """
        pass

    @abstractmethod
    def upload_image(self, image_path: str) -> Dict[str, Any]:
        """
        Upload image to provider's file API

        Args:
            image_path: Path to image file

        Returns:
            Dict with file_id and upload success info
        """
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        Delete file from provider's file API

        Args:
            file_id: File identifier to delete

        Returns:
            Dict with deletion success info
        """
        pass

    @abstractmethod
    def delete_all_files(self) -> Dict[str, Any]:
        """
        Delete all files from provider's file API

        Returns:
            Dict with deletion summary
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name (e.g., 'claude', 'gemini')

        Returns:
            String identifier for the provider
        """
        pass

    # ==== CONCRETE METHODS (common implementation using prompts) ====

    def classify_structure(self, text: str, text_blocks: list) -> Dict[str, Any]:
        """Step 1: Classify PDF structure as Form, Table, or Mixed"""

        provider = self.get_provider_name()
        prompt = self.prompt_registry.get_prompt(
            provider, 'classification',
            text_length=len(text),
            total_blocks=len(text_blocks),
            sample_text=text
        )

        result = self._make_request(prompt, 'classification')

        if result.get("success"):
            return result["data"]
        else:
            return {
                "classification": "unknown",
                "confidence": 0.0,
                "reasoning": f"Error in classification: {result.get('error')}",
                "regions": [],
                "error": result.get("error")
            }

    def identify_fields(self, text: str, user_feedback: str = "") -> Dict[str, Any]:
        """Step 2: Identify form fields and table headers"""

        provider = self.get_provider_name()
        prompt = self.prompt_registry.get_prompt(
            provider, 'field_extraction',
            text=text,
            user_feedback=user_feedback or "No specific user feedback provided. Perform initial extraction with high accuracy."
        )

        result = self._make_request(prompt, 'field_identification')

        if result.get("success"):
            return result["data"]
        else:
            return {
                "form_fields": [],
                "tables": [],
                "extraction_summary": {
                    "total_fields": 0,
                    "total_tables": 0,
                    "error": result.get("error")
                }
            }

    def extract_data(self, text: str, field_mapping: Dict[str, Any],
                    user_feedback: str = "", **kwargs) -> Dict[str, Any]:
        """Step 3: Extract actual data using validated structure"""

        provider = self.get_provider_name()

        # Prepare schema strings
        form_fields_schema = field_mapping.get('form_fields', [])
        tables_schema = field_mapping.get('tables', [])

        # Use unified schema extraction if available, otherwise fall back to data extraction
        try:
            prompt = self.prompt_registry.get_prompt(
                provider, 'data_extraction',
                form_fields_schema=json.dumps(form_fields_schema, indent=2),
                tables_schema=json.dumps(tables_schema, indent=2),
                text=text,
                enhanced_instructions=kwargs.get('enhanced_instructions', 'No specific enhancements available'),
                validation_rules=kwargs.get('validation_rules', 'Standard validation applies'),
                detection_improvements=kwargs.get('detection_improvements', 'Standard detection methods apply'),
                format_handling=kwargs.get('format_handling', 'Standard format handling applies')
            )
        except ValueError:
            # Fallback for simpler providers
            schema = {
                "form_fields": form_fields_schema,
                "tables": tables_schema
            }
            prompt = self.prompt_registry.get_prompt(
                provider, 'data_extraction',
                schema=json.dumps(schema, indent=2),
                text=text
            )

        result = self._make_request(prompt, 'data_extraction')

        if result.get("success"):
            # Normalize response format
            extracted_result = result["data"]

            # Handle different response formats
            if "form_data" in extracted_result and "table_data" in extracted_result:
                # Claude format
                return {
                    "extracted_data": extracted_result.get("form_data", {}),
                    "table_data": extracted_result.get("table_data", []),
                    "extraction_summary": {
                        "total_extracted_fields": len(extracted_result.get("form_data", {})),
                        "total_extracted_tables": len(extracted_result.get("table_data", [])),
                        "extraction_success": True,
                        "provider": provider
                    }
                }
            else:
                # Gemini or other format - assume direct extraction
                return {
                    "extracted_data": extracted_result,
                    "table_data": [],
                    "extraction_summary": {
                        "total_extracted_fields": len(extracted_result) if isinstance(extracted_result, dict) else 0,
                        "total_extracted_tables": 0,
                        "extraction_success": True,
                        "provider": provider
                    }
                }
        else:
            return {
                "extracted_data": {},
                "table_data": [],
                "extraction_summary": {
                    "total_extracted_fields": 0,
                    "total_extracted_tables": 0,
                    "extraction_success": False,
                    "error": result.get("error"),
                    "provider": provider
                }
            }

    def extract_with_text_schema(self, raw_text: str, schema: dict) -> Dict[str, Any]:
        """Extract data using text-based schema approach"""

        provider = self.get_provider_name()
        prompt = self.prompt_registry.get_prompt(
            provider, 'text_schema_extraction',
            raw_text=raw_text,
            schema=json.dumps(schema, indent=2)
        )

        result = self._make_request(prompt, 'data_extraction')

        if result.get("success"):
            return {
                "success": True,
                "extracted_data": result["data"],
                "provider": provider
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "provider": provider
            }

    def validate_extraction_with_vision(self, extracted_data: Dict, schema: Dict,
                                       image_data: Any = None, file_id: str = None,
                                       page_num: int = 0, use_comprehensive: bool = True) -> Dict[str, Any]:
        """Validate extracted data against visual document"""

        provider = self.get_provider_name()

        # Choose validation prompt type
        if use_comprehensive and provider == 'claude':
            task_type = 'comprehensive_visual_validation'
            prompt = self.prompt_registry.get_prompt(
                provider, task_type,
                extracted_data=json.dumps(extracted_data, indent=2),
                schema=json.dumps(schema, indent=2),
                page_num=page_num
            )
        else:
            task_type = 'vision_validation'
            if provider == 'claude':
                prompt = self.prompt_registry.get_prompt(
                    provider, task_type,
                    extracted_json=json.dumps(extracted_data, indent=2)
                )
            else:
                prompt = self.prompt_registry.get_prompt(
                    provider, task_type,
                    extracted_data=json.dumps(extracted_data, indent=2),
                    schema=json.dumps(schema, indent=2)
                )

        # Use file_id if available, otherwise image_data
        if file_id:
            return self.validate_with_vision_file(file_id, prompt)
        elif image_data:
            return self.validate_with_vision(image_data, prompt)
        else:
            return {
                "success": False,
                "error": "Either file_id or image_data must be provided"
            }

    def correct_extraction_with_vision(self, extracted_data: Dict, validation_result: Dict,
                                     schema: Dict, image_data: Any = None, file_id: str = None,
                                     page_num: int = 0) -> Dict[str, Any]:
        """Correct extracted data based on visual inspection"""

        provider = self.get_provider_name()
        prompt = self.prompt_registry.get_prompt(
            provider, 'visual_correction',
            extracted_data=json.dumps(extracted_data, indent=2),
            validation_result=json.dumps(validation_result, indent=2),
            schema=json.dumps(schema, indent=2),
            page_num=page_num
        )

        # Use file_id if available, otherwise image_data
        if file_id:
            return self.validate_with_vision_file(file_id, prompt)
        elif image_data:
            return self.validate_with_vision(image_data, prompt)
        else:
            return {
                "success": False,
                "error": "Either file_id or image_data must be provided"
            }

    # ==== UTILITY METHODS ====

    def get_available_tasks(self) -> List[str]:
        """Get list of available task types for this provider"""
        provider = self.get_provider_name()
        prompts = self.prompt_registry.list_available_prompts()
        return list(prompts.get(provider, {}).keys())

    def validate_task_requirements(self, task_type: str, **kwargs) -> bool:
        """Check if all required parameters are provided for a task"""
        provider = self.get_provider_name()
        return self.prompt_registry.validate_prompt_requirements(provider, task_type, **kwargs)

    def get_task_requirements(self, task_type: str) -> List[str]:
        """Get required parameters for a specific task"""
        provider = self.get_provider_name()
        return self.prompt_registry.get_required_variables(provider, task_type)

    def _extract_json_from_response(self, content: str, model: str, task_type: str) -> Dict[str, Any]:
        """Common JSON extraction logic for all providers"""
        import re

        # Strategy 1: Extract from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
        if json_match:
            try:
                json_str = json_match.group(1).strip()
                result = json.loads(json_str)
                return {"success": True, "data": result}
            except json.JSONDecodeError:
                pass

        # Strategy 2: Extract JSON object from response
        json_match = re.search(r'(\{[\s\S]*\})', content)
        if json_match:
            try:
                json_str = json_match.group(1).strip()
                result = json.loads(json_str)
                return {"success": True, "data": result}
            except json.JSONDecodeError:
                pass

        # Strategy 3: Create fallback response
        return {
            "success": False,
            "error": f"Failed to extract valid JSON from {model} response",
            "raw_content": content,
            "model_used": model,
            "task_type": task_type
        }

    def _create_debug_log(self, task_type: str, prompt: str, response: Any) -> str:
        """Create debug log for debugging purposes"""
        import os
        import time

        debug_dir = "debug_responses"
        os.makedirs(debug_dir, exist_ok=True)

        timestamp = int(time.time())
        debug_file = os.path.join(debug_dir, f"debug_{self.get_provider_name()}_{task_type}_{timestamp}.txt")

        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"=== {self.get_provider_name().upper()} DEBUG SESSION ===\n")
                f.write(f"Task Type: {task_type}\n")
                f.write(f"Provider: {self.get_provider_name()}\n")
                f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
                f.write("PROMPT SENT TO LLM:\n")
                f.write("-" * 80 + "\n")
                f.write(prompt)
                f.write("\n" + "=" * 80 + "\n")
                f.write("RAW RESPONSE FROM LLM:\n")
                f.write("-" * 80 + "\n")
                f.write(str(response))
                f.write("\n" + "=" * 80 + "\n")

            return debug_file
        except Exception as e:
            print(f"DEBUG - Failed to save debug log: {e}")
            return ""

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.get_provider_name()}, {self.model_config_name})"

    def __repr__(self) -> str:
        return self.__str__()


# Provider factory function
def create_llm_provider(provider_name: str, api_key: str, model_config_name: str = 'default') -> BaseLLMProvider:
    """
    Factory function to create LLM provider instances

    Args:
        provider_name: 'claude' or 'gemini'
        api_key: API key for the provider
        model_config_name: Model configuration name

    Returns:
        Concrete LLM provider instance

    Raises:
        ValueError: If provider_name is not supported
    """
    if provider_name.lower() == 'claude':
        from .claude_provider import ClaudeProvider
        return ClaudeProvider(api_key, model_config_name)
    elif provider_name.lower() == 'gemini':
        from .gemini_provider import GeminiProvider
        return GeminiProvider(api_key, model_config_name)
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")


if __name__ == "__main__":
    # Demo the base interface
    print("=== Base LLM Provider Interface ===")
    print("✓ Abstract base class defined")
    print("✓ Common methods implemented")
    print("✓ Provider-specific methods abstracted")
    print("✓ Centralized prompt registry integration")
    print("✓ Consistent interface across all providers")
    print("✓ Factory pattern for provider creation")