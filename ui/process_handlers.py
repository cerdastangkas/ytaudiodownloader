"""Handlers for audio processing operations."""
import streamlit as st
from domain.youtube_service import YouTubeService
from domain.audio_service import AudioService
from domain.transcription_service import TranscriptionService
from domain.audio_splitter import AudioSplitter

def get_processing_state(video_id: str, grid_position: str, action: str) -> bool:
    """Get the processing state for a specific action."""
    state_key = f"{action}_processing_{video_id}_{grid_position}"
    if state_key not in st.session_state:
        st.session_state[state_key] = False
    return st.session_state[state_key]

def set_processing_state(video_id: str, grid_position: str, action: str, state: bool):
    """Set the processing state for a specific action."""
    state_key = f"{action}_processing_{video_id}_{grid_position}"
    st.session_state[state_key] = state

def handle_process_error(error: Exception, video_id: str, grid_position: str, action: str):
    """Handle process errors uniformly."""
    st.error(f"❌ An error occurred: {str(error)}")
    set_processing_state(video_id, grid_position, action, False)
    st.rerun()

def handle_split_audio(video_id: str, file_path: str, grid_position: str, audio_splitter: AudioSplitter, transcription_service: TranscriptionService):
    """Handle the audio splitting process."""
    try:
        with st.spinner("Splitting audio based on transcription..."):
            split_success, split_result = audio_splitter.split_audio(
                file_path,
                video_id,
                transcription_service.get_excel_path(video_id),
                'wav'
            )
            if split_success:
                st.success("✅ Audio split successfully!")
            else:
                st.warning(f"⚠️ Audio split failed: {split_result}")
        
        set_processing_state(video_id, grid_position, "split", False)
        st.rerun()
    except Exception as e:
        handle_process_error(e, video_id, grid_position, "split")

def handle_transcription(video_id: str, file_path: str, grid_position: str, 
                        transcription_service: TranscriptionService, 
                        audio_splitter: AudioSplitter):
    """Handle the audio transcription process."""
    try:
        transcribe_success = False
        with st.spinner("Transcribing audio..."):
            transcribe_success, transcribe_result = transcription_service.transcribe_audio(file_path, video_id)
            if transcribe_success:
                st.success("✅ Audio transcribed successfully!")
            else:
                st.warning(f"⚠️ Audio transcription failed: {transcribe_result}")
                set_processing_state(video_id, grid_position, "transcribe", False)
                st.rerun()
                return
        
        # Proceed with splitting if transcription was successful
        if transcribe_success:
            handle_split_audio(video_id, file_path, grid_position, audio_splitter, transcription_service)
        
        set_processing_state(video_id, grid_position, "transcribe", False)
        st.rerun()
    except Exception as e:
        handle_process_error(e, video_id, grid_position, "transcribe")

def handle_conversion(video_id: str, file_path: str, grid_position: str, 
                     audio_service: AudioService, transcription_service: TranscriptionService,
                     audio_splitter: AudioSplitter):
    """Handle the audio conversion process."""
    try:
        convert_success = False
        with st.spinner("Converting to OGG format..."):
            convert_success, convert_result = audio_service.convert_to_ogg(file_path)
            if convert_success:
                st.success("✅ Conversion successful!")
            else:
                st.error(f"❌ Conversion failed: {convert_result}")
                set_processing_state(video_id, grid_position, "convert", False)
                st.rerun()
                return
        
        # Proceed with transcription if conversion was successful
        if convert_success:
            handle_transcription(video_id, file_path, grid_position, transcription_service, audio_splitter)
        
        set_processing_state(video_id, grid_position, "convert", False)
        st.rerun()
    except Exception as e:
        handle_process_error(e, video_id, grid_position, "convert")

def handle_download(video_id: str, grid_position: str, youtube_service: YouTubeService,
                   audio_service: AudioService, transcription_service: TranscriptionService,
                   audio_splitter: AudioSplitter):
    """Handle the video download process."""
    try:
        progress_bar = st.progress(0, text="Starting download...")
        result = youtube_service.download_audio(
            video_id,
            progress_callback=lambda p: progress_bar.progress(int(p)/100, text=f"Downloading... {int(p)}%")
        )
        
        if not result['success']:
            progress_bar.empty()
            st.error("❌ Download failed")
            set_processing_state(video_id, grid_position, "download", False)
            st.rerun()
            return
        
        progress_bar.empty()
        mp3_path = youtube_service.get_source_path(video_id)
        
        # Proceed with conversion after successful download
        handle_conversion(video_id, mp3_path, grid_position, audio_service, 
                         transcription_service, audio_splitter)
        
        set_processing_state(video_id, grid_position, "download", False)
        st.rerun()
    except Exception as e:
        handle_process_error(e, video_id, grid_position, "download")
