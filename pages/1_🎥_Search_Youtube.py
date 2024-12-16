import streamlit as st
import os
from domain.youtube_service import YouTubeService
from domain.data_service import DataService
from ui.search_form import search_youtube_videos
from ui.results_display import display_search_results
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variables
api_key = os.getenv('YOUTUBE_API_KEY')
if not api_key:
    st.error('YouTube API key not found in environment variables. Please check your .env file.')
    st.stop()

# Initialize services
youtube_service = YouTubeService(api_key)
data_service = DataService()

# Page config
st.set_page_config(
    page_title='YouTube Video Search',
    page_icon='🎥',
    layout='wide'
)

# Initialize session states
if 'search_params' not in st.session_state:
    st.session_state.search_params = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'page_token' not in st.session_state:
    st.session_state.page_token = None
if 'all_videos' not in st.session_state:
    st.session_state.all_videos = []
if 'videos_per_page' not in st.session_state:
    st.session_state.videos_per_page = 9
if 'download_states' not in st.session_state:
    st.session_state.download_states = {}

# Main app
st.title('🎥 YouTube Video Search')
st.markdown('Search for YouTube videos by license type')

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

# Search form
search_youtube_videos(youtube_service)

# Display search results
display_search_results(youtube_service)

# Auto-save to Excel if there are search results
if st.session_state.all_videos:
    excel_file = 'youtube_videos.xlsx'
    total_saved = data_service.save_videos_to_excel(st.session_state.all_videos, excel_file)
    st.info(f'💾 {total_saved} videos saved to database')
