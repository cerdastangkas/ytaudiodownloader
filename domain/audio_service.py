import os
from pathlib import Path
from pydub import AudioSegment

class AudioService:
    def __init__(self):
        self.download_dir = Path('data/downloaded')
        self.converted_dir = Path('data/converted')
        
        # Create directories if they don't exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.converted_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_to_ogg(self, mp3_path):
        """Convert MP3 file to OGG format"""
        try:
            # Load MP3 file
            audio = AudioSegment.from_mp3(mp3_path)
            
            # Create output path
            mp3_file = Path(mp3_path)
            ogg_path = self.converted_dir / f"{mp3_file.stem}.ogg"
            
            # Export as OGG
            audio.export(str(ogg_path), format='ogg')
            
            return True, str(ogg_path)
        except Exception as e:
            return False, str(e)
    
    def get_converted_file(self, video_id):
        """Check if converted OGG file exists"""
        ogg_path = self.converted_dir / f"{video_id}.ogg"
        return ogg_path if ogg_path.exists() else None
