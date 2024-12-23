import streamlit as st
from domain.audio_service import AudioService
from domain.audio_splitter import AudioSplitter
from domain.transcription_service import TranscriptionService

audio_service = AudioService()
audio_splitter = AudioSplitter()

def split_audio(mp3_path, video_id):
    transcription_service = TranscriptionService(api_key=st.session_state.openai_api_key)
    if st.button("✂️ Split Audio", key=f"split_audio_{file_info['id']}"):
        with st.spinner("Splitting audio based on transcription..."):
            split_success, split_result = audio_splitter.split_audio(
                mp3_path,
                video_id,
                transcription_service.get_excel_path(video_id),
                'wav'  # Use WAV format for high quality
            )
            if split_success:
                st.success("✅ Audio split successfully!")
            else:
                st.error(f"❌ Failed to split audio: {split_result}")
    
    return split_success, split_result

def transcribe_audio(mp3_path, video_id):
    transcription_service = TranscriptionService(api_key=st.session_state.openai_api_key)
    if st.button("🎯 Transcribe", key=f"transcribe_{file_info['id']}"):
        with st.spinner("Transcribing audio..."):
            transcribe_success, transcribe_result = transcription_service.transcribe_audio(mp3_path, video_id)
            if transcribe_success:
                st.success("✅ Audio transcription successfully!")
            else:
                st.warning(f"⚠️ Audio transcription failed: {transcribe_result}")
    
    if transcribe_success:
        # Auto Split audio
        split_audio(mp3_path, video_id)
    
    return transcribe_success, transcribe_result

def convert_audio(mp3_path, video_id):
    if st.button("🔄 Convert to OGG", key=f"convert_{video_id}"):
        with st.spinner("Converting to OGG format..."):
            convert_success, convert_result = audio_service.convert_to_ogg(mp3_path)
            if convert_success:
                st.success("✅ Conversion successful!")
                st.rerun()
            else:
                st.error(f"❌ Conversion failed: {result}")

    if convert_success:
        # Auto Transcribe audio
        transcribe_audio(convert_result, video_id)
    
    return convert_success, convert_result