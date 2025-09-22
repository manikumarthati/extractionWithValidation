#!/usr/bin/env python3
"""
Debug script for Step 2 timeout issues
"""
import os
from dotenv import load_dotenv
from services.openai_service import OpenAIService
from services.pdf_processor import PDFProcessor

load_dotenv()

def test_step2_debug():
    # Get the latest uploaded PDF
    doc_id = "a6494906-77bc-4e03-9a8b-7cfe6465b5ed"
    filepath = "uploads/20250912_123612_obfuscated_fake_cbiz_prof_10_pages_1.pdf"
    
    print(f"DEBUG: Starting Step 2 debug for {doc_id}")
    
    # Test PDF processing
    try:
        pdf_processor = PDFProcessor(filepath)
        page_data = pdf_processor.extract_text_and_structure(page_num=0)
        print(f"DEBUG: PDF processed successfully")
        print(f"DEBUG: Text length: {len(page_data['text'])}")
        print(f"DEBUG: Text blocks: {len(page_data['text_blocks'])}")
        print(f"DEBUG: First 200 chars: {page_data['text'][:200]}")
        pdf_processor.close()
    except Exception as e:
        print(f"ERROR: PDF processing failed: {e}")
        return
    
    # Test OpenAI service initialization
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        service = OpenAIService(api_key)
        print(f"DEBUG: OpenAI service initialized")
    except Exception as e:
        print(f"ERROR: OpenAI service init failed: {e}")
        return
    
    # Test a simple classification first
    try:
        result = service.classify_structure(
            page_data['text'][:1000],  # Limit text for test
            page_data['text_blocks'][:10]  # Limit blocks for test
        )
        print(f"DEBUG: Classification test: {result.get('classification', 'unknown')}")
    except Exception as e:
        print(f"ERROR: Classification test failed: {e}")
        return
    
    # Test field identification with limited text
    try:
        step1_result = {"classification": "mixed", "confidence": 0.9}
        print(f"DEBUG: Starting field identification test...")
        result = service.identify_fields(
            page_data['text'][:2000],  # Limit text to reduce timeout risk
            step1_result
        )
        print(f"DEBUG: Field identification result: {type(result)}")
        if isinstance(result, dict):
            print(f"DEBUG: Result keys: {list(result.keys())}")
    except Exception as e:
        print(f"ERROR: Field identification test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_step2_debug()