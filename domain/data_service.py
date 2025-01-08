import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from datetime import datetime

class DataService:
    def __init__(self, data_dir='data'):
        """Initialize the data service."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.downloads_file = self.data_dir / 'downloads.json'
        self.videos_excel = self.data_dir / 'youtube_videos.xlsx'
        self.downloaded_videos_excel = self.data_dir / 'downloaded_videos.xlsx'
        self.downloaded_dir = self.data_dir / 'downloaded'
        
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
                    # Convert the row to a dictionary
                    info_dict = video_info.iloc[0].to_dict()
                    # Clean up NaN values
                    return {k: v for k, v in info_dict.items() if pd.notna(v)}
        except Exception as e:
            print(f"Error reading Excel: {str(e)}")
        return None
    
    def get_video_info(self, video_id):
        """Get video information from Excel file."""
        return self._get_video_info_from_excel(video_id)
    
    def delete_video(self, video_id):
        """Delete a video from the Excel database."""
        try:
            if os.path.exists(self.videos_excel):
                df = pd.read_excel(self.videos_excel)
                # Remove the video with the given ID
                df = df[df['id'] != video_id]
                # Save the updated DataFrame back to Excel
                df.to_excel(self.videos_excel, index=False)
                return True
            return False
        except Exception as e:
            print(f"Error deleting video: {str(e)}")
            return False
    
    def get_downloaded_videos(self):
        """Get list of all downloaded videos from Excel."""
        try:
            if os.path.exists(self.videos_excel):
                df = pd.read_excel(self.videos_excel)
                # Convert DataFrame to list of dictionaries, removing NaN values
                videos = []
                for _, row in df.iterrows():
                    video_dict = {k: v for k, v in row.to_dict().items() if pd.notna(v)}
                    videos.append(video_dict)
                return videos
        except Exception as e:
            print(f"Error reading Excel: {str(e)}")
        return []
    
    def get_channel_names(self):
        """Get list of unique channel names from Excel."""
        try:
            if os.path.exists(self.videos_excel):
                df = pd.read_excel(self.videos_excel)
                return ["All Channels"] + sorted(df['channel_title'].unique().tolist())
        except Exception as e:
            print(f"Error reading Excel: {str(e)}")
        return ["All Channels"]
    
    def save_videos_to_excel(self, videos, excel_file=None):
        """Save videos data to Excel file"""
        if excel_file:
            self.videos_excel = excel_file
            
        # Convert videos to DataFrame
        df = pd.DataFrame(videos)
        
        # Add duration_seconds column
        def duration_to_seconds(duration):
            try:
                parts = duration.split(':')
                if len(parts) == 2:  # MM:SS format
                    return int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:  # HH:MM:SS format
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                return 0
            except:
                return 0
                
        df['duration_seconds'] = df['duration'].apply(duration_to_seconds)
        
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
            if not (self.data_dir / 'downloaded').exists():
                return initial_count, 0
            
            downloaded_files = list((self.data_dir / 'downloaded').glob('*.mp3'))
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

    def _is_video_downloaded(self, video_id):
        """Check if a video has been downloaded by looking for its audio file"""
        # Check in downloaded directory for any file starting with video_id
        if self.downloaded_dir.exists():
            for file in self.downloaded_dir.glob(f'{video_id}.*'):
                return True
        return False
            
    def update_downloaded_videos_excel(self):
        """Update downloaded_videos.xlsx with only downloaded audio files"""
        try:
            # Get all videos from main Excel
            if not os.path.exists(self.videos_excel):
                st.error("Main videos database (youtube_videos.xlsx) not found!")
                return 0
                
            df = pd.read_excel(self.videos_excel)
            if df.empty:
                return 0
                
            # Filter videos that have downloaded files
            downloaded_videos = []
            for _, row in df.iterrows():
                video_id = row['id']
                if self._is_video_downloaded(video_id):
                    downloaded_videos.append(row.to_dict())
            
            # Create new DataFrame and save
            if downloaded_videos:
                downloaded_df = pd.DataFrame(downloaded_videos)
                downloaded_df.to_excel(self.downloaded_videos_excel, index=False)
                return len(downloaded_videos)
            else:
                # Create empty Excel with columns
                empty_df = pd.DataFrame(columns=df.columns)
                empty_df.to_excel(self.downloaded_videos_excel, index=False)
                return 0
                
        except Exception as e:
            st.error(f"Error updating downloaded videos Excel: {str(e)}")
            return 0
            
    def clean_downloaded_videos_excel(self):
        """Remove entries from downloaded_videos.xlsx that don't have downloaded files"""
        try:
            if not os.path.exists(self.downloaded_videos_excel):
                st.error("Downloaded videos database not found! Please update it first.")
                return 0
                
            df = pd.read_excel(self.downloaded_videos_excel)
            if df.empty:
                return 0
                
            initial_count = len(df)
            
            # Filter videos that have downloaded files
            downloaded_videos = []
            for _, row in df.iterrows():
                video_id = row['id']
                if self._is_video_downloaded(video_id):
                    downloaded_videos.append(row.to_dict())
            
            # Save filtered DataFrame
            if downloaded_videos:
                downloaded_df = pd.DataFrame(downloaded_videos)
                downloaded_df.to_excel(self.downloaded_videos_excel, index=False)
                return initial_count - len(downloaded_videos)  # Return number of removed entries
            else:
                # Create empty Excel with columns
                empty_df = pd.DataFrame(columns=df.columns)
                empty_df.to_excel(self.downloaded_videos_excel, index=False)
                return initial_count
                
        except Exception as e:
            st.error(f"Error cleaning downloaded videos Excel: {str(e)}")
            return 0
