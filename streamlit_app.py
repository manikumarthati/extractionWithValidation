"""
Streamlit interface for schema-based PDF extraction with vision validation
"""

import streamlit as st
import json
import os
import tempfile
from services.schema_text_extractor import SchemaTextExtractor
from config import Config

# Configure page
st.set_page_config(
    page_title="Schema-Based PDF Extractor",
    page_icon="📄",
    layout="wide"
)

def init_extractor():
    """Initialize the schema text extractor"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        st.error("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        st.stop()

    return SchemaTextExtractor(api_key)

def validate_schema(schema_text):
    """Validate uploaded JSON schema"""
    try:
        schema = json.loads(schema_text)
        return True, schema, "✅ Valid JSON schema"
    except json.JSONDecodeError as e:
        return False, None, f"❌ Invalid JSON: {str(e)}"

def display_json(data, title):
    """Display JSON data in a formatted way"""
    st.subheader(title)
    st.json(data)

def main():
    st.title("📄 Schema-Based PDF Extractor with Vision Validation")
    st.markdown("Upload a PDF and JSON schema to extract structured data with automatic validation and correction.")

    # Initialize extractor
    extractor = init_extractor()

    # Create two columns for file uploads
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Upload PDF")
        pdf_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload the PDF file you want to extract data from"
        )

    with col2:
        st.subheader("📋 Upload JSON Schema")
        schema_file = st.file_uploader(
            "Choose a JSON schema file",
            type=['json'],
            help="Upload the JSON schema that defines the structure of data to extract"
        )

        # Option to input schema as text
        st.markdown("**OR** paste schema as text:")
        schema_text = st.text_area(
            "JSON Schema",
            height=200,
            placeholder="Paste your JSON schema here...",
            help="Paste your JSON schema directly"
        )

    # Process files if both are uploaded
    if pdf_file is not None and (schema_file is not None or schema_text.strip()):

        # Get schema from file or text
        if schema_file is not None:
            schema_content = schema_file.read().decode('utf-8')
        else:
            schema_content = schema_text.strip()

        # Validate schema
        schema_valid, schema, schema_message = validate_schema(schema_content)

        st.markdown("---")
        st.subheader("📋 Schema Validation")

        if schema_valid:
            st.success(schema_message)

            # Display schema
            with st.expander("📋 View Schema Structure"):
                st.json(schema)

            # Page selection
            st.subheader("📖 Page Selection")
            page_num = st.number_input(
                "Page number to process (1-based)",
                min_value=1,
                value=1,
                help="Select which page of the PDF to process"
            ) - 1  # Convert to 0-based indexing

            # Visual validation option
            use_visual_validation = st.checkbox(
                "🔍 Enable Visual Validation (Recommended)",
                value=True,
                help="Uses AI vision to validate and correct empty fields and column alignment issues"
            )

            # Process button
            if st.button("🚀 Extract Data", type="primary"):

                # Save PDF to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(pdf_file.read())
                    tmp_pdf_path = tmp_file.name

                try:
                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Use enhanced workflow
                    status_text.text("🚀 Starting enhanced extraction workflow...")
                    progress_bar.progress(10)

                    # Run enhanced workflow
                    result = extractor.enhanced_extraction_workflow(
                        tmp_pdf_path, schema, page_num, use_visual_validation
                    )

                    if not result["success"]:
                        st.error(f"❌ Extraction failed: {result['error']}")
                        return

                    # Update progress based on workflow completion
                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")

                    final_data = result["extracted_data"]
                    workflow_summary = result["workflow_summary"]

                    # Display results
                    st.markdown("---")
                    st.subheader("📊 Extraction Results")

                    # Summary
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "Text Extraction",
                            "✅ Success" if workflow_summary["text_extraction_success"] else "❌ Failed"
                        )

                    with col2:
                        st.metric(
                            "Schema Extraction",
                            "✅ Success" if workflow_summary["schema_extraction_success"] else "❌ Failed"
                        )

                    with col3:
                        st.metric(
                            "Visual Validation",
                            "✅ Applied" if workflow_summary["visual_validation_applied"] else "⏭️ Skipped"
                        )

                    with col4:
                        st.metric(
                            "Corrections Applied",
                            workflow_summary.get("corrections_applied", 0)
                        )

                    # Display accuracy estimate
                    accuracy = workflow_summary.get("final_accuracy_estimate", 0.98)
                    st.metric(
                        "🎯 Estimated Accuracy",
                        f"{accuracy:.1%}",
                        delta=f"+{(accuracy - 0.98):.1%}" if accuracy > 0.98 else None
                    )

                    # Display visual validation details if applied
                    if workflow_summary["visual_validation_applied"]:
                        visual_validation = result.get("detailed_results", {}).get("visual_validation_summary", {})

                        if visual_validation.get("corrections_needed") or visual_validation.get("correction_history"):
                            corrections_applied = visual_validation.get("total_corrections_applied", 0)
                            st.success(f"🔧 Applied {corrections_applied} visual corrections")

                            # Display correction details
                            _display_correction_details(visual_validation)

                        else:
                            st.success("✅ No visual corrections needed - extraction was accurate!")

                        if visual_validation.get("visual_validation_error"):
                            st.warning(f"⚠️ Visual validation encountered an issue: {visual_validation['visual_validation_error']}")

                    # Display final extracted data
                    st.subheader("📋 Final Extracted Data")
                    st.json(final_data)

                    # Download button
                    json_str = json.dumps(final_data, indent=2)
                    st.download_button(
                        label="💾 Download JSON",
                        data=json_str,
                        file_name=f"extracted_data_page_{page_num+1}.json",
                        mime="application/json"
                    )

                    # Show raw text for reference
                    with st.expander("📄 Raw Text Extracted"):
                        st.text_area(
                            "Raw text from PDF",
                            "",
                            height=300,
                            disabled=True
                        )

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(tmp_pdf_path)
                    except:
                        pass

        else:
            st.error(schema_message)

    else:
        st.info("👆 Please upload both a PDF file and a JSON schema to get started.")

    # Sidebar with example schema
    with st.sidebar:
        st.subheader("📋 Example Schema")
        st.markdown("Here's an example of a valid JSON schema:")

        example_schema = {
            "employee_info": {
                "name": "string",
                "id": "string",
                "department": "string",
                "salary": "number"
            },
            "benefits_table": [
                {
                    "benefit_type": "string",
                    "coverage": "string",
                    "cost": "number"
                }
            ]
        }

        st.json(example_schema)

        st.markdown("---")
        st.subheader("ℹ️ How it works")
        st.markdown("""
        1. **Text Extraction**: Extract raw text from PDF using PyMuPDF
        2. **Schema Extraction**: Use LLM to extract data according to your schema
        3. **Vision Validation**: Use vision AI to validate extracted data against PDF image
        4. **Automatic Correction**: Fix column shifting and field mapping issues
        """)

def _display_correction_details(visual_validation):
    """Display detailed correction information with before/after values"""

    correction_history = visual_validation.get("correction_history", [])

    if not correction_history:
        return

    st.markdown("### 🔧 Correction Details")
    st.markdown("**Here's what was corrected during visual validation:**")

    # Group corrections by type for better organization
    correction_types = {}
    for correction in correction_history:
        change_type = correction.get("change_type", "unknown")
        if change_type not in correction_types:
            correction_types[change_type] = []
        correction_types[change_type].append(correction)

    # Display each correction type
    for change_type, corrections in correction_types.items():
        change_type_display = change_type.replace("_", " ").title()

        with st.expander(f"📝 {change_type_display} ({len(corrections)} items)", expanded=True):

            for i, correction in enumerate(corrections, 1):
                field = correction.get("field", "Unknown field")
                round_num = correction.get("round", 1)

                st.markdown(f"**{i}. {field}** *(Round {round_num})*")

                if change_type == "value_corrected":
                    before_val = correction.get("before_value", "N/A")
                    after_val = correction.get("after_value", "N/A")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Before:**")
                        st.code(str(before_val), language="text")

                    with col2:
                        st.markdown("**After:**")
                        st.code(str(after_val), language="text")

                elif change_type == "complex_column_realignment":
                    shift_pattern = correction.get("shift_pattern", "unknown")
                    columns_affected = correction.get("columns_affected", 0)
                    complexity = correction.get("complexity", "medium")

                    st.info(f"**Pattern:** {shift_pattern} | **Columns affected:** {columns_affected} | **Complexity:** {complexity}")

                    # Show detailed shifts
                    shift_details = correction.get("shift_details", [])
                    if shift_details:
                        st.markdown("**Detailed column movements:**")

                        for detail in shift_details:
                            column = detail.get("column", "unknown")
                            movement = detail.get("movement_type", "unknown")

                            if movement == "value_moved":
                                moved_to = detail.get("moved_to_column", "unknown")
                                shift_dir = detail.get("shift_direction", "unknown")
                                st.markdown(f"- **{column}**: Value moved to *{moved_to}* ({shift_dir})")
                            elif movement == "value_replaced":
                                before = detail.get("before", "N/A")
                                after = detail.get("after", "N/A")
                                st.markdown(f"- **{column}**: `{before}` → `{after}`")
                            else:
                                st.markdown(f"- **{column}**: {movement}")

                elif change_type == "table_rows_changed":
                    before_val = correction.get("before_value", "N/A")
                    after_val = correction.get("after_value", "N/A")
                    st.info(f"**Row count changed:** {before_val} → {after_val}")

                elif change_type == "field_added":
                    after_val = correction.get("after_value", "N/A")
                    st.success(f"**Added:** {str(after_val)[:100]}...")

                elif change_type == "field_removed":
                    before_val = correction.get("before_value", "N/A")
                    st.error(f"**Removed:** {str(before_val)[:100]}...")

                st.markdown("---")

    # Summary statistics
    total_corrections = len(correction_history)
    rounds_completed = visual_validation.get("validation_rounds_completed", 1)
    accuracy_estimate = visual_validation.get("final_accuracy_estimate", 0.95)

    st.markdown("### 📊 Correction Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Corrections", total_corrections)

    with col2:
        st.metric("Validation Rounds", rounds_completed)

    with col3:
        st.metric("Final Accuracy", f"{accuracy_estimate:.1%}")

if __name__ == "__main__":
    main()