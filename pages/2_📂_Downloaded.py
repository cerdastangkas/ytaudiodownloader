import streamlit as st
import pandas as pd
import os
from domain.youtube_service import YouTubeService
from domain.data_service import DataService
from domain.audio_service import AudioService
from domain.transcription_service import TranscriptionService
from domain.audio_splitter import AudioSplitter
from domain.config_service import ConfigService
from ui.process_handlers import (
    get_processing_state,
    set_processing_state,
    handle_split_audio,
    handle_transcription,
    handle_conversion
)
import math
from pathlib import Path
import datetime
from utils.date_formatter import format_published_date

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
config_service = ConfigService()
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
    st.session_state.downloaded_per_page = 15

# Title
st.title('📂 Downloaded Videos')

# Database management buttons
st.markdown("### Database Management")
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("📝 Update Downloaded Videos List"):
        total_saved = data_service.update_downloaded_videos_excel()
        st.success(f"✅ Downloaded videos list updated! Found {total_saved} downloaded videos.")

with col2:
    if st.button("🧹 Clean Downloaded Videos List"):
        removed = data_service.clean_downloaded_videos_excel()
        if removed > 0:
            st.warning(f"🗑️ Removed {removed} entries that no longer have audio files.")
        else:
            st.success("✅ No invalid entries found in the downloaded videos list.")

st.markdown("---")

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
    final_result_dir = data_dir / 'final_result'
    
    try:
        # Create directories if they don't exist
        os.makedirs(final_result_dir, exist_ok=True)
        
        # Get list of downloaded audio files from the new directory structure
        downloaded_files = {}
        if final_result_dir.exists():
            for video_dir in final_result_dir.iterdir():
                if video_dir.is_dir():
                    vid_id = video_dir.name
                    audio_file = video_dir / 'original' / f'{vid_id}.mp3'
                    if audio_file.exists():
                        downloaded_files[vid_id] = str(audio_file)
        
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
                video_info['file_name'] = f'{vid_id}.mp3'
                video_info['file_path'] = downloaded_files[vid_id]
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
    """Display a single downloaded file with audio player and processing options."""
    video_id = file_info['id']
    file_path = file_info['file_path']
    grid_position = f"downloaded_{video_id}"
    
    with col:
        if 'thumbnail' in file_info:
            st.image(file_info['thumbnail'], width=None, caption=file_info['title'])

        # Process existing transcription
        existing_transcription = transcription_service.get_transcription(video_id)
        has_wav_splits = audio_splitter.has_wav_splits(video_id)
        has_splits = audio_splitter.has_splits(video_id)
        has_converted = audio_service.get_converted_file(video_id)
        
        if has_wav_splits:
            st.success("✅ Transcription and WAV audio segments are available")
        elif has_splits:
            st.success("✅ Transcription and audio segments available (not WAV)")
        elif existing_transcription:
            st.success("✅ Transcription available")
        elif has_converted:
            st.success("✅ Converted to OGG")
        else:
            st.success("✅ Downloaded")

        # Display audio player
        ogg_file = audio_service.get_converted_file(video_id)
        audio_file = str(ogg_file) if ogg_file else file_path
        file_format = "OGG" if ogg_file else "MP3"
        
        # st.markdown(f"##### 🎵 Audio Player ({file_format})")
        # Add checkbox to load audio
        load_audio = st.checkbox(f"🎵 Load Audio Player ({file_format})", key=f"load_{video_id}")
        if load_audio:
            st.audio(audio_file)
        
        # st.markdown(f"### {file_info['title']}")
        st.markdown(f"**Channel:** {file_info['channel_title']}")
        st.markdown(f"**Duration:** {file_info['duration']}")
        st.markdown(f"**Video ID:** {video_id}")
        
        if 'published_at' in file_info:
            st.markdown(f"**Published:** {file_info['published_at']}")
        
        # Process existing transcription
        # existing_transcription = transcription_service.get_transcription(video_id)
        
        if existing_transcription:
            if not has_wav_splits:             
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
                
        else:
            # Handle convert button and processing
            if not get_processing_state(video_id, grid_position, "convert"):
                if st.button("🔄 Convert to OGG", key=f"convert_{video_id}_{grid_position}"):
                    set_processing_state(video_id, grid_position, "convert", True)
                    st.rerun()
            
            if get_processing_state(video_id, grid_position, "convert"):
                handle_conversion(video_id, file_path, grid_position, audio_service, 
                               transcription_service, audio_splitter)
        
        # Display file size
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        st.markdown(f"**Size:** {file_size:.1f} MB")
        
        st.divider()

if not downloaded_videos:
    st.info("❌ No downloaded files found. Go to Search page to download some audio!")
else:
    display_stats(downloaded_videos)
    
    # Calculate pagination
    total_pages = math.ceil(len(downloaded_videos) / st.session_state.downloaded_per_page)
    start_idx = (st.session_state.downloaded_page - 1) * st.session_state.downloaded_per_page
    end_idx = start_idx + st.session_state.downloaded_per_page
    current_videos = downloaded_videos[start_idx:end_idx]
    
    # Display videos in grid
    cols = st.columns(3)
    for i, video in enumerate(current_videos):
        display_downloaded_file(video, cols[i % 3])
    
    # Pagination controls
    if total_pages > 1:
        cols = st.columns([1, 3, 1])
        
        # Previous page button
        with cols[0]:
            if st.session_state.downloaded_page > 1:
                if st.button("← Previous"):
                    st.session_state.downloaded_page -= 1
                    st.rerun()
        
        # Page indicator
        with cols[1]:
            st.markdown(f"""
                <div class="pagination-text">
                    Page {st.session_state.downloaded_page} of {total_pages}
                </div>
            """, unsafe_allow_html=True)
        
        # Next page button
        with cols[2]:
            if st.session_state.downloaded_page < total_pages:
                if st.button("Next →"):
                    st.session_state.downloaded_page += 1
                    st.rerun()
