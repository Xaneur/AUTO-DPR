import streamlit as st
import requests
from audio_recorder_streamlit import audio_recorder
from src.main import updated_quantity_in_sheet
from src.sheet_data_fetch import get_available_sheets
from utils.logger import get_logger
from config.configuration import FILE_PATH
from dotenv import load_dotenv

load_dotenv()

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

# ─── Groq Configuration ─────────────────────────────────────────────
GROQ_API_KEY = st.sidebar.text_input("Groq API Key", type="password", help="Enter your Groq API key")
GROQ_MODEL = st.sidebar.selectbox("Groq Model", ["whisper-large-v3", "whisper-large-v3-turbo"], index=1)

# ─── Groq STT Function ──────────────────────────────────────────────
def transcribe_via_groq_api(audio_bytes):
    """Transcribe audio using Groq API"""
    try:
        if not GROQ_API_KEY:
            raise Exception("Groq API key is required")
        
        # Prepare the file for upload
        files = {
            "file": ("audio.wav", audio_bytes, "audio/wav")
        }
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        
        data = {
            "model": GROQ_MODEL,
            "response_format": "json"
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("text", "").strip()
        else:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Groq API transcription error: {str(e)}")
        raise e

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

# Load Whisper model only if using local method
# No local Whisper model needed - using Groq API only
model = None

# ─── Audio Recording Section ────────────────────────────────────────
st.subheader("Record Audio")
st.caption("Using: Groq API")

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
        with st.spinner("Transcribing audio using Groq API..."):
            try:
                new_transcription = transcribe_via_groq_api(audio_bytes)

                if new_transcription:
                    st.session_state.combined_transcription.append(new_transcription)
                    st.session_state.audio_counter += 1
                    st.success("Transcription added.")
                    st.rerun()
                else:
                    st.warning("No transcription received. Please try again.")

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
**Setup**
- Enter your Groq API key in the sidebar
- Select your preferred Groq model (whisper-large-v3-turbo is recommended for speed)

**Record Audio**
- Click the mic to start recording
- Speak and click again to stop
- Click "Transcribe This Recording" to convert it to text using Groq API

**Edit Transcription**
- All your transcribed audio will appear in one editable text box
- Each transcription is separated by a blank line

**Approve**
- Click "Approve & Update Sheet" to submit each line separately to the sheet

**Reset**
- "Clear All" wipes current transcriptions
""")