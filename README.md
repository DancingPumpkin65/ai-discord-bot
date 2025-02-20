# AI Discord Bot

This is a Discord bot that uses OpenAI's GPT-4o model to generate responses to user messages. The bot is built using the `discord` library and interacts with the OpenAI API to generate responses.

## Project Structure

```text
    ai-discord-bot
    ├── .env                   # Environment variables
    ├── main.py                # The main bot service that handles Discord events
    ├── responses.py           # The module that provides responses to user inputs using your AI Model
    ├── requirements.txt       # Project dependencies
    └── README.md              # Project documentation
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
    Create a `.env` file in the root directory and add your Discord token:
```sh
    DISCORD_TOKEN=YOUR_DISCORD_TOKEN
    OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

## Running the Discord Bot

1. Start the bot:
```sh
python main.py
```

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.