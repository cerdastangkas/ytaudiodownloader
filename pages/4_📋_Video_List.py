import streamlit as st
import pandas as pd
import os
from pathlib import Path
from domain.data_service import DataService
from domain.youtube_service import YouTubeService
from utils.date_formatter import format_published_date
import math

# Page config
st.set_page_config(
    page_title='Video List',
    page_icon='📋',
    layout='wide'
)

# Initialize services
data_service = DataService()
youtube_service = YouTubeService(os.getenv('YOUTUBE_API_KEY'))

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
    .stButton button {
        width: 100%;
    }
    .delete-warning {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .delete-warning .warning-text {
        flex-grow: 1;
    }
    .delete-warning .warning-buttons {
        display: flex;
        gap: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session states
if 'list_page' not in st.session_state:
    st.session_state.list_page = 1
if 'list_per_page' not in st.session_state:
    st.session_state.list_per_page = 15
if 'sort_by' not in st.session_state:
    st.session_state.sort_by = 'published_at'
if 'sort_order' not in st.session_state:
    st.session_state.sort_order = 'desc'
if 'show_delete_dialog' not in st.session_state:
    st.session_state.show_delete_dialog = False
if 'video_to_delete' not in st.session_state:
    st.session_state.video_to_delete = None
if 'video_to_delete_title' not in st.session_state:
    st.session_state.video_to_delete_title = None
if 'download_states' not in st.session_state:
    st.session_state.download_states = {}
if 'channel_filter' not in st.session_state:
    st.session_state.channel_filter = "All Channels"

# Title
st.title('📋 Video List')
st.markdown('View and manage your saved YouTube videos')

def duration_to_seconds(duration_str):
    """Convert duration string (HH:MM:SS or MM:SS) to seconds"""
    try:
        parts = duration_str.split(':')
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    except:
        return 0

def get_video_list():
    """Get the list of videos from Excel file"""
    try:
        df = pd.read_excel(data_service.videos_excel)
        # Print column names for debugging
        print("Available columns:", df.columns.tolist())
        
        # Add duration_seconds column for sorting
        df['duration_seconds'] = df['duration'].apply(duration_to_seconds)
        return df
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        return pd.DataFrame()

def display_stats(df):
    """Display statistics about the video list"""
    if df.empty:
        return
    
    total_videos = len(df)
    total_duration = df['duration'].apply(lambda x: sum(int(i) * 60 ** idx for idx, i in enumerate(reversed(str(x).split(':'))))).sum()
    unique_channels = df['channel_title'].nunique()
    
    # Convert total duration to hours:minutes:seconds
    hours = total_duration // 3600
    minutes = (total_duration % 3600) // 60
    seconds = total_duration % 60
    
    # Create three columns for stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Videos", f"{total_videos:,}")
    with col2:
        st.metric("Total Duration", f"{int(hours)}h {int(minutes)}m {int(seconds)}s")
    with col3:
        st.metric("Unique Channels", f"{unique_channels:,}")
    
    st.markdown("---")

def display_video_info(video, col):
    """Display a single video with its information and action buttons"""
    with col:
        with st.container():
            # Video thumbnail and title
            st.image(video['thumbnail'], use_container_width=True)
            st.markdown(f"#### {video['title']}")
            
            # Channel and metadata
            st.markdown(f"**Channel:** {video['channel_title']}")
            st.markdown(f"**Duration:** {video['duration']}")
            published_date = pd.to_datetime(video['published_at']).strftime('%Y-%m-%d')
            st.markdown(f"**Published:** {published_date}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🎵 Download", key=f"download_{video['id']}"):
                    st.session_state.download_states[video['id']] = 'downloading'
                    youtube_service.download_audio(video['id'], video['title'])
            
            with col2:
                if st.button("🔗 Watch", key=f"watch_{video['id']}"):
                    video_url = f"https://www.youtube.com/watch?v={video['id']}"
                    st.markdown(f'<a href="{video_url}" target="_blank">Open in YouTube</a>', unsafe_allow_html=True)
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{video['id']}", type="secondary"):
                    st.session_state.video_to_delete = video['id']
                    st.session_state.video_to_delete_title = video['title']
                    st.session_state.show_delete_dialog = True
                    st.rerun()
            
            # Show delete confirmation if this is the video being deleted
            if st.session_state.show_delete_dialog and st.session_state.video_to_delete == video['id']:
                st.markdown("""
                    <div style="flex-grow: 1;">⚠️ Delete this video?</div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✅ Yes", key=f"confirm_delete_{video['id']}", type="primary", use_container_width=True):
                        if data_service.delete_video(video['id']):
                            st.success("Video deleted successfully!")
                            st.session_state.show_delete_dialog = False
                            st.session_state.video_to_delete = None
                            st.session_state.video_to_delete_title = None
                            st.rerun()
                        else:
                            st.error("Failed to delete video.")
                with col2:
                    if st.button("❌ No", key=f"cancel_delete_{video['id']}", type="secondary", use_container_width=True):
                        st.session_state.show_delete_dialog = False
                        st.session_state.video_to_delete = None
                        st.session_state.video_to_delete_title = None
                        st.rerun()

# Get video list
video_list = get_video_list()

# Sidebar controls
with st.sidebar:
    st.subheader("Sort Options")
    if st.button("Sort by Longest Duration ⏱️", use_container_width=True):
        # Convert duration to seconds for sorting
        video_list['duration_seconds'] = video_list['duration'].apply(duration_to_seconds)
        video_list = video_list.sort_values('duration_seconds', ascending=False)
        video_list = video_list.drop('duration_seconds', axis=1)
        # Save the sorted data back to Excel using the correct path
        video_list.to_excel(data_service.videos_excel, index=False)
        st.success("Videos sorted by duration and saved!")
        st.rerun()

    st.subheader("Clean Data")
    if st.button("Remove Duplicate Titles 🧹", use_container_width=True):
        # Keep only the first occurrence of each title
        video_list = video_list.drop_duplicates(subset=['title'], keep='first')
        # Save the deduplicated data back to Excel
        video_list.to_excel(data_service.videos_excel, index=False)
        st.success("Duplicate videos removed!")
        st.rerun()

if video_list.empty:
    st.info("No videos found in the database. Search and save some videos first!")
else:
    # Display statistics
    display_stats(video_list)
    
    # Sorting controls
    st.markdown("### Sort Videos")
    col1, col2, col3 = st.columns([2, 2, 2])
    
    # Channel filter
    with col1:
        channel_names = data_service.get_channel_names()
        selected_channel = st.selectbox(
            "Filter by Channel:",
            options=channel_names,
            key='channel_filter'
        )
    
    # Sorting controls
    with col2:
        sort_options = {
            'published_at': 'Published Date',
            'duration_seconds': 'Duration',
            'title': 'Title',
            'channel_title': 'Channel Name'
        }
        selected_sort = st.selectbox(
            "Sort by:",
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
            key='sort_by'
        )
    
    with col3:
        order_options = {
            'asc': 'Ascending',
            'desc': 'Descending'
        }
        selected_order = st.selectbox(
            "Order:",
            options=list(order_options.keys()),
            format_func=lambda x: order_options[x],
            key='sort_order'
        )
    
    # Apply channel filter
    if selected_channel != "All Channels":
        video_list = video_list[video_list['channel_title'] == selected_channel]
    
    # Apply sorting
    ascending = selected_order == 'asc'
    video_list = video_list.sort_values(by=selected_sort, ascending=ascending)
    
    # Reset to first page when sort changes
    if 'last_sort' not in st.session_state or 'last_order' not in st.session_state:
        st.session_state.last_sort = selected_sort
        st.session_state.last_order = selected_order
    elif st.session_state.last_sort != selected_sort or st.session_state.last_order != selected_order:
        st.session_state.list_page = 1
        st.session_state.last_sort = selected_sort
        st.session_state.last_order = selected_order
    
    # Pagination
    total_videos = len(video_list)
    total_pages = math.ceil(total_videos / st.session_state.list_per_page)
    start_idx = (st.session_state.list_page - 1) * st.session_state.list_per_page
    end_idx = start_idx + st.session_state.list_per_page
    
    # Display videos in grid
    current_videos = video_list.iloc[start_idx:end_idx]
    
    # Create columns for the grid
    cols = st.columns(3)
    for idx, (_, video) in enumerate(current_videos.iterrows()):
        display_video_info(video, cols[idx % 3])
    
    # Pagination controls
    st.markdown('<div class="pagination-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.list_page > 1:
            if st.button("⬅️ Previous"):
                st.session_state.list_page -= 1
                st.rerun()
    
    with col2:
        st.markdown(
            f'<div class="pagination-text">Page {st.session_state.list_page} of {total_pages}</div>',
            unsafe_allow_html=True
        )
    
    with col3:
        if st.session_state.list_page < total_pages:
            if st.button("Next ➡️"):
                st.session_state.list_page += 1
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
