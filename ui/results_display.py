import streamlit as st
import math
from domain.youtube_service import YouTubeService
from ui.video_card import display_video_card

def display_search_results(youtube_service: YouTubeService):
    """Display search results with pagination"""
    
    # Initialize debug state if not exists
    if 'debug_state' not in st.session_state:
        st.session_state.debug_state = {
            'last_search_params': None,
            'last_page': None,
            'last_videos': None
        }
    
    # Only log when search parameters change
    if 'last_search_params' not in st.session_state:
        st.session_state.last_search_params = None
        
    if not st.session_state.search_params:
        if st.session_state.last_search_params is not None:  # Only log when state changes
            print("[DEBUG] No search parameters found in session state")
            st.session_state.last_search_params = None
        return

    # Log only when search parameters or page changes
    params_changed = st.session_state.debug_state['last_search_params'] != st.session_state.search_params
    page_changed = st.session_state.debug_state['last_page'] != st.session_state.current_page
    
    if params_changed:
        print(f"[DEBUG] Search parameters changed to: {st.session_state.search_params}")
        st.session_state.debug_state['last_search_params'] = st.session_state.search_params

    # Fetch videos if needed
    if not st.session_state.all_videos:
        if params_changed:  # Only print if params changed
            print("[DEBUG] Fetching new videos from YouTube...")
            print(f"[DEBUG] Query: {st.session_state.search_params['query']}")
            print(f"[DEBUG] License: {st.session_state.search_params['license_type']}")
        
        results = youtube_service.search_videos(
            query=st.session_state.search_params['query'],
            license_type=st.session_state.search_params['license_type'],
            page_token=st.session_state.page_token
        )
        
        if results['success']:
            st.session_state.all_videos = results['videos']
            st.session_state.page_token = results.get('next_page_token')
            if params_changed:  # Only print if params changed
                print(f"[DEBUG] Successfully fetched {len(results['videos'])} videos")
                if results.get('next_page_token'):
                    print("[DEBUG] More pages available")
        else:
            if params_changed:  # Only print if params changed
                print(f"[DEBUG] Error fetching videos: {results['error']}")
            st.error(results['error'])
            return

    # Calculate pagination
    total_videos = len(st.session_state.all_videos)
    
    # Only log pagination info when it changes
    videos_changed = st.session_state.debug_state['last_videos'] != len(st.session_state.all_videos)
    if params_changed or page_changed or videos_changed:
        print(f"[DEBUG] Total videos in session: {total_videos}")
        print(f"[DEBUG] Current page: {st.session_state.current_page}")
        print(f"[DEBUG] Videos per page: {st.session_state.videos_per_page}")
        
        # Update debug state
        st.session_state.debug_state.update({
            'last_videos': len(st.session_state.all_videos),
            'last_page': st.session_state.current_page
        })

    if total_videos > 0:
        st.success(f'Found {total_videos} videos')
        
        total_pages = math.ceil(total_videos / st.session_state.videos_per_page)
        start_idx = (st.session_state.current_page - 1) * st.session_state.videos_per_page
        end_idx = start_idx + st.session_state.videos_per_page
        
        # Display videos in grid
        print(f"[DEBUG] Displaying videos from index {start_idx} to {end_idx}")
        
        # Add custom CSS for the grid
        st.markdown("""
            <style>
            .video-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                padding: 1rem 0;
            }
            .video-card {
                background: white;
                border-radius: 8px;
                padding: 1rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Create grid container
        grid = st.container()
        
        with grid:
            cols = st.columns(3)
            current_page = st.session_state.current_page
            for i, video in enumerate(st.session_state.all_videos[start_idx:end_idx]):
                print(f"[DEBUG] Rendering video {i+1} of page (ID: {video['id']})")
                with cols[i % 3]:
                    with st.container():
                        # Add grid position to context
                        grid_position = f"p{current_page}_r{i//3}_c{i%3}"
                        display_video_card(video, youtube_service, grid_position)
        
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
