#!/usr/bin/env python3
"""
Test different text extraction methods to find why 'Minnesota Federal Loan'
is being truncated to 'Minnesota Federal Lo'
"""

import fitz  # PyMuPDF
import os

def test_pdf_text_extraction_methods():
    """Compare different PyMuPDF text extraction methods"""

    pdf_path = "D:/learning/stepwisePdfParsing/obfuscated_fake_cbiz_prof_10_pages_1.pdf"
    page_num = 0

    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return False

    print("Analyzing PDF Text Extraction Methods")
    print("=" * 50)
    print("Looking for 'Minnesota Federal Loan' vs 'Minnesota Federal Lo'")
    print()

    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]

        # Method 1: Basic text extraction (current method)
        print("[METHOD 1] Basic get_text():")
        print("-" * 30)
        text1 = page.get_text()

        # Search for the problematic text
        if "Minnesota Federal Lo" in text1:
            print("FOUND: 'Minnesota Federal Lo' (truncated)")
            # Get surrounding context
            start_idx = text1.find("Minnesota Federal Lo") - 50
            end_idx = text1.find("Minnesota Federal Lo") + 100
            print(f"Context: ...{text1[max(0,start_idx):end_idx]}...")

        if "Minnesota Federal Loan" in text1:
            print("FOUND: 'Minnesota Federal Loan' (complete)")

        print(f"Total text length: {len(text1)} characters")
        print()

        # Method 2: Text with layout preserved
        print("[METHOD 2] get_text('text') with layout:")
        print("-" * 40)
        text2 = page.get_text("text")

        if "Minnesota Federal Lo" in text2:
            print("FOUND: 'Minnesota Federal Lo' (truncated)")
        if "Minnesota Federal Loan" in text2:
            print("FOUND: 'Minnesota Federal Loan' (complete)")

        print(f"Total text length: {len(text2)} characters")
        print(f"Same as method 1: {text1 == text2}")
        print()

        # Method 3: Text with word-level information
        print("[METHOD 3] get_text('words') analysis:")
        print("-" * 35)
        words = page.get_text("words")

        # Find words containing "Minnesota", "Federal", "Lo"
        relevant_words = []
        for word in words:
            word_text = word[4]  # word[4] is the text content
            if any(term in word_text for term in ["Minnesota", "Federal", "Lo", "Loan"]):
                relevant_words.append({
                    'text': word_text,
                    'bbox': word[:4],  # x0, y0, x1, y1
                    'word_info': word
                })

        print("Relevant words found:")
        for word in relevant_words:
            print(f"  '{word['text']}' at bbox {word['bbox']}")
        print()

        # Method 4: Dictionary format with detailed structure
        print("[METHOD 4] get_text('dict') block analysis:")
        print("-" * 40)
        text_dict = page.get_text("dict")

        minnesota_blocks = []
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        if "Minnesota" in text or "Federal" in text or "Loan" in text:
                            minnesota_blocks.append({
                                'text': text,
                                'bbox': span["bbox"],
                                'flags': span.get("flags", 0),
                                'font': span.get("font", ""),
                                'size': span.get("size", 0)
                            })

        print("Text spans containing 'Minnesota/Federal/Loan':")
        for span in minnesota_blocks:
            print(f"  Text: '{span['text']}'")
            print(f"    BBox: {span['bbox']}")
            print(f"    Font: {span['font']}, Size: {span['size']}")
            print(f"    Flags: {span['flags']}")
            print()

        # Method 5: HTML extraction (preserves more formatting)
        print("[METHOD 5] get_text('html') analysis:")
        print("-" * 35)
        html_text = page.get_text("html")

        if "Minnesota Federal Lo" in html_text:
            print("FOUND in HTML: 'Minnesota Federal Lo' (truncated)")
        if "Minnesota Federal Loan" in html_text:
            print("FOUND in HTML: 'Minnesota Federal Loan' (complete)")

        # Extract the relevant HTML snippet
        if "Minnesota Federal" in html_text:
            start = html_text.find("Minnesota Federal") - 100
            end = html_text.find("Minnesota Federal") + 200
            html_snippet = html_text[max(0, start):end]
            print("HTML snippet:")
            print(html_snippet)
        print()

        # Method 6: XHTML extraction
        print("[METHOD 6] get_text('xhtml') analysis:")
        print("-" * 36)
        try:
            xhtml_text = page.get_text("xhtml")

            if "Minnesota Federal Lo" in xhtml_text:
                print("FOUND in XHTML: 'Minnesota Federal Lo' (truncated)")
            if "Minnesota Federal Loan" in xhtml_text:
                print("FOUND in XHTML: 'Minnesota Federal Loan' (complete)")

            print(f"XHTML text length: {len(xhtml_text)} characters")
        except Exception as e:
            print(f"XHTML extraction failed: {e}")
        print()

        # Method 7: Check for clipping or overlapping text
        print("[METHOD 7] Clipping/Overlapping Analysis:")
        print("-" * 38)

        # Look for text that might be clipped by page margins or overlapping elements
        page_rect = page.rect
        print(f"Page dimensions: {page_rect}")

        # Check if any text spans are near the page edges or overlapping
        potentially_clipped = []
        for span in minnesota_blocks:
            bbox = span['bbox']
            x0, y0, x1, y1 = bbox

            # Check if text extends beyond visible area or is very close to edges
            near_edge = (x1 > page_rect.width * 0.95 or  # Close to right edge
                        x0 < page_rect.width * 0.05 or   # Close to left edge
                        y1 > page_rect.height * 0.95 or  # Close to bottom
                        y0 < page_rect.height * 0.05)    # Close to top

            if near_edge:
                potentially_clipped.append(span)

        if potentially_clipped:
            print("Potentially clipped text spans:")
            for span in potentially_clipped:
                print(f"  '{span['text']}' near edge at {span['bbox']}")
        else:
            print("No text spans appear to be clipped by page edges")

        doc.close()

        # Summary and recommendations
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)

        print("Possible causes of text truncation:")
        print("1. Text is visually clipped but full text exists in PDF")
        print("2. Font rendering issues causing text to appear cut off")
        print("3. Overlapping elements hiding part of the text")
        print("4. PDF creation process truncated the actual text content")
        print("5. Character encoding issues")

        print("\nRecommended solutions:")
        print("1. Try different extraction methods (HTML, XHTML)")
        print("2. Extract at higher resolution/zoom")
        print("3. Use OCR as fallback for problematic areas")
        print("4. Parse the underlying PDF structure directly")

        return True

    except Exception as e:
        print(f"Analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_text_extraction_methods()
    if success:
        print("\n[SUCCESS] Text extraction analysis completed")
    else:
        print("\n[FAILED] Text extraction analysis failed")