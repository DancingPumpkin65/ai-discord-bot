# AI Discord Bot

This is a Discord bot that uses OpenAI's GPT-4o model to generate responses to user messages. The bot is built using the `discord` library and interacts with the OpenAI API to generate responses.

## Project Structure

```text
    ai-discord-bot
    ├── .env                   # Environment variables
    ├── .env.example           # Example environment variables configuration
    ├── main.py                # The main bot service that handles Discord events
    ├── responses.py           # The module that provides responses to user inputs using your AI Modelides responses to user inputs using your AI Model
    ├── requirements.txt       # Project dependencies
    └── README.md              # Project documentation └── README.md              # Project documentation
```

## Setup## Setup

1. Clone the repository:one the repository:
```sh
    git clone https://github.com/DancingPumpkin65/ai-discord-bot.git/github.com/DancingPumpkin65/ai-discord-bot.git
    cd ai-discord-bot cd ai-discord-bot
``````

2. Create and activate a virtual environment:eate and activate a virtual environment:
```sh
    python -m venv env
    source env/Scripts/activate  # On Windows
    source env/bin/activate      # On Unix or MacOS source env/bin/activate      # On Unix or MacOS
``````

3. Install the dependencies:stall the dependencies:
```sh
    pip install -r requirements.txt pip install -r requirements.txt
``````

4. Set up the environment variables:
    Create a `.env` file in the root directory based on `.env.example`:reate a `.env` file in the root directory based on the `.env.example` file:
```sh
    DISCORD_TOKEN=YOUR_DISCORD_TOKEN
    OPENAI_API_KEY=YOUR_OPENAI_API_KEY
    ANNOUNCEMENT_CHANNEL_ID=YOUR_CHANNEL_ID DISCORD_TOKEN=YOUR_DISCORD_TOKEN
    AZURE_ENDPOINT=https://models.inference.ai.azure.com    OPENAI_API_KEY=YOUR_OPENAI_API_KEY
    MODEL_NAME=gpt-4oD=YOUR_CHANNEL_ID
```    AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
SION=2023-05-15
## Running the Discord BotZURE_DEPLOYMENT_NAME=deployment-name

1. Start the bot:
```sh    For standard OpenAI API:
python main.py
```

## Features

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