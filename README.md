# YouTube Video Downloader

A Streamlit-based application for searching, downloading, and managing YouTube videos with a focus on license filtering and audio extraction.

## Features

### Search YouTube Videos
- Search YouTube videos by keywords
- Filter videos by license type (Creative Commons, Standard YouTube)
- View video thumbnails, titles, descriptions, and durations
- Download selected videos as audio files

### Video List
- View all searched videos in a paginated list
- Filter videos by channel name
- Sort videos by:
  - Published Date
  - Duration
  - Title
  - Channel Name
- Sort in ascending or descending order
- Track which videos have been downloaded

### Downloaded Videos
- View and manage downloaded audio files
- Play audio files directly in the browser
- Delete downloaded files
- Database management:
  - Update downloaded videos list (creates/updates `downloaded_videos.xlsx`)
  - Clean up database by removing entries without audio files
  - Two separate databases:
    - `youtube_videos.xlsx`: All searched videos
    - `downloaded_videos.xlsx`: Only downloaded videos

### Settings
- Set YouTube API Key
- Configure download settings
- Set data directory paths

## File Structure
```
asix_ytdl/
├── data/
│   ├── downloaded/     # Downloaded audio files
│   ├── downloads.json  # Download history
│   ├── youtube_videos.xlsx      # All searched videos
│   └── downloaded_videos.xlsx   # Only downloaded videos
├── domain/            # Business logic
├── pages/            # Streamlit pages
├── ui/               # UI components
└── README.md
```

## Requirements
- Python 3.8+
- Streamlit
- pandas
- pytube
- youtube-dl
- YouTube Data API v3 key

## Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your YouTube API key in the Settings page
4. Run the application:
   ```bash
   streamlit run Home.py
   ```

## Usage
1. **Search Videos**:
   - Enter keywords in the search box
   - Select license type filter
   - Click search
   - Download desired videos

2. **View All Videos**:
   - Go to Video List page
   - Filter by channel
   - Sort by various criteria
   - Track downloaded status

3. **Manage Downloads**:
   - Go to Downloaded Videos page
   - Update downloaded videos database
   - Clean up database if needed
   - Play or delete downloaded files

4. **Settings**:
   - Configure YouTube API key
   - Set download preferences
   - Manage data directories

## License
MIT License
