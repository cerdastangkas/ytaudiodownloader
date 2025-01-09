import os
from pathlib import Path
from pydub import AudioSegment

class AudioService:
    def __init__(self):
        self.final_result_dir = Path('data/final_result')
        self.final_result_dir.mkdir(parents=True, exist_ok=True)
        self.converted_dir = Path('data/converted')
        
        # Create directories if they don't exist
        self.converted_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_to_ogg(self, mp3_path, video_id=None):
        """Convert MP3 file to OGG format"""
        try:
            print(f"[DEBUG] Converting {mp3_path} to OGG")
            # Load MP3 file
            audio = AudioSegment.from_mp3(mp3_path)
            
            # Create output path
            if video_id is None:
                mp3_file = Path(mp3_path)
                video_id = mp3_file.stem
                
            ogg_path = self.converted_dir / f"{video_id}.ogg"
            print(f"[DEBUG] Output OGG path: {ogg_path}")
            
            # Export as OGG
            audio.export(str(ogg_path), format='ogg')
            print(f"[DEBUG] Successfully converted to OGG: {ogg_path}")
            
            return True, str(ogg_path)
        except Exception as e:
            print(f"[ERROR] Failed to convert to OGG: {str(e)}")
            return False, str(e)
    
    def get_converted_file(self, video_id):
        """Check if converted OGG file exists"""
        ogg_path = self.converted_dir / f"{video_id}.ogg"
        exists = ogg_path.exists()
        print(f"[DEBUG] Checking for converted file: {ogg_path} (exists: {exists})")
        return ogg_path if exists else None

    def get_original_audio_path(self, video_id):
        """Get the path for the original audio file"""
        video_dir = self.final_result_dir / video_id / 'original'
        video_dir.mkdir(parents=True, exist_ok=True)
        return video_dir
