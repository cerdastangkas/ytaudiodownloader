import pandas as pd
import streamlit as st
import os
from pathlib import Path

class DataService:
    def __init__(self):
        self.excel_file = 'youtube_videos.xlsx'
        self.download_dir = Path('data/downloaded')

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
            self.excel_file = excel_file
            
        # Convert videos to DataFrame
        df = pd.DataFrame(videos)
        
        try:
            # If file exists, append new data
            if os.path.exists(self.excel_file):
                existing_df = pd.read_excel(self.excel_file)
                # Remove duplicates based on video ID
                df = pd.concat([existing_df, df]).drop_duplicates(subset=['id'], keep='last')
            
            # Save to Excel
            df.to_excel(self.excel_file, index=False)
            return len(df)
        except Exception as e:
            st.error(f"Error saving to Excel: {str(e)}")
            return 0
    
    def clean_excel_data(self):
        """Remove entries from Excel that don't have corresponding audio files"""
        try:
            if not os.path.exists(self.excel_file):
                return 0, 0
            
            # Read Excel file
            df = pd.read_excel(self.excel_file)
            initial_count = len(df)
            
            # Get list of downloaded files
            if not self.download_dir.exists():
                return initial_count, 0
            
            downloaded_files = list(self.download_dir.glob('*.mp3'))
            downloaded_ids = [f.stem for f in downloaded_files]
            
            # Filter DataFrame to keep only downloaded files
            df = df[df['id'].isin(downloaded_ids)]
            
            # Save cleaned DataFrame
            df.to_excel(self.excel_file, index=False)
            final_count = len(df)
            
            return initial_count, final_count
        except Exception as e:
            st.error(f"Error cleaning Excel data: {str(e)}")
            return 0, 0
