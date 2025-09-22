#!/usr/bin/env python3
"""
Test script for spatial preprocessing functionality
"""

from services.pdf_processor import PDFProcessor
from services.spatial_preprocessor import SpatialPreprocessor
import os

def test_word_coordinate_extraction():
    """Test word coordinate extraction from PDF"""
    print("=== Testing Word Coordinate Extraction ===")
    
    # Look for a PDF file to test with
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
        if pdf_files:
            test_pdf = os.path.join(uploads_dir, pdf_files[0])
            print(f"Testing with PDF: {test_pdf}")
            
            try:
                processor = PDFProcessor(test_pdf)
                page_data = processor.extract_text_and_structure(page_num=0)
                
                print(f"Page dimensions: {page_data['page_width']} x {page_data['page_height']}")
                print(f"Total words extracted: {len(page_data['word_coordinates'])}")
                
                # Show first 10 words with coordinates
                print("\nFirst 10 words with coordinates:")
                for i, word in enumerate(page_data['word_coordinates'][:10]):
                    print(f"{i+1:2d}. '{word['text']}' at ({word['x0']:.1f}, {word['y0']:.1f}) -> ({word['x1']:.1f}, {word['y1']:.1f})")
                
                processor.close()
                return page_data['word_coordinates']
                
            except Exception as e:
                print(f"Error processing PDF: {e}")
                return None
        else:
            print("No PDF files found in uploads directory")
            return None
    else:
        print("Uploads directory not found")
        return None

def test_spatial_preprocessing(word_coordinates):
    """Test spatial preprocessing of word coordinates"""
    if not word_coordinates:
        print("No word coordinates available for testing")
        return
        
    print("\n=== Testing Spatial Preprocessing ===")
    
    preprocessor = SpatialPreprocessor()
    
    # Test preprocessing
    formatted_text = preprocessor.preprocess_document(word_coordinates)
    print(f"Original text length: {len(' '.join([w['text'] for w in word_coordinates]))}")
    print(f"Formatted text length: {len(formatted_text)}")
    
    print("\n=== Formatted Text Output ===")
    print(formatted_text)
    
    # Test spacing statistics
    stats = preprocessor.calculate_word_spacing_stats(word_coordinates)
    print(f"\n=== Spacing Statistics ===")
    print(f"Average spacing: {stats['avg_spacing']:.2f}")
    print(f"Median spacing: {stats['median_spacing']:.2f}")
    print(f"Spacing std dev: {stats['spacing_std']:.2f}")
    
    # Test table identification
    table_regions = preprocessor.identify_table_regions(word_coordinates)
    print(f"\n=== Table Detection ===")
    print(f"Potential table regions found: {len(table_regions)}")
    for i, table in enumerate(table_regions):
        print(f"Table {i+1}: {table['row_count']} rows x {table['column_count']} columns")
        print(f"  Headers: {table['headers']}")

def test_status_field_issue():
    """Test the specific Status field issue where 'A' should be the value for Status"""
    print("\n=== Testing Status Field Issue ===")
    
    # Simulate the exact pattern from the document:
    # Line with "Status" field
    # Next line with "A" value
    status_test_words = [
        # Line 1: "Emp Id 4632 Status"
        {"text": "Emp", "x0": 100, "y0": 200, "x1": 130, "y1": 215, "center_x": 115, "center_y": 207.5, "width": 30, "height": 15},
        {"text": "Id", "x0": 140, "y0": 200, "x1": 160, "y1": 215, "center_x": 150, "center_y": 207.5, "width": 20, "height": 15},
        {"text": "4632", "x0": 200, "y0": 200, "x1": 240, "y1": 215, "center_x": 220, "center_y": 207.5, "width": 40, "height": 15},
        {"text": "Status", "x0": 300, "y0": 200, "x1": 350, "y1": 215, "center_x": 325, "center_y": 207.5, "width": 50, "height": 15},
        
        # Line 2: "A" (value for Status)
        {"text": "A", "x0": 300, "y0": 220, "x1": 310, "y1": 235, "center_x": 305, "center_y": 227.5, "width": 10, "height": 15},
        
        # Line 3: "Emp Type"
        {"text": "Emp", "x0": 100, "y0": 240, "x1": 130, "y1": 255, "center_x": 115, "center_y": 247.5, "width": 30, "height": 15},
        {"text": "Type", "x0": 140, "y0": 240, "x1": 180, "y1": 255, "center_x": 160, "center_y": 247.5, "width": 40, "height": 15},
    ]
    
    preprocessor = SpatialPreprocessor()
    
    print("Input coordinates:")
    for word in status_test_words:
        print(f"  '{word['text']}' at ({word['x0']}, {word['y0']})")
    
    # Test line grouping
    lines = preprocessor.group_words_into_lines(status_test_words)
    print(f"\nDetected {len(lines)} lines:")
    for i, line in enumerate(lines):
        line_text = " ".join([w['text'] for w in line])
        print(f"  Line {i+1}: {line_text}")
    
    # Test full preprocessing
    formatted_text = preprocessor.preprocess_document(status_test_words)
    print(f"\nFormatted output:")
    print(formatted_text)
    
    # Expected output should be:
    # Emp Id: 4632    Status: A
    # Emp Type: [EMPTY]
    
    print(f"\nExpected:")
    print("Emp Id: 4632    Status: A")
    print("Emp Type: [EMPTY]")

def test_sample_field_patterns():
    """Test with sample field patterns that cause issues"""
    print("\n=== Testing Sample Field Patterns ===")
    
    # Create sample word coordinates that represent "Pay Group Domestic Emp No"
    # Expected interpretation:
    # - "Pay Group" = field name with empty value
    # - "Domestic Emp" = field name with "No" as value
    sample_words = [
        {"text": "Pay", "x0": 100, "y0": 200, "x1": 130, "y1": 215, "center_x": 115, "center_y": 207.5, "width": 30, "height": 15},
        {"text": "Group", "x0": 140, "y0": 200, "x1": 180, "y1": 215, "center_x": 160, "center_y": 207.5, "width": 40, "height": 15},
        {"text": "Domestic", "x0": 250, "y0": 200, "x1": 310, "y1": 215, "center_x": 280, "center_y": 207.5, "width": 60, "height": 15},
        {"text": "Emp", "x0": 320, "y0": 200, "x1": 350, "y1": 215, "center_x": 335, "center_y": 207.5, "width": 30, "height": 15},
        {"text": "No", "x0": 360, "y0": 200, "x1": 380, "y1": 215, "center_x": 370, "center_y": 207.5, "width": 20, "height": 15},
        
        # Add another line
        {"text": "Employee", "x0": 100, "y0": 230, "x1": 170, "y1": 245, "center_x": 135, "center_y": 237.5, "width": 70, "height": 15},
        {"text": "Name", "x0": 180, "y0": 230, "x1": 220, "y1": 245, "center_x": 200, "center_y": 237.5, "width": 40, "height": 15},
        {"text": "Caroline", "x0": 290, "y0": 230, "x1": 350, "y1": 245, "center_x": 320, "center_y": 237.5, "width": 60, "height": 15},
        {"text": "Jones", "x0": 360, "y0": 230, "x1": 400, "y1": 245, "center_x": 380, "center_y": 237.5, "width": 40, "height": 15},
        
        # Add a field with no value
        {"text": "Status", "x0": 100, "y0": 260, "x1": 140, "y1": 275, "center_x": 120, "center_y": 267.5, "width": 40, "height": 15},
        {"text": "Department", "x0": 300, "y0": 260, "x1": 390, "y1": 275, "center_x": 345, "center_y": 267.5, "width": 90, "height": 15},
    ]
    
    preprocessor = SpatialPreprocessor()
    formatted_text = preprocessor.preprocess_document(sample_words)
    
    print("Sample input coordinates:")
    for word in sample_words:
        print(f"  '{word['text']}' at ({word['x0']}, {word['y0']})")
    
    print(f"\nFormatted output:")
    print(formatted_text)
    
    # Test individual components
    lines = preprocessor.group_words_into_lines(sample_words)
    print(f"\nDetected {len(lines)} lines:")
    for i, line in enumerate(lines):
        line_text = " ".join([w['text'] for w in line])
        print(f"  Line {i+1}: {line_text}")
        
        clusters = preprocessor.cluster_words_by_proximity(line)
        print(f"    Clusters: {len(clusters)}")
        for j, cluster in enumerate(clusters):
            cluster_text = " ".join([w['text'] for w in cluster])
            is_field = preprocessor.is_field_pattern(cluster)
            print(f"      Cluster {j+1}: '{cluster_text}' (field: {is_field})")

if __name__ == "__main__":
    print("Starting Spatial Preprocessing Tests")
    print("=" * 50)
    
    # Test 1: Extract word coordinates from actual PDF
    word_coords = test_word_coordinate_extraction()
    
    # Test 2: Process with spatial preprocessor
    if word_coords:
        test_spatial_preprocessing(word_coords)
    
    # Test 3: Test the Status field issue specifically
    test_status_field_issue()
    
    # Test 4: Test with sample problematic patterns
    test_sample_field_patterns()
    
    print("\n" + "=" * 50)
    print("Tests completed!")