import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


class Config:
    """System-wide configuration settings"""

    # YouTube API Configuration
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    YOUTUBE_API_VERSION = 'v3'

    # Firebase Configuration
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    FIREBASE_CREDENTIALS_PATH = os.getenv(
        'FIREBASE_CREDENTIALS_PATH', 'deployment/firebase/credentials.json')

    # Claude AI Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    CLAUDE_MODEL = 'claude-3-sonnet-20240229'

    # Analysis Parameters
    MAX_VIDEOS_PER_SEARCH = 50
    DEFAULT_REGION_CODE = 'US'
    DEFAULT_LANGUAGE = 'en'

    # Scoring Weights
    SENTIMENT_WEIGHT = 0.3
    ENGAGEMENT_WEIGHT = 0.4
    CREDIBILITY_WEIGHT = 0.3

    # Directory Configuration
    PROJECT_ROOT = Path(__file__).parent
    OUTPUT_DIR = PROJECT_ROOT / 'output'
    MODELS_DIR = PROJECT_ROOT / 'models'

    # MCP Server Configuration
    MCP_SERVER_NAME = 'youtube-intelligence'
    MCP_SERVER_VERSION = '1.0.0'
    MCP_SERVER_PORT = 8000

    # Rate Limiting
    API_RATE_LIMIT = 100  # requests per minute

    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        required_vars = [
            'YOUTUBE_API_KEY',
            'FIREBASE_PROJECT_ID',
            'ANTHROPIC_API_KEY'
        ]

        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}")

        return True


# .env template file
ENV_TEMPLATE = """
# YouTube Intelligence MCP Server - Environment Configuration
# Episode 3: Configuration & API Setup

# YouTube Data API
YOUTUBE_API_KEY=your_youtube_api_key_here

# Firebase Configuration
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_CREDENTIALS_PATH=deployment/firebase/credentials.json

# Claude AI API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Custom Settings
MAX_VIDEOS_PER_SEARCH=50
DEFAULT_REGION_CODE=US
DEFAULT_LANGUAGE=en
"""

if __name__ == "__main__":
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(ENV_TEMPLATE)
        print("Created .env template file. Please fill in your API keys.")
    else:
        print("Configuration file already exists.")

    # Validate configuration
    try:
        Config.validate_config()
        print("Configuration validated successfully!")
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file and add missing API keys.")
