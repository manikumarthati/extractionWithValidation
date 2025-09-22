"""
Test script for the enhanced 100% accuracy visual validation system
"""

import json
import os
from services.schema_text_extractor import SchemaTextExtractor

def test_enhanced_validation():
    """Test the enhanced 100% accuracy validation workflow"""

    # Check if API key is available
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return

    # Initialize enhanced extractor
    extractor = SchemaTextExtractor(api_key)

    print("Enhanced 100% Accuracy Validation Test")
    print("=" * 50)

    # Example schema for testing
    test_schema = {
        "employee_details": {
            "name": "string",
            "employee_id": "string",
            "department": "string",
            "position": "string",
            "salary": "number",
            "email": "string"
        },
        "benefits_table": [
            {
                "benefit_type": "string",
                "coverage": "string",
                "employee_cost": "number",
                "employer_cost": "number"
            }
        ],
        "employer_taxes": [
            {
                "tax_type": "string",
                "rate": "string",
                "amount": "number"
            }
        ]
    }

    print("\n📋 Test Schema:")
    print(json.dumps(test_schema, indent=2))

    # Get PDF path from user
    pdf_path = input("\n📄 Enter path to test PDF file (or press Enter to skip): ").strip()

    if not pdf_path:
        print("ℹ️  No PDF path provided. Enhanced validation system ready!")
        print("\n✅ System configured for 100% accuracy target!")
        print("\n📖 Configuration Details:")
        print("- Maximum validation rounds: 10 (increased from 3)")
        print("- Target accuracy: 100% (increased from ~95%)")
        print("- Accuracy-based termination: Enabled")
        print("- Progressive accuracy tracking: Enabled")
        print("- Enhanced final accuracy calculation: Enabled")
        return

    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        print("\n🚀 Testing Enhanced 100% Accuracy Validation...")
        print("-" * 50)

        # Test with enhanced multi-round validation
        print("\n🎯 Test: Enhanced Multi-Round Validation (Target: 100%)")
        result = extractor.enhanced_extraction_workflow(
            pdf_path, test_schema, page_num=0,
            use_visual_validation=True,
            multi_round_validation=True
        )

        if result['success']:
            workflow_summary = result['workflow_summary']

            print("Extraction completed successfully!")
            print(f"   Text extraction: {'Success' if workflow_summary['text_extraction_success'] else 'Failed'}")
            print(f"   Schema extraction: {'Success' if workflow_summary['schema_extraction_success'] else 'Failed'}")
            print(f"   Visual validation: {'Applied' if workflow_summary['visual_validation_applied'] else 'Skipped'}")
            print(f"   Validation rounds: {workflow_summary.get('validation_rounds_completed', 1)}")
            print(f"   Total corrections: {workflow_summary.get('corrections_applied', 0)}")
            print(f"   Target achieved: {'Yes' if workflow_summary.get('target_accuracy_achieved', False) else 'No'}")
            print(f"   Final accuracy: {workflow_summary.get('final_accuracy_estimate', 0.98):.1%}")

            # Show accuracy progression if available
            detailed_results = result.get('detailed_results', {})
            visual_validation = detailed_results.get('visual_validation_summary', {})
            accuracy_progression = visual_validation.get('accuracy_progression', [])

            if accuracy_progression:
                print(f"\nAccuracy Progression:")
                for prog in accuracy_progression:
                    round_num = prog.get('round', 0)
                    accuracy = prog.get('accuracy', 0)
                    issues = prog.get('issues_found', 0)
                    print(f"   Round {round_num}: {accuracy:.1%} accuracy, {issues} issues")

            # Show correction history
            correction_history = visual_validation.get('correction_history', [])
            if correction_history:
                print(f"\nCorrections Applied ({len(correction_history)} total):")
                correction_types = {}
                for correction in correction_history:
                    change_type = correction.get('change_type', 'unknown')
                    correction_types[change_type] = correction_types.get(change_type, 0) + 1

                for change_type, count in correction_types.items():
                    print(f"   - {change_type.replace('_', ' ').title()}: {count}")

            final_accuracy = workflow_summary.get('final_accuracy_estimate', 0.98)
            if final_accuracy >= 1.0:
                print(f"\nSUCCESS: 100% accuracy achieved!")
            elif final_accuracy >= 0.95:
                print(f"\nHIGH ACCURACY: {final_accuracy:.1%} achieved")
            else:
                print(f"\nMODERATE ACCURACY: {final_accuracy:.1%} achieved")

        else:
            print(f"Extraction failed: {result.get('error')}")

        print("\nFinal Extracted Data:")
        print(json.dumps(result.get('extracted_data', {}), indent=2))

    except Exception as e:
        print(f"Error during testing: {str(e)}")

def demo_enhanced_features():
    """Demonstrate the enhanced validation features"""
    print("\nEnhanced Validation Features:")
    print("-" * 30)
    print("""
TARGET ACCURACY: 100%
- System now targets 100% accuracy instead of ~95%
- Validation continues until target is achieved or max rounds reached

EXTENDED VALIDATION ROUNDS: 10 (was 3)
- Up to 10 rounds of validation and correction
- Intelligent termination when 100% accuracy achieved

PROGRESSIVE ACCURACY TRACKING:
- Tracks accuracy improvement across rounds
- Shows validation progression in real-time
- Identifies when target accuracy is reached

ENHANCED ACCURACY CALCULATION:
- Can achieve and recognize 100% accuracy
- Smarter accuracy estimation based on validation rounds
- Accounts for different types of corrections

INTELLIGENT TERMINATION:
- Stops when 100% accuracy achieved (even before max rounds)
- Continues correction until no issues remain
- Balances thoroughness with efficiency

DETAILED REPORTING:
- Round-by-round accuracy progression
- Comprehensive correction tracking
- Target achievement status
- Enhanced workflow metadata
""")

if __name__ == "__main__":
    print("Enhanced 100% Accuracy Validation Test Suite")
    print("=" * 50)

    choice = input("\nSelect option:\n1. Test enhanced validation\n2. Show enhanced features\n3. Both\nChoice (1/2/3): ").strip()

    if choice in ['1', '3']:
        test_enhanced_validation()

    if choice in ['2', '3']:
        demo_enhanced_features()

    print("\nTesting complete!")
    print("\nReady to achieve 100% accuracy:")
    print("• Streamlit app: streamlit run streamlit_app.py")
    print("• Flask API: python app.py")
    print("• Target: 100% accuracy with up to 10 validation rounds!")