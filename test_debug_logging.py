#!/usr/bin/env python3
"""
Test the comprehensive debug logging functionality
"""

import json
import os
from services.advanced_pipeline import AdvancedPDFExtractionPipeline

def test_debug_logging():
    """Test comprehensive debug logging throughout pipeline"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # PDF path and schema
    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_1.pdf"
    schema_path = "D:/learning/stepwisePdfParsing/employee_profile_hierarchical_schema.json"

    try:
        # Load schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        print("Testing Debug Logging Functionality")
        print("=" * 50)
        print("This will create comprehensive debug files for each step:")
        print("1. Pipeline input parameters")
        print("2. Extracted raw text from PDF")
        print("3. Extraction prompt sent to Claude")
        print("4. Claude's response")
        print("5. Raw extracted data")
        print("6. Validated extracted data")
        print("7. Validation inputs for each round")
        print("8. Validation prompts for each round")
        print("9. Validation responses for each round")
        print("10. Parsed validation results for each round")
        print("11. Final compilation input")
        print("12. Final compiled results")
        print("13. Final pipeline result")
        print()

        # Create pipeline with debug enabled (default)
        pipeline = AdvancedPDFExtractionPipeline(api_key, 'budget', enable_debug=True)

        print(f"Debug files will be saved to: {pipeline.debug_logger.debug_dir}")
        print(f"Session ID: {pipeline.debug_logger.session_id}")
        print()

        print("Running pipeline...")
        result = pipeline.process_document(
            pdf_path=pdf_path,
            schema=schema,
            page_num=0,
            max_rounds=2,  # Limit rounds for testing
            target_accuracy=0.85
        )

        print(f"Pipeline completed: {result.get('success')}")

        # Show debug files created
        debug_dir = pipeline.debug_logger.debug_dir
        if os.path.exists(debug_dir):
            debug_files = [f for f in os.listdir(debug_dir) if str(pipeline.debug_logger.session_id) in f]
            debug_files.sort()

            print(f"\n[DEBUG FILES CREATED] ({len(debug_files)} files):")
            print("-" * 40)

            for file in debug_files:
                file_path = os.path.join(debug_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  {file} ({file_size:,} bytes)")

                # Show a preview of the content for some key files
                if "pipeline_input" in file or "final_pipeline_result" in file:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                        print(f"    Preview: {list(content.keys())}")
                    except:
                        pass

            print(f"\n[ANALYSIS GUIDE]:")
            print("To analyze the pipeline execution:")
            print("1. Start with '00_pipeline_input' to see what was sent")
            print("2. Check '01_extracted_raw_text.txt' to see PDF text")
            print("3. Review '02_extraction_prompt.txt' to see the prompt")
            print("4. Check '03_claude_response.json' to see Claude's raw response")
            print("5. Follow validation rounds if any were executed")
            print("6. End with '12_final_pipeline_result.json' to see the output")

            print(f"\n[TROUBLESHOOTING]:")
            print("If extraction fails:")
            print("- Check if raw text extraction worked (step 01)")
            print("- Verify the extraction prompt is well-formed (step 02)")
            print("- Check Claude's response for errors (step 03)")
            print()
            print("If validation fails:")
            print("- Check validation inputs (step 06_*)")
            print("- Review validation prompts (step 07_*)")
            print("- Examine Claude's validation responses (step 08_*)")

            return True

        else:
            print("Debug directory not found")
            return False

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_debug_logging()
    if success:
        print(f"\n[SUCCESS] Debug logging test completed!")
        print("Check the debug_pipeline directory for comprehensive step-by-step files.")
    else:
        print(f"\n[FAILED] Debug logging test failed")