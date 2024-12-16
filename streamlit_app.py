import streamlit as st
import os
from domain.youtube_service import YouTubeService
from dotenv import load_dotenv
import math
import pandas as pd
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Get API key from environment variables
api_key = os.getenv('YOUTUBE_API_KEY')
if not api_key:
    st.error('YouTube API key not found in environment variables. Please check your .env file.')
    st.stop()

# Initialize YouTube Service
youtube_service = YouTubeService(api_key)

# Page config
st.set_page_config(
    page_title='YouTube Video Search',
    page_icon='🎥',
    layout='wide'
)

# Initialize session state for pagination
if 'page_token' not in st.session_state:
    st.session_state.page_token = None
if 'search_params' not in st.session_state:
    st.session_state.search_params = None
if 'all_videos' not in st.session_state:
    st.session_state.all_videos = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'videos_per_page' not in st.session_state:
    st.session_state.videos_per_page = 9

# Initialize session state for downloads if not exists
if 'download_states' not in st.session_state:
    st.session_state.download_states = {}

def update_progress(video_id, progress):
    """Update download progress in session state"""
    if video_id in st.session_state.download_states:
        st.session_state.download_states[video_id]['progress'] = progress

# Function to load existing Excel data
def load_excel_data(file_path):
    try:
        df = pd.read_excel(file_path)
        return df.to_dict('records')
    except FileNotFoundError:
        return []
    except Exception as e:
        st.error(f"Error loading Excel file: {str(e)}")
        return []

# Function to format published date
def format_published_date(date_str):
    """Convert ISO date to human readable format"""
    try:
        date = pd.to_datetime(date_str)
        now = pd.Timestamp.now(tz=date.tz)
        diff = now - date
        
        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago"
            return f"{hours} hours ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} weeks ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} months ago"
        else:
            years = diff.days // 365
            return f"{years} years ago"
    except:
        return date_str[:10]  # Fallback to YYYY-MM-DD format

# Function to save videos to Excel
def save_videos_to_excel(videos, file_path):
    try:
        # Convert videos to DataFrame and format dates for Excel
        df = pd.DataFrame(videos)
        
        # Load existing data
        existing_data = []
        try:
            existing_df = pd.read_excel(file_path)
            # Convert existing dates to timezone-aware
            existing_df['published_at'] = pd.to_datetime(existing_df['published_at']).dt.tz_localize('UTC')
            existing_data = existing_df.to_dict('records')
        except FileNotFoundError:
            pass
        
        # Combine existing and new data, removing duplicates based on video ID
        all_data = existing_data + videos
        df_all = pd.DataFrame(all_data).drop_duplicates(subset=['id'])
        
        # Convert all published_at to human readable format
        df_all['published_at'] = pd.to_datetime(df_all['published_at'])
        df_all['published_date'] = df_all['published_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_all = df_all.sort_values('published_at', ascending=False)
        
        # Drop the timezone-aware column and rename the formatted one
        df_all = df_all.drop(columns=['published_at'])
        df_all = df_all.rename(columns={'published_date': 'published_at'})
        
        # Save to Excel
        df_all.to_excel(file_path, index=False)
        return len(df_all)
    except Exception as e:
        st.error(f"Error saving to Excel: {str(e)}")
        return 0

# Add custom CSS
st.markdown("""
    <style>
    .stVideo {
        width: 100%;
    }
    .video-container {
        margin-bottom: 2rem;
    }
    .pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title('🎥 YouTube Video Search')
st.markdown('Search for YouTube videos by license type')

# Search interface
with st.form('search_form'):
    # Search query (optional)
    query = st.text_input('Search query (optional - leave empty to browse recent videos)')
    
    # License type selection
    license_types = youtube_service.get_license_types()
    selected_license = st.selectbox(
        'Select License Type',
        options=[''] + list(license_types.keys()),
        format_func=lambda x: 'All Licenses' if x == '' else license_types.get(x, x)
    )
    
    col1, col2 = st.columns([3, 1])
    with col2:
        st.session_state.videos_per_page = st.selectbox(
            'Videos per page',
            options=[6, 9, 12, 15],
            index=1
        )
    
    # Search button
    search_submitted = st.form_submit_button('Search Videos')

# Excel file path
excel_file = 'youtube_videos.xlsx'

# Handle new search
if search_submitted:
    st.session_state.page_token = None
    st.session_state.all_videos = []
    st.session_state.current_page = 1
    st.session_state.search_params = {
        'query': query if query else None,
        'license_type': selected_license if selected_license else None
    }

# Process search
if st.session_state.search_params is not None:
    with st.spinner('Searching for videos...'):
        # Get the next batch of videos if needed
        if len(st.session_state.all_videos) < st.session_state.current_page * st.session_state.videos_per_page:
            result = youtube_service.search_videos(
                query=st.session_state.search_params['query'],
                license_type=st.session_state.search_params['license_type'],
                page_token=st.session_state.page_token
            )
            
            # Add new videos to the list
            st.session_state.all_videos.extend(result['videos'])
            st.session_state.page_token = result['nextPageToken']
            
            # Save to Excel
            total_saved = save_videos_to_excel(result['videos'], excel_file)
            if total_saved > 0:
                st.success(f"✅ Saved {len(result['videos'])} new videos to Excel. Total unique videos: {total_saved}")
        
        # Calculate pagination
        total_videos = len(st.session_state.all_videos)
        total_pages = math.ceil(total_videos / st.session_state.videos_per_page)
        start_idx = (st.session_state.current_page - 1) * st.session_state.videos_per_page
        end_idx = start_idx + st.session_state.videos_per_page
        current_videos = st.session_state.all_videos[start_idx:end_idx]
        
        # Display total results
        if total_videos > 0:
            st.success(f'Found {total_videos} videos')
            
            # Add Excel download button
            if os.path.exists(excel_file):
                with open(excel_file, 'rb') as f:
                    st.download_button(
                        label="📥 Download Excel file",
                        data=f,
                        file_name='youtube_videos.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
            
            # Display current page videos in a grid
            cols = st.columns(3)
            for idx, video in enumerate(current_videos):
                with cols[idx % 3]:
                    with st.container():
                        # Thumbnail
                        st.image(video['thumbnail'], use_container_width=True)
                        
                        # Video title as a link
                        st.markdown(f"### [{video['title']}](https://youtube.com/watch?v={video['id']})")
                        
                        # Channel, duration and publish date
                        st.markdown(f"Channel: {video['channel_title']}")
                        st.markdown(f"Duration: {video.get('duration', 'N/A')}")
                        st.markdown(f"Published: {format_published_date(video['published_at'])}")
                        
                        # Description
                        description = video['description'][:150] + '...' if len(video['description']) > 150 else video['description']
                        st.markdown(f"Description: {description}")
                        
                        # Download controls
                        video_id = video['id']
                        download_key = f"download_{video_id}"
                        
                        if youtube_service.is_audio_downloaded(video_id):
                            st.success("✅ Downloaded")
                        elif download_key in st.session_state and st.session_state[download_key]:
                            progress_bar = st.progress(0, text="Starting download...")
                            result = youtube_service.download_audio(
                                video_id,
                                progress_callback=lambda p: progress_bar.progress(int(p)/100, text=f"Downloading... {int(p)}%")
                            )
                            if result['success']:
                                st.success("✅ Downloaded")
                                st.session_state[download_key] = False
                                st.rerun()
                        else:
                            if st.button("🎵 Download", key=download_key):
                                st.session_state[download_key] = True
                                st.rerun()
                        
                        st.markdown("---")
            
            # Pagination controls
            st.markdown('<div class="pagination">', unsafe_allow_html=True)
            cols = st.columns([1, 1, 2, 1, 1])
            
            # Previous page button
            with cols[0]:
                if st.session_state.current_page > 1:
                    if st.button('← Previous'):
                        st.session_state.current_page -= 1
                        st.rerun()
            
            # Current page indicator
            with cols[2]:
                st.markdown(f'<div style="text-align: center;">Page {st.session_state.current_page} of {total_pages}</div>', unsafe_allow_html=True)
            
            # Next page button
            with cols[4]:
                if st.session_state.current_page < total_pages or st.session_state.page_token:
                    if st.button('Next →'):
                        st.session_state.current_page += 1
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning('No videos found. Try adjusting your search criteria.')
