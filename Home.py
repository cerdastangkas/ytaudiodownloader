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
    page_title="YouTube Audio Downloader",
    page_icon="🎵",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        background: linear-gradient(120deg, #4A90E2, #67B26F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 1.5rem 0;
        color: #31333F;
    }
    .feature-section {
        background: linear-gradient(145deg, #2b2b2b, #3a3a3a);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.1);
        color: #ffffff;
    }
    .feature-title {
        font-weight: bold;
        background: linear-gradient(120deg, #4A90E2, #67B26F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-fill-color: transparent;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .feature-section ul {
        list-style-type: none;
        padding-left: 0;
        margin-top: 1rem;
    }
    .feature-section ul li {
        margin: 0.8rem 0;
        padding-left: 1.5rem;
        position: relative;
    }
    .feature-section ul li:before {
        content: "→";
        position: absolute;
        left: 0;
        color: #4A90E2;
    }
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

# Main header
st.markdown('<p class="main-header">🎵 YouTube Audio Downloader</p>', unsafe_allow_html=True)

# Welcome message
st.markdown("""
Welcome to YouTube Audio Downloader! This application allows you to easily search for YouTube videos 
and download their audio content in high quality. Perfect for creating your music playlist, 
podcast collection, or educational content library.
""")

# Features section
st.markdown('<p class="sub-header">✨ Key Features</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-section">
        <p class="feature-title">🔍 Smart Search</p>
        <ul>
            <li>Search YouTube videos by keywords</li>
            <li>Filter videos longer than 3 minutes</li>
            <li>View video thumbnails and details</li>
            <li>Results automatically saved to Excel</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-section">
        <p class="feature-title">📥 Download Management</p>
        <ul>
            <li>Download audio in high quality</li>
            <li>View download progress</li>
            <li>Access downloaded files easily</li>
            <li>Manage your audio collection</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# How to use section
st.markdown('<p class="sub-header">📖 How to Use</p>', unsafe_allow_html=True)

st.markdown("""
1. **Search for Videos**
   - Go to the "🎥 Search Youtube" page
   - Enter your search keywords
   - Browse through the results with pagination
   - Click "Download Audio" on any video you want

2. **Manage Downloads**
   - Visit the "📂 Downloaded" page
   - View all your downloaded audio files
   - Play or delete files as needed
   - See video details for each download

3. **Tips**
   - Search results are automatically saved to Excel
   - Only videos longer than 3 minutes are shown
   - Downloaded files are stored in the 'data/downloaded' folder
   - Use clear search terms for better results
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Made with ❤️ by Cerdas Tangkas<br>
    Need help? Check out our documentation or contact support
</div>
""", unsafe_allow_html=True)

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