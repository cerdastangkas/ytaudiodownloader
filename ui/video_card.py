import streamlit as st
from domain.youtube_service import YouTubeService
from utils.date_formatter import format_published_date

def display_video_card(video: dict, youtube_service: YouTubeService):
    """Display a single video card with download functionality"""
    with st.container():
        # Thumbnail
        if 'thumbnail' in video:
            st.image(video['thumbnail'], width=None)
        
        # Video title as a link
        st.markdown(f"### [{video.get('title', 'Unknown Title')}](https://youtube.com/watch?v={video['id']})")
        
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

        # Channel, duration and publish date
        st.markdown(f"Channel: {video.get('channel_title', 'Unknown Channel')}")
        st.markdown(f"Duration: {video.get('duration', 'N/A')}")
        st.markdown(f"Published: {format_published_date(video['published_at'])}")
        
        # Description
        description = video['description'][:150] + '...' if len(video['description']) > 150 else video['description']
        st.markdown(f"Description: {description}")
        
        st.markdown("---")
