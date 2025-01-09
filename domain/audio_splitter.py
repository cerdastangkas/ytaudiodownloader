from pathlib import Path
import pandas as pd
from pydub import AudioSegment
import os

class AudioSplitter:
    def __init__(self):
        """Initialize the audio splitter service."""
        self.final_result_dir = Path('data/final_result')
        self.final_result_dir.mkdir(parents=True, exist_ok=True)
    
    def get_splits_directory(self, video_id):
        """Get the directory for storing splits of a specific video."""
        splits_dir = self.final_result_dir / video_id / 'split'
        splits_dir.mkdir(parents=True, exist_ok=True)
        return splits_dir
    
    def is_already_split(self, video_id):
        """Check if audio has already been split."""
        splits_dir = self.get_splits_directory(video_id)
        # Check for either mp3 or ogg files
        has_splits = any(splits_dir.glob('*.mp3')) or any(splits_dir.glob('*.ogg')) or any(splits_dir.glob('*.wav'))
        return has_splits and splits_dir.exists()
    
    def has_wav_splits(self, video_id):
        """Check if video has WAV format splits."""
        splits_dir = self.get_splits_directory(video_id)
        return any(splits_dir.glob('*.wav')) if splits_dir.exists() else False

    def has_splits(self, video_id):
        """Check if video has any splits."""
        splits_dir = self.get_splits_directory(video_id)
        return any(splits_dir.glob('*.*')) if splits_dir.exists() else False
    
    def get_splits(self, transcription_path):
        """Get information about splits for a video."""
        try:
            transcription_df = pd.read_csv(transcription_path)
            splits = transcription_df.to_dict('records')
            
            # Filter out splits where audio file doesn't exist
            valid_splits = []
            for split in splits:
                if 'audio_file' in split and os.path.exists(os.path.join(os.path.dirname(transcription_path), split['audio_file'])):
                    valid_splits.append(split)
            
            return valid_splits
            
        except Exception as e:
            print(f"Error getting splits: {e}")
            return []
    
    def get_splitted_audio_path(self, video_id, audio_file):
        """Get the path to a specific split audio file."""
        return str(self.final_result_dir / video_id / audio_file)
    
    def split_audio(self, source_path, video_id, transcription_path, output_format='wav'):
        """Split audio file based on transcription segments.
        
        Args:
            source_path: Path to the source audio file
            video_id: Video ID for organizing splits
            transcription_path: Path to the transcription CSV file
            output_format: Format to save split files in ('wav' recommended for high quality)
        """
        try:
            # Read transcription data
            transcription_df = pd.read_csv(transcription_path)
            
            # Load audio file
            print(f"[DEBUG] Loading audio file from {source_path}")
            audio = AudioSegment.from_file(source_path)
            
            # Get splits directory for this video
            splits_dir = self.get_splits_directory(video_id)
            print(f"[DEBUG] Using splits directory: {splits_dir}")
            
            # Clear existing splits if any
            for ext in ['mp3', 'ogg', 'wav']:
                for existing_file in splits_dir.glob(f'*.{ext}'):
                    try:
                        os.remove(existing_file)
                    except OSError as e:
                        print(f"[WARNING] Could not remove existing file {existing_file}: {e}")
            
            # Process each segment
            split_info = []
            for idx, segment in transcription_df.iterrows():
                try:
                    # Convert times to milliseconds
                    start_ms = int(segment['start_time_seconds'] * 1000)
                    end_ms = int(segment['end_time_seconds'] * 1000)
                    
                    print(f"[DEBUG] Processing segment {idx}: {start_ms}ms to {end_ms}ms")
                    
                    # Extract segment
                    segment_audio = audio[start_ms:end_ms]
                    
                    # Generate filename with video ID
                    filename = f"{video_id}_segment_{idx:03d}.{output_format}"
                    output_path = splits_dir / filename
                    
                    print(f"[DEBUG] Exporting segment to {output_path}")
                    
                    # Export segment with appropriate settings
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
                    
                    # Store relative path from transcription file location
                    relative_path = f"split/{filename}"
                    
                    # Only add to split_info if export was successful
                    split_info.append({
                        'video_id': video_id,
                        'audio_file': relative_path,  # Use relative path
                        'start_time_seconds': segment['start_time_seconds'],
                        'end_time_seconds': segment['end_time_seconds'],
                        'duration_seconds': segment['duration_seconds'],
                        'text': segment['text'],
                        'language': segment['language'],
                        'timestamp': segment['timestamp']
                    })
                    print(f"[DEBUG] Successfully processed segment {idx}")
                except Exception as e:
                    print(f"[ERROR] Failed to process segment {idx}: {e}")
                    continue
            
            if not split_info:
                return False, "Failed to create any valid splits"
            
            # Update CSV file with split information
            splits_df = pd.DataFrame(split_info)
            
            # Update transcription data with split information
            transcription_df['audio_file'] = splits_df['audio_file']
            
            # Write updated transcription data
            transcription_df.to_csv(transcription_path, index=False)
            
            return True, f"Split {len(split_info)} segments successfully"
            
        except Exception as e:
            print(f"[ERROR] Split audio failed: {e}")
            return False, str(e)
