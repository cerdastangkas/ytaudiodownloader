from pathlib import Path
import pandas as pd
from pydub import AudioSegment
import os

class AudioSplitter:
    def __init__(self):
        """Initialize the audio splitter service."""
        self.splits_dir = Path('data/splits')
        self.splits_dir.mkdir(parents=True, exist_ok=True)
    
    def get_splits_directory(self, video_id):
        """Get the directory for storing splits of a specific video."""
        splits_dir = self.splits_dir / video_id
        splits_dir.mkdir(parents=True, exist_ok=True)
        return splits_dir
    
    def is_already_split(self, video_id):
        """Check if audio has already been split."""
        splits_dir = self.get_splits_directory(video_id)
        # Check for either mp3 or ogg files
        has_splits = any(splits_dir.glob('*.mp3')) or any(splits_dir.glob('*.ogg')) or any(splits_dir.glob('*.wav'))
        return has_splits and splits_dir.exists()
    
    def get_splits(self, transcription_path):
        """Get information about splits for a video."""
        try:
            try:
                # Try new format first
                transcription_df = pd.read_excel(transcription_path, sheet_name='Transcription')
            except ValueError:  # Sheet not found, try old format
                splits_df = pd.read_excel(transcription_path, sheet_name='Splits')
                if not splits_df.empty:
                    return splits_df.to_dict('records')
                return []
                
            splits = transcription_df.to_dict('records')
            
            # Filter out splits where audio file doesn't exist
            valid_splits = []
            for split in splits:
                if 'audio_file' in split and os.path.exists(split['audio_file']):
                    valid_splits.append(split)
            
            return valid_splits
            
        except Exception as e:
            print(f"Error getting splits: {e}")
            return []
    
    def split_audio(self, audio_path, video_id, transcription_path, output_format='wav'):
        """Split audio file based on transcription segments.
        
        Args:
            audio_path: Path to the source audio file
            video_id: Video ID for organizing splits
            transcription_path: Path to the transcription Excel file
            output_format: Format to save split files in ('wav' recommended for high quality)
        """
        try:
            # Read transcription data - handle both old and new formats
            try:
                transcription_df = pd.read_excel(transcription_path, sheet_name='Transcription')
            except ValueError:  # Sheet not found, try old format
                segments_df = pd.read_excel(transcription_path, sheet_name='Segments')
                metadata_df = pd.read_excel(transcription_path, sheet_name='Metadata')
                
                # Convert to new format
                segments_data = []
                for _, segment in segments_df.iterrows():
                    segments_data.append({
                        'video_id': metadata_df['video_id'].iloc[0],
                        'audio_path': metadata_df['audio_path'].iloc[0],
                        'start_time_seconds': segment['start_time'],
                        'end_time_seconds': segment['end_time'],
                        'duration_seconds': segment['end_time'] - segment['start_time'],
                        'text': segment['text'],
                        'language': segment['language'],
                        'timestamp': metadata_df['timestamp'].iloc[0]
                    })
                transcription_df = pd.DataFrame(segments_data)
            
            # Load audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Get splits directory for this video
            splits_dir = self.get_splits_directory(video_id)
            
            # Clear existing splits if any
            for ext in ['mp3', 'ogg', 'wav']:
                for existing_file in splits_dir.glob(f'*.{ext}'):
                    try:
                        os.remove(existing_file)
                    except OSError:
                        pass  # Ignore errors when removing files
            
            # Process each segment
            split_info = []
            for idx, segment in transcription_df.iterrows():
                # Convert times to milliseconds
                start_ms = int(segment['start_time_seconds'] * 1000)
                end_ms = int(segment['end_time_seconds'] * 1000)
                
                # Extract segment
                segment_audio = audio[start_ms:end_ms]
                
                # Generate filename with video ID
                filename = f"{video_id}_segment_{idx:03d}.{output_format}"
                output_path = splits_dir / filename
                
                # Export segment with appropriate settings
                try:
                    if output_format == 'wav':
                        # Export as 24-bit WAV with 48kHz sample rate
                        segment_audio.export(
                            str(output_path),
                            format="wav",
                            parameters=[
                                "-acodec", "pcm_s24le",  # 24-bit depth
                                "-ar", "48000"  # 48kHz sample rate
                            ]
                        )
                    elif output_format == 'mp3':
                        segment_audio.export(
                            str(output_path),
                            format="mp3",
                            bitrate="192k",
                            parameters=["-q:a", "0"]
                        )
                    else:
                        segment_audio.export(str(output_path), format=output_format)
                    
                    # Only add to split_info if export was successful
                    split_info.append({
                        'video_id': video_id,
                        'filename': filename,
                        'relative_path': str(output_path.relative_to(self.splits_dir)),
                        'audio_file': str(output_path),
                        'start_time_seconds': segment['start_time_seconds'],
                        'end_time_seconds': segment['end_time_seconds'],
                        'duration_seconds': segment['duration_seconds'],
                        'text': segment['text'],
                        'language': segment['language'],
                        'timestamp': segment['timestamp']
                    })
                except Exception as e:
                    print(f"Error exporting segment {idx}: {e}")
                    continue
            
            if not split_info:
                return False, "Failed to create any valid splits"
            
            # Update Excel file with split information
            splits_df = pd.DataFrame(split_info)
            
            try:
                # Read existing Excel file
                with pd.ExcelFile(transcription_path) as xls:
                    transcription_df = pd.read_excel(xls, sheet_name='Transcription')
            except Exception as e:
                print(f"Error reading existing Excel file: {e}")
                transcription_df = pd.DataFrame()
            
            # Create a new Excel writer
            with pd.ExcelWriter(transcription_path, engine='openpyxl') as writer:
                # Update transcription data with split information
                transcription_df['filename'] = splits_df['filename']
                transcription_df['relative_path'] = splits_df['relative_path']
                transcription_df['audio_file'] = splits_df['audio_file']
                
                # Write updated transcription data
                transcription_df.to_excel(writer, sheet_name='Transcription', index=False)
            
            return True, f"Split {len(split_info)} segments successfully"
            
        except Exception as e:
            return False, str(e)
