from typing import Final
import os
from dotenv import load_dotenv
from discord.ext import commands
from discord import Intents, Attachment
from responses import get_response

# Load the environment variables
load_dotenv()

TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Set up the bot with a command prefix
intents: Intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Command: Ping
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

# Command: Info
@bot.command(name='info')
async def info(ctx):
    info_text = """
    **Bot Information:**
    - Name: AI Discord Bot
    - Version: 1.0.0
    - Description: A Discord bot that uses OpenAI's GPT-4o model to generate responses to user messages.
    """
    await ctx.send(info_text)

# Command: Help
@bot.command(name='help')
async def help_command(ctx):
    help_text = """
    **Available Commands:**
    `!ping` - Check if the bot is responsive.
    `!info` - Get information about the bot.
    `!help` - Display this help message.
    `!lumos <message>` - Interact with the bot using the AI model.
    """
    await ctx.send(help_text)

# Command: Process message with !lumos prefix
@bot.command(name='lumos')
async def lumos(ctx, *, user_message: str = None):
    image_file = None
    image_format = None

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        image_file = attachment.filename
        image_format = attachment.filename.split('.')[-1]
        await attachment.save(image_file)

    response = await get_response(user_message or "", image_file, image_format)
    response_chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
    
    for chunk in response_chunks:
        await ctx.send(chunk)

# Main entry point
def main():
    bot.run(TOKEN)

if __name__ == '__main__':
    main()