import json
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import streamlit as st

class DataService:
    def __init__(self):
        """Initialize the data service."""
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        self.downloads_file = self.data_dir / 'downloads.json'
        self.videos_excel = self.data_dir / 'youtube_videos.xlsx'
        
        # Create downloads file if it doesn't exist
        if not self.downloads_file.exists():
            self._save_downloads([])
    
    def _load_downloads(self):
        """Load downloads data from JSON file."""
        try:
            with open(self.downloads_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_downloads(self, downloads):
        """Save downloads data to JSON file."""
        with open(self.downloads_file, 'w') as f:
            json.dump(downloads, f, indent=2)
    
    def _get_video_info_from_excel(self, video_id):
        """Get video information from Excel file."""
        try:
            if os.path.exists(self.videos_excel):
                df = pd.read_excel(self.videos_excel)
                video_info = df[df['id'] == video_id]
                if not video_info.empty:
                    return {
                        'id': video_id,
                        'title': video_info['title'].iloc[0],
                        'channel_title': video_info['channel_title'].iloc[0],
                        'duration': video_info['duration'].iloc[0],
                        'published_at': video_info['published_at'].iloc[0]
                    }
        except Exception as e:
            print(f"Error reading Excel: {str(e)}")
        return None
    
    def get_downloaded_videos(self):
        """Get list of all downloaded videos."""
        # First try to load from downloads.json
        downloads = self._load_downloads()
        
        # If no downloads found, reconstruct from files
        if not downloads:
            downloads = []
            downloaded_dir = Path('data/downloaded')
            if downloaded_dir.exists():
                for file in downloaded_dir.glob('*.mp3'):
                    video_id = file.stem  # Get filename without extension
                    
                    # Try to get video info from Excel
                    video_info = self._get_video_info_from_excel(video_id)
                    
                    if video_info:
                        video_info['file_path'] = str(file)
                        downloads.append(video_info)
                    else:
                        # Fallback to basic info if not found in Excel
                        downloads.append({
                            'id': video_id,
                            'title': f'Video {video_id}',  # Default title
                            'file_path': str(file),
                            'duration': '00:00',  # Default duration
                        })
                # Save reconstructed downloads
                self._save_downloads(downloads)
        
        # Filter out entries where file doesn't exist
        valid_downloads = []
        for download in downloads:
            if os.path.exists(download['file_path']):
                # Try to update title from Excel if it's using default
                if download['title'].startswith('Video '):
                    video_info = self._get_video_info_from_excel(download['id'])
                    if video_info:
                        download.update(video_info)
                valid_downloads.append(download)
        
        return valid_downloads
    
    def add_download(self, video_info, file_path):
        """Add a new download entry."""
        downloads = self._load_downloads()
        
        # Check if video already exists
        for download in downloads:
            if download['id'] == video_info['id']:
                # Update existing entry
                download.update({
                    'title': video_info['title'],
                    'channel_title': video_info['channel_title'],
                    'duration': video_info['duration'],
                    'published_at': video_info.get('published_at'),
                    'file_path': str(file_path),
                    'downloaded_at': datetime.now().isoformat()
                })
                self._save_downloads(downloads)
                return
        
        # Add new entry
        downloads.append({
            'id': video_info['id'],
            'title': video_info['title'],
            'channel_title': video_info['channel_title'],
            'duration': video_info['duration'],
            'published_at': video_info.get('published_at'),
            'file_path': str(file_path),
            'downloaded_at': datetime.now().isoformat()
        })
        
        self._save_downloads(downloads)
    
    def remove_download(self, video_id):
        """Remove a download entry."""
        downloads = self._load_downloads()
        downloads = [d for d in downloads if d['id'] != video_id]
        self._save_downloads(downloads)
    
    def get_download_info(self, video_id):
        """Get information about a downloaded video."""
        downloads = self._load_downloads()
        for download in downloads:
            if download['id'] == video_id:
                return download
        return None
    
    def load_excel_data(self, file_path):
        """Load data from Excel file"""
        try:
            df = pd.read_excel(file_path)
            return df.to_dict('records')
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Error loading Excel file: {str(e)}")
            return []

    def save_videos_to_excel(self, videos, excel_file=None):
        """Save videos data to Excel file"""
        if excel_file:
            self.videos_excel = excel_file
            
        # Convert videos to DataFrame
        df = pd.DataFrame(videos)
        
        try:
            # If file exists, append new data
            if os.path.exists(self.videos_excel):
                existing_df = pd.read_excel(self.videos_excel)
                # Remove duplicates based on video ID
                df = pd.concat([existing_df, df]).drop_duplicates(subset=['id'], keep='last')
            
            # Save to Excel
            df.to_excel(self.videos_excel, index=False)
            return len(df)
        except Exception as e:
            st.error(f"Error saving to Excel: {str(e)}")
            return 0
    
    def clean_excel_data(self):
        """Remove entries from Excel that don't have corresponding audio files"""
        try:
            if not os.path.exists(self.videos_excel):
                return 0, 0
            
            # Read Excel file
            df = pd.read_excel(self.videos_excel)
            initial_count = len(df)
            
            # Get list of downloaded files
            if not Path('data/downloaded').exists():
                return initial_count, 0
            
            downloaded_files = list(Path('data/downloaded').glob('*.mp3'))
            downloaded_ids = [f.stem for f in downloaded_files]
            
            # Filter DataFrame to keep only downloaded files
            df = df[df['id'].isin(downloaded_ids)]
            
            # Save cleaned DataFrame
            df.to_excel(self.videos_excel, index=False)
            final_count = len(df)
            
            return initial_count, final_count
        except Exception as e:
            st.error(f"Error cleaning Excel data: {str(e)}")
            return 0, 0
