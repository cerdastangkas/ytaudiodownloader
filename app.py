import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="YouTube Audio Downloader",
    page_icon="🎵",
    layout="wide"
)

# Initialize session state for API key
if 'youtube_api_key' not in st.session_state:
    st.session_state.youtube_api_key = os.getenv('YOUTUBE_API_KEY')

# Main page
st.title("🎵 YouTube Audio Downloader")
st.markdown("""
Welcome to YouTube Audio Downloader! This app allows you to:
- 🔍 Search for YouTube videos
- 🎵 Download audio from videos
- 📝 Transcribe audio content
- ✂️ Split audio into segments
""")

# API key input
api_key = st.text_input(
    "YouTube API Key",
    value=st.session_state.youtube_api_key if st.session_state.youtube_api_key else "",
    type="password"
)

if api_key:
    st.session_state.youtube_api_key = api_key
    if st.button("Save API Key"):
        st.success("API key saved! You can now use the Search page.")
else:
    st.warning("""
        Please enter your YouTube API key to use the search functionality.
        You can get one from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
    """)

# Instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. Enter your YouTube API key above
    2. Go to the Search page to find videos
    3. Download audio from videos you want
    4. View downloaded audio in the Downloads page
    5. Create transcriptions and split audio in the Transcriptions page
    """)
