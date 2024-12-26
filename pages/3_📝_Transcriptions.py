import streamlit as st
from domain.transcription_service import TranscriptionService
from domain.audio_splitter import AudioSplitter
from domain.data_service import DataService
from domain.audio_service import AudioService
from ui.process_handlers import (
    get_processing_state,
    set_processing_state,
    handle_split_audio
)

audio_service = AudioService()

# Page config
st.set_page_config(
    page_title="Transcriptions",
    page_icon="📝",
    layout="wide"
)

# Title
st.title("📝 Transcription Viewer")

# Check if API key is set
if 'openai_api_key' not in st.session_state:
    st.error("⚠️ OpenAI API key not found. Please set it in the Home page.")
    st.stop()

# Initialize services
transcription_service = TranscriptionService(api_key=st.session_state.openai_api_key)
audio_splitter = AudioSplitter()
data_service = DataService()

# Check if video ID is in session state
if 'selected_video_id' not in st.session_state:
    st.warning("⚠️ No transcription selected. Please select a transcription from the Downloaded page.")
    st.stop()

video_id = st.session_state['selected_video_id']
splits = audio_splitter.get_splits(transcription_service.get_excel_path(video_id))

# Get video info
video_info = data_service.get_video_info(video_id)
if video_info:
    # Create two columns for thumbnail and info
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display thumbnail if available
        if 'thumbnail' in video_info and video_info['thumbnail']:
            st.image(video_info['thumbnail'], use_container_width=True)
    
    with col2:
        # Display video info
        st.header(f"🎥 {video_info.get('title', 'Untitled Video')}")
        if 'id' in video_info:
            st.markdown(f"**Video ID**: {video_info['id']}")
        if 'channel_title' in video_info:
            st.markdown(f"**Channel**: {video_info['channel_title']}")
        if 'duration' in video_info:
            st.markdown(f"**Duration**: {video_info['duration']}")
        if 'view_count' in video_info and video_info['view_count']:
            st.markdown(f"**Views**: {video_info['view_count']:,}")
        if 'like_count' in video_info and video_info['like_count']:
            st.markdown(f"**Likes**: {video_info['like_count']:,}")
        if 'published_at' in video_info:
            st.markdown(f"**Published**: {video_info['published_at']}")
        
        # Add YouTube link
        st.markdown(f"🔗 [Watch on YouTube](https://youtu.be/{video_id})")

        if not splits:
            grid_position = f"transcribe_{video_id}"
            if not get_processing_state(video_id, grid_position, "split"):
                if st.button("✂️ Split Audio", key=f"split_{video_id}_{grid_position}"):
                    set_processing_state(video_id, grid_position, "split", True)
                    st.rerun()
            
            if get_processing_state(video_id, grid_position, "split"):
                file_path = audio_service.get_converted_file(video_id)
                handle_split_audio(video_id, file_path, grid_position, audio_splitter, transcription_service)

st.divider()

if not splits:
    st.error("❌ No audio segments found for this transcription.")

# Initialize expanded states in session state if not exists
if 'expanded_segments' not in st.session_state:
    st.session_state.expanded_segments = {}

for idx, split in enumerate(splits, 1):
    # Create a unique key for this segment
    segment_key = f"segment_{st.session_state.selected_video_id}_{idx}"
    
    # Initialize expanded state if not exists
    if segment_key not in st.session_state.expanded_segments:
        st.session_state.expanded_segments[segment_key] = False
    
    # Create expander
    with st.expander(f"🎵 - 📝 Segment {idx}"):
        st.markdown(f"**Time**: {split['start_time_seconds']:.2f}s - {split['end_time_seconds']:.2f}s")
        st.markdown(split['text'])
        
        # Add checkbox to load audio
        load_audio = st.checkbox("🎵 Load Audio Player", key=f"load_{segment_key}")
        
        # Only load audio if checkbox is checked
        if load_audio:
            # Audio player
            st.audio(split['audio_file'])
            # Show segment duration
            st.caption(f"Duration: {split['duration_seconds']:.2f} seconds")

# Add a back button
if st.button("← Back to Downloads"):
    # Clear the session states
    if 'selected_video_id' in st.session_state:
        del st.session_state['selected_video_id']
    if 'expanded_segments' in st.session_state:
        del st.session_state['expanded_segments']
    st.switch_page("pages/2_📂_Downloaded.py")
