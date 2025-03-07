from typing import Final
import os
import time
import platform
import datetime
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import Intents, Attachment, Embed, version_info as discord_version
from responses import get_response

# Load the environment variables
load_dotenv()

TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
BOT_VERSION: Final[str] = "1.0.0"
BOT_CREATOR: Final[str] = "MAHITO"
ANNOUNCEMENT_CHANNEL_ID: Final[int] = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID', '0'))  # Set your default channel ID in .env

# Track start time for uptime command
start_time = time.time()

# Set up the bot with a command prefix
intents: Intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_uptime() -> str:
    """Calculate and format the bot's uptime"""
    uptime_seconds = int(time.time() - start_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # Start the daily announcement task
    if not daily_announcement.is_running():
        daily_announcement.start()
        print("Daily announcement task started.")

# Enhanced Command: Ping with latency
@bot.command(name='ping')
async def ping(ctx):
    start_time = time.time()
    msg = await ctx.send('Pinging...')
    end_time = time.time()
    
    # Calculate ping in ms
    ping_latency = round((end_time - start_time) * 1000)
    await msg.edit(content=f'Pong! Latency: {ping_latency}ms | API Latency: {round(bot.latency * 1000)}ms')

# Enhanced Command: Info with more details
@bot.command(name='info')
async def info(ctx):
    embed = Embed(title="Bot Information", color=0x2ecc71)
    embed.add_field(name="Name", value="AI Discord Bot", inline=True)
    embed.add_field(name="Version", value=BOT_VERSION, inline=True)
    embed.add_field(name="Creator", value=BOT_CREATOR, inline=True)
    embed.add_field(name="Discord.py Version", value=f"{discord_version.major}.{discord_version.minor}.{discord_version.micro}", inline=True)
    embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
    embed.add_field(name="Platform", value=platform.system() + " " + platform.release(), inline=True)
    embed.add_field(name="Uptime", value=get_uptime(), inline=True)
    embed.add_field(name="Description", value="A Discord bot that uses OpenAI's GPT-4o model to generate responses to user messages.", inline=False)
    embed.set_footer(text="Use !help to see available commands")
    
    await ctx.send(embed=embed)

# Enhanced Command: Help with embeds
@bot.command(name='help')
async def help_command(ctx):
    embed = Embed(title="Bot Help", description="List of available commands:", color=0x3498db)
    embed.add_field(name="!help", value="Shows this help message", inline=False)
    embed.add_field(name="!info", value="Shows information about the bot", inline=False)
    embed.add_field(name="!ping", value="Shows the bot's latency", inline=False)
    embed.add_field(name="!lumos <message>", value="Interact with the bot using the AI model", inline=False)
    embed.set_footer(text=f"Bot created by {BOT_CREATOR}")
    
    await ctx.send(embed=embed)

# Command: Process message with !lumos prefix
@bot.command(name='lumos')
async def lumos(ctx, *, user_message: str = None):
    try:
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
            
    except Exception as e:
        print(f"Error in lumos command: {str(e)}")
        await ctx.send("Sorry, I encountered an error while processing your request.")

# Define the daily scheduled task
@tasks.loop(hours=24)
async def daily_announcement():
    if ANNOUNCEMENT_CHANNEL_ID == 0:
        print("WARNING: No announcement channel ID set. Skipping daily announcement.")
        return
    
    try:
        channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if channel:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            embed = Embed(
                title="Daily Announcement", 
                description="This is an automated daily announcement from AI Discord Bot.", 
                color=0x9b59b6
            )
            embed.add_field(name="Current Date", value=current_time, inline=False)
            embed.add_field(name="Bot Uptime", value=get_uptime(), inline=False)
            embed.set_footer(text=f"Bot Version: {BOT_VERSION}")
            
            await channel.send(embed=embed)
            print(f"Daily announcement sent at {current_time}")
        else:
            print(f"ERROR: Could not find channel with ID {ANNOUNCEMENT_CHANNEL_ID}")
    except Exception as e:
        print(f"ERROR: Failed to send daily announcement: {str(e)}")

# Error handling for commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Bad argument: {str(error)}")
    else:
        print(f"Command error: {str(error)}")
        await ctx.send(f"An error occurred while executing the command: {str(error)}")

# Main entry point
def main():
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Failed to start the bot: {str(e)}")
        
        # Check for common errors
        if not TOKEN:
            print("ERROR: DISCORD_TOKEN is not set in your .env file")
        elif "improper token" in str(e).lower():
            print("ERROR: Your Discord token appears to be invalid")

if __name__ == '__main__':
    main()