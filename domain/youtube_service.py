from googleapiclient.discovery import build
from pathlib import Path

class YouTubeService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube_client = None
        self.download_dir = Path(__file__).parent.parent / 'data' / 'downloaded'
        
    def get_youtube_client(self):
        """Lazy initialization of YouTube API client"""
        if self.youtube_client is None:
            self.youtube_client = build('youtube', 'v3', developerKey=self.api_key)
        return self.youtube_client

    def search_videos(self, query=None, license_type=None, page_token=None, max_results=50):
        youtube = self.get_youtube_client()

        # If no query provided, use a broad search term
        search_query = query if query else '*'
        
        print(f"[DEBUG] Starting search with query: {search_query}, license: {license_type}")

        # Build search parameters
        search_params = {
            'q': search_query,
            'part': 'snippet',
            'maxResults': min(max_results, 50),
            'type': 'video',
            'order': 'date'  # Sort by date when no specific query to get recent videos
        }

        if license_type:
            search_params['videoLicense'] = license_type
            
        if page_token:
            search_params['pageToken'] = page_token
            
        print(f"[DEBUG] Search parameters: {search_params}")

        try:
            # Execute search request
            request = youtube.search().list(**search_params)
            response = request.execute()
            
            print(f"[DEBUG] Initial search found {len(response.get('items', []))} items")

            # Get video details including duration
            video_ids = [item['id']['videoId'] for item in response.get('items', [])]
            
            # Initialize duration map
            duration_map = {}
            
            if video_ids:
                print(f"[DEBUG] Fetching details for {len(video_ids)} videos")
                video_details = youtube.videos().list(
                    part='contentDetails',
                    id=','.join(video_ids)
                ).execute()
                
                # Create a mapping of video ID to duration
                for item in video_details.get('items', []):
                    duration = item['contentDetails']['duration']
                    duration_seconds = self._duration_to_seconds(duration)
                    # Only include videos longer than 3 minutes
                    if duration_seconds >= 180:  # 3 minutes = 180 seconds
                        duration_map[item['id']] = self._format_duration(duration)
                
                print(f"[DEBUG] Found {len(duration_map)} videos longer than 3 minutes")

            # Process search results and filter out videos with no duration (too short)
            videos = []
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                # Only include videos that are in our duration map (longer than 3 minutes)
                if video_id in duration_map:
                    snippet = item['snippet']
                    video_info = {
                        'id': video_id,
                        'title': snippet['title'],
                        'description': snippet['description'],
                        'thumbnail': snippet['thumbnails']['medium']['url'],
                        'channel_title': snippet['channelTitle'],
                        'published_at': snippet['publishedAt'],
                        'duration': duration_map[video_id],
                        'license': license_type
                    }
                    videos.append(video_info)

            # Return both videos and pagination tokens
            return {
                'success': True,
                'videos': videos,
                'next_page_token': response.get('nextPageToken'),
                'error': None
            }

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return {
                'success': False,
                'videos': [],
                'next_page_token': None,
                'error': str(e)
            }

    def download_audio(self, video_id, progress_callback=None):
        """Download audio from YouTube video"""
        import yt_dlp
        import os

        def progress_hook(d):
            if d['status'] == 'downloading' and progress_callback:
                # Calculate download progress
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total_bytes:
                    progress = (d['downloaded_bytes'] / total_bytes) * 100
                    progress_callback(min(progress, 100))
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'downloaded')
        output_template = os.path.join(output_dir, f'{video_id}.%(ext)s')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_url = f'https://www.youtube.com/watch?v={video_id}'
                info = ydl.extract_info(video_url, download=True)
                return {
                    'success': True,
                    'title': info['title'],
                    'filename': os.path.join(output_dir, f'{video_id}.mp3')
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_source_path(self, video_id):
        """Get the path to the downloaded audio file."""
        path = self.download_dir / f"{video_id}.mp3"
        return str(path.relative_to(Path.cwd()))

    def is_audio_downloaded(self, video_id):
        """Check if audio for this video is already downloaded"""
        import os
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'downloaded')
        audio_file = os.path.join(output_dir, f'{video_id}.mp3')
        return os.path.exists(audio_file)

    @staticmethod
    def _format_duration(duration):
        """Convert ISO 8601 duration to human readable format"""
        import re
        import datetime
        
        # Remove 'PT' from the beginning
        duration = duration[2:]
        
        # Initialize hours, minutes, seconds
        hours = minutes = seconds = 0
        
        # Extract hours if present
        if 'H' in duration:
            hours = int(re.search(r'(\d+)H', duration).group(1))
            
        # Extract minutes if present
        if 'M' in duration:
            minutes = int(re.search(r'(\d+)M', duration).group(1))
            
        # Extract seconds if present
        if 'S' in duration:
            seconds = int(re.search(r'(\d+)S', duration).group(1))
        
        # Format the duration string
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    @staticmethod
    def _duration_to_seconds(duration):
        """Convert ISO 8601 duration to total seconds"""
        import re
        
        # Remove 'PT' from the beginning
        duration = duration[2:]
        
        # Initialize hours, minutes, seconds
        hours = minutes = seconds = 0
        
        # Extract hours if present
        if 'H' in duration:
            hours = int(re.search(r'(\d+)H', duration).group(1))
            
        # Extract minutes if present
        if 'M' in duration:
            minutes = int(re.search(r'(\d+)M', duration).group(1))
            
        # Extract seconds if present
        if 'S' in duration:
            seconds = int(re.search(r'(\d+)S', duration).group(1))
        
        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def get_license_types():
        return {
            'creativeCommon': 'Creative Commons',
            'youtube': 'Standard YouTube License'
        }
