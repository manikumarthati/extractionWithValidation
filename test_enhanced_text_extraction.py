#!/usr/bin/env python3
"""
Test the enhanced text extraction to see if it fixes the truncation issue
"""

import os
from services.schema_text_extractor import SchemaTextExtractor

def test_enhanced_extraction():
    """Test enhanced text extraction vs original basic method"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_1.pdf"

    print("Testing Enhanced Text Extraction")
    print("=" * 40)
    print("Checking if enhanced extraction fixes truncated text issues")
    print()

    try:
        # Create extractor
        extractor = SchemaTextExtractor(api_key)

        # Extract text using enhanced method
        result = extractor.extract_raw_text(pdf_path, page_num=0)

        if not result["success"]:
            print(f"Extraction failed: {result.get('error')}")
            return False

        raw_text = result["raw_text"]
        extraction_method = result["extraction_method"]
        methods_tried = result.get("extraction_methods_tried", [])
        method_scores = result.get("extraction_method_scores", [])

        print(f"Extraction successful using method: {extraction_method}")
        print(f"Methods tried: {methods_tried}")
        print()

        print("Method comparison:")
        for method, score in method_scores:
            print(f"  {method}: {score} characters")
        print()

        # Test for the specific truncation issues
        test_cases = [
            ("Minnesota Federal Loan", "Minnesota Federal Lo", "Tax code description"),
            ("Workforce Enhancement Fee", "Workforce Enhancem", "Another tax description"),
            ("Assessment", "Assessm", "Common truncation pattern")
        ]

        print("Truncation Issue Analysis:")
        print("-" * 30)

        for complete_text, truncated_text, description in test_cases:
            if complete_text in raw_text:
                print(f"[FIXED] Found complete '{complete_text}' ({description})")
            elif truncated_text in raw_text:
                print(f"[STILL TRUNCATED] Found '{truncated_text}' instead of '{complete_text}'")
            else:
                print(f"[NOT FOUND] Neither '{complete_text}' nor '{truncated_text}' found")

        print()

        # Show context around Minnesota Federal text
        if "Minnesota Federal" in raw_text:
            print("Context around 'Minnesota Federal':")
            print("-" * 35)

            # Find all occurrences
            text_lower = raw_text.lower()
            start_pos = text_lower.find("minnesota federal")

            while start_pos != -1:
                # Get surrounding context
                context_start = max(0, start_pos - 50)
                context_end = min(len(raw_text), start_pos + 100)
                context = raw_text[context_start:context_end]

                # Highlight the relevant part
                context_highlighted = context.replace(
                    raw_text[start_pos:start_pos + 17],
                    f">>>{raw_text[start_pos:start_pos + 17]}<<<", 1
                )

                print(f"  ...{context_highlighted}...")

                # Find next occurrence
                start_pos = text_lower.find("minnesota federal", start_pos + 1)

        print()

        # Show sample of extracted text
        print("Sample of extracted text (first 500 characters):")
        print("-" * 50)
        print(raw_text[:500])
        print("...")

        # Check total text length and completeness
        print(f"\nExtraction Statistics:")
        print(f"  Total characters: {len(raw_text):,}")
        print(f"  Total lines: {raw_text.count(chr(10)) + 1}")
        print(f"  Contains 'Caroline Jones': {'Caroline Jones' in raw_text}")
        print(f"  Contains tax codes: {'MNAST' in raw_text and 'MNDW' in raw_text}")

        return True

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_extraction()
    if success:
        print(f"\n[SUCCESS] Enhanced extraction test completed!")
        print("Check the results above to see if truncation issues are resolved.")
    else:
        print(f"\n[FAILED] Enhanced extraction test failed")