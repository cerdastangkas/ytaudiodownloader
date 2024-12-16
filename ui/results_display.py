import streamlit as st
import math
from domain.youtube_service import YouTubeService
from ui.video_card import display_video_card

def display_search_results(youtube_service: YouTubeService):
    """Display search results with pagination"""
    if not st.session_state.search_params:
        return

    # Fetch videos if needed
    if not st.session_state.all_videos:
        results = youtube_service.search_videos(
            query=st.session_state.search_params['query'],
            license_type=st.session_state.search_params['license_type'],
            page_token=st.session_state.page_token
        )
        
        if results['success']:
            st.session_state.all_videos = results['videos']
            st.session_state.page_token = results.get('next_page_token')
        else:
            st.error(results['error'])
            return

    # Calculate pagination
    total_videos = len(st.session_state.all_videos)
    if total_videos > 0:
        st.success(f'Found {total_videos} videos')
        
        total_pages = math.ceil(total_videos / st.session_state.videos_per_page)
        start_idx = (st.session_state.current_page - 1) * st.session_state.videos_per_page
        end_idx = start_idx + st.session_state.videos_per_page
        
        # Display videos in grid
        cols = st.columns(3)
        for i, video in enumerate(st.session_state.all_videos[start_idx:end_idx]):
            with cols[i % 3]:
                display_video_card(video, youtube_service)
        
        # Pagination controls
        if total_pages > 1:
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col2:
                pagination = st.container()
                
                # Previous page button
                if st.session_state.current_page > 1:
                    if pagination.button("← Previous", key="prev"):
                        st.session_state.current_page -= 1
                        st.rerun()
                
                # Page indicator
                pagination.write(f"Page {st.session_state.current_page} of {total_pages}")
                
                # Next page button
                if st.session_state.current_page < total_pages or st.session_state.page_token:
                    if pagination.button("Next →", key="next"):
                        if end_idx >= len(st.session_state.all_videos) and st.session_state.page_token:
                            # Fetch more videos
                            results = youtube_service.search_videos(
                                query=st.session_state.search_params['query'],
                                license_type=st.session_state.search_params['license_type'],
                                page_token=st.session_state.page_token
                            )
                            
                            if results['success']:
                                st.session_state.all_videos.extend(results['videos'])
                                st.session_state.page_token = results.get('next_page_token')
                            else:
                                st.error(results['error'])
                                return
                        
                        st.session_state.current_page += 1
                        st.rerun()
