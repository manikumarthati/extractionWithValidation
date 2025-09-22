#!/usr/bin/env python3
"""
Test the new comprehensive extraction system
"""
import os
from dotenv import load_dotenv
from services.openai_service import OpenAIService
from services.pdf_processor import PDFProcessor

load_dotenv()

def test_comprehensive_extraction():
    # Get the latest uploaded PDF
    doc_id = "8eed35fa-b626-4162-960a-eb653db485bb"
    filepath = "uploads/20250912_132614_obfuscated_fake_cbiz_prof_10_pages_1.pdf"
    
    print(f"Testing comprehensive extraction for {doc_id}")
    
    try:
        # Process PDF
        pdf_processor = PDFProcessor(filepath)
        page_data = pdf_processor.extract_text_and_structure(page_num=0)
        print(f"✓ PDF processed - text length: {len(page_data['text'])}")
        
        # Test comprehensive extraction
        service = OpenAIService(os.environ.get('OPENAI_API_KEY'))
        step1_result = {"classification": "mixed", "confidence": 0.9}
        
        result = service.identify_fields(page_data['text'], step1_result, "")
        
        print(f"✓ Extraction completed")
        print(f"✓ Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"✓ Form fields found: {len(result.get('form_fields', []))}")
            print(f"✓ Tables found: {len(result.get('tables', []))}")
            
            # Show sample results
            if result.get('form_fields'):
                print(f"✓ Sample form field: {result['form_fields'][0].get('label', 'unknown')}")
            
            if result.get('tables'):
                print(f"✓ Sample table: {result['tables'][0].get('title', 'unknown')}")
                print(f"✓ Sample headers: {len(result['tables'][0].get('headers', []))}")
            
            if result.get('extraction_summary'):
                print(f"✓ Confidence: {result['extraction_summary'].get('confidence_score', 0)}")
        
        pdf_processor.close()
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_comprehensive_extraction()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")