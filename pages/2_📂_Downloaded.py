import streamlit as st
import pandas as pd
import os
from domain.youtube_service import YouTubeService
from domain.data_service import DataService
from domain.audio_service import AudioService
from domain.transcription_service import TranscriptionService
from domain.audio_splitter import AudioSplitter
import math
from pathlib import Path
import datetime
from utils.date_formatter import format_published_date
from domain.audio_splitter import AudioSplitter

# Page config
st.set_page_config(
    page_title='Downloaded Files',
    page_icon='📂',
    layout='wide'
)

# Check for API key
if 'openai_api_key' not in st.session_state or not st.session_state.openai_api_key:
    st.error("⚠️ Please set your OpenAI API key in the main page first!")
    st.stop()

# Initialize services
youtube_service = YouTubeService(os.getenv('YOUTUBE_API_KEY'))
data_service = DataService()
audio_service = AudioService()
transcription_service = TranscriptionService(api_key=st.session_state.openai_api_key)
audio_splitter = AudioSplitter()

# Custom CSS
st.markdown("""
    <style>
    .pagination-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
    }
    .pagination-text {
        text-align: center;
        font-size: 1rem;
        color: #31333F;
    }
    .audio-controls {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .file-info {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for pagination
if 'downloaded_page' not in st.session_state:
    st.session_state.downloaded_page = 1
if 'downloaded_per_page' not in st.session_state:
    st.session_state.downloaded_per_page = 9

# Title
st.title('📂 Downloaded Files')
st.markdown('View, play, and manage your downloaded audio files')

# Add cleanup button in sidebar
with st.sidebar:
    if st.button("🧹 Clean Database", help="Remove entries from database that don't have corresponding audio files"):
        initial_count, final_count = data_service.clean_excel_data()
        removed = initial_count - final_count
        if removed > 0:
            st.success(f"Removed {removed} entries from database that don't have audio files")
        else:
            st.info("Database is already clean!")

# Function to get downloaded videos
def get_downloaded_videos():
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    excel_file = data_dir / 'youtube_videos.xlsx'
    downloaded_dir = data_dir / 'downloaded'
    
    try:
        # Create directories if they don't exist
        os.makedirs(downloaded_dir, exist_ok=True)
        
        # Get list of downloaded audio files
        downloaded_files = {
            f.split('.')[0]: f 
            for f in os.listdir(downloaded_dir) 
            if f.endswith('.mp3')
        }
        
        if not downloaded_files:
            st.info('No audio files have been downloaded yet. Go to the Search page to download some videos!')
            return []
        
        # Load Excel data
        try:
            df = pd.read_excel(excel_file)
        except FileNotFoundError:
            st.warning('YouTube videos database not found. Downloaded files may not have complete information.')
            return [{'id': vid_id, 'title': 'Unknown Title'} for vid_id in downloaded_files.keys()]
        
        # Filter for downloaded videos only
        downloaded_videos = []
        for _, row in df.iterrows():
            vid_id = str(row['id'])
            if vid_id in downloaded_files:
                video_info = row.to_dict()
                video_info['file_name'] = downloaded_files[vid_id]
                video_info['file_path'] = os.path.join(downloaded_dir, downloaded_files[vid_id])
                downloaded_videos.append(video_info)
        
        return downloaded_videos
        
    except Exception as e:
        st.error(f'Error loading downloaded videos: {str(e)}')
        return []

# Get downloaded videos
downloaded_videos = get_downloaded_videos()

def display_stats(df):
    """Display statistics about downloaded files"""
    total_files = len(df)
    
    # Calculate total size
    total_size_mb = sum(os.path.getsize(file_info['file_path']) / (1024 * 1024) 
                       for file_info in df 
                       if os.path.exists(file_info['file_path']))
    
    # Calculate total duration in seconds
    total_duration_sec = sum(duration_to_seconds(file_info['duration']) 
                           for file_info in df)
    
    # Convert total duration to hours:minutes:seconds
    hours = total_duration_sec // 3600
    minutes = (total_duration_sec % 3600) // 60
    seconds = total_duration_sec % 60
    
    # Create three columns for stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Files", f"{total_files:,}")
    with col2:
        st.metric("Total Size", f"{total_size_mb:.1f} MB")
    with col3:
        st.metric("Total Duration", f"{int(hours)}h {int(minutes)}m {int(seconds)}s")
    
    st.markdown("---")

def duration_to_seconds(duration_str):
    """Convert duration string (HH:MM:SS) to seconds"""
    try:
        # Handle different duration formats
        if ':' not in duration_str:
            return 0
        
        parts = duration_str.split(':')
        if len(parts) == 3:  # HH:MM:SS
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + int(s)
        elif len(parts) == 2:  # MM:SS
            m, s = parts
            return int(m) * 60 + int(s)
        else:
            return 0
    except:
        return 0

def display_downloaded_file(file_info, col):
    with col:
        if 'thumbnail' in file_info:
            st.image(file_info['thumbnail'], width=None)
        
        st.markdown(f"### {file_info['title']}")
        st.markdown(f"**Video ID:** {file_info['id']}")
        st.markdown(f"**Channel:** {file_info['channel_title']}")
        st.markdown(f"**Duration:** {file_info['duration']}")
        
        if 'published_at' in file_info:
            st.markdown(f"**Published:** {file_info['published_at']}")
        
        ogg_file = audio_service.get_converted_file(file_info['id'])
        audio_file = str(ogg_file) if ogg_file else file_info['file_path']
        file_format = "OGG" if ogg_file else "MP3"
        
        st.markdown(f"##### 🎵 Audio Player ({file_format})")
        st.audio(audio_file)
        
        file_size = os.path.getsize(file_info['file_path']) / (1024 * 1024)
        st.markdown(f"**Size:** {file_size:.1f} MB")
        
        # Check if transcription exists
        existing_transcription = transcription_service.get_transcription(file_info['id'])
        
        if existing_transcription:
            st.success("✅ Transcription available")            
            if st.button("📝 View Transcription", key=f"view_transcription_{file_info['id']}"):
                st.switch_page("pages/3_📝_Transcriptions.py")
            
            # Check if audio is already split
            has_splits = audio_splitter.is_already_split(file_info['id'])
            if not has_splits:
                if st.button("✂️ Split Audio", key=f"split_audio_{file_info['id']}"):
                    with st.spinner("Splitting audio based on transcription..."):
                        success, result = audio_splitter.split_audio(
                            file_info['file_path'], 
                            file_info['id'],
                            transcription_service.get_excel_path(file_info['id']),
                            'wav'  # Use WAV format for high quality
                        )
                        if success:
                            st.success("✅ Audio split successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to split audio: {result}")
            else:
                st.info("✅ Audio already split into segments")
                
        elif ogg_file:
            if st.button("🎯 Transcribe", key=f"transcribe_{file_info['id']}"):
                with st.spinner("Transcribing audio... This may take a while."):
                    success, result = transcription_service.transcribe_audio(ogg_file, file_info['id'])
                    if success:
                        st.success("✅ Transcription complete!")
                        # Automatically split audio after successful transcription
                        with st.spinner("Splitting audio into segments..."):
                            split_success, split_result = audio_splitter.split_audio(
                                file_info['file_path'],
                                file_info['id'],
                                transcription_service.get_excel_path(file_info['id']),
                                'wav'  # Use WAV format for high quality
                            )
                            if split_success:
                                st.success("✅ Audio split successfully!")
                            else:
                                st.warning(f"⚠️ Audio split failed: {split_result}")
                        st.rerun()
                    else:
                        st.error(f"❌ Transcription failed: {result}")
        else:
            if st.button("🔄 Convert to OGG", key=f"convert_{file_info['id']}"):
                with st.spinner("Converting to OGG format..."):
                    success, result = audio_service.convert_to_ogg(file_info['file_path'])
                    if success:
                        st.success("✅ Conversion successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ Conversion failed: {result}")

        if st.button(f"🗑️ Delete", key=f"delete_{file_info['id']}"):
            try:
                os.remove(file_info['file_path'])
                if ogg_file:
                    os.remove(ogg_file)
                transcription_path = transcription_service.get_excel_path(file_info['id'])
                if os.path.exists(transcription_path):
                    os.remove(transcription_path)
                splits_dir = audio_splitter.get_splits_directory(file_info['id'])
                if splits_dir.exists():
                    for split_file in splits_dir.glob('*.ogg'):
                        os.remove(split_file)
                    os.rmdir(splits_dir)
                st.success("File deleted successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting file: {str(e)}")
        
        st.markdown("---")

if not downloaded_videos:
    st.info("No downloaded files found. Go to Search page to download some audio!")
else:
    display_stats(downloaded_videos)
    total_files = len(downloaded_videos)
    total_pages = math.ceil(total_files / st.session_state.downloaded_per_page)
    
    # Calculate start and end indices for current page
    start_idx = (st.session_state.downloaded_page - 1) * st.session_state.downloaded_per_page
    end_idx = start_idx + st.session_state.downloaded_per_page
    
    # Display current page files in grid
    current_videos = downloaded_videos[start_idx:end_idx]
    cols = st.columns(3)
    for i, video in enumerate(current_videos):
        display_downloaded_file(video, cols[i % 3])
    
    # Pagination controls
    if total_pages > 1:
        cols = st.columns([1, 3, 1])
        
        # Previous page button
        with cols[0]:
            if st.session_state.downloaded_page > 1:
                if st.button("← Previous", use_container_width=True):
                    st.session_state.downloaded_page -= 1
                    st.rerun()
            else:
                st.write("")
        
        # Page indicator
        with cols[1]:
            st.markdown(
                f'<div style="text-align: center;">Page {st.session_state.downloaded_page} of {total_pages}</div>',
                unsafe_allow_html=True
            )
        
        # Next page button
        with cols[2]:
            if st.session_state.downloaded_page < total_pages:
                if st.button("Next →", use_container_width=True):
                    st.session_state.downloaded_page += 1
                    st.rerun()
            else:
                st.write("")
