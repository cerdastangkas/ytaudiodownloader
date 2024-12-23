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
    
    def get_splits(self, video_id, transcription_path):
        """Get information about splits for a video."""
        try:
            splits_df = pd.read_excel(transcription_path, sheet_name='Splits')
            splits = splits_df.to_dict('records')
            
            # Filter out splits where audio file doesn't exist
            valid_splits = []
            for split in splits:
                if os.path.exists(split['audio_file']):
                    valid_splits.append(split)
                else:
                    # Try to find the file with a different extension
                    base_path = os.path.splitext(split['audio_file'])[0]
                    mp3_path = f"{base_path}.mp3"
                    ogg_path = f"{base_path}.ogg"
                    wav_path = f"{base_path}.wav"
                    
                    if os.path.exists(mp3_path):
                        split['audio_file'] = mp3_path
                        valid_splits.append(split)
                    elif os.path.exists(ogg_path):
                        split['audio_file'] = ogg_path
                        valid_splits.append(split)
                    elif os.path.exists(wav_path):
                        split['audio_file'] = wav_path
                        valid_splits.append(split)
            
            return valid_splits if valid_splits else None
            
        except Exception:
            return None
    
    def split_audio(self, audio_path, video_id, transcription_path, output_format='wav'):
        """Split audio file based on transcription segments.
        
        Args:
            audio_path: Path to the source audio file
            video_id: Video ID for organizing splits
            transcription_path: Path to the transcription Excel file
            output_format: Format to save split files in ('wav' recommended for high quality)
        """
        try:
            # Read transcription data
            segments_df = pd.read_excel(transcription_path, sheet_name='Segments')
            
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
            for idx, segment in segments_df.iterrows():
                # Convert times to milliseconds
                start_ms = int(segment['start_time'] * 1000)
                end_ms = int(segment['end_time'] * 1000)
                
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
                        'segment_index': idx,
                        'start_time': segment['start_time'],
                        'end_time': segment['end_time'],
                        'text': segment['text'],
                        'audio_file': str(output_path),
                        'duration': (end_ms - start_ms) / 1000,  # Duration in seconds
                        'filename': filename,
                        'relative_path': str(output_path.relative_to(self.splits_dir))
                    })
                except Exception as e:
                    print(f"Error exporting segment {idx}: {e}")
                    continue
            
            if not split_info:
                return False, "Failed to create any valid splits"
            
            # Update Excel file with split information
            splits_df = pd.DataFrame(split_info)
            
            # Create a new Excel writer
            with pd.ExcelWriter(transcription_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                # Write splits information to 'Splits' sheet
                splits_df.to_excel(writer, sheet_name='Splits', index=False)
                
                # Create a mapping sheet with filename and text
                mapping_df = pd.DataFrame({
                    'filename': splits_df['filename'],
                    'relative_path': splits_df['relative_path'],
                    'duration': splits_df['duration'],
                    'text': splits_df['text'],
                    'start_time': splits_df['start_time'],
                    'end_time': splits_df['end_time']
                })
                mapping_df.to_excel(writer, sheet_name='AudioTextMapping', index=False)
            
            return True, f"Split {len(split_info)} segments successfully"
            
        except Exception as e:
            return False, str(e)
