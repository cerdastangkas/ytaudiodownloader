import streamlit as st
from domain.youtube_service import YouTubeService
from domain.audio_service import AudioService
from utils.date_formatter import format_published_date
from domain.transcription_service import TranscriptionService
from domain.audio_splitter import AudioSplitter

def display_video_card(video: dict, youtube_service: YouTubeService, grid_position: str):
    """Display a single video card with download functionality"""
    # Initialize audio service
    audio_service = AudioService()
    transcription_service = TranscriptionService(api_key=st.session_state.openai_api_key)
    audio_splitter = AudioSplitter()
    
    with st.container():
        # Add debug info
        print(f"[DEBUG] Displaying video card for ID: {video['id']} at position {grid_position}")
        print(f"[DEBUG] Video title: {video.get('title', 'Unknown Title')}")
        
        # Card container with fixed height and scrollable content
        with st.container():
            # Thumbnail with fixed dimensions
            if 'thumbnail' in video:
                st.image(video['thumbnail'], use_container_width=True)
            
            # Video title as a link (limit length)
            title = video.get('title', 'Unknown Title')
            if len(title) > 60:
                title = title[:57] + "..."
            st.markdown(f"### [{title}](https://youtube.com/watch?v={video['id']})")
            
            # Channel and duration info
            st.markdown(f"**Video ID:** {video.get('id', 'Unknown')}")
            st.markdown(f"**Channel:** {video.get('channel_title', 'Unknown Channel')}")
            st.markdown(f"**Duration:** {video.get('duration', 'Unknown')}")
            
            # Download controls
            video_id = video['id']
            download_key = f"download_{video_id}_{grid_position}"
            split_key = f"split_{video_id}_{grid_position}"
            transcribe_key = f"transcribe_{video_id}_{grid_position}"
            convert_key = f"convert_{video_id}_{grid_position}"
            view_transcription_key = f"view_transcription_{video_id}_{grid_position}"
            
            file_path = youtube_service.get_audio_path(video_id)
            
            # Initialize success flags
            transcribe_success = False
            convert_success = False
            
            # Check if transcription exists
            existing_transcription = transcription_service.get_transcription(video_id)
            
            if existing_transcription:
                st.success("✅ Transcription available")
                # Check if audio is already split
                has_splits = audio_splitter.is_already_split(video_id)
                
                if has_splits:
                    st.info("✅ Audio segments are available")
                else:
                    # Initialize split processing state if not exists
                    split_processing_key = f"split_processing_{video_id}_{grid_position}"
                    if split_processing_key not in st.session_state:
                        st.session_state[split_processing_key] = False
                    
                    # Only show split button if not processing
                    if not st.session_state[split_processing_key]:
                        if st.button("✂️ Split Audio", key=f"{split_key}_{grid_position}"):
                            st.session_state[split_processing_key] = True
                            st.rerun()
                    
                    # If processing, show the split operation
                    if st.session_state[split_processing_key]:
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
                            
                            # Reset processing state after completion
                            st.session_state[split_processing_key] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ An error occurred: {str(e)}")
                            st.session_state[split_processing_key] = False
                            st.rerun()
                
                if st.button("📝 View Transcription", key=view_transcription_key):
                    st.session_state['selected_video_id'] = video_id
                    st.switch_page("pages/3_📝_Transcriptions.py")
                    
            elif audio_service.get_converted_file(video_id):
                st.success("✅ Converted to OGG")
                # Initialize transcribe processing state if not exists
                transcribe_processing_key = f"transcribe_processing_{video_id}_{grid_position}"
                if transcribe_processing_key not in st.session_state:
                    st.session_state[transcribe_processing_key] = False
                
                # Only show transcribe button if not processing
                if not st.session_state[transcribe_processing_key]:
                    if st.button("🎯 Transcribe", key=f"{transcribe_key}_{grid_position}"):
                        st.session_state[transcribe_processing_key] = True
                        st.rerun()
                
                # If processing, show the transcription operation
                if st.session_state[transcribe_processing_key]:
                    try:
                        # Step 2: Transcribe audio (only if conversion was successful)
                        transcribe_success = False
                        with st.spinner("Transcribing audio..."):
                            transcribe_success, transcribe_result = transcription_service.transcribe_audio(file_path, video_id)
                            if transcribe_success:
                                st.success("✅ Audio transcribed successfully!")
                            else:
                                st.warning(f"⚠️ Audio transcription failed: {transcribe_result}")
                        
                        # Step 3: Split audio (only if transcription was successful)
                        if transcribe_success:
                            with st.spinner("Splitting audio into segments..."):
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
                        
                        # Reset processing state after completion
                        st.session_state[transcribe_processing_key] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
                        st.session_state[transcribe_processing_key] = False
                        st.rerun()
                    
            elif youtube_service.is_audio_downloaded(video_id):
                st.success("✅ Downloaded")
                # Initialize processing state if not exists
                processing_key = f"processing_{video_id}_{grid_position}"
                if processing_key not in st.session_state:
                    st.session_state[processing_key] = False
                
                # Only show button if not processing
                if not st.session_state[processing_key]:
                    if st.button("🔄 Convert to OGG", key=f"{convert_key}_{grid_position}"):
                        st.session_state[processing_key] = True
                        st.rerun()
                
                # If processing, show the conversion steps
                if st.session_state[processing_key]:
                    try:
                        # Step 1: Convert to OGG
                        convert_success = False
                        with st.spinner("Converting to OGG format..."):
                            convert_success, convert_result = audio_service.convert_to_ogg(file_path)
                            if convert_success:
                                st.success("✅ Conversion successful!")
                            else:
                                st.error(f"❌ Conversion failed: {convert_result}")
                                st.session_state[processing_key] = False
                                st.rerun()
                        
                        # Step 2: Transcribe audio (only if conversion was successful)
                        transcribe_success = False
                        if convert_success:
                            with st.spinner("Transcribing audio..."):
                                transcribe_success, transcribe_result = transcription_service.transcribe_audio(file_path, video_id)
                                if transcribe_success:
                                    st.success("✅ Audio transcribed successfully!")
                                else:
                                    st.warning(f"⚠️ Audio transcription failed: {transcribe_result}")
                                    st.session_state[processing_key] = False
                                    st.rerun()
                        
                        # Step 3: Split audio (only if transcription was successful)
                        if transcribe_success:
                            with st.spinner("Splitting audio into segments..."):
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
                        
                        # Reset processing state after completion
                        st.session_state[processing_key] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
                        st.session_state[processing_key] = False
                        st.rerun()
                    
            elif download_key in st.session_state and st.session_state[download_key]:
                # Step 1: Download audio
                progress_bar = st.progress(0, text="Starting download...")
                result = youtube_service.download_audio(
                    video_id,
                    progress_callback=lambda p: progress_bar.progress(int(p)/100, text=f"Downloading... {int(p)}%")
                )
                
                if not result['success']:
                    progress_bar.empty()
                    st.error("❌ Download failed")
                    st.rerun()
                
                progress_bar.empty()
                mp3_path = youtube_service.get_audio_path(video_id)
                
                # Step 2: Convert to OGG
                convert_success = False
                with st.spinner("Converting to OGG format..."):
                    convert_success, convert_result = audio_service.convert_to_ogg(mp3_path)
                    if convert_success:
                        st.success("✅ Downloaded and converted to OGG")
                    else:
                        st.error(f"❌ OGG conversion failed: {convert_result}")
                        st.rerun()
                
                # Step 3: Transcribe audio
                transcribe_success = False
                if convert_success:
                    with st.spinner("Transcribing audio..."):
                        transcribe_success, transcribe_result = transcription_service.transcribe_audio(file_path, video_id)
                        if transcribe_success:
                            st.success("✅ Audio transcribed successfully!")
                        else:
                            st.warning(f"⚠️ Audio transcription failed: {transcribe_result}")
                            st.rerun()
                
                # Step 4: Split audio
                if transcribe_success:
                    with st.spinner("Splitting audio into segments..."):
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
                
                st.rerun()
            else:
                # Initialize download processing state if not exists
                download_processing_key = f"download_processing_{video_id}_{grid_position}"
                if download_processing_key not in st.session_state:
                    st.session_state[download_processing_key] = False
                
                # Only show download button if not processing
                if not st.session_state[download_processing_key]:
                    if st.button("🎵 Download", key=f"{download_key}_{grid_position}"):
                        st.session_state[download_processing_key] = True
                        st.rerun()
                
                # If processing, show the download steps
                if st.session_state[download_processing_key]:
                    try:
                        # Step 1: Download audio
                        progress_bar = st.progress(0, text="Starting download...")
                        result = youtube_service.download_audio(
                            video_id,
                            progress_callback=lambda p: progress_bar.progress(int(p)/100, text=f"Downloading... {int(p)}%")
                        )
                        
                        if not result['success']:
                            progress_bar.empty()
                            st.error("❌ Download failed")
                            st.session_state[download_processing_key] = False
                            st.rerun()
                        
                        progress_bar.empty()
                        mp3_path = youtube_service.get_audio_path(video_id)
                        
                        # Step 2: Convert to OGG
                        convert_success = False
                        with st.spinner("Converting to OGG format..."):
                            convert_success, convert_result = audio_service.convert_to_ogg(mp3_path)
                            if convert_success:
                                st.success("✅ Downloaded and converted to OGG")
                            else:
                                st.error(f"❌ OGG conversion failed: {convert_result}")
                                st.session_state[download_processing_key] = False
                                st.rerun()
                        
                        # Step 3: Transcribe audio
                        transcribe_success = False
                        if convert_success:
                            with st.spinner("Transcribing audio..."):
                                transcribe_success, transcribe_result = transcription_service.transcribe_audio(file_path, video_id)
                                if transcribe_success:
                                    st.success("✅ Audio transcribed successfully!")
                                else:
                                    st.warning(f"⚠️ Audio transcription failed: {transcribe_result}")
                                    st.session_state[download_processing_key] = False
                                    st.rerun()
                        
                        # Step 4: Split audio
                        if transcribe_success:
                            with st.spinner("Splitting audio into segments..."):
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
                        
                        # Reset processing state after completion
                        st.session_state[download_processing_key] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
                        st.session_state[download_processing_key] = False
                        st.rerun()
            
            # Published date
            st.markdown(f"**Published:** {format_published_date(video['published_at'])}")
            
            # Description
            description = video['description'][:150] + '...' if len(video['description']) > 150 else video['description']
            st.markdown(f"**Description:** {description}")
            
            st.markdown("---")
