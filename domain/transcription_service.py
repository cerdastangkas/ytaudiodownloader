import os
from pathlib import Path
import pandas as pd
from datetime import datetime
from openai import OpenAI
from pydub import AudioSegment
import math

class TranscriptionService:
    def __init__(self, data_dir='data', api_key=None):
        """Initialize the transcription service."""
        self.data_dir = Path(data_dir)
        self.transcriptions_dir = self.data_dir / 'transcriptions'
        self.chunks_dir = self.data_dir / 'chunks'
        self.transcriptions_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client with provided API key
        self.client = OpenAI(api_key=api_key)
        
        # Maximum file size for Whisper API (25MB)
        self.MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes
    
    def get_excel_path(self, video_id):
        """Get the Excel file path for a specific video."""
        return self.transcriptions_dir / f"{video_id}_transcription.xlsx"
    
    def get_chunk_dir(self, video_id):
        """Get the directory for storing audio chunks."""
        chunk_dir = self.chunks_dir / video_id
        chunk_dir.mkdir(parents=True, exist_ok=True)
        return chunk_dir
    
    def split_audio_file(self, audio_path, video_id):
        """Split audio file into chunks of maximum 25MB."""
        try:
            # Load the audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Get file size in bytes
            file_size = os.path.getsize(audio_path)
            
            if file_size <= self.MAX_FILE_SIZE:
                return [(audio_path, 0, len(audio))]
            
            # Calculate number of chunks needed
            num_chunks = math.ceil(file_size / self.MAX_FILE_SIZE)
            chunk_duration = len(audio) / num_chunks
            
            chunks = []
            chunk_dir = self.get_chunk_dir(video_id)
            
            # Clear existing chunks
            for existing_file in chunk_dir.glob('*.ogg'):
                os.remove(existing_file)
            
            # Split audio into chunks
            for i in range(num_chunks):
                start_ms = int(i * chunk_duration)
                end_ms = int(min((i + 1) * chunk_duration, len(audio)))
                
                chunk = audio[start_ms:end_ms]
                chunk_path = chunk_dir / f"chunk_{i:03d}.ogg"
                
                # Export chunk with lower bitrate to ensure it's under 25MB
                chunk.export(
                    chunk_path,
                    format="ogg",
                    parameters=["-q:a", "3"]  # Lower quality to reduce file size
                )
                
                chunks.append((str(chunk_path), start_ms, end_ms))
            
            return chunks
            
        except Exception as e:
            raise Exception(f"Error splitting audio: {str(e)}")
    
    def transcribe_audio(self, audio_path, video_id):
        """Transcribe audio using OpenAI Whisper API."""
        try:
            # Split audio into chunks if necessary
            chunks = self.split_audio_file(audio_path, video_id)
            
            all_segments = []
            full_text = []
            
            # Process each chunk
            for chunk_path, start_ms, end_ms in chunks:
                with open(chunk_path, 'rb') as audio_file:
                    # Call OpenAI's transcription API
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="id",
                        response_format="verbose_json"
                    )
                
                # Adjust timestamps for this chunk
                for segment in transcript.segments:
                    adjusted_segment = {
                        'start': segment.start + (start_ms / 1000),  # Convert ms to seconds
                        'end': segment.end + (start_ms / 1000),
                        'text': segment.text
                    }
                    all_segments.append(adjusted_segment)
                
                full_text.append(transcript.text)
            
            # Combine all transcriptions
            transcription_data = {
                'video_id': video_id,
                'audio_path': str(audio_path),
                'full_text': ' '.join(full_text),
                'segments': all_segments,
                'language': 'id',
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to Excel
            self._save_to_excel(transcription_data)
            
            # Clean up chunks if they were created
            if len(chunks) > 1:
                chunk_dir = self.get_chunk_dir(video_id)
                for chunk_file in chunk_dir.glob('*.ogg'):
                    os.remove(chunk_file)
                os.rmdir(chunk_dir)
            
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
                'text': segment['text'].strip(),
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
    
    def has_transcription(self, video_id):
        """Check if transcription exists for a video."""
        excel_path = self.get_excel_path(video_id)
        return os.path.exists(excel_path)
