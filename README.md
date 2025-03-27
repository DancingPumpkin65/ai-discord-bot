# AI Discord Bot

This is a Discord bot that uses OpenAI's GPT-4o model to generate responses to user messages. The bot is built using the `discord.py` library and interacts with the OpenAI API to generate responses.

## Project Structure

The bot is organized into a modular structure:
```text
    ai-discord-bot
    ├── .env                   # Environment variables
    ├── .env.example           # Example environment variables configuration
    ├── main.py                # The main bot service that handles Discord events
    ├── config.py              # Configuration settings
    ├── cogs/                  # Command modules
    ├── core/                  # Core functionality
    ├── services/              # Service modules 
    ├── utils/                 # Utility functions
    ├── assets/                # Static assets
    ├── lavalink/              # Lavalink server (music)
    └── requirements.txt       # Project dependencies
```

## Setup

1. Clone the repository:
```sh
    git clone https://github.com/DancingPumpkin65/ai-discord-bot.git
    cd ai-discord-bot
```

2. Create and activate a virtual environment:
```sh
    python -m venv env
    source env/Scripts/activate  # On Windows
    source env/bin/activate      # On Unix or MacOS
```

3. Install the dependencies:
```sh
    pip install -r requirements.txt
```

4. Set up the environment variables:
    Create a `.env` file in the root directory based on the `.env.example` file:
```sh
    DISCORD_TOKEN=YOUR_DISCORD_TOKEN
    OPENAI_API_KEY=YOUR_OPENAI_API_KEY
    ANNOUNCEMENT_CHANNEL_ID=YOUR_CHANNEL_ID
    AZURE_ENDPOINT=https://models.inference.ai.azure.com
    MODEL_NAME=gpt-4o
    
    # For music functionality:
    SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID
    SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET
```

5. Set up Lavalink (required for music functionality):
   - Make sure you have Java 11 or newer installed
   - Run the setup script: `python setup_lavalink.py`
   - Alternatively, download [Lavalink.jar](https://github.com/lavalink-devs/Lavalink/releases) manually and place it in the `lavalink` folder

## Running the Discord Bot

1. Start Lavalink (if using music features):
```sh
    # In one terminal:
    cd lavalink
    java -jar Lavalink.jar
```

2. Start the bot:
```sh
    # In another terminal:
    python main.py
```

## Features

### AI Conversation
Use the `!lumos` command to have a conversation with the AI:
```sh
!lumos <your question or message>  # Start a conversation with the AI
!memory show                       # Show your conversation history
!memory clear                      # Clear your conversation history
```

### Music Player
The bot can play music from YouTube and Spotify:
```sh
!play <song name or URL>    # Play a song or add to queue
!play <spotify playlist URL> # Play a Spotify playlist
!pause                      # Pause the current song
!resume                     # Resume playback
!skip                       # Skip to the next song
!stop                       # Stop playback and clear queue
!queue                      # Show the current queue
!np                         # Show the currently playing song
!volume <0-100>             # Adjust the volume
```

### Welcome Cards
The bot creates beautiful welcome cards for new members with:
- Customizable backgrounds (URL or uploaded images)
- Member count and personalized welcome message
- Professionally designed layout with user's avatar

To manage welcome backgrounds:
```sh
!backgrounds list              # List all available backgrounds
!backgrounds add name URL      # Add a background from URL
!backgrounds add name          # Add a background from attachment
!backgrounds preview name      # Preview a background
!backgrounds remove name       # Remove a background
!backgrounds set-default name  # Set the default background
```

Test welcome cards with:
```sh
!welcome                       # Test with default background
!welcome background-name       # Test with specific background
!welcome random                # Test with random background
```

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.