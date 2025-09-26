# PDF Data Extraction with Visual Validation

A sophisticated PDF data extraction system that combines text-based extraction with visual validation to achieve high accuracy rates up to 100%. Supports both Claude 3.5 Sonnet and Google Gemini 2.0 Flash for cost-effective processing.

## Features

- **Multi-Provider Support**: Choose between Claude 3.5 Sonnet and Google Gemini 2.0 Flash
- **Text-based Schema Extraction**: Extract structured data from PDFs using custom JSON schemas
- **Visual Validation**: Human-like visual inspection of extracted data using AI vision models
- **Multi-round Correction**: Up to 10 rounds of validation and correction for maximum accuracy
- **Progressive Accuracy Tracking**: Monitor accuracy improvement across validation rounds
- **Error Resilience**: Intelligent handling of API failures with acceptable accuracy thresholds
- **Complex Column Shift Detection**: Advanced detection and correction of table misalignments
- **Missing Row Recovery**: Aggressive scanning for incomplete table data extraction
- **Cost Optimization**: Use Gemini for budget-friendly POC evaluation (200 requests/day free tier)

## System Architecture

### Core Components

1. **Schema Text Extractor**: Primary extraction engine with unified provider support
2. **Visual Field Inspector**: Vision-based validation and correction system for both providers
3. **Advanced Pipeline**: Orchestrates multi-step extraction with provider routing
4. **Optimized File Manager**: Handles image uploads to Claude Files API or Gemini File API
5. **Model Configuration**: Easy switching between Claude and Gemini configurations

### Workflow Process

1. **Text Extraction**: Extract raw text from PDF using PyMuPDF
2. **Schema-based Extraction**: Use Claude or Gemini to extract structured data according to provided schema
3. **Image Upload**: Upload high-resolution PDF images to respective File APIs for efficient processing
4. **Visual Validation**: Validate extracted data using vision capabilities with file ID references
5. **Iterative Correction**: Apply corrections and re-validate until target accuracy achieved
6. **Final Output**: Return validated data with detailed accuracy reporting

## Installation

### Prerequisites

- Python 3.8+
- At least one of the following API keys:
  - **Anthropic API key** for Claude 3.5 Sonnet (premium accuracy)
  - **Google API key** for Gemini 2.0 Flash (cost-effective POC)
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
# Edit .env file with your API keys:
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here
# MODEL_CONFIG=claude_sonnet  # or gemini_flash
```

## Usage

### Web Interface (Streamlit)

```bash
streamlit run advanced_streamlit_app.py
```

The web interface provides:
- Model selection dropdown (Claude 3.5 Sonnet vs Gemini 2.0 Flash)
- Real-time cost estimation
- Progress tracking with accuracy metrics
- Interactive results display

### Programmatic Usage

```python
from services.advanced_pipeline import AdvancedPDFExtractionPipeline

# Initialize with Claude 3.5 Sonnet (premium accuracy)
pipeline = AdvancedPDFExtractionPipeline(
    api_key="your-anthropic-api-key",
    model_config_name="claude_sonnet"
)

# Or initialize with Gemini 2.0 Flash (cost-effective)
pipeline = AdvancedPDFExtractionPipeline(
    api_key="your-google-api-key",
    model_config_name="gemini_flash"
)

# Define your schema
schema = {
    "employee_name": "string",
    "employee_id": "string",
    "department": "string",
    "salary": "number"
}

# Extract with visual validation
result = pipeline.process_pdf_with_schema(
    pdf_path="document.pdf",
    schema=schema,
    enable_debug=True
)

# Access results
if result["success"]:
    extracted_data = result["extracted_data"]
    accuracy = result["final_accuracy_estimate"]
    provider_used = result["model_used"]
```

## Configuration

### Model Selection

Choose between two AI providers based on your needs:

#### Claude 3.5 Sonnet (`claude_sonnet`)
- **Best for**: Production use, maximum accuracy
- **Cost**: ~$0.12-0.25 per document
- **Features**: Superior accuracy, excellent table reasoning, vision + text

#### Gemini 2.0 Flash (`gemini_flash`)
- **Best for**: POC evaluation, budget-conscious development
- **Cost**: $0.05-0.10 per document (200 free requests/day)
- **Features**: Ultra fast, multimodal, 1M token context

### Available Configurations

```python
from model_configs import list_available_configs

# View all configurations
configs = list_available_configs()
for name, details in configs.items():
    print(f"{name}: {details['description']}")
    print(f"Cost: {details['estimated_cost']}")
```

## Testing

### Run Test Suite

```bash
# Test model routing and provider switching
python test_model_routing.py

# Test specific components
python test_enhanced_extraction.py
python test_complete_pipeline_enhanced.py
```

### Testing Both Providers

The system includes tests for:
- Provider routing (Claude vs Gemini)
- Visual validation accuracy comparison
- File upload/delete operations
- Schema compliance validation
- Cost and performance benchmarking

## Performance

### Accuracy Rates

- **Claude 3.5 Sonnet**: ~99% accuracy, excellent for complex tables
- **Gemini 2.0 Flash**: ~97% accuracy, very fast processing
- **With multi-round visual validation**: Up to 100% accuracy for both providers

### Processing Times

| Provider | Text Extraction | Visual Validation | Complete Workflow |
|----------|----------------|-------------------|-------------------|
| **Claude 3.5 Sonnet** | 2-4 seconds | 8-15 seconds/round | 45-120 seconds |
| **Gemini 2.0 Flash** | 1-2 seconds | 5-10 seconds/round | 20-60 seconds |

### Cost Comparison

| Provider | Per Document | Free Tier | Best For |
|----------|-------------|-----------|----------|
| **Claude 3.5 Sonnet** | $0.12-0.25 | None | Production, maximum accuracy |
| **Gemini 2.0 Flash** | $0.05-0.10 | 200/day | POC, development, testing |

## Error Handling

The system includes robust error handling for:
- API rate limiting with automatic retry logic
- JSON parsing failures with fallback extraction
- Vision model timeouts with graceful degradation
- Network connectivity issues
- Malformed PDF documents

## Limitations

- Requires at least one API key (Anthropic or Google)
- Processing time increases with validation rounds
- Complex documents may require manual schema tuning
- Large documents may hit token limits (1M tokens for Gemini, varies for Claude)
- Gemini free tier limited to 200 requests/day

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with appropriate tests
4. Submit pull request with detailed description

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please use the GitHub issue tracker.