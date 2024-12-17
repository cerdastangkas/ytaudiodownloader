# YouTube Audio Downloader

A streamlined Streamlit application for searching and downloading audio from YouTube videos, with advanced features like audio format conversion and comprehensive metadata display.

## Features

- 🔍 Search YouTube videos with custom queries
- 📜 Filter videos by license type
- ⏱️ Duration-based filtering (>3 minutes)
- 🎵 Download audio in MP3 format
- 🔄 Convert audio to OGG format
- 🖼️ Thumbnail previews for videos and downloaded files
- 📊 Progress tracking for downloads
- 📑 Export video details to Excel
- 🔑 In-app API key management
- 📱 Responsive and modern UI

## Prerequisites

### YouTube API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API key)
5. Copy your API key

### OpenAI API Key (Optional)
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Go to API keys section
4. Create a new API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ytaudiodownloader.git
cd ytaudiodownloader
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (optional, keys can be set in the app):
```bash
YOUTUBE_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_key_here
```

## Usage

1. Start the application:
```bash
streamlit run Home.py
```

2. Configure API Keys:
   - Open the sidebar (≡ menu)
   - Enter your YouTube API key
   - (Optional) Enter your OpenAI API key
   - Click "Apply" for each key

3. Search and Download:
   - Go to "Search YouTube" page
   - Enter search terms and click "Search"
   - Click "Download" on any video to save its audio
   - Download progress will be displayed

4. Manage Downloads:
   - Go to "Downloaded" page
   - View all downloaded files with thumbnails
   - Play audio directly in the browser
   - Convert MP3 files to OGG format
   - Delete unwanted files

## Project Structure

```
ytaudiodownloader/
├── Home.py                 # Main application and configuration
├── pages/
│   ├── 1_Search_Youtube.py # Search and download interface
│   └── 2_Downloaded.py     # Downloaded files management
├── domain/
│   ├── youtube_service.py  # YouTube API interactions
│   ├── audio_service.py    # Audio conversion and management
│   ├── data_service.py     # Excel data operations
│   └── config_service.py   # API key management
├── ui/
│   ├── video_card.py       # Video display component
│   └── results_display.py  # Results and pagination
├── data/
│   ├── downloaded/         # Downloaded MP3 files
│   └── converted/          # Converted OGG files
├── requirements.txt        # Dependencies
└── .env                    # Configuration (optional)
```

## Dependencies

- streamlit
- yt-dlp
- google-api-python-client
- python-dotenv
- pandas
- openpyxl
- pydub

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Version History

- v1.4.0: Added thumbnails, audio conversion, and in-app API key management
- v1.3.0: Added audio format conversion and improved UI
- v1.2.0: Added thumbnail preview and enhanced metadata display
- v1.1.0: Refactored codebase with modular structure
- v1.0.0: Initial release with basic functionality
