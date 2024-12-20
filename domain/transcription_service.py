import whisper
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

class TranscriptionService:
    def __init__(self, data_dir='data', model_name='medium'):
        """Initialize the transcription service with the specified model."""
        self.model_name = model_name
        self.model = None
        self.data_dir = Path(data_dir)
        self.transcriptions_dir = self.data_dir / 'transcriptions'
        self.transcriptions_dir.mkdir(parents=True, exist_ok=True)
    
    def load_model(self):
        """Lazy load the Whisper model."""
        if self.model is None:
            self.model = whisper.load_model(self.model_name)
        return self.model
    
    def get_excel_path(self, video_id):
        """Get the Excel file path for a specific video."""
        return self.transcriptions_dir / f"{video_id}_transcription.xlsx"
    
    def transcribe_audio(self, audio_path, video_id):
        """Transcribe audio using OpenAI Whisper."""
        try:
            # Load model
            model = self.load_model()
            
            # Transcribe audio with Indonesian language setting
            result = model.transcribe(
                str(audio_path),
                language="id",  # Set Indonesian as the primary language
                task="transcribe",
                initial_prompt="Transkrip dalam Bahasa Indonesia:"  # Add Indonesian context
            )
            
            # Save transcription results
            transcription_data = {
                'video_id': video_id,
                'audio_path': str(audio_path),
                'full_text': result['text'],
                'segments': result['segments'],
                'language': result.get('language', 'id'),  # Store detected language
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to Excel
            self._save_to_excel(transcription_data)
            
            return True, transcription_data
            
        except Exception as e:
            return False, str(e)
    
    def _save_to_excel(self, transcription_data):
        """Save transcription data to Excel file."""
        video_id = transcription_data['video_id']
        excel_path = self.get_excel_path(video_id)
        
        # Prepare segments data
        segments_data = []
        for segment in transcription_data['segments']:
            segments_data.append({
                'start_time': segment['start'],
                'end_time': segment['end'],
                'text': segment['text'],
                'language': transcription_data['language']
            })
        
        # Create DataFrame with segments
        segments_df = pd.DataFrame(segments_data)
        
        # Create a writer object
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Write segments to 'Segments' sheet
            segments_df.to_excel(writer, sheet_name='Segments', index=False)
            
            # Write metadata to 'Metadata' sheet
            metadata = pd.DataFrame([{
                'video_id': transcription_data['video_id'],
                'audio_path': transcription_data['audio_path'],
                'language': transcription_data['language'],
                'timestamp': transcription_data['timestamp'],
                'full_text': transcription_data['full_text']
            }])
            metadata.to_excel(writer, sheet_name='Metadata', index=False)
    
    def get_transcription(self, video_id):
        """Get transcription data for a specific video."""
        excel_path = self.get_excel_path(video_id)
        
        if not os.path.exists(excel_path):
            return None
        
        try:
            # Read segments from Excel
            segments_df = pd.read_excel(excel_path, sheet_name='Segments')
            return segments_df.to_dict('records')
        except Exception as e:
            print(f"Error reading transcription: {e}")
            return None
