import streamlit as st
import pandas as pd
import os
from domain.youtube_service import YouTubeService
from domain.data_service import DataService
from utils.date_formatter import format_published_date
import math

# Page config
st.set_page_config(
    page_title='Downloaded Videos',
    page_icon='📂',
    layout='wide'
)

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
    </style>
""", unsafe_allow_html=True)

# Initialize services
youtube_service = YouTubeService(os.getenv('YOUTUBE_API_KEY'))
data_service = DataService()

# Initialize session state for pagination
if 'downloaded_page' not in st.session_state:
    st.session_state.downloaded_page = 1
if 'downloaded_per_page' not in st.session_state:
    st.session_state.downloaded_per_page = 9

# Title
st.title('📂 Downloaded Files')
st.markdown('View and manage your downloaded audio files')

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
    excel_file = 'youtube_videos.xlsx'
    downloaded_dir = os.path.join('data', 'downloaded')
    
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

if not downloaded_videos:
    st.info("No downloaded files found. Go to Search page to download some audio!")
else:
    total_files = len(downloaded_videos)
    total_pages = math.ceil(total_files / st.session_state.downloaded_per_page)
    
    # Calculate start and end indices for current page
    start_idx = (st.session_state.downloaded_page - 1) * st.session_state.downloaded_per_page
    end_idx = start_idx + st.session_state.downloaded_per_page
    
    # Display current page files in grid
    current_videos = downloaded_videos[start_idx:end_idx]
    cols = st.columns(3)
    for i, video in enumerate(current_videos):
        with cols[i % 3]:
            with st.container():
                # Video title and thumbnail if available
                if 'thumbnail' in video:
                    st.image(video['thumbnail'], use_container_width=True)
                st.markdown(f"### {video.get('title', 'Unknown Title')}")
                
                # Video details if available
                if 'channel_title' in video:
                    st.markdown(f"Channel: {video['channel_title']}")
                if 'duration' in video:
                    st.markdown(f"Duration: {video['duration']}")
                if 'published_at' in video:
                    st.markdown(f"Published: {format_published_date(video['published_at'])}")
                
                # File details and actions
                file_size = os.path.getsize(video['file_path']) / (1024 * 1024)  # Convert to MB
                st.markdown(f"File size: {file_size:.1f} MB")
                
                # Download button
                with open(video['file_path'], 'rb') as f:
                    st.download_button(
                        label="🎵 Download MP3",
                        data=f,
                        file_name=video['file_name'],
                        mime='audio/mpeg'
                    )
                
                # Delete button
                if st.button('🗑️ Delete', key=f"delete_{video['id']}"):
                    try:
                        os.remove(video['file_path'])
                        st.success('File deleted successfully!')
                        st.rerun()
                    except Exception as e:
                        st.error(f'Error deleting file: {str(e)}')
                
                st.markdown("---")

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
                st.write("")  # Placeholder for alignment
        
        # Page indicator
        with cols[1]:
            st.markdown(
                f'<div class="pagination-text">Page {st.session_state.downloaded_page} of {total_pages}</div>',
                unsafe_allow_html=True
            )
        
        # Next page button
        with cols[2]:
            if st.session_state.downloaded_page < total_pages:
                if st.button("Next →", use_container_width=True):
                    st.session_state.downloaded_page += 1
                    st.rerun()
            else:
                st.write("")  # Placeholder for alignment
