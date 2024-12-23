import streamlit as st
import pandas as pd
from pathlib import Path
from domain.data_service import DataService
from domain.transcription_service import TranscriptionService
from domain.audio_service import AudioService
from domain.audio_splitter import AudioSplitter

# Page config
st.set_page_config(page_title="Transcriptions", page_icon="📝", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0 1rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    .title-container {
        padding: 1rem 0;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .stButton button {
        background-color: #1a73e8;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
    }
    .segment-container {
        padding: 0.25rem 0;
        margin-bottom: 0.25rem;
    }
    .timestamp {
        font-weight: 500;
    }
    .text-content {
        line-height: 1.4;
        margin: 0.25rem 0;
    }
    .controls-container {
        padding: 0.5rem 0;
        margin-bottom: 0.75rem;
    }
    .video-title {
        font-size: 1.25rem;
        font-weight: 500;
        margin-bottom: 0.75rem;
    }
    div[data-testid="stExpander"] {
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title with gradient background
st.markdown("""
    <div class="title-container">
        <h1>📝 Audio Transcriptions</h1>
        <p>View and manage your transcribed audio content</p>
    </div>
""", unsafe_allow_html=True)

# Check for API key
if 'openai_api_key' not in st.session_state or not st.session_state.openai_api_key:
    st.error("⚠️ Please set your OpenAI API key in the main page first!")
    st.stop()

# Initialize services
data_service = DataService()
transcription_service = TranscriptionService(api_key=st.session_state.openai_api_key)
audio_service = AudioService()
audio_splitter = AudioSplitter()

# Get all downloaded videos and filter for ones with transcriptions
downloaded_videos = data_service.get_downloaded_videos()
transcribed_videos = []

for video in downloaded_videos:
    if transcription_service.get_transcription(video['id']) is not None:
        transcribed_videos.append(video)

if not transcribed_videos:
    st.info("🎵 No transcribed videos found. Go to the Downloads page to transcribe some videos!")
else:
    # Create sections for each transcribed video
    for video in transcribed_videos:
        video_id = video['id']
        transcription = transcription_service.get_transcription(video_id)
        
        if transcription:
            with st.expander(f"🎵 {video['title']}", expanded=True):
                # Check if audio needs to be split
                is_split = audio_splitter.is_already_split(video_id)
                
                if not is_split:
                    st.markdown('<div class="controls-container">', unsafe_allow_html=True)
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        output_format = st.selectbox(
                            "🎵 Output Format",
                            ["mp3", "ogg"],
                            key=f"format_{video_id}"
                        )
                    with col2:
                        ogg_file = audio_service.get_converted_file(video_id)
                        if st.button("✂️ Split Audio", key=f"split_{video_id}"):
                            if ogg_file:
                                with st.spinner("🎵 Splitting audio into segments..."):
                                    success, result = audio_splitter.split_audio(
                                        ogg_file,
                                        video_id,
                                        transcription_service.get_excel_path(video_id),
                                        output_format=output_format
                                    )
                                    if success:
                                        st.success("✅ Audio split successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Splitting failed: {result}")
                            else:
                                st.error("⚠️ Please convert the audio to OGG format first")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="controls-container">', unsafe_allow_html=True)
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        output_format = st.selectbox(
                            "🎵 Output Format",
                            ["mp3", "ogg"],
                            key=f"format_{video_id}"
                        )
                    with col2:
                        if st.button("🔄 Re-split Audio", key=f"resplit_{video_id}"):
                            ogg_file = audio_service.get_converted_file(video_id)
                            with st.spinner("🎵 Re-splitting audio into segments..."):
                                success, result = audio_splitter.split_audio(
                                    ogg_file,
                                    video_id,
                                    transcription_service.get_excel_path(video_id),
                                    output_format=output_format
                                )
                                if success:
                                    st.success("✅ Audio re-split successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Splitting failed: {result}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Display transcription with audio segments
                splits = audio_splitter.get_splits(video_id, transcription_service.get_excel_path(video_id))
                split_dict = {split['segment_index']: split for split in splits} if splits else {}
                
                for idx, segment in enumerate(transcription, 1):
                    st.markdown(f'<div class="segment-container">', unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div class="timestamp">🕒 Segment {idx} [{segment['start_time']:.1f}s - {segment['end_time']:.1f}s]</div>
                        <div class="text-content">{segment['text']}</div>
                        """,
                        unsafe_allow_html=True
                    )
                    # Add audio player if split exists
                    if idx-1 in split_dict:
                        try:
                            st.audio(split_dict[idx-1]['audio_file'])
                        except Exception as e:
                            st.error(f"⚠️ Error loading audio segment {idx}")
                    st.markdown('</div>', unsafe_allow_html=True)
