"""
AI Discord Bot - Main Module

This module handles Discord event processing and bot command handling.
"""
# Standard library imports
import os
import time
import platform
import datetime
import difflib
from typing import Final, Optional

# Third-party imports
import discord
from discord.ext import commands, tasks
from discord import Intents, Attachment, Embed, version_info as discord_version
from dotenv import load_dotenv

# Local imports
from responses import get_response
from welcome_card import (
    create_welcome_card, create_welcome_embed, add_background,
    remove_background, set_default_background, list_backgrounds,
    create_background_preview
)

# --- Configuration ---

# Load environment variables
load_dotenv()

# Bot constants
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
BOT_VERSION: Final[str] = "1.0.0"
BOT_CREATOR: Final[str] = "MAHITO"
ANNOUNCEMENT_CHANNEL_ID: Final[int] = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID', '0'))
WELCOME_CHANNEL_ID: Final[int] = int(os.getenv('WELCOME_CHANNEL_ID', '0'))
WELCOME_BACKGROUND_URL: Final[str] = os.getenv('WELCOME_BACKGROUND_URL', '')

# Bot storage
USER_CONVERSATIONS = {}  # Store conversation history by user ID
MAX_MEMORY_LENGTH = 10   # Maximum number of conversation turns to remember
start_time = time.time() # Track start time for uptime command

# Available commands dictionary for suggestions
COMMANDS = {
    'help': 'Shows the help message with available commands',
    'info': 'Shows information about the bot',
    'ping': 'Shows the bot\'s latency',
    'lumos': 'Interact with the bot using the AI model',
    'memory': 'View or clear your conversation history with the bot',
    'config': 'Configure bot settings for this server (admin only)',
    'welcome': 'Test the welcome card feature (admin only)',
    'backgrounds': 'Manage welcome card backgrounds (admin only)'
}

# --- Bot Setup ---

# Initialize bot with intents
intents: Intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- Utility Functions ---

def get_uptime() -> str:
    """Calculate and format the bot's uptime."""
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

def get_command_suggestion(cmd: str) -> Optional[str]:
    """Get a command suggestion based on user input."""
    available_commands = list(COMMANDS.keys())
    matches = difflib.get_close_matches(cmd, available_commands, n=1, cutoff=0.5)
    return matches[0] if matches else None

# --- Event Handlers ---

@bot.event
async def on_ready():
    """Handle bot initialization when connection to Discord is established."""
    print(f'{bot.user} has connected to Discord!')
    
    # Start the daily announcement task
    if not daily_announcement.is_running():
        daily_announcement.start()
        print("Daily announcement task started.")

    # Set status
    activity = discord.Activity(type=discord.ActivityType.listening, name="!help")
    await bot.change_presence(activity=activity)

@bot.event
async def on_member_join(member):
    """Send welcome message when a new member joins the server."""
    if WELCOME_CHANNEL_ID == 0:
        print("WARNING: No welcome channel ID set. Skipping welcome message.")
        return
    
    try:
        welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if not welcome_channel:
            print(f"ERROR: Could not find welcome channel with ID {WELCOME_CHANNEL_ID}")
            return
            
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
    except Exception as e:
        print(f"ERROR: Failed to send welcome message: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors with appropriate responses."""
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

# --- Scheduled Tasks ---

@tasks.loop(hours=24)
async def daily_announcement():
    """Send a daily announcement to the configured channel."""
    if ANNOUNCEMENT_CHANNEL_ID == 0:
        print("WARNING: No announcement channel ID set. Skipping daily announcement.")
        return
    
    try:
        channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if not channel:
            print(f"ERROR: Could not find channel with ID {ANNOUNCEMENT_CHANNEL_ID}")
            return
            
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
    except Exception as e:
        print(f"ERROR: Failed to send daily announcement: {str(e)}")

# --- Basic Commands ---

@bot.command(name='ping')
async def ping(ctx):
    """Show the bot's latency."""
    start_time = time.time()
    msg = await ctx.send('Pinging...')
    end_time = time.time()
    
    # Calculate ping in ms
    ping_latency = round((end_time - start_time) * 1000)
    await msg.edit(content=f'Pong! Latency: {ping_latency}ms | API Latency: {round(bot.latency * 1000)}ms')

@bot.command(name='info')
async def info(ctx):
    """Show information about the bot."""
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

@bot.command(name='help')
async def help_command(ctx, command_name: str = None):
    """Show the help message with available commands."""
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

# --- AI Commands ---

@bot.command(name='lumos')
async def lumos(ctx, *, user_message: str = None):
    """Interact with the bot using the AI model."""
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
                
            # Clean up any saved file
            if image_file and os.path.exists(image_file):
                try:
                    os.remove(image_file)
                except Exception:
                    pass
            
    except Exception as e:
        print(f"Error in lumos command: {str(e)}")
        await ctx.send("Sorry, I encountered an error while processing your request. Please try again later.")

# --- Welcome Card Commands ---

@bot.command(name='welcome')
@commands.has_permissions(administrator=True)
async def test_welcome(ctx, background: str = None):
    """Test the welcome card feature (admin only)."""
    try:
        async with ctx.typing():
            # Check if using a specific background
            if background and background.lower() == "random":
                use_random = True
                bg_name = None
            else:
                use_random = False
                bg_name = background
            
            # Generate welcome card for the command user
            card_buffer = await create_welcome_card(
                username=ctx.author.display_name,
                avatar_url=ctx.author.display_avatar.url,
                server_name=ctx.guild.name,
                member_count=ctx.guild.member_count,
                background_url=WELCOME_BACKGROUND_URL if not bg_name else None,
                background_name=bg_name,
                use_random_bg=use_random,
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

# --- Background Management Commands ---

@bot.group(name="backgrounds")
@commands.has_permissions(administrator=True)
async def backgrounds(ctx):
    """Manage welcome card backgrounds (admin only)."""
    if ctx.invoked_subcommand is None:
        await ctx.send("Please specify a subcommand. Type `!help backgrounds` for more info.")

@backgrounds.command(name="list")
async def list_bg(ctx):
    """List all available backgrounds."""
    backgrounds_list = list_backgrounds()
    
    if not backgrounds_list:
        await ctx.send("No backgrounds available. Add backgrounds with `!backgrounds add <name> <url>`")
        return
    
    embed = discord.Embed(
        title="Welcome Card Backgrounds", 
        description=f"Total backgrounds: {len(backgrounds_list)}", 
        color=0x3498db
    )
    
    for bg in backgrounds_list:
        name = bg["name"]
        status = "✅ Default" if bg["is_default"] else ""
        embed.add_field(name=f"{name} {status}", value=f"Use: `!welcome {name}`", inline=True)
    
    embed.set_footer(text="Use !backgrounds preview <name> to see a preview")
    await ctx.send(embed=embed)

@backgrounds.command(name="add")
async def add_bg(ctx, name: str, url: str = None):
    """Add a new background from URL or attachment."""
    if not name.isalnum():
        await ctx.send("Background name must contain only letters and numbers.")
        return
    
    # Check if URL or attachment provided
    if not url and not ctx.message.attachments:
        await ctx.send("Please provide a URL or attach an image.")
        return
    
    attachment_data = None
    if ctx.message.attachments:
        # Get the first attachment
        attachment = ctx.message.attachments[0]
        # Check if it's an image
        if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            await ctx.send("Attachment must be an image file (PNG, JPG, JPEG, GIF).")
            return
        
        # Download the attachment
        attachment_data = await attachment.read()
    
    # Show typing indicator while processing
    async with ctx.typing():
        success = await add_background(name, url, attachment_data)
        
        if success:
            # Create a preview
            preview = await create_background_preview(name)
            
            embed = discord.Embed(
                title="Background Added", 
                description=f"Successfully added background: `{name}`", 
                color=0x2ecc71
            )
            embed.add_field(name="Usage", value=f"Use `!welcome {name}` to test this background", inline=False)
            
            if preview:
                await ctx.send(
                    embed=embed, 
                    file=discord.File(fp=preview, filename="preview.png")
                )
            else:
                await ctx.send(embed=embed)
        else:
            await ctx.send(f"Failed to add background `{name}`. The name may be taken or the image is invalid.")

@backgrounds.command(name="remove")
async def remove_bg(ctx, name: str):
    """Remove a background."""
    success = remove_background(name)
    
    if success:
        await ctx.send(f"Successfully removed background: `{name}`")
    else:
        await ctx.send(f"Failed to remove background `{name}`. It may not exist.")

@backgrounds.command(name="set-default")
async def set_default_bg(ctx, name: str):
    """Set the default background."""
    success = set_default_background(name)
    
    if success:
        await ctx.send(f"Successfully set `{name}` as the default background!")
    else:
        await ctx.send(f"Failed to set default background. `{name}` may not exist.")

@backgrounds.command(name="preview")
async def preview_bg(ctx, name: str):
    """Preview a background."""
    preview = await create_background_preview(name)
    
    if preview:
        await ctx.send(
            content=f"Background preview for: `{name}`",
            file=discord.File(fp=preview, filename="preview.png")
        )
    else:
        await ctx.send(f"Background `{name}` not found.")

# --- Main Entry Point ---

def main():
    """Main entry point for the bot."""
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