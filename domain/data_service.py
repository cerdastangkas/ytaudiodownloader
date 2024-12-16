import pandas as pd
import streamlit as st

class DataService:
    def __init__(self):
        pass

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

    def save_videos_to_excel(self, videos, file_path):
        """Save videos to Excel file"""
        try:
            # Convert videos to DataFrame and format dates for Excel
            df = pd.DataFrame(videos)
            
            # Load existing data
            existing_data = []
            try:
                existing_df = pd.read_excel(file_path)
                # Convert existing dates to timezone-aware
                existing_df['published_at'] = pd.to_datetime(existing_df['published_at']).dt.tz_localize('UTC')
                existing_data = existing_df.to_dict('records')
            except FileNotFoundError:
                pass
            
            # Combine existing and new data, removing duplicates based on video ID
            all_data = existing_data + videos
            df_all = pd.DataFrame(all_data).drop_duplicates(subset=['id'])
            
            # Convert all published_at to human readable format
            df_all['published_at'] = pd.to_datetime(df_all['published_at'])
            df_all['published_date'] = df_all['published_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df_all = df_all.sort_values('published_at', ascending=False)
            
            # Drop the timezone-aware column and rename the formatted one
            df_all = df_all.drop(columns=['published_at'])
            df_all = df_all.rename(columns={'published_date': 'published_at'})
            
            # Save to Excel
            df_all.to_excel(file_path, index=False)
            return len(df_all)
        except Exception as e:
            st.error(f"Error saving to Excel: {str(e)}")
            return 0
