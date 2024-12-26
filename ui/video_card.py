import streamlit as st
from domain.youtube_service import YouTubeService
from domain.audio_service import AudioService
from domain.transcription_service import TranscriptionService
from domain.audio_splitter import AudioSplitter
from utils.date_formatter import format_published_date
from ui.process_handlers import (
    get_processing_state,
    set_processing_state,
    handle_split_audio,
    handle_transcription,
    handle_conversion,
    handle_download
)

def display_video_info(video: dict, video_id: str):
    """Display video information."""
    st.image(
        video['thumbnail'],
        use_container_width=True,
        caption=video['title']
    )
    
    st.markdown(f"**Channel:** {video['channel_title']}")
    st.markdown(f"**Duration:** {video['duration']}")
    st.markdown(f"**Video ID:** {video_id}")
    st.markdown(f"**Published:** {format_published_date(video['published_at'])}")

def display_video_card(video: dict, youtube_service: YouTubeService, grid_position: str):
    """Display a single video card with download functionality."""
    audio_service = AudioService()
    transcription_service = TranscriptionService(api_key=st.session_state.openai_api_key)
    audio_splitter = AudioSplitter()
    
    video_id = video['id']
    file_path = youtube_service.get_audio_path(video_id)
    
    with st.container():
        print(f"[DEBUG] Displaying video card for ID: {video_id} at position {grid_position}")
        print(f"[DEBUG] Video title: {video.get('title', 'Unknown Title')}")
        
        # Card container with fixed height and scrollable content
        with st.container():
            # Display video information
            """Display video information."""
            st.image(
                video['thumbnail'],
                use_container_width=True
            )
            
            # Process existing transcription
            existing_transcription = transcription_service.get_transcription(video_id)
            has_splits = audio_splitter.is_already_split(video_id)
            has_converted = audio_service.get_converted_file(video_id)
            has_downloaded = youtube_service.is_audio_downloaded(video_id)

            if has_splits:
                st.success("✅ Transcription and audio segments are available")
            elif existing_transcription:
                st.success("✅ Transcription available")
            elif has_converted:
                st.success("✅ Converted to OGG")
            elif has_downloaded:
                st.success("✅ Downloaded")
            
            st.markdown(f"##### [{video['title']}](https://youtu.be/{video_id})")
            st.markdown(f"**Channel:** {video['channel_title']}")
            st.markdown(f"**Duration:** {video['duration']}")
            st.markdown(f"**Video ID:** {video_id}")
            st.markdown(f"**Published:** {format_published_date(video['published_at'])}")
            
            if existing_transcription:              
                if not has_splits:
                    # Handle split audio button and processing
                    if not get_processing_state(video_id, grid_position, "split"):
                        if st.button("✂️ Split Audio", key=f"split_{video_id}_{grid_position}"):
                            set_processing_state(video_id, grid_position, "split", True)
                            st.rerun()
                    
                    if get_processing_state(video_id, grid_position, "split"):
                        handle_split_audio(video_id, file_path, grid_position, audio_splitter, transcription_service)
            
                if st.button("📝 View Transcription", key=f"view_transcription_{video_id}_{grid_position}"):
                    st.session_state['selected_video_id'] = video_id
                    st.switch_page("pages/3_📝_Transcriptions.py")
                    
            elif has_converted:
                # Handle transcribe button and processing
                if not get_processing_state(video_id, grid_position, "transcribe"):
                    if st.button("🎯 Transcribe", key=f"transcribe_{video_id}_{grid_position}"):
                        set_processing_state(video_id, grid_position, "transcribe", True)
                        st.rerun()
            
                if get_processing_state(video_id, grid_position, "transcribe"):
                    handle_transcription(video_id, file_path, grid_position, transcription_service, audio_splitter)
                    
            elif youtube_service.is_audio_downloaded(video_id):
                # Handle convert button and processing
                if not get_processing_state(video_id, grid_position, "convert"):
                    if st.button("🔄 Convert to OGG", key=f"convert_{video_id}_{grid_position}"):
                        set_processing_state(video_id, grid_position, "convert", True)
                        st.rerun()
            
                if get_processing_state(video_id, grid_position, "convert"):
                    handle_conversion(video_id, file_path, grid_position, audio_service, 
                                   transcription_service, audio_splitter)
                    
            else:
                # Handle download button and processing
                if not get_processing_state(video_id, grid_position, "download"):
                    if st.button("🎵 Download", key=f"download_{video_id}_{grid_position}"):
                        set_processing_state(video_id, grid_position, "download", True)
                        st.rerun()
                
                if get_processing_state(video_id, grid_position, "download"):
                    handle_download(video_id, grid_position, youtube_service, audio_service,
                                 transcription_service, audio_splitter)
    
    st.divider()
