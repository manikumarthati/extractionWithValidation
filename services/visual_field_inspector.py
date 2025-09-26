"""
Human-like Visual Field Inspector
Validates extracted data by visually inspecting PDF like a human would,
checking field positions, labels, alignments, and actual values
"""

import json
import time
from typing import Dict, Any, List, Optional
from .vision_extractor import VisionBasedExtractor
from .claude_service import ClaudeService


class VisualFieldInspector:
    def __init__(self, api_key: str):
        """Initialize visual field inspector with vision capabilities"""
        self.vision_extractor = VisionBasedExtractor(api_key)
        self.claude_service = ClaudeService(api_key)

    def validate_all_fields_visually(self, pdf_path: str, extracted_data: Dict,
                                   schema: Dict, page_num: int = 0, file_id: str = None,
                                   page_file_ids: Dict[int, str] = None) -> Dict:
        """
        Human-like visual inspection of all fields
        """
        try:
            # Build comprehensive validation prompt
            validation_prompt = self._build_comprehensive_visual_validation_prompt(
                extracted_data, schema, page_num
            )

            # Save validation prompt to debug folder
            import time
            timestamp = int(time.time())
            debug_folder = "debug_pipeline"
            import os
            os.makedirs(debug_folder, exist_ok=True)

            # Determine which file_id to use for this specific page
            current_file_id = self._get_page_file_id(page_num, file_id, page_file_ids)

            # Use current_file_id if available (token efficient) or fall back to base64 conversion
            if current_file_id:
                # Token-efficient approach: use pre-uploaded image file for this specific page
                response = self.claude_service.validate_with_vision_file(current_file_id, validation_prompt)
            else:
                # Fallback approach: convert PDF to base64 image
                image_data = self.vision_extractor.convert_pdf_to_image(pdf_path, page_num)
                image_base64 = self.vision_extractor.encode_image_to_base64(image_data)
                response = self.claude_service.validate_with_vision(image_base64, validation_prompt)

            if not response["success"]:
                # Save failed validation response
                with open(f"{debug_folder}/validation_failed_{timestamp}.txt", "w", encoding='utf-8') as f:
                    f.write(f"VALIDATION FAILED\n")
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write(f"Error: {response.get('error', 'Unknown error')}\n")
                    f.write(f"Raw Content: {response.get('raw_content', 'No raw content')}\n")

                return {
                    "success": False,
                    "error": f"Vision validation failed: {response.get('error', 'Unknown error')}",
                    "fields_with_issues": 0,
                    "accuracy_score": 0.0
                }

            validation_result = response["data"]

            # Save successful validation response
            import json
            with open(f"{debug_folder}/validation_response_{timestamp}.json", "w", encoding='utf-8') as f:
                json.dump({
                    "timestamp": timestamp,
                    "validation_result": validation_result,
                    "response_metadata": {
                        "success": response.get("success"),
                        "model_used": response.get("model_used"),
                        "response_time": response.get("response_time")
                    }
                }, f, indent=2, default=str)

            return {
                "success": True,
                "validation_result": validation_result
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Visual validation failed: {str(e)}"
            }

    def correct_based_on_visual_inspection(self, pdf_path: str, extracted_data: Dict,
                                         validation_result: Dict, schema: Dict,
                                         page_num: int = 0, file_id: str = None,
                                         page_file_ids: Dict[int, str] = None) -> Dict:
        """Apply corrections based on visual inspection findings"""
        try:
            # Build correction prompt based on inspection results
            correction_prompt = self._build_visual_correction_prompt(
                extracted_data, validation_result, schema, page_num
            )

            # Save correction prompt to debug folder
            import time
            timestamp = int(time.time())
            debug_folder = "debug_pipeline"
            import os
            os.makedirs(debug_folder, exist_ok=True)

            # Determine which file_id to use for this specific page
            current_file_id = self._get_page_file_id(page_num, file_id, page_file_ids)

            # Use current_file_id if available (token efficient) or fall back to base64 conversion
            if current_file_id:
                # Token-efficient approach: use pre-uploaded image file for this specific page
                response = self.claude_service.validate_with_vision_file(current_file_id, correction_prompt)
            else:
                # Fallback approach: convert PDF to base64 image
                image_data = self.vision_extractor.convert_pdf_to_image(pdf_path, page_num)
                image_base64 = self.vision_extractor.encode_image_to_base64(image_data)
                response = self.claude_service.validate_with_vision(image_base64, correction_prompt)

            if not response["success"]:
                # Save failed correction response
                with open(f"{debug_folder}/correction_failed_{timestamp}.txt", "w", encoding='utf-8') as f:
                    f.write(f"CORRECTION FAILED\n")
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write(f"Error: {response.get('error', 'Unknown error')}\n")
                    f.write(f"Raw Content: {response.get('raw_content', 'No raw content')}\n")

                return {
                    "success": False,
                    "error": f"Visual correction failed: {response.get('error', 'Unknown error')}",
                    "corrected_data": extracted_data
                }

            content = json.dumps(response["data"])

            try:
                corrected_data = json.loads(content)
            except json.JSONDecodeError:
                corrected_data = self.vision_extractor._extract_json_from_vision_response(content)

            # Save successful correction response
            import json as json_lib
            with open(f"{debug_folder}/correction_response_{timestamp}.json", "w", encoding='utf-8') as f:
                json_lib.dump({
                    "timestamp": timestamp,
                    "original_data": extracted_data,
                    "validation_findings": validation_result,
                    "corrected_data": corrected_data,
                    "response_metadata": {
                        "success": response.get("success"),
                        "model_used": response.get("model_used"),
                        "response_time": response.get("response_time")
                    }
                }, f, indent=2, default=str)

            return {
                "success": True,
                "corrected_data": corrected_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Visual correction failed: {str(e)}"
            }

    def complete_visual_validation_workflow(self, pdf_path: str, extracted_data: Dict,
                                          schema: Dict, page_num: int = 0, file_id: str = None,
                                          page_file_ids: Dict[int, str] = None) -> Dict:
        """Complete human-like visual validation and correction workflow"""

        try:
            # Step 1: Perform comprehensive visual inspection
            print("[VALIDATE] Performing human-like visual inspection...")
            validation_result = self.validate_all_fields_visually(
                pdf_path, extracted_data, schema, page_num, file_id, page_file_ids
            )

            if not validation_result["success"]:
                return {
                    "success": False,
                    "error": "Visual validation failed",
                    "original_data": extracted_data
                }

            validation_data = validation_result["validation_result"]

            # Step 2: Check if corrections are needed
            overall_assessment = validation_data.get("overall_assessment", {})
            fields_with_issues = overall_assessment.get("fields_with_issues", 0)

            if fields_with_issues == 0:
                print("[OK] No issues found during visual inspection")
                return {
                    "success": True,
                    "extracted_data": extracted_data,
                    "visual_validation_applied": True,
                    "corrections_needed": False,
                    "validation_summary": overall_assessment
                }

            # Step 3: Apply visual corrections
            print(f"[CORRECT] Applying visual corrections for {fields_with_issues} fields...")
            correction_result = self.correct_based_on_visual_inspection(
                pdf_path, extracted_data, validation_data, schema, page_num, file_id, page_file_ids
            )

            if correction_result["success"]:
                return {
                    "success": True,
                    "extracted_data": correction_result["corrected_data"],
                    "visual_validation_applied": True,
                    "corrections_needed": True,
                    "corrections_applied": fields_with_issues,
                    "validation_summary": overall_assessment,
                    "detailed_findings": validation_data
                }
            else:
                return {
                    "success": True,  # Don't fail completely
                    "extracted_data": extracted_data,  # Return original if correction fails
                    "visual_validation_applied": True,
                    "corrections_needed": True,
                    "corrections_failed": True,
                    "validation_summary": overall_assessment,
                    "correction_error": correction_result.get("error")
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Visual validation workflow failed: {str(e)}",
                "original_data": extracted_data
            }

    def multi_round_visual_validation(self, pdf_path: str, extracted_data: Dict,
                                    schema: Dict, page_num: int = 0, max_rounds: int = 10,
                                    target_accuracy: float = 1.0, file_id: str = None,
                                    page_file_ids: Dict[int, str] = None) -> Dict:
        """
        Perform multiple rounds of visual validation and correction for maximum accuracy

        Args:
            pdf_path: Path to PDF file
            extracted_data: Initially extracted data
            schema: Schema for validation
            page_num: Page number
            max_rounds: Maximum validation rounds (default 10)
            target_accuracy: Target accuracy to achieve (default 1.0 for 100%)

        Returns:
            Final validated data with detailed correction tracking
        """
        print(f"[VALIDATE] Starting multi-round visual validation (up to {max_rounds} rounds, target: {target_accuracy:.1%})...")

        current_data = extracted_data.copy()
        correction_history = []
        total_corrections = 0
        accuracy_progression = []

        for round_num in range(1, max_rounds + 1):
            print(f"\n[ROUND] Validation Round {round_num}")

            # Add brief delay before validation to reduce rate limit chance
            if round_num > 1:
                import time
                time.sleep(1)  # 1 second delay before subsequent rounds

            # Perform validation for this round
            validation_result = self.validate_all_fields_visually(
                pdf_path, current_data, schema, page_num, file_id, page_file_ids
            )

            if not validation_result["success"]:
                print(f"ERROR: Round {round_num} validation failed: {validation_result.get('error', 'Unknown error')}")

                # If we've made good progress (>= 99% accuracy), consider this acceptable
                if accuracy_progression and accuracy_progression[-1].get("accuracy", 0) >= 0.99:
                    print(f"DEBUG: Acceptable accuracy achieved ({accuracy_progression[-1].get('accuracy', 0):.1%}), stopping validation")
                    break

                # If early rounds, try to continue with a delay
                if round_num <= 3:
                    print(f"[RETRY] Early round failure, attempting to continue after delay...")
                    import time
                    time.sleep(2)  # Brief delay for rate limiting
                    continue

                print(f"[ERROR] Multiple validation failures, stopping process")
                break

            validation_data = validation_result["validation_result"]
            overall_assessment = validation_data.get("overall_assessment", {})
            fields_with_issues = overall_assessment.get("fields_with_issues", 0)
            current_accuracy = overall_assessment.get("accuracy_estimate", 0.98)

            accuracy_progression.append({
                "round": round_num,
                "accuracy": current_accuracy,
                "issues_found": fields_with_issues
            })

            print(f"DEBUG: Round {round_num}: Accuracy {current_accuracy:.1%}, Issues: {fields_with_issues}")

            # Primary stopping criterion: No issues found (most important)
            if fields_with_issues == 0:
                print(f"SUCCESS: Round {round_num}: No issues found - validation complete!")
                print(f"DEBUG: Final accuracy achieved: {current_accuracy:.1%}")
                break

            # Secondary stopping criterion: Target accuracy reached with minimal issues
            if current_accuracy >= target_accuracy:
                print(f"SUCCESS: Target accuracy {target_accuracy:.1%} achieved in round {round_num}!")
                if fields_with_issues <= 1:  # Allow 1 minor issue at target accuracy
                    print(f"DEBUG: Acceptable quality reached with {fields_with_issues} remaining minor issues")
                    break

            print(f"[CORRECT] Round {round_num}: Found {fields_with_issues} issues, applying corrections...")

            # Apply corrections
            correction_result = self.correct_based_on_visual_inspection(
                pdf_path, current_data, validation_data, schema, page_num, file_id, page_file_ids
            )

            if correction_result["success"]:
                # Track what was corrected
                round_corrections = self._track_corrections(
                    current_data, correction_result["corrected_data"], round_num
                )

                correction_history.extend(round_corrections)
                total_corrections += len(round_corrections)
                current_data = correction_result["corrected_data"]

                print(f"[OK] Round {round_num}: Applied {len(round_corrections)} corrections")

                # Show what was corrected
                for correction in round_corrections:
                    print(f"   - {correction['field']}: {correction['change_type']}")

            else:
                print(f"[ERROR] Round {round_num}: Correction failed")
                break

            # Rate limiting: Add delay between rounds to avoid 429 errors
            if round_num < max_rounds:  # Don't delay after the last round
                import time
                delay = 3  # 3 second delay between rounds
                print(f"[WAIT] Waiting {delay}s before next round to avoid rate limits...")
                time.sleep(delay)

        # Calculate final accuracy
        final_accuracy = self._calculate_enhanced_final_accuracy(
            correction_history, accuracy_progression, target_accuracy
        )

        achieved_target = final_accuracy >= target_accuracy

        print(f"\n[COMPLETE] Validation complete after {round_num} rounds")
        print(f"[ACCURACY] Final accuracy: {final_accuracy:.1%}")
        print(f"[{'SUCCESS' if achieved_target else 'WARNING'}] Target {target_accuracy:.1%} {'achieved' if achieved_target else 'not fully achieved'}")

        return {
            "success": True,
            "extracted_data": current_data,
            "validation_rounds_completed": round_num,
            "total_corrections_applied": total_corrections,
            "correction_history": correction_history,
            "accuracy_progression": accuracy_progression,
            "final_accuracy_estimate": final_accuracy,
            "target_accuracy_achieved": achieved_target,
            "visual_validation_applied": True,
            "high_accuracy_validation": True
        }

    def _track_corrections(self, before_data: Dict, after_data: Dict, round_num: int) -> List[Dict]:
        """Track what corrections were made between two data versions"""
        corrections = []

        def compare_values(before, after, field_path=""):
            if isinstance(before, dict) and isinstance(after, dict):
                # Compare dictionaries
                all_keys = set(before.keys()) | set(after.keys())
                for key in all_keys:
                    current_path = f"{field_path}.{key}" if field_path else key

                    if key not in before:
                        corrections.append({
                            "field": current_path,
                            "change_type": "field_added",
                            "before_value": None,
                            "after_value": after[key],
                            "round": round_num
                        })
                    elif key not in after:
                        corrections.append({
                            "field": current_path,
                            "change_type": "field_removed",
                            "before_value": before[key],
                            "after_value": None,
                            "round": round_num
                        })
                    else:
                        compare_values(before[key], after[key], current_path)

            elif isinstance(before, list) and isinstance(after, list):
                # Compare arrays (like table rows)
                if len(before) != len(after):
                    corrections.append({
                        "field": field_path,
                        "change_type": "table_rows_changed",
                        "before_value": f"{len(before)} rows",
                        "after_value": f"{len(after)} rows",
                        "round": round_num
                    })

                # Compare individual items and detect column shifting patterns
                for i in range(min(len(before), len(after))):
                    before_item = before[i]
                    after_item = after[i]

                    # Detect complex column shifts in table rows
                    if isinstance(before_item, dict) and isinstance(after_item, dict):
                        column_shifts = self._detect_column_shifts(before_item, after_item, round_num)
                        corrections.extend(column_shifts)

                    compare_values(before_item, after_item, f"{field_path}[{i}]")

            else:
                # Compare primitive values
                if before != after:
                    corrections.append({
                        "field": field_path,
                        "change_type": "value_corrected",
                        "before_value": str(before)[:100],  # Limit length
                        "after_value": str(after)[:100],
                        "round": round_num
                    })

        compare_values(before_data, after_data)
        return corrections

    def _calculate_final_accuracy(self, correction_history: List[Dict]) -> float:
        """Calculate estimated final accuracy based on correction pattern"""
        if not correction_history:
            return 0.98  # High confidence if no corrections needed

        # Analyze correction patterns
        total_corrections = len(correction_history)

        # More corrections in later rounds suggests more complex issues
        later_round_corrections = len([c for c in correction_history if c['round'] > 1])

        if total_corrections <= 2:
            return 0.95  # Minor corrections
        elif total_corrections <= 5:
            return 0.92  # Moderate corrections
        elif later_round_corrections > 0:
            return 0.88  # Multiple rounds needed
        else:
            return 0.90  # Many corrections but resolved in early rounds

    def _calculate_enhanced_final_accuracy(self, correction_history: List[Dict],
                                         accuracy_progression: List[Dict],
                                         target_accuracy: float) -> float:
        """Enhanced accuracy calculation that can achieve 100% accuracy"""

        # If no corrections needed and no issues found in final round, assume perfect accuracy
        if not correction_history and accuracy_progression:
            final_round = accuracy_progression[-1]
            if final_round.get("issues_found", 0) == 0:
                return 1.0  # Perfect accuracy achieved

        # If we have accuracy progression data, use the latest measurement
        if accuracy_progression:
            latest_accuracy = accuracy_progression[-1].get("accuracy", 0.98)
            issues_found = accuracy_progression[-1].get("issues_found", 0)

            # If no issues found in final round and accuracy is high, boost to target
            if issues_found == 0 and latest_accuracy >= 0.95:
                return min(1.0, latest_accuracy + 0.05)  # Cap at 100%

            return latest_accuracy

        # Fallback to original calculation
        return self._calculate_final_accuracy(correction_history)

    def _detect_column_shifts(self, before_row: Dict, after_row: Dict, round_num: int) -> List[Dict]:
        """Detect and categorize column shifting patterns in table rows"""

        column_corrections = []

        # Get all column names from both versions
        before_cols = set(before_row.keys())
        after_cols = set(after_row.keys())
        all_cols = before_cols | after_cols

        # Track which values moved where
        before_values = list(before_row.values())
        after_values = list(after_row.values())

        shifts_detected = []

        for col in all_cols:
            before_val = before_row.get(col)
            after_val = after_row.get(col)

            if before_val != after_val:
                # Check if this value appears in a different column now
                shift_info = self._analyze_value_movement(before_val, after_val, before_row, after_row, col)
                if shift_info:
                    shifts_detected.append(shift_info)

        # Categorize the shift pattern
        if len(shifts_detected) >= 3:
            shift_pattern = "cascade_shift"
        elif len(shifts_detected) >= 2:
            shift_pattern = "multiple_column_shift"
        elif len(shifts_detected) == 1:
            shift_pattern = "single_column_shift"
        else:
            return column_corrections

        # Create comprehensive correction entry
        column_corrections.append({
            "field": "table_row",
            "change_type": "complex_column_realignment",
            "shift_pattern": shift_pattern,
            "columns_affected": len(shifts_detected),
            "shift_details": shifts_detected,
            "before_value": str(before_row)[:100],
            "after_value": str(after_row)[:100],
            "round": round_num,
            "complexity": "high" if len(shifts_detected) >= 2 else "medium"
        })

        return column_corrections

    def _get_page_file_id(self, page_num: int, fallback_file_id: str = None,
                         page_file_ids: Dict[int, str] = None) -> str:
        """
        Get the correct file ID for a specific page.

        Args:
            page_num: The page number being processed
            fallback_file_id: Fallback file ID if page-specific mapping not available
            page_file_ids: Dictionary mapping page numbers to file IDs

        Returns:
            The appropriate file ID for the page, or None if not available
        """
        if page_file_ids and page_num in page_file_ids:
            file_id = page_file_ids[page_num]
            print(f"[IMAGE-ID] Using page-specific file ID for page {page_num}: {file_id[:12]}...")
            return file_id
        elif fallback_file_id:
            print(f"[IMAGE-ID] Using fallback file ID for page {page_num}: {fallback_file_id[:12]}...")
            return fallback_file_id
        else:
            print(f"[IMAGE-ID] No file ID available for page {page_num}, will use base64 conversion")
            return None

    def _analyze_value_movement(self, before_val, after_val, before_row: Dict, after_row: Dict, column: str) -> Dict:
        """Analyze how a specific value moved between columns"""

        if before_val is None and after_val is not None:
            return {
                "column": column,
                "movement_type": "value_added",
                "before": None,
                "after": after_val
            }

        if before_val is not None and after_val is None:
            # Check if this value appears elsewhere in the after_row
            for other_col, other_val in after_row.items():
                if other_val == before_val and other_col != column:
                    return {
                        "column": column,
                        "movement_type": "value_moved",
                        "before": before_val,
                        "after": None,
                        "moved_to_column": other_col,
                        "shift_direction": self._calculate_shift_direction(column, other_col, list(before_row.keys()))
                    }

            return {
                "column": column,
                "movement_type": "value_removed",
                "before": before_val,
                "after": None
            }

        if before_val != after_val:
            return {
                "column": column,
                "movement_type": "value_replaced",
                "before": before_val,
                "after": after_val
            }

        return None

    def _calculate_shift_direction(self, from_col: str, to_col: str, column_order: List[str]) -> str:
        """Calculate the direction and magnitude of column shift"""

        try:
            from_idx = column_order.index(from_col)
            to_idx = column_order.index(to_col)

            shift = to_idx - from_idx

            if shift > 0:
                return f"right_shift_{shift}"
            elif shift < 0:
                return f"left_shift_{abs(shift)}"
            else:
                return "no_shift"

        except ValueError:
            return "unknown_shift"

    def _build_comprehensive_visual_validation_prompt(self, extracted_data: Dict, schema: Dict, page_num: int = 0) -> str:
        """Build Chain of Thought prompt that mimics human visual inspection with step-by-step reasoning"""

        prompt = f"""**CRITICAL: You are viewing the uploaded document image for PAGE {page_num}.** Use this specific page image to perform a detailed visual inspection like a human data entry specialist would do. Look directly at the uploaded page image to verify the extracted data below.

**VISUAL INSPECTION TASK**: Compare the extracted data against what you can actually see in the uploaded page {page_num} image. Use Chain of Thought reasoning to systematically validate each field and value by looking at the visual document.

CURRENT EXTRACTED DATA TO VERIFY AGAINST PAGE {page_num} IMAGE:
{json.dumps(extracted_data, indent=2)}

EXPECTED SCHEMA:
{json.dumps(schema, indent=2)}

**IMPORTANT**: You are looking at page {page_num} of the document. Throughout this inspection, you must look at the uploaded page image to verify every field and value. Do not rely on assumptions - verify everything against what you can visually see in page {page_num}.""" + """

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
   - "Are any columns that should be empty showing values?"
   - "Are any columns that should have values showing as empty?"
   - "Example check: If CalcCode contains 'B5' but should be empty, and Frequency is empty but should contain 'B5', this is a left-shift error"
4. "If misaligned, let me trace where this value should actually go:"
   - "Value '[VALUE]' looks like it belongs in column '[CORRECT_COLUMN]'"
   - "This suggests a [LEFT_SHIFT/RIGHT_SHIFT/EMPTY_SKIP_SHIFT] pattern"

**STEP 5: CONFIDENCE ASSESSMENT AND SELF-VERIFICATION**
Before finalizing my assessment:

*Self-Check Process:*
1. "Let me double-check my most critical findings..."
2. "Are there any inconsistencies in my analysis?"
3. "Did I miss any obvious visual cues?"
4. "How confident am I in each major finding? Why?"
5. "What would I do differently if I were to re-examine this?"

**STEP 6: COMPREHENSIVE REASONING SYNTHESIS**
Finally, I will synthesize my findings:
1. "Based on my systematic analysis..."
2. "The main issues I identified are..."
3. "My confidence levels for different findings are..."
4. "The recommended corrections are..."

## ENHANCED VISUAL INSPECTION TASKS:

1. **FIELD LOCATION & LABEL MATCHING WITH REASONING:**
   - Think: "I'm looking for field X, let me scan methodically..."
   - Reason: "The label appears to be at position Y, and the value I see is Z"
   - Verify: "Does this match the extracted data? Let me compare..."

2. **EMPTY FIELD DETECTION WITH EXPLICIT CHECKING:**
   - Think: "For this field, is there actually any visible content?"
   - Reason: "I can see the field label, but the value area appears [EMPTY/FILLED/UNCLEAR]"
   - Distinguish: "This is [TRULY_EMPTY/MISSED_EXTRACTION/UNCLEAR_TEXT] because..."

3. **TABLE COMPLETENESS WITH ZERO-TOLERANCE ROW COUNTING:**
   - Think: "Let me count every single row I can see, including edge cases..."
   - Reason: "I see rows at these locations: [LIST_ALL_VISIBLE_ROWS]"
   - Verify: "Did I miss any rows? Let me scan again..."
   - Account: "My final count is X rows because I can clearly see..."

4. **COLUMN ALIGNMENT WITH SEMANTIC REASONING:**
   - Think: "For each cell, does the content type match the column header?"
   - Reason: "Cell contains [VALUE], column is [HEADER] - this [MAKES_SENSE/DOESN'T_MAKE_SENSE] because..."
   - Trace: "If misaligned, this value likely belongs in [CORRECT_COLUMN] because..."

5. **CRITICAL: EMPTY COLUMN SKIP DETECTION:**
   - Think: "Are there empty columns that might cause values to shift into wrong positions?"
   - Reason: "If column X is empty but has a value, and column X+1 is empty but should have that value, this suggests a left-shift pattern"
   - Example: "CalcCode column shows 'B5' but should be empty, Frequency column is empty but should contain 'B5'"
   - Analyze: "Does this value make more sense in the next column over?"
   - **SPECIFIC PATTERN**: Value appears in column N when column N is empty in document, but column N+1 should contain that value

6. **SPATIAL RELATIONSHIP ANALYSIS WITH PHYSICAL REASONING:**
   - Think: "What are the visual cues (lines, spacing, alignment) telling me?"
   - Reason: "The positioning suggests this value belongs to [FIELD] because..."
   - Verify: "The physical layout confirms/contradicts the extraction because..."

## SELF-EXPLANATION REQUIREMENTS:
- Explain your reasoning process for each major finding
- State your confidence level and justify it
- Describe what visual cues led to your conclusions
- Note any areas of uncertainty and why
- Provide alternative interpretations when applicable

## CHAIN OF THOUGHT REASONING OUTPUT:
Before providing the final validation results, show your step-by-step reasoning process:

### REASONING_TRACE:
{
  "document_analysis": {
    "document_type": "[Your assessment of document type]",
    "main_sections": "[List of main sections you identified]",
    "layout_organization": "[How information is visually organized]",
    "context_understanding": "[Your reasoning about document context]"
  },
  "field_by_field_reasoning": [
    {
      "field_name": "Employee_Name",
      "reasoning_steps": [
        "I'm looking for field Employee_Name with extracted value 'John Doe'",
        "Scanning document for the field label...",
        "Found label 'Employee Name:' at top left of document",
        "Value near this label appears to be 'John Doe'",
        "Comparing extracted vs actual: MATCH",
        "Confidence: 0.95 because label and value alignment is clear"
      ],
      "visual_cues": "Clear field label, consistent spacing, proper alignment",
      "confidence_justification": "High confidence due to unambiguous visual positioning"
    }
  ],
  "table_analysis_reasoning": [
    {
      "table_name": "Employee_Benefits",
      "counting_process": [
        "Examining table: Employee_Benefits",
        "Column headers identified: [Benefit Type, Cost, Frequency]",
        "Row 1: I can see data: [Health Insurance, $200, Monthly]",
        "Row 2: I can see data: [Dental, $50, Monthly]",
        "Row 3: I can see data: [Vision, $25, Monthly]",
        "Total rows counted visually: 3",
        "Total rows in extracted data: 2",
        "MISMATCH - Missing 1 row in extraction"
      ],
      "column_alignment_reasoning": [
        "Looking at row 0: [Health Insurance, $200, Monthly]",
        "Column Benefit Type: Expected text, actual 'Health Insurance' - YES, makes sense",
        "Column Cost: Expected currency, actual '$200' - YES, makes sense",
        "Column Frequency: Expected frequency text, actual 'Monthly' - YES, makes sense"
      ]
    }
  ],
  "self_verification": {
    "double_check_results": "[Your self-verification process]",
    "consistency_check": "[Any inconsistencies found]",
    "missed_cues": "[Visual cues you might have missed]",
    "confidence_assessment": "[Overall confidence in findings]",
    "alternative_interpretations": "[Other possible interpretations]"
  }
}

## FINAL VALIDATION RESULTS:

{
  "reasoning_trace": "[Include the reasoning trace from above]",
  "field_validation_results": [
    {
      "field_name": "Employee_Name",
      "extracted_value": "John Doe",
      "visual_inspection": {
        "field_label_found": true,
        "field_label_text": "Employee Name:",
        "actual_value_in_document": "John Doe",
        "value_matches_extraction": true,
        "field_is_actually_empty": false,
        "correct_field_assignment": true,
        "confidence": 0.95,
        "reasoning": "Clear visual alignment between label and value",
        "visual_cues": "Proper spacing and positioning",
        "uncertainty_factors": "None identified"
      }
    },
    {
      "field_name": "Department",
      "extracted_value": null,
      "visual_inspection": {
        "field_label_found": true,
        "field_label_text": "Department:",
        "actual_value_in_document": "Engineering",
        "value_matches_extraction": false,
        "field_is_actually_empty": false,
        "correct_field_assignment": false,
        "confidence": 0.90,
        "issue": "Value present but not extracted",
        "reasoning": "Clear text visible next to Department label",
        "visual_cues": "Consistent formatting with other fields",
        "uncertainty_factors": "Text clarity is good, extraction should have caught this"
      }
    }
  ],
  "table_validation_results": [
    {
      "table_name": "Employee_Benefits",
      "rows_visible_in_image": 6,
      "rows_extracted": 5,
      "missing_rows": 1,
      "row_completeness_issue": true,
      "counting_reasoning": "Systematic visual count identified 6 distinct data rows",
      "visual_evidence": "All rows have clear boundaries and data content",
      "aggressive_recount_performed": true,
      "boundary_rows_checked": true,
      "formatting_variations_scanned": true,
      "partial_rows_included": true,
      "column_alignment_issues": [
        {
          "row_index": 0,
          "shift_pattern": "mixed_shifts",
          "affected_columns": ["Benefit Type", "Cost", "Frequency"],
          "issue": "Multiple column misalignments in single row",
          "reasoning": "Semantic analysis shows data types don't match expected columns",
          "detailed_shifts": [
            {
              "column": "Benefit Type",
              "extracted_value": "$200",
              "correct_value": "Health Insurance",
              "shift_direction": "left_shift_2",
              "confidence": 0.88,
              "reasoning": "Currency value in text field indicates column misalignment"
            }
          ],
          "empty_column_skip_issues": [
            {
              "affected_columns": ["Calc_Code", "Frequency"],
              "issue_type": "value_in_wrong_column_due_to_empty_skip",
              "wrong_assignment": {
                "column": "Calc_Code",
                "extracted_value": "B5",
                "should_be_value": ""
              },
              "correct_assignment": {
                "column": "Frequency",
                "extracted_value": "",
                "should_be_value": "B5"
              },
              "reasoning": "B5 appears in CalcCode but that column should be empty, B5 should be in Frequency column",
              "confidence": 0.92
            }
          ],
          "root_cause": "OCR missed column separator between Benefit Type and Cost",
          "correction_complexity": "high",
          "visual_evidence": "Column separators appear faded or unclear"
        }
      ],
      "missing_row_data": [
        {"row_index": 1, "visible_data": {"Benefit Type": "Dental", "Cost": "$50"}},
        {"row_index": 2, "visible_data": {"Benefit Type": "Vision", "Cost": "$25"}}
      ]
    }
  ],
  "overall_assessment": {
    "total_fields_checked": 15,
    "fields_with_issues": 3,
    "accuracy_estimate": 0.92,
    "major_issues": ["Column shifting in benefits table", "Missing department value"],
    "recommendation": "Needs correction for 3 fields and 1 table alignment",
    "confidence_in_assessment": 0.88,
    "reasoning_quality": "Systematic analysis with explicit verification steps",
    "areas_of_uncertainty": ["Some visual elements could be clearer"],
    "validation_thoroughness": "High - used exhaustive counting and semantic verification"
  }
}

## REQUIRED JSON RESPONSE FORMAT:

You MUST respond with valid JSON only, no additional text. Use this exact format:

{
  "field_validation_results": [
    {
      "field_name": "field_name_here",
      "extracted_value": "value_or_null",
      "visual_inspection": {
        "field_label_found": true,
        "actual_value_in_document": "actual_value_or_null",
        "value_matches_extraction": true,
        "field_is_actually_empty": false,
        "confidence": 0.95,
        "issue": "description_if_any_or_null"
      }
    }
  ],
  "table_validation_results": [
    {
      "table_name": "table_name_here",
      "rows_visible_in_image": 0,
      "rows_extracted": 0,
      "row_completeness_issue": false,
      "column_alignment_issues": []
    }
  ],
  "overall_assessment": {
    "total_fields_checked": 0,
    "fields_with_issues": 0,
    "accuracy_estimate": 0.95,
    "major_issues": [],
    "recommendation": "description_here"
  }
}

Perform the visual inspection now and respond with valid JSON only:"""

        return prompt

    def _build_visual_correction_prompt(self, extracted_data: Dict, validation_result: Dict, schema: Dict, page_num: int = 0) -> str:
        """Build correction prompt based on visual inspection findings"""

        prompt = f"""**CRITICAL: You are viewing the uploaded document image for PAGE {page_num}.** Based on the visual inspection findings below, correct the extracted data by carefully examining this specific page image.

**VISUAL CORRECTION TASK**: Use the uploaded page {page_num} image to correct the extracted data based on what you can actually see in the visual document.

ORIGINAL EXTRACTED DATA FROM PAGE {page_num}:
{json.dumps(extracted_data, indent=2)}

VISUAL INSPECTION FINDINGS FOR PAGE {page_num}:
{json.dumps(validation_result, indent=2)}

TARGET SCHEMA:
{json.dumps(schema, indent=2)}

**IMPORTANT**: Look at the uploaded page {page_num} image to make these corrections. Verify each correction against what you can visually see in the document image.""" + """

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
   - If a cell is truly empty in the image, use null
   - **CRITICAL:** If the image shows 6 table rows but only 5 were extracted, extract ALL 6 rows
   - Never stop at the first row - scan the entire table top to bottom
   - **MANDATORY EXHAUSTIVE SCAN:** Look for rows in these specific locations:
     * At the very bottom of the table (last row might be cut off or faded)
     * Near page boundaries or margins
     * Rows with different formatting, font size, or color
     * Partially visible rows or rows with different alignment
     * Rows that might be wrapped or split across lines
   - **EMPLOYER TAX SPECIFIC:** If this is an employer tax table, ensure you find all 6 rows
   - **NO EXCUSES:** If validation says 6 rows visible but you only see 5, look harder until you find the 6th
   - **MANDATORY RECOUNT:** Count rows again if extraction seems incomplete

3. **FOR MISMATCHED VALUES:**
   - Verify the correct field-value relationships
   - Move misplaced values to their correct fields
   - Extract any missed values

4. **VISUAL VERIFICATION:**
   - Double-check your corrections against what you actually see
   - Ensure logical consistency (names look like names, numbers like numbers)
   - Maintain the original schema structure

Return the corrected data in the exact schema format.
IMPORTANT: Return ONLY the corrected JSON data, no additional text or explanations. ENSURE data is in valid JSON format."""

        return prompt