import os
from pathlib import Path
from dotenv import load_dotenv, set_key

class ConfigService:
    def __init__(self):
        self.env_path = Path('.env')
        # Create .env file if it doesn't exist
        if not self.env_path.exists():
            self.env_path.touch()
        load_dotenv(self.env_path)

    def get_api_key(self, key_name):
        """Get API key from environment variables"""
        return os.getenv(key_name, '')

    def set_api_key(self, key_name, value):
        """Set API key in .env file"""
        try:
            # Remove any surrounding whitespace or quotes
            value = value.strip().strip("'").strip('"')
            
            # Update .env file
            set_key(self.env_path, key_name, value)
            
            # Also update current environment
            os.environ[key_name] = value
            return True, "API key updated successfully"
        except Exception as e:
            return False, f"Error updating API key: {str(e)}"

    def validate_youtube_api_key(self, api_key):
        """Basic validation for YouTube API key format"""
        if not api_key:
            return False, "API key cannot be empty"
        if not api_key.startswith('AIza'):
            return False, "Invalid YouTube API key format"
        return True, "Valid API key format"

    def validate_openai_api_key(self, api_key):
        """Basic validation for OpenAI API key format"""
        if not api_key:
            return False, "API key cannot be empty"
        if not api_key.startswith('sk-'):
            return False, "Invalid OpenAI API key format"
        return True, "Valid API key format"
