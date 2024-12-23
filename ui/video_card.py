import streamlit as st
from domain.youtube_service import YouTubeService
from domain.audio_service import AudioService
from utils.date_formatter import format_published_date
from domain.transcription_service import TranscriptionService
from domain.audio_splitter import AudioSplitter

def display_video_card(video: dict, youtube_service: YouTubeService):
    """Display a single video card with download functionality"""
    # Initialize audio service
    audio_service = AudioService()
    transcription_service = TranscriptionService(api_key=st.session_state.openai_api_key)
    audio_splitter = AudioSplitter()
    
    with st.container():
        # Thumbnail
        if 'thumbnail' in video:
            st.image(video['thumbnail'], width=None)
        
        # Video title as a link
        st.markdown(f"### [{video.get('title', 'Unknown Title')}](https://youtube.com/watch?v={video['id']})")
        
        # Download controls
        video_id = video['id']
        download_key = f"download_{video_id}"
        file_path = youtube_service.get_audio_path(video_id)
        
        # Check if transcription exists
        existing_transcription = transcription_service.get_transcription(video_id)
        
        if existing_transcription:
            st.success("✅ Transcription available")
            # Check if audio is already split
            has_splits = audio_splitter.is_already_split(video_id)
            if not has_splits:
                if st.button("✂️ Split Audio", key=f"split_audio_{video_id}"):
                    with st.spinner("Splitting audio based on transcription..."):
                        success, result = audio_splitter.split_audio(
                            file_path, 
                            video_id,
                            transcription_service.get_excel_path(video_id),
                            'wav'  # Use WAV format for high quality
                        )
                        if success:
                            st.success("✅ Audio split successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to split audio: {result}")
            else:
                st.info("✅ Audio already splitted into segments")
                
            if st.button("📝 View Transcription", key=f"view_transcription_{video_id}"):
                st.session_state['selected_video_id'] = video_id
                st.switch_page("pages/3_📝_Transcriptions.py")
                
        elif audio_service.get_converted_file(video_id):
            st.success("✅ Converted to OGG")
            if st.button("🎯 Transcribe", key=f"transcribe_{video_id}"):
                with st.spinner("Transcribing audio..."):
                    transcribe_success, transcribe_result = transcription_service.transcribe_audio(file_path, video_id)
                    if transcribe_success:
                        st.success("✅ Audio transcribed successfully!")
                    else:
                        st.warning(f"⚠️ Audio transcribed failed: {transcribe_result}")
                
                if transcribe_success:  # Only attempt splitting if transcription was successful
                    with st.spinner("Splitting audio into segments..."):
                        split_success, split_result = audio_splitter.split_audio(
                            file_path,
                            video_id,
                            transcription_service.get_excel_path(video_id),
                            'wav'  # Use WAV format for high quality
                        )
                        if split_success:
                            st.success("✅ Audio split successfully!")
                        else:
                            st.warning(f"⚠️ Audio split failed: {split_result}")
                    
            st.rerun()

        elif youtube_service.is_audio_downloaded(video_id):
            st.success("✅ Downloaded")
            if st.button("🔄 Convert to OGG", key=f"convert_{video_id}"):
                with st.spinner("Converting to OGG format..."):
                    convert_success, convert_result = audio_service.convert_to_ogg(file_path)
                    if convert_success:
                        st.success("✅ Conversion successful!")
                    else:
                        st.error(f"❌ Conversion failed: {convert_result}")

                if convert_success:
                    with st.spinner("Transcribing audio..."):
                        transcribe_success, transcribe_result = transcription_service.transcribe_audio(file_path, video_id)
                        if transcribe_success:
                            st.success("✅ Audio transcribed successfully!")
                        else:
                            st.warning(f"⚠️ Audio transcribed failed: {transcribe_result}")
                
                    if transcribe_success:  # Only attempt splitting if transcription was successful
                        with st.spinner("Splitting audio into segments..."):
                            split_success, split_result = audio_splitter.split_audio(
                                file_path,
                                video_id,
                                transcription_service.get_excel_path(video_id),
                                'wav'  # Use WAV format for high quality
                            )
                            if split_success:
                                st.success("✅ Audio split successfully!")
                            else:
                                st.warning(f"⚠️ Audio split failed: {split_result}")
                        
                st.rerun()

        elif download_key in st.session_state and st.session_state[download_key]:
            progress_bar = st.progress(0, text="Starting download...")
            result = youtube_service.download_audio(
                video_id,
                progress_callback=lambda p: progress_bar.progress(int(p)/100, text=f"Downloading... {int(p)}%")
            )
            if result['success']:
                progress_bar.empty()
                # Auto-convert to OGG after successful download
                mp3_path = youtube_service.get_audio_path(video_id)
                with st.spinner("Converting to OGG format..."):
                    success, result = audio_service.convert_to_ogg(mp3_path)
                    if success:
                        st.success("✅ Downloaded and converted to OGG")
                    else:
                        st.error(f"❌ OGG conversion failed: {result}")
            
                if success and result:  # Only attempt transcription if conversion was successful
                    # auto transcribe
                    with st.spinner("Transcribing audio... This may take a while."):
                        success, result = transcription_service.transcribe_audio(result, video_id)
                        if success:
                            st.success("✅ Transcription complete!")    
                        else:
                            st.error(f"❌ Transcription failed: {result}")
            
                    if success:  # Only attempt splitting if transcription was successful
                        with st.spinner("Splitting audio into segments..."):
                            split_success, split_result = audio_splitter.split_audio(
                                mp3_path,
                                video_id,
                                transcription_service.get_excel_path(video_id),
                                'wav'  # Use WAV format for high quality
                            )
                            if split_success:
                                st.success("✅ Audio split successfully!")
                            else:
                                st.warning(f"⚠️ Audio split failed: {split_result}")
                        
                st.rerun()
                
        else:
            if st.button("🎵 Download", key=download_key):
                st.session_state[download_key] = True
                st.rerun()

        # Channel, duration and publish date
        st.markdown(f"Channel: {video.get('channel_title', 'Unknown Channel')}")
        st.markdown(f"Duration: {video.get('duration', 'N/A')}")
        st.markdown(f"Published: {format_published_date(video['published_at'])}")
        
        # Description
        description = video['description'][:150] + '...' if len(video['description']) > 150 else video['description']
        st.markdown(f"Description: {description}")
        
        st.markdown("---")
