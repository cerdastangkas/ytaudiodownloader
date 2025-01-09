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
        self.final_result_dir = self.data_dir / 'final_result'
        self.chunks_dir = self.data_dir / 'chunks'
        self.final_result_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client with provided API key
        self.client = OpenAI(api_key=api_key)
        
        # Maximum file size for Whisper API (25MB)
        self.MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes
    
    def get_excel_path(self, video_id):
        """Get the CSV file path for a specific video."""
        video_dir = self.final_result_dir / video_id
        video_dir.mkdir(parents=True, exist_ok=True)
        return video_dir / f"{video_id}_transcription.csv"
    
    def get_chunk_dir(self, video_id):
        """Get the directory for storing audio chunks."""
        chunk_dir = self.chunks_dir / video_id
        chunk_dir.mkdir(parents=True, exist_ok=True)
        return chunk_dir
    
    def split_audio_file(self, source_path, video_id):
        """Split large audio files into chunks for transcription."""
        try:
            # Load audio file
            audio = AudioSegment.from_file(source_path)
            
            # Get file size
            file_size = os.path.getsize(source_path)
            
            # If file is small enough, return it as a single chunk
            if file_size < self.MAX_FILE_SIZE:
                return [(source_path, 0, len(audio))]
            
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
    
    def transcribe_audio(self, source_path, video_id):
        """Transcribe audio file and save transcription data."""
        try:
            print(f"[DEBUG] Starting transcription for video {video_id}")
            # Split audio into chunks if needed
            chunks = self.split_audio_file(source_path, video_id)
            print(f"[DEBUG] Split audio into {len(chunks)} chunks")
            
            all_segments = []
            full_text = []
            
            # Process each chunk
            for i, (chunk_path, start_ms, end_ms) in enumerate(chunks):
                print(f"[DEBUG] Processing chunk {i+1}/{len(chunks)}")
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
            
            print(f"[DEBUG] Transcription completed. Creating transcription data")
            # Combine all transcriptions
            transcription_data = {
                'video_id': video_id,
                'source_path': source_path,
                'full_text': ' '.join(full_text),
                'segments': all_segments,
                'language': 'id',
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"[DEBUG] Saving transcription data to CSV")
            try:
                # Save to CSV
                self._save_to_csv(transcription_data)
                print(f"[DEBUG] CSV file saved successfully at {self.get_excel_path(video_id)}")
            except Exception as csv_error:
                print(f"[ERROR] Failed to save CSV file: {str(csv_error)}")
                return False, f"Transcription successful but failed to save CSV: {str(csv_error)}"
            
            # Clean up chunks if they were created
            if len(chunks) > 1:
                chunk_dir = self.get_chunk_dir(video_id)
                for chunk_file in chunk_dir.glob('*.ogg'):
                    os.remove(chunk_file)
                os.rmdir(chunk_dir)
            
            return True, transcription_data
            
        except Exception as e:
            print(f"[ERROR] Transcription failed: {str(e)}")
            return False, str(e)
    
    def _save_to_csv(self, transcription_data):
        """Save transcription data to CSV file."""
        try:
            video_id = transcription_data['video_id']
            csv_path = self.get_excel_path(video_id)
            print(f"[DEBUG] Preparing CSV data for {video_id}")
            
            # Convert source path to relative path
            source_path = Path(transcription_data['source_path'])
            video_dir = self.final_result_dir / video_id
            try:
                relative_path = source_path.relative_to(video_dir)
            except ValueError:
                # If path is already relative or can't be made relative, use original
                relative_path = source_path.name
            
            # Prepare segments data
            segments_data = []
            for segment in transcription_data['segments']:
                segments_data.append({
                    'video_id': video_id,
                    'source_path': str(relative_path),
                    'start_time_seconds': segment['start'],
                    'end_time_seconds': segment['end'],
                    'duration_seconds': segment['end'] - segment['start'],
                    'text': segment['text'].strip(),
                    'language': transcription_data['language'],
                    'timestamp': transcription_data['timestamp']
                })
            
            print(f"[DEBUG] Creating DataFrame with {len(segments_data)} segments")
            # Create DataFrame with segments
            segments_df = pd.DataFrame(segments_data)
            
            print(f"[DEBUG] Writing CSV file to {csv_path}")
            # Write segments to single sheet
            segments_df.to_csv(csv_path, index=False)
            print(f"[DEBUG] CSV file written successfully")
            
        except Exception as e:
            print(f"[ERROR] Error in _save_to_csv: {str(e)}")
            raise Exception(f"Failed to save CSV file: {str(e)}")
    
    def get_transcription(self, video_id):
        """Get transcription data for a specific video."""
        csv_path = self.get_excel_path(video_id)
        
        if not os.path.exists(csv_path):
            return None
        
        try:
            # Try reading from new format first
            try:
                segments_df = pd.read_csv(csv_path)
                return segments_df.to_dict('records')
            except ValueError:  # Sheet not found, try old format
                # Read from old format
                segments_df = pd.read_csv(csv_path)
                metadata_df = pd.read_csv(csv_path)
                
                # Convert to new format
                segments_data = []
                for _, segment in segments_df.iterrows():
                    segments_data.append({
                        'video_id': metadata_df['video_id'].iloc[0],
                        'source_path': str(Path(metadata_df['source_path'].iloc[0]).relative_to(Path.cwd())),
                        'start_time_seconds': segment['start_time'],
                        'end_time_seconds': segment['end_time'],
                        'duration_seconds': segment['end_time'] - segment['start_time'],
                        'text': segment['text'],
                        'language': segment['language'],
                        'timestamp': metadata_df['timestamp'].iloc[0]
                    })
                
                # Save in new format for future use
                new_df = pd.DataFrame(segments_data)
                new_df.to_csv(csv_path, index=False)
                
                return segments_data
                
        except Exception as e:
            print(f"Error reading transcription: {e}")
            return None
    
    def has_transcription(self, video_id):
        """Check if transcription exists for a video."""
        csv_path = self.get_excel_path(video_id)
        return os.path.exists(csv_path)
