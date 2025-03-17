from typing import Final
import os
import time
import platform
import datetime
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import Intents, Attachment, Embed, version_info as discord_version
from responses import get_response
import difflib  # For finding similar commands
import discord
from welcome_card import create_welcome_card, create_welcome_embed

# Load the environment variables
load_dotenv()

TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
BOT_VERSION: Final[str] = "1.0.0"
BOT_CREATOR: Final[str] = "MAHITO"
ANNOUNCEMENT_CHANNEL_ID: Final[int] = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID', '0'))  # Set your default channel ID in .env
WELCOME_CHANNEL_ID: Final[int] = int(os.getenv('WELCOME_CHANNEL_ID', '0'))  # Channel ID for welcome messages
WELCOME_BACKGROUND_URL: Final[str] = os.getenv('WELCOME_BACKGROUND_URL', '')  # Optional background image URL

# Bot memory storage for conversations
USER_CONVERSATIONS = {}  # Store conversation history by user ID
MAX_MEMORY_LENGTH = 10   # Maximum number of conversation turns to remember

# Track start time for uptime command
start_time = time.time()

# Set up the bot with a command prefix
intents: Intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # Disable default help to use our custom one

# Available commands dictionary for suggestions
COMMANDS = {
    'help': 'Shows the help message with available commands',
    'info': 'Shows information about the bot',
    'ping': 'Shows the bot\'s latency',
    'lumos': 'Interact with the bot using the AI model',
    'memory': 'View or clear your conversation history with the bot',
    'config': 'Configure bot settings for this server (admin only)',
    'welcome': 'Test the welcome card feature (admin only)'
}

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

def get_command_suggestion(cmd: str) -> str:
    """Get a command suggestion based on user input"""
    # Get list of available commands
    available_commands = list(COMMANDS.keys())
    
    # Find closest match
    matches = difflib.get_close_matches(cmd, available_commands, n=1, cutoff=0.5)
    if matches:
        return matches[0]
    return None

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # Start the daily announcement task
    if not daily_announcement.is_running():
        daily_announcement.start()
        print("Daily announcement task started.")

    # Set status
    activity = discord.Activity(type=discord.ActivityType.listening, name="!help")
    await bot.change_presence(activity=activity)

# Enhanced Command: Ping with latency
@bot.command(name='ping')
async def ping(ctx):
    """Shows the bot's latency"""
    start_time = time.time()
    msg = await ctx.send('Pinging...')
    end_time = time.time()
    
    # Calculate ping in ms
    ping_latency = round((end_time - start_time) * 1000)
    await msg.edit(content=f'Pong! Latency: {ping_latency}ms | API Latency: {round(bot.latency * 1000)}ms')

# Enhanced Command: Info with more details
@bot.command(name='info')
async def info(ctx):
    """Shows information about the bot"""
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
async def help_command(ctx, command_name: str = None):
    """Shows the help message with available commands"""
    if command_name:
        # Show help for specific command
        cmd_name = command_name.lower().strip()
        
        # Handle commands with aliases or additional details
        if cmd_name in COMMANDS:
            embed = Embed(title=f"Help: !{cmd_name}", description=COMMANDS[cmd_name], color=0x3498db)
            
            # Add specific usage examples
            if cmd_name == 'lumos':
                embed.add_field(name="Usage", value="!lumos <your question or prompt>", inline=False)
                embed.add_field(name="Example", value="!lumos What is artificial intelligence?", inline=False)
                embed.add_field(name="With Image", value="You can also attach an image with your prompt", inline=False)
            elif cmd_name == 'ping':
                embed.add_field(name="Usage", value="!ping", inline=False)
                embed.add_field(name="Description", value="Shows the bot's response time and API latency", inline=False)
            
            embed.set_footer(text="Type !help for a list of all commands")
        else:
            # Command not found - suggest similar commands
            suggestion = get_command_suggestion(cmd_name)
            embed = Embed(title="Command Not Found", color=0xe74c3c)
            embed.description = f"The command `!{cmd_name}` was not found."
            
            if suggestion:
                embed.add_field(name="Did you mean?", value=f"!{suggestion}", inline=False)
            
            embed.add_field(name="Available Commands", value="Type `!help` to see all available commands", inline=False)
            
        await ctx.send(embed=embed)
    else:
        # Show general help
        embed = Embed(title="Bot Help", description="List of available commands:", color=0x3498db)
        
        for cmd, desc in COMMANDS.items():
            embed.add_field(name=f"!{cmd}", value=desc, inline=False)
            
        embed.add_field(name="Detailed Help", value="Type `!help <command>` for more info on a specific command", inline=False)
        embed.set_footer(text=f"Bot created by {BOT_CREATOR}")
        
        await ctx.send(embed=embed)

# Command: Process message with !lumos prefix
@bot.command(name='lumos')
async def lumos(ctx, *, user_message: str = None):
    """Interact with the bot using the AI model"""
    # If no message provided
    if not user_message and not ctx.message.attachments:
        await ctx.send("Please provide a message or attach an image. Type `!help lumos` for usage examples.")
        return
        
    try:
        # Show typing indicator while processing
        async with ctx.typing():
            image_file = None
            image_format = None

            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                image_file = attachment.filename
                image_format = attachment.filename.split('.')[-1]
                await attachment.save(image_file)

            response = await get_response(user_message or "", image_file, image_format)
            
            # Split response into chunks if it's too long
            response_chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            
            for chunk in response_chunks:
                await ctx.send(chunk)
            
    except Exception as e:
        print(f"Error in lumos command: {str(e)}")
        await ctx.send("Sorry, I encountered an error while processing your request. Please try again later.")

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

# Enhanced error handling for commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Extract the attempted command name from the error message
        command = ctx.message.content.split()[0][1:]  # Remove the prefix
        suggestion = get_command_suggestion(command)
        
        embed = Embed(title="Command Not Found", color=0xe74c3c)
        embed.description = f"The command `!{command}` was not found."
        
        if suggestion:
            embed.add_field(name="Did you mean?", value=f"!{suggestion}", inline=False)
        
        embed.add_field(name="Available Commands", value="Type `!help` to see all available commands", inline=False)
        await ctx.send(embed=embed)
        
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = Embed(title="Missing Argument", color=0xe74c3c)
        embed.description = f"The command is missing a required argument: `{error.param.name}`"
        
        # Add command-specific help
        command = ctx.command.name
        embed.add_field(name="Usage", value=f"Type `!help {command}` for proper usage", inline=False)
        
        await ctx.send(embed=embed)
        
    elif isinstance(error, commands.BadArgument):
        embed = Embed(title="Invalid Argument", color=0xe74c3c)
        embed.description = f"Invalid argument provided for command `!{ctx.command.name}`"
        embed.add_field(name="Details", value=str(error), inline=False)
        embed.add_field(name="Usage", value=f"Type `!help {ctx.command.name}` for proper usage", inline=False)
        
        await ctx.send(embed=embed)
        
    elif isinstance(error, commands.CommandOnCooldown):
        # For rate-limited commands
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        
        if int(hours):
            time_format = f"{int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds"
        elif int(minutes):
            time_format = f"{int(minutes)} minutes and {int(seconds)} seconds"
        else:
            time_format = f"{int(seconds)} seconds"
            
        embed = Embed(title="Command on Cooldown", color=0xe74c3c)
        embed.description = f"This command is on cooldown. Please try again in {time_format}."
        await ctx.send(embed=embed)
        
    else:
        # For other, unexpected errors
        print(f"Command error: {str(error)}")
        embed = Embed(title="Error", color=0xe74c3c)
        embed.description = "An unexpected error occurred while processing your command."
        embed.add_field(name="Error Details", value=str(error)[:1024], inline=False)  # Truncate if too long
        
        await ctx.send(embed=embed)

# New command for testing welcome cards
@bot.command(name='welcome')
@commands.has_permissions(administrator=True)
async def test_welcome(ctx):
    """Test the welcome card feature (admin only)"""
    try:
        async with ctx.typing():
            # Generate welcome card for the command user
            card_buffer = await create_welcome_card(
                username=ctx.author.display_name,
                avatar_url=ctx.author.display_avatar.url,
                server_name=ctx.guild.name,
                member_count=ctx.guild.member_count,
                background_url=WELCOME_BACKGROUND_URL,
                custom_message="Welcome card test!"
            )
            
            if card_buffer:
                # Create accompanying embed
                welcome_embed = create_welcome_embed(
                    username=ctx.author.display_name,
                    server_name=ctx.guild.name,
                    member_count=ctx.guild.member_count,
                    user_id=ctx.author.id
                )
                
                # Update the embed to make it clear it's a test
                welcome_embed.title = "Welcome Card Test"
                welcome_embed.set_footer(text=f"Test card for {ctx.author.display_name}")
                
                # Send the welcome card with the embed
                await ctx.send(
                    content="Here's a preview of the welcome card:",
                    file=discord.File(fp=card_buffer, filename="welcome.png"),
                    embed=welcome_embed
                )
            else:
                await ctx.send("Error generating welcome card.")
    except Exception as e:
        print(f"Error in welcome command: {str(e)}")
        await ctx.send(f"Failed to generate welcome card: {str(e)}")

# Add new member welcome event
@bot.event
async def on_member_join(member):
    """Event handler that triggers when a new member joins"""
    if WELCOME_CHANNEL_ID == 0:
        print("WARNING: No welcome channel ID set. Skipping welcome message.")
        return
    
    try:
        welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if welcome_channel:
            # Generate welcome card
            card_buffer = await create_welcome_card(
                username=member.display_name,
                avatar_url=member.display_avatar.url,
                server_name=member.guild.name,
                member_count=member.guild.member_count,
                background_url=WELCOME_BACKGROUND_URL
            )
            
            if card_buffer:
                # Create accompanying embed
                welcome_embed = create_welcome_embed(
                    username=member.display_name,
                    server_name=member.guild.name,
                    member_count=member.guild.member_count,
                    user_id=member.id
                )
                
                # Send the welcome card with the embed
                await welcome_channel.send(
                    content=f"Welcome {member.mention} to the server!",
                    file=discord.File(fp=card_buffer, filename="welcome.png"),
                    embed=welcome_embed
                )
                print(f"Welcome card sent for {member.display_name}")
            else:
                await welcome_channel.send(f"Welcome {member.mention} to the server!")
        else:
            print(f"ERROR: Could not find welcome channel with ID {WELCOME_CHANNEL_ID}")
    except Exception as e:
        print(f"ERROR: Failed to send welcome message: {str(e)}")

# Import discord for status
import discord

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