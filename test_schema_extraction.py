"""
Test script for schema-based PDF extraction with vision validation
Demonstrates the complete workflow
"""

import json
import os
from services.schema_text_extractor import SchemaTextExtractor

def test_schema_extraction():
    """Test the complete schema extraction workflow"""

    # Check if API key is available
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return

    # Initialize extractor
    extractor = SchemaTextExtractor(api_key)

    # Example schema (user would provide this)
    example_schema = {
        "employee_info": {
            "name": "string",
            "employee_id": "string",
            "department": "string",
            "position": "string",
            "hire_date": "string",
            "salary": "number"
        },
        "benefits_table": [
            {
                "benefit_type": "string",
                "coverage_amount": "string",
                "employee_contribution": "string",
                "employer_contribution": "string"
            }
        ]
    }

    print("🚀 Schema-Based PDF Extraction Test")
    print("=" * 50)

    # Display schema
    print("\n📋 Example Schema:")
    print(json.dumps(example_schema, indent=2))

    # Test with a PDF file (user would provide this)
    test_pdf_path = input("\n📄 Enter path to test PDF file (or press Enter to skip): ").strip()

    if not test_pdf_path:
        print("ℹ️  No PDF path provided. Test skipped.")
        print("\n✅ Schema extractor initialized successfully!")
        print("\n📖 How to use:")
        print("1. Run: streamlit run streamlit_app.py")
        print("2. Upload your PDF and JSON schema")
        print("3. The system will:")
        print("   - Extract text from PDF")
        print("   - Extract data using your schema")
        print("   - Validate with vision AI")
        print("   - Correct any issues automatically")
        return

    if not os.path.exists(test_pdf_path):
        print(f"❌ PDF file not found: {test_pdf_path}")
        return

    try:
        print("\n🔄 Starting extraction workflow...")

        # Run complete workflow
        result = extractor.process_complete_workflow(test_pdf_path, example_schema, page_num=0)

        if result['success']:
            print("✅ Extraction completed successfully!")

            # Display summary
            summary = result['workflow_summary']
            print(f"\n📊 Workflow Summary:")
            print(f"   Text extraction: {'✅' if summary['text_extraction_success'] else '❌'}")
            print(f"   Schema extraction: {'✅' if summary['schema_extraction_success'] else '❌'}")
            print(f"   Vision validation: {'✅' if summary['vision_validation_success'] else '❌'}")
            print(f"   Correction applied: {'✅' if summary['correction_applied'] else '❌'}")

            # Display final data
            print(f"\n📋 Final Extracted Data:")
            print(json.dumps(result['extracted_data'], indent=2))

            # Display validation details if available
            if 'validation_result' in result and result['validation_result']['success']:
                validation_data = result['validation_result']['validation_result']
                accuracy = validation_data.get('accuracy_score', 'N/A')
                issues = validation_data.get('issues_found', 0)
                print(f"\n👁️  Vision Validation:")
                print(f"   Accuracy score: {accuracy}")
                print(f"   Issues found: {issues}")

                if issues > 0:
                    print(f"   Column shifting: {'✅' if validation_data.get('column_shifting_detected') else '❌'}")
                    print(f"   Field mapping issues: {'✅' if validation_data.get('field_mapping_issues_detected') else '❌'}")
        else:
            print(f"❌ Extraction failed: {result.get('error')}")

    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")

def demo_schema_formats():
    """Show examples of different schema formats"""
    print("\n📋 Schema Format Examples")
    print("=" * 30)

    # Simple form schema
    print("\n1️⃣  Simple Form Schema:")
    simple_schema = {
        "name": "string",
        "age": "number",
        "email": "string",
        "phone": "string"
    }
    print(json.dumps(simple_schema, indent=2))

    # Complex nested schema
    print("\n2️⃣  Complex Nested Schema:")
    complex_schema = {
        "personal_info": {
            "full_name": "string",
            "date_of_birth": "string",
            "social_security": "string"
        },
        "employment": {
            "company": "string",
            "position": "string",
            "start_date": "string",
            "annual_salary": "number"
        },
        "dependents": [
            {
                "name": "string",
                "relationship": "string",
                "age": "number"
            }
        ]
    }
    print(json.dumps(complex_schema, indent=2))

    # Table-focused schema
    print("\n3️⃣  Table-Focused Schema:")
    table_schema = {
        "employee_records": [
            {
                "employee_id": "string",
                "name": "string",
                "department": "string",
                "salary": "number",
                "status": "string"
            }
        ],
        "benefit_costs": [
            {
                "benefit_type": "string",
                "monthly_cost": "number",
                "coverage_level": "string"
            }
        ]
    }
    print(json.dumps(table_schema, indent=2))

if __name__ == "__main__":
    print("🧪 Schema-Based PDF Extraction Test Suite")
    print("=" * 50)

    choice = input("\nSelect option:\n1. Run extraction test\n2. Show schema examples\n3. Both\nChoice (1/2/3): ").strip()

    if choice in ['1', '3']:
        test_schema_extraction()

    if choice in ['2', '3']:
        demo_schema_formats()

    print("\n🎉 Test complete!")
    print("\n📖 Next steps:")
    print("1. Run Streamlit app: streamlit run streamlit_app.py")
    print("2. Or use Flask API: python app.py")
    print("3. Upload your PDF + JSON schema")
    print("4. Get validated, corrected data!")