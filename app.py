import streamlit as st
import whisper
import tempfile
import os
from audio_recorder_streamlit import audio_recorder
from src.main import updated_quantity_in_sheet
from src.sheet_data_fetch import get_available_sheets
from utils.logger import get_logger
from config.configuration import FILE_PATH

logger = get_logger(__name__)

# ─── Page Configuration ─────────────────────────────────────────────
st.set_page_config(
    page_title="Update Sheet with AI",
    layout="centered"
)

# ─── Custom Styling ─────────────────────────────────────────────────
st.markdown("""
<style>
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', sans-serif;
        background-color: #ffffff;
        color: #111;
    }

    /* Container adjustments */
    .block-container {
        padding: 2rem 2rem 4rem;
        max-width: 720px;
        margin: auto;
    }

    h1, h2, h3 {
        color: #111111;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }

    .stTextInput>div>div>input,
    .stTextArea textarea {
        font-size: 16px;
        border-radius: 8px;
        border: 1px solid #ccc;
        padding: 0.5rem 1rem;
        background-color: #f9f9f9;
        color: #111;
    }

    .stSelectbox > div:first-child {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    display: block !important;
    font-size: 1rem !important;
    }

    .stTextInput>div>div>input:focus,
    .stTextArea textarea:focus {
        border: 1px solid #333;
        background-color: #fff;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #111 !important;
        color: white !important;
        padding: 0.6rem 1.2rem;
        font-size: 1rem;
        border: none;
        border-radius: 10px;
        width: 100%;
        margin-top: 1rem;
        transition: background-color 0.2s ease-in-out;
    }

    .stButton>button:hover {
        background-color: #333 !important;
    }

    /* Audio Recorder Section */
    .audio-recorder {
        margin: 1rem 0;
        width: 100%;
    }

    /* TextArea Custom */
    textarea {
        border-radius: 10px !important;
        font-size: 1rem !important;
        padding: 1rem !important;
        line-height: 1.5 !important;
    }

    /* Expander (Instructions) */
    .streamlit-expanderHeader {
        font-size: 1rem;
        font-weight: 500;
    }

    /* Hide warning for Streamlit deprecation (optional) */
    .stAlert {
        background-color: #f5f5f5;
        border-left: 5px solid #111;
    }

    /* Caption */
    .stCaption {
        font-size: 0.85rem;
        color: #555;
        margin-top: -0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Title is now in the main column

# ─── Load Whisper Model ─────────────────────────────────────────────
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

# ─── Session State Initialization ──────────────────────────────────
if 'combined_transcription' not in st.session_state:
    st.session_state.combined_transcription = []

if isinstance(st.session_state.combined_transcription, str):
    st.session_state.combined_transcription = [st.session_state.combined_transcription]

if 'audio_counter' not in st.session_state:
    st.session_state.audio_counter = 0

# Function to get available sheets with error handling
@st.cache_resource(show_spinner="Loading available sheets...")
def load_available_sheets():
    try:
        sheets = get_available_sheets(FILE_PATH)
        # Filter out LOGS sheet
        sheets = [sheet for sheet in sheets if sheet.upper() != "LOGS"]
        if not sheets:
            logger.warning("No valid sheets found in the workbook")
            return ["No valid sheets found"]
        return sheets
    except Exception as e:
        logger.error(f"Error loading sheets: {str(e)}")
        return [f"Error: {str(e)}"]

# Main content container
st.title("Update Sheet with AI")

# User information section
with st.container():
    st.subheader("User Information")
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Your Name", key="user_name", help="Enter your name")
    with col2:
        location = st.text_input("Location", key="user_location", help="Enter your site location")
    
    st.markdown("---")

# Sheet selection
with st.container():
    st.subheader("Sheet Selection")
    # Get available sheets
    available_sheets = load_available_sheets()
    
    # Sheet selection UI in main area
    if available_sheets[0].startswith("Error:") or available_sheets[0] == "No valid sheets found":
        st.error(available_sheets[0])
        st.session_state.selected_sheet = None
    else:
        # Create a dropdown for sheet selection
        selected_sheet = st.selectbox(
            "Select a sheet to update:",
            options=available_sheets,
            index=0,
            key="sheet_selector",
            help="Select which sheet to update with your transcriptions"
        )
        
        # Store the selected sheet in session state
        st.session_state.selected_sheet = selected_sheet
        st.caption(f"{len(available_sheets)} sheet{'s' if len(available_sheets) > 1 else ''} available")
        
        # Add some space
        st.markdown("---")

with st.spinner("Loading Whisper model..."):
    model = load_whisper_model()

# ─── Audio Recording Section ────────────────────────────────────────
st.subheader("Record Audio")

audio_bytes = audio_recorder(
    recording_color="#000000",
    neutral_color="#777777",
    icon_name="microphone",
    icon_size="3x",
    text="Click icon to record"
)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")

    if st.button("Transcribe This Recording"):
        with st.spinner("Transcribing audio..."):
            try:
                # Create a temporary directory that works cross-platform
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Create a temporary file with a proper path for the current OS
                    temp_file = os.path.join(temp_dir, f"recording_{st.session_state.audio_counter}.wav")
                    
                    # Write audio data to the temporary file
                    with open(temp_file, 'wb') as f:
                        f.write(audio_bytes)
                    
                    # Transcribe the audio file
                    result = model.transcribe(temp_file)
                    new_transcription = result['text'].strip()

                    if new_transcription:
                        st.session_state.combined_transcription.append(new_transcription)
                        st.session_state.audio_counter += 1
                st.success("Transcription added.")
                st.rerun()

            except Exception as e:
                st.error(f"Error during transcription: {str(e)}")
                logger.error(f"Transcription Error: {str(e)}")

# ─── Combined Transcription ─────────────────────────────────────────
if st.session_state.combined_transcription:
    st.subheader("Combined Transcription")

    # Join transcriptions into one editable string
    combined_text = "\n\n".join(st.session_state.combined_transcription)

    # Show single editable text box
    edited_text = st.text_area(
        "Edit Combined Transcription:",
        value=combined_text,
        height=300,
        key="combined_text_area"
    )

    # Split back into list and update session state
    st.session_state.combined_transcription = [
        t.strip() for t in edited_text.split("\n\n") if t.strip()
    ]

    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.combined_transcription = []
        st.session_state.audio_counter = 0
        st.success("All transcriptions cleared.")
        st.rerun()

    if st.button("✅ Approve & Update Sheet", type="primary", use_container_width=True):
            with st.spinner("Processing transcription..."):
                try:
                    if not st.session_state.selected_sheet or st.session_state.selected_sheet in ["No sheets found", "Error loading sheets"]:
                        st.error("Please select a valid sheet first")
                    elif not name.strip():
                        st.error("Please enter your name")
                    else:
                        for transcription in st.session_state.combined_transcription:
                            updated_quantity_in_sheet(
                                description=transcription,
                                sheet_name=st.session_state.selected_sheet,
                                name=name.strip(),
                                location=location.strip() if location else ""
                            )
                        st.success(f"Successfully updated sheet: {st.session_state.selected_sheet}")
                        st.session_state.combined_transcription = []
                        st.session_state.audio_counter = 0
                        st.rerun()
                except Exception as e:
                    st.error(f"Error updating sheet: {str(e)}")
                    logger.error(f"Update Sheet Error: {str(e)}")

# ─── How to Use ─────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📋 Instructions"):
    st.markdown("""
**Record Audio**
- Click the mic to start recording
- Speak and click again to stop
- Click “Transcribe This Recording” to convert it to text

**Edit Transcription**
- All your transcribed audio will appear in one editable text box
- Each transcription is separated by a blank line

**Approve**
- Click “Approve & Update Sheet” to submit each line separately to the sheet

**Reset**
- “Clear All” wipes current transcriptions
""")