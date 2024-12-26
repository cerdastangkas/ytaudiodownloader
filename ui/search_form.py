import streamlit as st
from domain.youtube_service import YouTubeService

def search_youtube_videos(youtube_service: YouTubeService):
    """Handle YouTube video search"""
    with st.form('search_form'):
        cols = st.columns([3, 1, 1])
        
        with cols[0]:
            query = st.text_input('Search Query (optional)', 
                placeholder='Enter keywords to search for specific videos')
            
        with cols[1]:
            license_types = youtube_service.get_license_types()
            selected_license = st.selectbox(
                'License Type',
                options=[None] + list(license_types.keys()),
                index=1,
                format_func=lambda x: 'Any License' if x is None else license_types[x]
            )
        
        with cols[2]:
            st.session_state.videos_per_page = st.selectbox(
                'Videos per page',
                options=[6, 9, 12, 15],
                index=3
            )
        
        search_submitted = st.form_submit_button('Search Videos')
        
        if search_submitted:
            print("\n[DEBUG] ===== New Search Started =====")
            print(f"[DEBUG] Search Query: '{query}'")
            print(f"[DEBUG] License Type: {selected_license}")
            print(f"[DEBUG] Videos per page: {st.session_state.videos_per_page}")
            
            # Reset pagination state
            st.session_state.page_token = None
            st.session_state.all_videos = []
            st.session_state.current_page = 1
            
            # Update search parameters
            st.session_state.search_params = {
                'query': query if query else None,
                'license_type': selected_license if selected_license else None
            }
            print("[DEBUG] Search state reset and parameters updated")
