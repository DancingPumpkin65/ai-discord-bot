"""
AI Discord Bot - Main Module

This is the entry point for the Discord bot that loads all cogs and starts the bot.
"""
# Standard library imports
import os
import sys
import asyncio
import platform

# Third-party imports
import discord
from discord.ext import commands

# Local imports
import config
from utils import get_uptime, get_command_suggestion

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True  # Required to access message content
bot = commands.Bot(command_prefix=config.DEFAULT_PREFIX, intents=intents, help_command=None)

# --- Bot Events ---
@bot.event
async def on_ready():
    """Handle bot initialization when connection to Discord is established."""
    print(f'{"="*50}')
    print(f'Bot is online as {bot.user}')
    print(f'Discord.py version: {discord.__version__}')
    print(f'Python version: {platform.python_version()}')
    print(f'Running on: {platform.system()} {platform.release()}')
    print(f'{"="*50}')
    
    # Set status
    activity = discord.Activity(type=discord.ActivityType.listening, name=f"{config.DEFAULT_PREFIX}help")
    await bot.change_presence(activity=activity)

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for command errors."""
    if isinstance(error, commands.CommandNotFound):
        # Extract the attempted command name
        command = ctx.message.content.split()[0][1:]  # Remove the prefix
        suggestion = get_command_suggestion(command)
        
        embed = discord.Embed(title="Command Not Found", color=config.COLORS['error'])
        embed.description = f"The command `{config.DEFAULT_PREFIX}{command}` was not found."
        
        if suggestion:
            embed.add_field(name="Did you mean?", value=f"{config.DEFAULT_PREFIX}{suggestion}", inline=False)
        
        embed.add_field(name="Available Commands", 
                     value=f"Type `{config.DEFAULT_PREFIX}help` to see all available commands", 
                     inline=False)
        await ctx.send(embed=embed)
    
    # Let individual cogs handle their own errors
    elif hasattr(ctx.command, 'on_error'):
        pass
    
    # Handle common Discord.py errors
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="Missing Argument", color=config.COLORS['error'])
        embed.description = f"The command is missing a required argument: `{error.param.name}`"
        embed.add_field(name="Usage", 
                      value=f"Type `{config.DEFAULT_PREFIX}help {ctx.command.name}` for proper usage", 
                      inline=False)
        await ctx.send(embed=embed)
        
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"You don't have permission to use the `{ctx.command.name}` command.")
    
    elif isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        
        if int(hours):
            time_format = f"{int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds"
        elif int(minutes):
            time_format = f"{int(minutes)} minutes and {int(seconds)} seconds"
        else:
            time_format = f"{int(seconds)} seconds"
            
        embed = discord.Embed(title="Command on Cooldown", color=config.COLORS['warning'])
        embed.description = f"This command is on cooldown. Please try again in {time_format}."
        await ctx.send(embed=embed)
    
    # Generic error handler
    else:
        print(f"Unhandled error: {error}")
        embed = discord.Embed(title="Error", color=config.COLORS['error'])
        embed.description = "An unexpected error occurred while processing your command."
        embed.add_field(name="Error Details", value=str(error)[:1024], inline=False)
        await ctx.send(embed=embed)

# --- Load Cogs ---
async def load_extensions():
    """Load all cogs from the cogs directory."""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded extension: {filename[:-3]}')
            except Exception as e:
                print(f'Failed to load extension {filename[:-3]}: {e}')

# --- Main Entry Point ---
async def main():
    """Main entry point for the bot."""
    try:
        # Load cogs
        await load_extensions()
        # Start the bot
        await bot.start(config.TOKEN)
    except KeyboardInterrupt:
        # Handle graceful shutdown
        await bot.close()
    except Exception as e:
        print(f"Error: {e}")
        # Check for common errors
        if not config.TOKEN:
            print("ERROR: DISCORD_TOKEN is not set in your .env file")
        elif "improper token" in str(e).lower():
            print("ERROR: Your Discord token appears to be invalid")

if __name__ == "__main__":
    # Setup asyncio for Windows if needed
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the bot
    asyncio.run(main())