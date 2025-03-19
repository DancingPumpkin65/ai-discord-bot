"""
General Commands Cog

This cog contains general utility commands like help, info, and ping.
"""
import platform
import time
import discord
from discord.ext import commands, tasks
import datetime

import config
from utils import get_uptime

class GeneralCog(commands.Cog, name="General"):
    """General commands for basic bot interactions."""

    def __init__(self, bot):
        self.bot = bot
        # Start daily announcement task
        self.daily_announcement.start()
    
    def cog_unload(self):
        """Clean up when the cog is unloaded."""
        self.daily_announcement.cancel()
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Show the bot's latency."""
        start_time = time.time()
        msg = await ctx.send('Pinging...')
        end_time = time.time()
        
        # Calculate ping in ms
        ping_latency = round((end_time - start_time) * 1000)
        await msg.edit(content=f'Pong! Latency: {ping_latency}ms | API Latency: {round(self.bot.latency * 1000)}ms')

    @commands.command(name='info')
    async def info(self, ctx):
        """Show information about the bot."""
        embed = discord.Embed(title="Bot Information", color=config.COLORS['info'])
        
        # Basic info fields
        embed.add_field(name="Name", value="AI Discord Bot", inline=True)
        embed.add_field(name="Version", value=config.BOT_VERSION, inline=True)
        embed.add_field(name="Creator", value=config.BOT_CREATOR, inline=True)
        
        # Technical details
        discord_version = discord.version_info
        embed.add_field(name="Discord.py Version", 
                       value=f"{discord_version.major}.{discord_version.minor}.{discord_version.micro}", 
                       inline=True)
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="Platform", value=platform.system() + " " + platform.release(), inline=True)
        
        # Runtime stats
        embed.add_field(name="Uptime", value=get_uptime(), inline=True)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        
        # Description
        embed.add_field(name="Description", 
                       value="A Discord bot that uses OpenAI's GPT-4o model to generate responses to user messages.", 
                       inline=False)
        
        embed.set_footer(text=f"Use {config.DEFAULT_PREFIX}help to see available commands")
        
        await ctx.send(embed=embed)

    @commands.command(name='help')
    async def help_command(self, ctx, command_name: str = None):
        """Show the help message with available commands."""
        if command_name:
            # Show help for specific command
            cmd_name = command_name.lower().strip()
            
            # Handle commands with aliases or additional details
            if cmd_name in config.COMMANDS:
                embed = discord.Embed(title=f"Help: {config.DEFAULT_PREFIX}{cmd_name}", 
                                    description=config.COMMANDS[cmd_name], 
                                    color=config.COLORS['info'])
                
                # Add specific usage examples
                if cmd_name == 'lumos':
                    embed.add_field(name="Usage", value=f"{config.DEFAULT_PREFIX}lumos <your question or prompt>", inline=False)
                    embed.add_field(name="Example", value=f"{config.DEFAULT_PREFIX}lumos What is artificial intelligence?", inline=False)
                    embed.add_field(name="With Image", value="You can also attach an image with your prompt", inline=False)
                elif cmd_name == 'ping':
                    embed.add_field(name="Usage", value=f"{config.DEFAULT_PREFIX}ping", inline=False)
                    embed.add_field(name="Description", value="Shows the bot's response time and API latency", inline=False)
                
                embed.set_footer(text=f"Type {config.DEFAULT_PREFIX}help for a list of all commands")
            else:
                # Command not found - get suggestion from utils
                from utils import get_command_suggestion
                suggestion = get_command_suggestion(cmd_name)
                
                embed = discord.Embed(title="Command Not Found", color=config.COLORS['error'])
                embed.description = f"The command `{config.DEFAULT_PREFIX}{cmd_name}` was not found."
                
                if suggestion:
                    embed.add_field(name="Did you mean?", value=f"{config.DEFAULT_PREFIX}{suggestion}", inline=False)
                
                embed.add_field(name="Available Commands", 
                             value=f"Type `{config.DEFAULT_PREFIX}help` to see all available commands", 
                             inline=False)
                
            await ctx.send(embed=embed)
        else:
            # Show general help
            embed = discord.Embed(title="Bot Help", 
                                description="List of available commands:", 
                                color=config.COLORS['info'])
            
            # Group commands by category
            categories = {}
            for cmd, desc in config.COMMANDS.items():
                # Determine category (simple version)
                if cmd in ['help', 'info', 'ping']:
                    category = 'General'
                elif cmd in ['lumos']:
                    category = 'AI'
                elif cmd in ['welcome']:
                    category = 'Welcome'
                elif cmd in ['backgrounds']:
                    category = 'Backgrounds'
                else:
                    category = 'Other'
                
                if category not in categories:
                    categories[category] = []
                categories[category].append((cmd, desc))
            
            # Add fields by category
            for category, commands_list in categories.items():
                commands_text = "\n".join([f"`{config.DEFAULT_PREFIX}{cmd}`: {desc}" for cmd, desc in commands_list])
                embed.add_field(name=f"{category} Commands", value=commands_text, inline=False)
                
            embed.add_field(name="Detailed Help", 
                         value=f"Type `{config.DEFAULT_PREFIX}help <command>` for more info on a specific command", 
                         inline=False)
            embed.set_footer(text=f"Bot created by {config.BOT_CREATOR}")
            
            await ctx.send(embed=embed)
    
    @tasks.loop(hours=24)
    async def daily_announcement(self):
        """Send a daily announcement to the configured channel."""
        if config.ANNOUNCEMENT_CHANNEL_ID == 0:
            print("WARNING: No announcement channel ID set. Skipping daily announcement.")
            return
        
        try:
            channel = self.bot.get_channel(config.ANNOUNCEMENT_CHANNEL_ID)
            if not channel:
                print(f"ERROR: Could not find channel with ID {config.ANNOUNCEMENT_CHANNEL_ID}")
                return
                
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            embed = discord.Embed(
                title="Daily Announcement", 
                description="This is an automated daily announcement from AI Discord Bot.", 
                color=config.COLORS['purple']
            )
            embed.add_field(name="Current Date", value=current_time, inline=False)
            embed.add_field(name="Bot Uptime", value=get_uptime(), inline=False)
            embed.set_footer(text=f"Bot Version: {config.BOT_VERSION}")
            
            await channel.send(embed=embed)
            print(f"Daily announcement sent at {current_time}")
        except Exception as e:
            print(f"ERROR: Failed to send daily announcement: {str(e)}")
    
    @daily_announcement.before_loop
    async def before_daily_announcement(self):
        """Wait for the bot to be ready before starting the announcement task."""
        await self.bot.wait_until_ready()

async def setup(bot):
    """Set up the cog with the bot."""
    await bot.add_cog(GeneralCog(bot))
