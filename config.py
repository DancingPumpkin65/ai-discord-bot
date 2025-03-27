"""
AI Discord Bot - Configuration Module

This module centralizes configuration settings and constants for the bot.
"""
import os
from typing import Final
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Information
BOT_VERSION: Final[str] = "2.5.0"
BOT_CREATOR: Final[str] = "MAHITO"
DEFAULT_PREFIX: Final[str] = "!"

# Discord API Token
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Channel IDs
ANNOUNCEMENT_CHANNEL_ID: Final[int] = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID', '0'))
WELCOME_CHANNEL_ID: Final[int] = int(os.getenv('WELCOME_CHANNEL_ID', '0'))

# AI Configuration
OPENAI_API_KEY: Final[str] = os.getenv('OPENAI_API_KEY')
AZURE_ENDPOINT: Final[str] = os.getenv('AZURE_ENDPOINT', 'https://models.inference.ai.azure.com')
MODEL_NAME: Final[str] = os.getenv('MODEL_NAME', 'gpt-4o')

# Welcome Card Configuration
WELCOME_BACKGROUND_URL: Final[str] = os.getenv('WELCOME_BACKGROUND_URL', '')
USE_RANDOM_BACKGROUNDS: Final[bool] = os.getenv('USE_RANDOM_BACKGROUNDS', 'false').lower() == 'true'

# Memory Configuration
MAX_MEMORY_LENGTH: Final[int] = int(os.getenv('MAX_MEMORY_LENGTH', '10'))

# Music Configuration
SPOTIFY_CLIENT_ID: Final[str] = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET: Final[str] = os.getenv('SPOTIFY_CLIENT_SECRET', '')
LAVALINK_HOST: Final[str] = os.getenv('LAVALINK_HOST', '127.0.0.1')
LAVALINK_PORT: Final[int] = int(os.getenv('LAVALINK_PORT', '2333'))
LAVALINK_PASSWORD: Final[str] = os.getenv('LAVALINK_PASSWORD', 'youshallnotpass')

# Available commands dictionary for suggestions
COMMANDS = {
    'help': 'Shows the help message with available commands',
    'info': 'Shows information about the bot',
    'ping': 'Shows the bot\'s latency',
    'lumos': 'Interact with the bot using the AI model',
    'memory': 'View or clear your conversation history with the bot',
    'play': 'Play music from YouTube or Spotify',
    'pause': 'Pause the current song',
    'resume': 'Resume playback',
    'skip': 'Skip to the next song',
    'stop': 'Stop playback and clear the queue',
    'queue': 'Show the current music queue',
    'welcome': 'Test the welcome card feature (admin only)',
    'backgrounds': 'Manage welcome card backgrounds (admin only)'
}

# Color schemes
COLORS = {
    'success': 0x2ecc71,  # Green
    'info': 0x3498db,     # Blue
    'warning': 0xf39c12,  # Orange
    'error': 0xe74c3c,    # Red
    'purple': 0x9b59b6    # Purple
}
