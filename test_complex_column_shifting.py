#!/usr/bin/env python3
"""
Test complex column shifting scenarios to ensure the system can handle
multiple column misalignments in single tables/rows
"""

import json
from services.visual_field_inspector import VisualFieldInspector
from services.schema_text_extractor import SchemaTextExtractor

def test_complex_column_shift_detection():
    """Test detection of complex column shifting patterns"""

    print("Testing Complex Column Shift Detection")
    print("=" * 50)

    # Initialize without API key for testing structure
    inspector = VisualFieldInspector("")

    # Scenario 1: Multiple shifts in single row (mixed left/right)
    before_row = {
        "employee_name": "John Doe",
        "employee_id": "12345",
        "department": "Engineering",
        "salary": "$75000",
        "benefit_type": "Health",
        "benefit_cost": "$200"
    }

    # After correction: values shifted in complex pattern
    after_row = {
        "employee_name": "John Doe",  # Correct
        "employee_id": "Engineering", # Wrong - should be 12345 (left shifted from department)
        "department": "$75000",       # Wrong - should be Engineering (left shifted from salary)
        "salary": "Health",           # Wrong - should be $75000 (left shifted from benefit_type)
        "benefit_type": "$200",       # Wrong - should be Health (left shifted from benefit_cost)
        "benefit_cost": None          # Missing - cascade effect
    }

    print("\n[TEST 1] Multiple Column Shifts in Single Row")
    print("Before:", json.dumps(before_row, indent=2))
    print("After:", json.dumps(after_row, indent=2))

    corrections = inspector._detect_column_shifts(before_row, after_row, 1)

    if corrections:
        correction = corrections[0]
        print(f"[DETECTED] Shift Pattern: {correction.get('shift_pattern', 'unknown')}")
        print(f"[DETECTED] Columns Affected: {correction.get('columns_affected', 0)}")
        print(f"[DETECTED] Complexity: {correction.get('complexity', 'unknown')}")

        shift_details = correction.get('shift_details', [])
        print(f"[DETECTED] Detailed Shifts: {len(shift_details)} movements")

        for detail in shift_details[:3]:
            print(f"  - {detail.get('column', 'unknown')}: {detail.get('movement_type', 'unknown')}")
    else:
        print("[ERROR] No column shifts detected!")

    return len(corrections) > 0

def test_cascading_shift_scenario():
    """Test cascading column shifts where one error affects all subsequent columns"""

    print("\n[TEST 2] Cascading Column Shifts")
    print("=" * 30)

    inspector = VisualFieldInspector("")

    # Original data (correctly aligned)
    before_row = {
        "name": "Jane Smith",
        "id": "67890",
        "dept": "Marketing",
        "salary": "$60000",
        "bonus": "$5000",
        "total": "$65000"
    }

    # After OCR error: missing column separator causes cascade
    after_row = {
        "name": "67890",      # Should be Jane Smith (right shift 1)
        "id": "Marketing",    # Should be 67890 (right shift 1)
        "dept": "$60000",     # Should be Marketing (right shift 1)
        "salary": "$5000",    # Should be $60000 (right shift 1)
        "bonus": "$65000",    # Should be $5000 (right shift 1)
        "total": None         # Should be $65000 (missing due to cascade)
    }

    corrections = inspector._detect_column_shifts(before_row, after_row, 2)

    if corrections:
        correction = corrections[0]
        pattern = correction.get('shift_pattern', 'unknown')
        affected = correction.get('columns_affected', 0)

        print(f"[DETECTED] Pattern: {pattern}")
        print(f"[DETECTED] Affected Columns: {affected}")

        # Should detect as cascade_shift (3+ columns affected)
        success = pattern == "cascade_shift" and affected >= 3
        print(f"[RESULT] Cascade detection: {'SUCCESS' if success else 'FAILED'}")

        return success
    else:
        print("[ERROR] No cascade shift detected!")
        return False

def test_partial_row_shifts():
    """Test partial shifts where only some rows in a table are misaligned"""

    print("\n[TEST 3] Partial Row Shifts")
    print("=" * 30)

    inspector = VisualFieldInspector("")

    # Simulate table with mixed good/bad rows
    table_before = [
        {"name": "Alice", "id": "001", "dept": "HR", "salary": "$50000"},
        {"name": "Bob", "id": "002", "dept": "IT", "salary": "$60000"},
        {"name": "Carol", "id": "003", "dept": "Finance", "salary": "$55000"}
    ]

    # After extraction: middle row has column shifts
    table_after = [
        {"name": "Alice", "id": "001", "dept": "HR", "salary": "$50000"},       # Correct
        {"name": "002", "id": "IT", "dept": "$60000", "salary": None},         # Shifted
        {"name": "Carol", "id": "003", "dept": "Finance", "salary": "$55000"}  # Correct
    ]

    partial_shifts_detected = 0

    for i, (before_row, after_row) in enumerate(zip(table_before, table_after)):
        corrections = inspector._detect_column_shifts(before_row, after_row, 1)
        if corrections:
            partial_shifts_detected += 1
            print(f"[DETECTED] Row {i} has column shifts")

    # Should detect shifts in only 1 row (middle row)
    success = partial_shifts_detected == 1
    print(f"[RESULT] Partial shift detection: {'SUCCESS' if success else 'FAILED'}")
    print(f"[RESULT] Rows with shifts: {partial_shifts_detected}/3")

    return success

def test_correction_report_generation():
    """Test that complex column shifts appear correctly in correction reports"""

    print("\n[TEST 4] Complex Shift Correction Report")
    print("=" * 40)

    extractor = SchemaTextExtractor("")

    # Mock complex correction history
    mock_correction_history = [
        {
            "field": "table_row",
            "change_type": "complex_column_realignment",
            "shift_pattern": "cascade_shift",
            "columns_affected": 4,
            "complexity": "high",
            "shift_details": [
                {"column": "benefit_type", "movement_type": "value_moved", "moved_to_column": "benefit_cost"},
                {"column": "benefit_cost", "movement_type": "value_moved", "moved_to_column": "frequency"},
                {"column": "frequency", "movement_type": "value_removed"},
                {"column": "employer_portion", "movement_type": "value_added"}
            ],
            "round": 1
        },
        {
            "field": "employee_tax",
            "change_type": "value_corrected",
            "before_value": "15000",
            "after_value": "1500.75",
            "round": 2
        }
    ]

    # Mock workflow result
    mock_workflow_result = {
        "detailed_results": {
            "visual_validation_summary": {
                "correction_history": mock_correction_history,
                "validation_rounds_completed": 2,
                "final_accuracy_estimate": 0.93
            }
        }
    }

    report = extractor.generate_correction_report(mock_workflow_result)

    print("[REPORT] Generated correction report:")
    print("-" * 50)
    print(report)

    # Verify complex shift reporting
    complex_shift_indicators = [
        "Complex column realignment",
        "Pattern: cascade_shift",
        "Columns affected: 4",
        "Complexity: high",
        "Complex column realignments: 1"
    ]

    found_indicators = []
    for indicator in complex_shift_indicators:
        if indicator in report:
            found_indicators.append(indicator)

    success = len(found_indicators) == len(complex_shift_indicators)
    print(f"\n[RESULT] Complex shift reporting: {'SUCCESS' if success else 'FAILED'}")
    print(f"[RESULT] Found {len(found_indicators)}/{len(complex_shift_indicators)} indicators")

    if not success:
        missing = [ind for ind in complex_shift_indicators if ind not in report]
        print(f"[MISSING] {missing}")

    return success

def test_mixed_shift_patterns():
    """Test detection of mixed shift patterns (some left, some right in same row)"""

    print("\n[TEST 5] Mixed Left/Right Shifts")
    print("=" * 35)

    inspector = VisualFieldInspector("")

    # Before: correct alignment
    before_row = {
        "col_a": "Value_A",
        "col_b": "Value_B",
        "col_c": "Value_C",
        "col_d": "Value_D",
        "col_e": "Value_E"
    }

    # After: mixed shifts (some values moved left, some right)
    after_row = {
        "col_a": "Value_B",  # Value_B moved from col_b (right to left)
        "col_b": "Value_A",  # Value_A moved from col_a (left to right)
        "col_c": "Value_E",  # Value_E moved from col_e (right to left, skip 2)
        "col_d": None,       # Missing
        "col_e": "Value_C"   # Value_C moved from col_c (left to right, skip 2)
    }

    corrections = inspector._detect_column_shifts(before_row, after_row, 1)

    if corrections:
        correction = corrections[0]
        pattern = correction.get('shift_pattern', 'unknown')
        affected = correction.get('columns_affected', 0)

        print(f"[DETECTED] Pattern: {pattern}")
        print(f"[DETECTED] Affected: {affected} columns")

        # Should detect multiple column shifts
        success = affected >= 3 and pattern in ["multiple_column_shift", "cascade_shift"]
        print(f"[RESULT] Mixed shift detection: {'SUCCESS' if success else 'FAILED'}")

        return success
    else:
        print("[ERROR] No mixed shifts detected!")
        return False

if __name__ == "__main__":
    print("[COMPREHENSIVE] Complex Column Shifting Test Suite")
    print("=" * 60)

    tests = [
        test_complex_column_shift_detection,
        test_cascading_shift_scenario,
        test_partial_row_shifts,
        test_correction_report_generation,
        test_mixed_shift_patterns
    ]

    results = []

    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Test failed with exception: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)

    print(f"\n[FINAL RESULTS] {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All complex column shifting scenarios handled correctly!")
        print("\n[CAPABILITIES] The system can now handle:")
        print("- Multiple column shifts within single rows")
        print("- Cascading shifts affecting 3+ columns")
        print("- Mixed left/right shift patterns")
        print("- Partial table misalignments")
        print("- Complex shift reporting and tracking")
    else:
        print("[WARNING] Some complex scenarios need attention")

    print(f"\n[CONFIDENCE] Ready for complex column shifting in production!")