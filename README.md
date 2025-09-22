# PDF Data Extraction with Visual Validation

A sophisticated PDF data extraction system that combines text-based extraction with visual validation to achieve high accuracy rates up to 100%.

## Features

- **Text-based Schema Extraction**: Extract structured data from PDFs using custom JSON schemas
- **Visual Validation**: Human-like visual inspection of extracted data using AI vision models
- **Multi-round Correction**: Up to 10 rounds of validation and correction for maximum accuracy
- **Progressive Accuracy Tracking**: Monitor accuracy improvement across validation rounds
- **Error Resilience**: Intelligent handling of API failures with acceptable accuracy thresholds
- **Complex Column Shift Detection**: Advanced detection and correction of table misalignments
- **Missing Row Recovery**: Aggressive scanning for incomplete table data extraction

## System Architecture

### Core Components

1. **Schema Text Extractor**: Primary extraction engine using text analysis
2. **Visual Field Inspector**: Vision-based validation and correction system
3. **Vision Extractor**: PDF to image conversion and AI vision processing
4. **Cost Tracker**: Monitor API usage and costs
5. **Result Merger**: Combine multi-page extraction results

### Workflow Process

1. **Text Extraction**: Extract raw text from PDF using PyMuPDF
2. **Schema-based Extraction**: Use LLM to extract structured data according to provided schema
3. **Visual Validation**: Convert PDF to high-resolution image and validate extracted data
4. **Iterative Correction**: Apply corrections and re-validate until target accuracy achieved
5. **Final Output**: Return validated data with detailed accuracy reporting

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Required Python packages (see requirements.txt)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/manikumarthati/extractionWithValidation.git
cd extractionWithValidation
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env file with your OpenAI API key
```

## Usage

### Web Interface (Streamlit)

```bash
streamlit run streamlit_app.py
```

### Flask API

```bash
python app.py
```

### Programmatic Usage

```python
from services.schema_text_extractor import SchemaTextExtractor

# Initialize extractor
extractor = SchemaTextExtractor(api_key="your-openai-api-key")

# Define your schema
schema = {
    "employee_name": "string",
    "employee_id": "string",
    "department": "string",
    "salary": "number"
}

# Extract with visual validation
result = extractor.enhanced_extraction_workflow(
    pdf_path="document.pdf",
    schema=schema,
    page_num=0,
    use_visual_validation=True,
    multi_round_validation=True
)

# Access results
if result["success"]:
    extracted_data = result["extracted_data"]
    accuracy = result["workflow_summary"]["final_accuracy_estimate"]
    rounds_completed = result["workflow_summary"]["validation_rounds_completed"]
```

## Configuration

### Validation Parameters

- **max_rounds**: Maximum validation rounds (default: 10)
- **target_accuracy**: Target accuracy threshold (default: 1.0 for 100%)
- **use_visual_validation**: Enable/disable visual validation (default: True)
- **multi_round_validation**: Enable iterative validation (default: True)

### API Endpoints

#### Schema Extraction
```
POST /api/schema-extraction/<doc_id>
```

Request body:
```json
{
    "schema": {
        "field_name": "field_type"
    },
    "page_num": 0,
    "use_visual_validation": true
}
```

Response:
```json
{
    "success": true,
    "extracted_data": {},
    "workflow_summary": {
        "final_accuracy_estimate": 0.99,
        "validation_rounds_completed": 3,
        "target_accuracy_achieved": true
    }
}
```

## Testing

### Run Test Suite

```bash
# Test enhanced validation system
python test_enhanced_validation.py

# Test specific components
python test_visual_validation.py
python test_complex_column_shifting.py
python test_missing_row_extraction.py
```

### Accuracy Testing

The system includes comprehensive test scripts for:
- Visual validation accuracy
- Complex column shift correction
- Missing row detection and recovery
- Schema compliance validation
- Multi-page document processing

## Performance

### Accuracy Rates

- **Text-only extraction**: ~98% accuracy
- **With single-round visual validation**: ~99% accuracy
- **With multi-round visual validation**: Up to 100% accuracy

### Processing Times

- **Text extraction**: 1-3 seconds per page
- **Visual validation round**: 5-15 seconds per round
- **Complete workflow**: 30-120 seconds depending on complexity and rounds needed

## Error Handling

The system includes robust error handling for:
- API rate limiting with automatic retry logic
- JSON parsing failures with fallback extraction
- Vision model timeouts with graceful degradation
- Network connectivity issues
- Malformed PDF documents

## Limitations

- Requires OpenAI API access (paid service)
- Processing time increases with validation rounds
- Complex documents may require manual schema tuning
- Large documents may hit token limits

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with appropriate tests
4. Submit pull request with detailed description

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please use the GitHub issue tracker.