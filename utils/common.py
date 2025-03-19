"""
AI Discord Bot - Common Utilities Module

This module contains utility functions used throughout the bot.
"""
import time
import difflib
from typing import Optional
import discord
from config import COMMANDS

# Bot start time for uptime calculation
start_time = time.time()

def get_uptime() -> str:
    """
    Calculate and format the bot's uptime.
    
    Returns:
        Formatted string showing the uptime duration
    """
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
    """
    Get a command suggestion based on user input.
    
    Args:
        cmd: The command string to find matches for
        
    Returns:
        The closest matching command, or None if no match found
    """
    available_commands = list(COMMANDS.keys())
    matches = difflib.get_close_matches(cmd, available_commands, n=1, cutoff=0.5)
    return matches[0] if matches else None

def create_error_embed(title: str, description: str, **kwargs) -> discord.Embed:
    """
    Create a standardized error embed.
    
    Args:
        title: The error title
        description: The error description
        **kwargs: Additional fields to add to the embed
        
    Returns:
        A formatted Discord Embed for error messages
    """
    embed = discord.Embed(title=title, description=description, color=0xe74c3c)
    
    for name, value in kwargs.items():
        embed.add_field(name=name, value=value, inline=False)
    
    return embed

def ordinal_suffix(num: int) -> str:
    """
    Return the ordinal suffix for a number (1st, 2nd, 3rd, etc).
    
    Args:
        num: The number to get ordinal suffix for
        
    Returns:
        The number with its ordinal suffix
    """
    if 11 <= num % 100 <= 13:
        return f"{num}th"
        
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(num % 10, "th")
    return f"{num}{suffix}"
