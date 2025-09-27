"""
Advanced PDF Extraction Pipeline - Streamlit Application
Modern, sleek UI for the complete extraction pipeline with real-time progress tracking
"""

import streamlit as st
import json
import os
import time
import tempfile
import io
import base64
from typing import Dict, Any, List
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Import our pipeline components
from services.schema_text_extractor import SchemaTextExtractor
from services.advanced_pipeline import AdvancedPDFExtractionPipeline
from model_configs import get_model_config, list_available_configs, get_cost_comparison

# Configure page
st.set_page_config(
    page_title="Advanced PDF Extractor",
    page_icon=":rocket:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern sleek CSS styling
st.markdown("""
<style>
    /* Hide sidebar completely */
    .css-1d391kg {display: none;}
    section[data-testid="stSidebar"] {display: none !important;}

    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }

    .main-header h1 {
        font-size: 3rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }

    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }

    /* Card styling */
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border: 1px solid rgba(0,0,0,0.05);
        margin-bottom: 2rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }

    /* Pipeline step styling */
    .pipeline-step {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #f0f2f6;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }

    .step-complete {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        transform: scale(1.02);
    }

    .step-active {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #ffc107;
        animation: pulse 2s infinite;
    }

    .step-error {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 2px solid #dc3545;
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }

    /* Metric styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 3px 15px rgba(0,0,0,0.08);
        text-align: center;
        border: 1px solid rgba(0,0,0,0.05);
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }

    /* Upload area styling */
    .uploadedFile {
        border-radius: 12px;
        border: 2px dashed #667eea;
        padding: 2rem;
        background: rgba(102, 126, 234, 0.05);
    }

    /* Section headers */
    h2, h3 {
        color: #2d3748;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* Accuracy indicators */
    .accuracy-high {
        color: #28a745;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .accuracy-medium {
        color: #ffc107;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .accuracy-low {
        color: #dc3545;
        font-weight: bold;
        font-size: 1.1rem;
    }

    .correction-item {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
    }

    /* Clean spacing */
    .block-container {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class AdvancedPipelineUI:
    def __init__(self):
        self.pipeline_state = self._init_pipeline_state()

    def _init_pipeline_state(self):
        """Initialize pipeline state"""
        if 'pipeline_state' not in st.session_state:
            st.session_state.pipeline_state = {
                'current_step': 0,
                'steps_completed': [],
                'processing': False,
                'results': {},
                'error': None,
                'start_time': None,
                'file_id': None
            }
        return st.session_state.pipeline_state

    def render_header(self):
        """Render main application header"""
        st.markdown("""
        <div class="main-header">
            <h1>PDF Data Extraction</h1>
            <p>Claude vs Gemini Comparison • 600 DPI Processing • POC Evaluation</p>
            <small style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px;">Enhanced v2.0 - Dynamic Metrics & Console Validation Logging</small>
        </div>
        """, unsafe_allow_html=True)

    def render_pipeline_overview(self):
        """Render pipeline steps overview"""
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("Processing Pipeline")

        steps = [
            {"name": "PDF Preprocessing", "desc": "600 DPI conversion, skew correction, enhancement"},
            {"name": "AI Upload", "desc": "Upload preprocessed image to AI provider Files API"},
            {"name": "Data Extraction", "desc": "LLM-based schema extraction"},
            {"name": "Vision Validation", "desc": "Iterative validation with vision models (up to 10 rounds)"}
        ]

        cols = st.columns(4)

        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                # Determine step status
                if i in self.pipeline_state['steps_completed']:
                    status_class = "step-complete"
                    status_icon = "[OK]"
                elif i == self.pipeline_state['current_step'] and self.pipeline_state['processing']:
                    status_class = "step-active"
                    status_icon = "[ACTIVE]"
                elif self.pipeline_state.get('error') and i == self.pipeline_state['current_step']:
                    status_class = "step-error"
                    status_icon = "[ERROR]"
                else:
                    status_class = "pipeline-step"
                    status_icon = "[PENDING]"

                st.markdown(f"""
                <div class="pipeline-step {status_class}">
                    <h4>{status_icon} Step {i+1}</h4>
                    <h5>{step['name']}</h5>
                    <p>{step['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def render_upload_section(self):
        """Render file upload section"""
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("📁 Upload Documents")

        col1, col2 = st.columns([2, 1])

        # Initialize default values
        page_num = 0
        schema = None

        with col1:
            # File selection options
            st.markdown("**File Selection**")
            file_option = st.radio(
                "Choose file input method:",
                ["Upload new PDF", "Select uploaded file"],
                disabled=self.pipeline_state['processing'],
                help="Upload a new file or select from previously uploaded files"
            )

            pdf_file = None
            selected_file_id = None

            if file_option == "Upload new PDF":
                # PDF Upload
                pdf_file = st.file_uploader(
                    "Choose PDF file",
                    type=['pdf'],
                    help="Upload the PDF document for data extraction",
                    disabled=self.pipeline_state['processing']
                )
            else:
                # Show uploaded files list
                selected_file_id = self.render_uploaded_files_section()

            # Add file management section that's always visible
            st.markdown("---")
            self.render_file_management_section()

            # Page selection
            if pdf_file:
                page_num = st.number_input(
                    "Page number to process",
                    min_value=1,
                    value=1,
                    help="Select which page to process (1-based)",
                    disabled=self.pipeline_state['processing']
                ) - 1

        with col2:
            # Schema input options
            st.markdown("**Schema Input**")
            schema_option = st.radio(
                "Choose schema input method:",
                ["Upload JSON file", "Paste JSON text"],
                disabled=self.pipeline_state['processing']
            )

        # Schema input based on selection
        if schema_option == "Upload JSON file":
            schema_file = st.file_uploader(
                "Upload JSON schema",
                type=['json'],
                help="JSON schema defining the data structure to extract",
                disabled=self.pipeline_state['processing']
            )
            if schema_file:
                try:
                    schema = json.loads(schema_file.read().decode('utf-8'))
                    st.success("✅ Schema loaded successfully")
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON schema: {str(e)}")
        else:
            schema_text = st.text_area(
                "Paste JSON schema",
                height=200,
                placeholder='{"field_name": "field_type", ...}',
                help="Paste your JSON schema here",
                disabled=self.pipeline_state['processing']
            )
            if schema_text.strip():
                try:
                    schema = json.loads(schema_text)
                    st.success("✅ Schema parsed successfully")
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {str(e)}")

        # Model Selection Section
        st.markdown("---")
        st.markdown("**🤖 Model Configuration**")

        # Get available model configurations
        available_configs = list_available_configs()

        # Create a more user-friendly display for model options
        model_options = {
            'Claude 3.5 Sonnet': 'claude_sonnet',
            'Gemini 2.0 Flash ': 'gemini_flash'
        }

        # Model selection
        col1, col2 = st.columns([2, 1])

        with col1:
            selected_model_display = st.selectbox(
                "Choose model configuration:",
                options=list(model_options.keys()),
                index=1,  # Default to "Gemini"
                disabled=self.pipeline_state['processing'],
                help="Select Claude or Gemini model for extraction comparison"
            )

            selected_model_config = model_options[selected_model_display]

            # Store selected model in session state for use in file management
            st.session_state['selected_model_config'] = selected_model_config

        with col2:
            # Show cost and features for selected model
            if selected_model_config in available_configs:
                config_info = available_configs[selected_model_config]
                st.markdown(f"**Cost:** {config_info['estimated_cost']}")
                st.markdown(f"**Features:**")
                for feature in config_info['features'][:2]:  # Show first 2 features
                    st.markdown(f"• {feature}")

        st.markdown('</div>', unsafe_allow_html=True)
        return pdf_file, page_num, schema, selected_file_id, selected_model_config

    def render_uploaded_files_section(self):
        """Render uploaded files selection section"""
        try:
            # Import here to avoid circular imports
            from services.advanced_pipeline import OptimizedFileManager
            from model_configs import get_provider

            # Get selected model config to determine provider
            selected_model_config = st.session_state.get('selected_model_config', 'gemini_flash')
            provider = get_provider(selected_model_config)
            provider_name = "Google Gemini" if provider == 'google' else "Anthropic Claude"

            # Get provider-specific API key
            if provider == 'google':
                api_key = os.environ.get('GOOGLE_API_KEY')
                if not api_key:
                    st.error(f"❌ GOOGLE_API_KEY not found for {provider_name}")
                    return None
            else:
                api_key = os.environ.get('ANTHROPIC_API_KEY')
                if not api_key:
                    st.error(f"❌ ANTHROPIC_API_KEY not found for {provider_name}")
                    return None

            # Create provider-aware file manager
            file_manager = OptimizedFileManager(api_key, provider, selected_model_config)

            # Show which provider's files we're accessing
            st.info(f"📁 Accessing {provider_name} uploaded files")

            with st.spinner("📋 Loading uploaded files..."):
                uploaded_files = file_manager.list_uploaded_files()

            if not uploaded_files:
                st.info("📄 No uploaded files found. Upload a file first.")
                return None

            # Create a selectbox with file information
            file_options = {}
            file_display_names = []

            for file_info in uploaded_files:
                # Get file metadata
                file_id = file_info.id if hasattr(file_info, 'id') else str(file_info)
                file_name = getattr(file_info, 'filename', f"File {file_id[:8]}...")
                file_size = getattr(file_info, 'size_bytes', 0)
                created_at = getattr(file_info, 'created_at', 'Unknown')

                # Format file size
                if file_size > 0:
                    if file_size > 1024*1024:
                        size_str = f"{file_size/(1024*1024):.1f} MB"
                    else:
                        size_str = f"{file_size/1024:.1f} KB"
                else:
                    size_str = "Unknown size"

                # Create display name
                display_name = f"📄 {file_name} ({size_str})"
                if created_at != 'Unknown':
                    display_name += f" - {created_at}"

                file_options[display_name] = file_id
                file_display_names.append(display_name)

            if file_display_names:
                st.markdown("**Select from uploaded files:**")
                selected_display = st.selectbox(
                    "Choose a file:",
                    [""] + file_display_names,
                    help="Select a previously uploaded file to process"
                )

                if selected_display:
                    selected_file_id = file_options[selected_display]
                    st.success(f"✅ Selected file: {selected_display}")

                    # Show file details
                    with st.expander("📋 File Details"):
                        st.code(f"File ID: {selected_file_id}")

                    return selected_file_id


        except Exception as e:
            st.error(f"❌ Error loading uploaded files: {str(e)}")

        return None

    def render_file_management_section(self):
        """Render file management section with delete functionality - always visible"""
        try:
            # Import here to avoid circular imports
            from services.advanced_pipeline import OptimizedFileManager
            from model_configs import get_provider

            # Get selected model config to determine provider
            selected_model_config = st.session_state.get('selected_model_config', 'gemini_flash')
            provider = get_provider(selected_model_config)
            provider_name = "Google Gemini" if provider == 'google' else "Anthropic Claude"

            # Get provider-specific API key
            if provider == 'google':
                api_key = os.environ.get('GOOGLE_API_KEY')
                if not api_key:
                    st.error(f"❌ GOOGLE_API_KEY not found for {provider_name}")
                    return
            else:
                api_key = os.environ.get('ANTHROPIC_API_KEY')
                if not api_key:
                    st.error(f"❌ ANTHROPIC_API_KEY not found for {provider_name}")
                    return

            # Create provider-aware file manager
            file_manager = OptimizedFileManager(api_key, provider, selected_model_config)

            # Get file count
            with st.spinner("📊 Getting file count..."):
                uploaded_files = file_manager.list_uploaded_files()
                file_count = len(uploaded_files) if uploaded_files else 0

            st.markdown(f"**📁 File Management ({provider_name}):**")

            col1, col2 = st.columns([2, 1])
            with col1:
                st.info(f"📊 Total {provider_name} files: {file_count}")

            with col2:
                if file_count > 0:
                    if st.button("🗑️ Delete All Files", type="secondary", use_container_width=True, key="delete_all_main"):
                        if st.session_state.get('confirm_delete_all_main', False):
                            # Perform deletion
                            with st.spinner("Deleting all files..."):
                                delete_result = file_manager.delete_all_files()

                            if delete_result["success"]:
                                st.success(f"✅ {delete_result['message']}")
                                # Reset confirmation
                                st.session_state['confirm_delete_all_main'] = False
                                # Refresh the page to update file list
                                st.rerun()
                            else:
                                st.error(f"❌ {delete_result['message']}")
                        else:
                            # Show confirmation
                            st.session_state['confirm_delete_all_main'] = True
                            st.warning("⚠️ Click again to confirm deletion of ALL files")
                else:
                    st.info("No files to delete")

        except Exception as e:
            st.error(f"❌ Error in file management: {str(e)}")

    def render_processing_controls(self, pdf_file, schema):
        """Render processing controls and settings - SIMPLIFIED"""
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("⚙️ Processing Settings")

        # Hardcoded target accuracy - always 100%
        target_accuracy = 1.0  # Fixed to 100%

        st.markdown("---")

        # Fixed configuration display
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.info("🤖 **Model: Gemini 2.0 Flash**")

        with col2:
            st.info("🔄 **Max rounds: 10**")

        with col3:
            st.info("🖼️ **Resolution: 600 DPI**")

        with col4:
            st.info("🎯 **Target accuracy: 100%**")

        # Simplified status info
        with st.expander("ℹ️ Status", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📁 File: {'✅ Ready' if pdf_file or schema else '❌ Missing'}")
                st.write(f"📝 Schema: {'✅ Ready' if schema else '❌ Missing'}")
            with col2:
                st.write("✅ **Debug mode: Active**")
                st.write("✅ **Enhanced processing: Active**")

        # Hardcoded settings - all optimal values
        max_rounds = 10  # Fixed to 3
        dpi_setting = 600  # Fixed to 600 DPI
        selected_config_name = 'claude'  # Hardcoded to Claude Sonnet
        enable_preprocessing = True
        enable_visual_guides = True
        enhanced_validation = True
        debug_mode = True
        save_intermediate = True
        confidence_threshold = 0.95

        # Process button
        can_process = (pdf_file is not None and
                      schema is not None and
                      not self.pipeline_state['processing'])

        st.markdown("---")
        if st.button(
            "🚀 Start Processing Pipeline",
            type="primary",
            disabled=not can_process,
            use_container_width=True
        ):
            st.markdown('</div>', unsafe_allow_html=True)
            return {
                'start_processing': True,
                'settings': {
                    'max_rounds': max_rounds,
                    'target_accuracy': target_accuracy,
                    'dpi_setting': dpi_setting,
                    'enable_preprocessing': enable_preprocessing,
                    'enable_visual_guides': enable_visual_guides,
                    'enhanced_validation': enhanced_validation,
                    'debug_mode': debug_mode,
                    'save_intermediate': save_intermediate,
                    'confidence_threshold': confidence_threshold,
                    'model_config': selected_config_name
                }
            }

        st.markdown('</div>', unsafe_allow_html=True)
        return {'start_processing': False}

    def render_real_time_progress(self):
        """Render real-time processing progress - SIMPLIFIED"""
        if not self.pipeline_state['processing'] and not self.pipeline_state['results']:
            return

        # Only show basic processing indicator when active
        if self.pipeline_state['processing']:
            st.subheader("🔄 Processing...")
            current_step = self.pipeline_state['current_step']
            step_names = ["Preprocessing PDF", "Uploading to AI provider", "Extracting data", "Validating (3 rounds max)"]

            if current_step < len(step_names):
                st.info(f"📋 {step_names[current_step]}")

            # Simple processing time
            if self.pipeline_state['start_time']:
                elapsed = time.time() - self.pipeline_state['start_time']
                st.metric("⏱️ Processing Time", f"{elapsed:.1f}s")

    def render_validation_rounds(self):
        """Render validation rounds progress with detailed corrections"""
        if 'validation_rounds' not in st.session_state:
            return

        rounds = st.session_state.validation_rounds
        if not rounds:
            return

        st.subheader("🔍 Validation Rounds")

        # Create progress chart with dynamic data
        round_numbers = list(range(1, len(rounds) + 1))
        accuracies = [r.get('accuracy_estimate', 0) for r in rounds]
        corrections = [len(r.get('corrections_applied', [])) for r in rounds]

        # Only create chart if we have data
        if accuracies and any(acc > 0 for acc in accuracies):
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Accuracy Progress', 'Corrections per Round'),
                vertical_spacing=0.1
            )

            # Accuracy line with actual values
            fig.add_trace(
                go.Scatter(
                    x=round_numbers,
                    y=accuracies,
                    mode='lines+markers',
                    name='Accuracy',
                    line=dict(color='#28a745', width=3),
                    marker=dict(size=8),
                    text=[f"{acc*100:.1f}%" for acc in accuracies],
                    textposition="top center"
                ),
                row=1, col=1
            )

            # Corrections bar with values
            fig.add_trace(
                go.Bar(
                    x=round_numbers,
                    y=corrections,
                    name='Corrections',
                    marker_color='#667eea',
                    text=corrections,
                    textposition='outside'
                ),
                row=2, col=1
            )

            fig.update_layout(
                height=400,
                showlegend=False,
                title=f"Validation Progress ({len(rounds)} rounds completed)"
            )

            fig.update_yaxes(title_text="Accuracy", range=[0, 1], row=1, col=1)
            fig.update_yaxes(title_text="Corrections", row=2, col=1)
            fig.update_xaxes(title_text="Round", row=2, col=1)

            st.plotly_chart(fig, use_container_width=True)

        # Enhanced round details with old vs new values
        for i, round_data in enumerate(rounds, 1):
            with st.expander(f"🔄 Round {i} Details", expanded=(i == len(rounds))):  # Expand latest round
                col1, col2, col3 = st.columns(3)

                with col1:
                    accuracy = round_data.get('accuracy_estimate', 0)
                    accuracy_class = ('accuracy-high' if accuracy >= 0.95 else
                                    'accuracy-medium' if accuracy >= 0.8 else 'accuracy-low')
                    st.markdown(f'<p class="{accuracy_class}">Accuracy: {accuracy*100:.1f}%</p>',
                              unsafe_allow_html=True)

                with col2:
                    corrections_count = len(round_data.get('corrections_applied', []))
                    st.metric("Corrections", corrections_count)

                with col3:
                    duration = round_data.get('round_duration', 0)
                    st.metric("Duration", f"{duration:.1f}s")

                # Enhanced corrections display with old vs new values
                corrections = round_data.get('corrections_applied', [])
                if corrections:
                    st.write("**📝 Corrections Applied:**")
                    for j, correction in enumerate(corrections, 1):
                        field = correction.get('field', 'Unknown')
                        old_value = correction.get('old_value', 'N/A')
                        new_value = correction.get('new_value', 'N/A')
                        reason = correction.get('reason', 'No reason provided')

                        st.markdown(f"""
                        <div class="correction-item">
                            <strong>#{j} Field: {field}</strong><br>
                            <span style="color: #dc3545;">❌ Old: '{old_value}'</span><br>
                            <span style="color: #28a745;">✅ New: '{new_value}'</span><br>
                            <small style="color: #6c757d;">💡 {reason}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ No corrections needed - data was accurate!")

    def render_results_dashboard(self):
        """Render final results dashboard"""
        if not self.pipeline_state['results']:
            return

        results = self.pipeline_state['results']

        if not results.get('success'):
            st.error(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
            return

        st.subheader("🎉 Extraction Complete!")

        # Enhanced summary metrics with workflow summary data
        workflow_summary = results.get('workflow_summary', {})

        # Debug logging for workflow summary
        print(f"\nDEBUG: Workflow Summary Contents:")
        print(f"  workflow_summary keys: {list(workflow_summary.keys())}")
        print(f"  final_accuracy: {workflow_summary.get('final_accuracy')}")
        print(f"  validation_rounds_completed: {workflow_summary.get('validation_rounds_completed')}")
        print(f"  total_corrections_applied: {workflow_summary.get('total_corrections_applied')}")

        # Get metrics from workflow summary (this is the authoritative source)
        final_accuracy = workflow_summary.get('final_accuracy', 0)
        total_corrections = workflow_summary.get('total_corrections_applied', 0)
        rounds_completed = workflow_summary.get('validation_rounds_completed', 0)

        # Fallback to validation rounds if workflow summary is empty
        validation_rounds = st.session_state.get('validation_rounds', [])
        print(f"  validation_rounds available: {len(validation_rounds) if validation_rounds else 0}")

        if final_accuracy == 0 and validation_rounds:
            final_accuracy = validation_rounds[-1].get('accuracy_estimate', 0) if validation_rounds else 0
            print(f"  Using fallback final_accuracy: {final_accuracy}")
        if total_corrections == 0 and validation_rounds:
            total_corrections = sum(len(r.get('corrections_applied', [])) for r in validation_rounds)
            print(f"  Using fallback total_corrections: {total_corrections}")
        if rounds_completed == 0 and validation_rounds:
            rounds_completed = len(validation_rounds)
            print(f"  Using fallback rounds_completed: {rounds_completed}")

        print(f"🐛 DEBUG: Final UI Values:")
        print(f"  Final Accuracy: {final_accuracy*100:.1f}%")
        print(f"  Validation Rounds: {rounds_completed}")
        print(f"  Total Corrections: {total_corrections}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            accuracy_delta = f"+{(final_accuracy - 0.80)*100:.1f}%" if final_accuracy > 0.80 else None
            st.metric(
                "🎯 Final Accuracy",
                f"{final_accuracy*100:.1f}%",
                delta=accuracy_delta
            )

        with col2:
            st.metric("🔄 Validation Rounds", f"{rounds_completed}/3")

        with col3:
            total_time = workflow_summary.get('total_processing_time', 0)
            if self.pipeline_state.get('start_time'):
                # Use actual elapsed time if processing
                elapsed = time.time() - self.pipeline_state['start_time']
                total_time = max(total_time, elapsed)
            st.metric("⏱️ Total Time", f"{total_time:.1f}s")

        with col4:
            st.metric("🔧 Total Corrections", total_corrections)

        # Show additional validation insights
        if validation_rounds:
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                avg_accuracy = sum(r.get('accuracy_estimate', 0) for r in validation_rounds) / len(validation_rounds)
                st.metric("📊 Average Accuracy", f"{avg_accuracy*100:.1f}%")

            with col2:
                total_duration = sum(r.get('round_duration', 0) for r in validation_rounds)
                st.metric("🔄 Validation Time", f"{total_duration:.1f}s")

            with col3:
                max_corrections = max(len(r.get('corrections_applied', [])) for r in validation_rounds) if validation_rounds else 0
                st.metric("🔧 Max Corrections/Round", max_corrections)

        # Final extracted data
        st.subheader("📋 Extracted Data")

        final_data = results.get('final_data', {})

        # Add data validation info
        if final_data:
            total_fields = self._count_total_fields(final_data)
            st.info(f"📊 Total extracted fields: {total_fields}")

        # Enhanced JSON display with truncation detection
        col1, col2 = st.columns([3, 1])

        with col1:
            # Display as formatted JSON
            st.json(final_data)

        with col2:
            # Data quality info
            st.write("**Data Quality:**")
            st.info("📊 Debug logging active for validation/correction responses")

        # Download buttons
        col1, col2 = st.columns(2)

        with col1:
            # Download extracted data
            json_str = json.dumps(final_data, indent=2)
            st.download_button(
                label="💾 Download Extracted Data",
                data=json_str,
                file_name=f"extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        with col2:
            # Download full results
            full_results_str = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="📊 Download Full Report",
                data=full_results_str,
                file_name=f"full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    def render_sidebar_info(self):
        """Render sidebar with information and examples - DISABLED for modern UI"""
        # Sidebar is now hidden via CSS, this method does nothing
        pass

    def _count_total_fields(self, data):
        """Count total number of fields in the extracted data"""
        if not data:
            return 0

        total = 0

        def count_recursive(obj):
            nonlocal total
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "table_data":
                        # Count table fields differently
                        if isinstance(value, list):
                            for table in value:
                                if isinstance(table, dict) and "rows" in table:
                                    rows = table["rows"]
                                    if isinstance(rows, list) and rows:
                                        # Count cells in table
                                        total += len(rows) * len(rows[0]) if rows and isinstance(rows[0], dict) else 0
                    elif isinstance(value, (dict, list)):
                        count_recursive(value)
                    else:
                        total += 1
            elif isinstance(obj, list):
                for item in obj:
                    count_recursive(item)

        count_recursive(data)
        return total

def init_extractor():
    """Initialize the schema text extractor"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        st.error("❌ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        st.stop()

    return SchemaTextExtractor(api_key)

def process_pipeline_sync(pdf_file, schema, page_num, settings, selected_model_config='current', selected_file_id=None):
    """Process the pipeline with real-time progress updates"""

    # Initialize pipeline state
    st.session_state.pipeline_state['processing'] = True
    st.session_state.pipeline_state['start_time'] = time.time()
    st.session_state.pipeline_state['current_step'] = 0
    st.session_state.pipeline_state['steps_completed'] = []
    st.session_state.validation_rounds = []

    # Create progress containers
    progress_container = st.empty()
    log_container = st.empty()

    def update_progress(step, message):
        """Update progress in real-time"""
        st.session_state.pipeline_state['current_step'] = step
        if step - 1 not in st.session_state.pipeline_state['steps_completed']:
            st.session_state.pipeline_state['steps_completed'].append(step - 1)

        with progress_container.container():
            st.progress((step) / 4)
            st.info(f"🔄 {message}")

    def log_message(message):
        """Log processing messages"""
        with log_container.container():
            st.text(f"📝 {message}")

    try:
        # Handle file input - either uploaded PDF or selected file ID
        if selected_file_id:
            # Using selected file from Claude Files API
            tmp_pdf_path = None  # Not needed for selected files
            update_progress(1, f"Using selected file: {selected_file_id[:12]}...")
        else:
            # Save uploaded PDF to temporary file
            if not pdf_file:
                st.error("❌ No PDF file provided")
                return {"success": False, "error": "No PDF file provided"}

            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_file.read())
                tmp_pdf_path = tmp_file.name
            update_progress(1, "PDF file saved for processing...")

        # Initialize the advanced pipeline
        #api_key = os.environ.get('OPENAI_API_KEY')
       

        # Use model configuration selected by user
        model_config = selected_model_config

        # Check if we're using Gemini
        config_details = list_available_configs().get(model_config, {})
        provider = config_details.get('provider', 'anthropic')

        # Get API key
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        api_key = anthropic_key

        # Show which configuration is being used with details
        config_name = model_config.title()
        config_cost = config_details.get('estimated_cost', 'Unknown cost')
        provider_name = "Google Gemini" if provider == 'google' else "Anthropic Claude"
        st.info(f"🤖 Using {provider_name} • {config_name} • {config_cost}")

        # For POC - show Gemini integration status
        if provider == 'google':
            gemini_key = os.environ.get('GOOGLE_API_KEY')
            if not gemini_key:
                st.error("❌ GOOGLE_API_KEY environment variable not found. Please set it to use Gemini.")
                st.stop()
            st.success("✅ Google Gemini API key configured")

        try:
            pipeline = AdvancedPDFExtractionPipeline(api_key, model_config)
        except Exception as e:
            if "proxies" in str(e) or "Claude" in str(e) or "anthropic" in str(e).lower():
                # Fallback to current configuration if selected one fails
                st.warning(f"⚠️ {model_config} initialization failed ({str(e)[:100]}...), falling back to current config")
                model_config = 'current'  # Update the config so retry works
                pipeline = AdvancedPDFExtractionPipeline(api_key, 'current')
            else:
                raise e

        # Enhanced progress callback to update UI and log validation details
        def progress_callback(message):
            log_message(message)

            # Log validation round details with corrections
            if "[ROUND]" in message:
                print(f"=== {message} ===")
                log_message(f"🔄 {message}")
            elif "validation failed" in message.lower():
                print(f"❌ VALIDATION FAILED: {message}")
                log_message(f"❌ {message}")
            elif "corrections applied" in message.lower():
                print(f"✅ CORRECTIONS: {message}")
                log_message(f"🔧 {message}")
            elif "accuracy" in message.lower():
                print(f"🎯 ACCURACY UPDATE: {message}")
                log_message(f"📊 {message}")

            # Update step based on message content
            if "Step 1" in message or "Preprocessing" in message:
                update_progress(1, "Preprocessing PDF to 600 DPI...")
            elif "Step 2" in message or "Uploading" in message:
                update_progress(2, f"Uploading to {provider_name} Files API...")
            elif "Step 3" in message or "extraction" in message.lower():
                update_progress(3, "Extracting data with schema...")
            elif "Step 4" in message or "Validation" in message:
                update_progress(4, "Validating and correcting data...")

        # Process the document
        if selected_file_id:
            # For selected files, we still need a dummy PDF path (AI provider will use the selected file)
            dummy_pdf_path = tmp_pdf_path or "dummy.pdf"  # Fallback for selected files
            result = pipeline.process_document(
                pdf_path=dummy_pdf_path,
                schema=schema,
                page_num=page_num,
                max_rounds=settings['max_rounds'],
                target_accuracy=settings['target_accuracy'],
                progress_callback=progress_callback,
                selected_file_id=selected_file_id
            )
        else:
            result = pipeline.process_document(
                pdf_path=tmp_pdf_path,
                schema=schema,
                page_num=page_num,
                max_rounds=settings['max_rounds'],
                target_accuracy=settings['target_accuracy'],
                progress_callback=progress_callback
            )

        # Update validation rounds for UI display and detailed logging
        if result.get('success') and 'step4_validation' in result.get('pipeline_steps', {}):
            step4_data = result['pipeline_steps']['step4_validation']
            if 'round_details' in step4_data:
                st.session_state.validation_rounds = step4_data['round_details']

                # Log detailed validation round information
                print("\n" + "="*80)
                print("📊 DETAILED VALIDATION ROUNDS SUMMARY")
                print("="*80)

                for i, round_data in enumerate(step4_data['round_details'], 1):
                    print(f"\n🔄 ROUND {i}:")
                    print(f"  📈 Accuracy: {round_data.get('accuracy_estimate', 0)*100:.1f}%")
                    print(f"  🔧 Corrections: {len(round_data.get('corrections_applied', []))}")
                    print(f"  ⏱️ Duration: {round_data.get('round_duration', 0):.1f}s")

                    # Log individual corrections with old vs new values
                    corrections = round_data.get('corrections_applied', [])
                    if corrections:
                        print(f"  🔍 CORRECTIONS APPLIED:")
                        for j, correction in enumerate(corrections, 1):
                            field = correction.get('field', 'Unknown')
                            old_value = correction.get('old_value', 'None')
                            new_value = correction.get('new_value', 'None')
                            reason = correction.get('reason', 'No reason provided')
                            print(f"    {j}. Field: {field}")
                            print(f"       Old: '{old_value}'")
                            print(f"       New: '{new_value}'")
                            print(f"       Reason: {reason}")
                    else:
                        print(f"  ✅ No corrections needed")

                print("="*80)

                # Also log final summary
                workflow_summary = result.get('workflow_summary', {})
                print(f"\n🎯 FINAL RESULTS:")
                print(f"  Final Accuracy: {workflow_summary.get('final_accuracy', 0)*100:.1f}%")
                print(f"  Total Rounds: {workflow_summary.get('validation_rounds_completed', 0)}")
                print(f"  Total Corrections: {workflow_summary.get('total_corrections_applied', 0)}")
                print(f"  Processing Time: {workflow_summary.get('total_processing_time', 0):.1f}s")
                print("="*80)

        # Mark all steps as completed
        st.session_state.pipeline_state['steps_completed'] = [0, 1, 2, 3]
        st.session_state.pipeline_state['results'] = result
        st.session_state.pipeline_state['processing'] = False

        # Clear progress containers
        progress_container.empty()
        log_container.empty()

        # Clean up
        if tmp_pdf_path and os.path.exists(tmp_pdf_path):
            os.unlink(tmp_pdf_path)

        return result

    except Exception as e:
        st.session_state.pipeline_state['processing'] = False
        st.session_state.pipeline_state['error'] = str(e)

        # Clear progress containers
        progress_container.empty()
        log_container.empty()

        # Also display the error immediately
        st.error(f"❌ Pipeline error: {str(e)}")
        st.exception(e)

        return {"success": False, "error": str(e)}

def main():
    """Main application function"""

    # Initialize UI
    ui = AdvancedPipelineUI()

    # Render header
    ui.render_header()

    # Sidebar is disabled in modern UI

    # Main content area - single column layout for modern design
    # Pipeline overview
    ui.render_pipeline_overview()

    # Upload section
    pdf_file, page_num, schema, selected_file_id, selected_model_config = ui.render_upload_section()

    # Processing controls
    controls = ui.render_processing_controls(pdf_file or selected_file_id, schema)

    # Real-time progress and validation in cards
    col1, col2 = st.columns([3, 2])

    with col1:

        # Debug info is always shown since debug mode is always enabled
        with st.expander("🐛 Debug Information", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write("✅ Debug mode: **Always Active**")
                st.write(f"📁 PDF file: {'Uploaded' if pdf_file else 'Not uploaded'}")
                st.write(f"🔗 Selected file: {selected_file_id[:12] + '...' if selected_file_id else 'None'}")
            with col2:
                st.write(f"📝 Schema: {'Provided' if schema else 'Not provided'}")
                st.write(f"🚀 Ready to process: {controls['start_processing']}")
                st.write(f"⚙️ Pipeline status: {st.session_state.pipeline_state.get('processing', 'Idle')}")

        # Start processing if requested
        if controls['start_processing']:
            st.info("🚀 Starting pipeline processing...")

            try:
                # Process the pipeline
                result = process_pipeline_sync(pdf_file, schema, page_num, controls['settings'], selected_model_config, selected_file_id)

                # Display result or error
                if result and not result.get('success', True):
                    st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                elif result and result.get('success'):
                    st.success("✅ Processing completed successfully!")
                else:
                    st.warning("⚠️ Processing completed but no clear result status")

            except Exception as e:
                st.error(f"❌ Unexpected error during processing: {str(e)}")
                st.exception(e)  # This will show the full traceback

        # Display any stored errors
        if 'error' in st.session_state.pipeline_state and st.session_state.pipeline_state['error']:
            st.error(f"❌ Error: {st.session_state.pipeline_state['error']}")
            # Clear the error after displaying
            del st.session_state.pipeline_state['error']

    with col2:
        # Real-time progress in card
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        ui.render_real_time_progress()
        st.markdown('</div>', unsafe_allow_html=True)

        # Validation rounds in card
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        ui.render_validation_rounds()
        st.markdown('</div>', unsafe_allow_html=True)

    # Results dashboard (full width)
    ui.render_results_dashboard()

    # Reset button
    if st.button("🔄 Reset Pipeline", help="Clear all results and start over"):
        # Clear session state
        for key in list(st.session_state.keys()):
            if key.startswith('pipeline') or key == 'validation_rounds':
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()