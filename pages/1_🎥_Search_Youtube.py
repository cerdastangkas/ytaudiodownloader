import streamlit as st
from domain.youtube_service import YouTubeService
from domain.data_service import DataService
from ui.search_form import search_youtube_videos
from ui.results_display import display_search_results

# Check for API key
if 'youtube_api_key' not in st.session_state or not st.session_state.youtube_api_key:
    st.error("⚠️ Please set your YouTube API key in the main page first!")
    st.stop()

# Initialize services with session state API key
youtube_service = YouTubeService(st.session_state.youtube_api_key)
data_service = DataService()

# Page config
st.set_page_config(
    page_title='Search YouTube Video',
    page_icon='🎥',
    layout='wide'
)

# Initialize session states
if 'search_params' not in st.session_state:
    st.session_state.search_params = None
if 'all_videos' not in st.session_state:
    st.session_state.all_videos = []
if 'page_token' not in st.session_state:
    st.session_state.page_token = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
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
    excel_file = f"{st.session_state.data_dir}/youtube_videos.xlsx"
    total_saved = data_service.save_videos_to_excel(st.session_state.all_videos, excel_file)
    st.info(f'💾 {total_saved} videos saved to database')
