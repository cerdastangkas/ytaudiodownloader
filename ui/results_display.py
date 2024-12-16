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
            st.markdown(
                """
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
                """,
                unsafe_allow_html=True
            )
            
            cols = st.columns([1, 3, 1])
            
            # Previous page button
            with cols[0]:
                if st.session_state.current_page > 1:
                    if st.button("← Previous", use_container_width=True):
                        st.session_state.current_page -= 1
                        st.rerun()
                else:
                    # Placeholder for alignment
                    st.write("")
            
            # Page indicator
            with cols[1]:
                st.markdown(
                    f'<div class="pagination-text">Page {st.session_state.current_page} of {total_pages}</div>',
                    unsafe_allow_html=True
                )
            
            # Next page button
            with cols[2]:
                if st.session_state.current_page < total_pages or st.session_state.page_token:
                    if st.button("Next →", use_container_width=True):
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
                else:
                    # Placeholder for alignment
                    st.write("")
