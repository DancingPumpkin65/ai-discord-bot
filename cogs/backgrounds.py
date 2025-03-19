"""
Backgrounds Cog

This cog handles background management for welcome cards.
"""
import discord
from discord.ext import commands
from services.welcome_cards import (
    add_background, remove_background, set_default_background,
    list_backgrounds, create_background_preview
)

class BackgroundsCog(commands.Cog, name="Backgrounds"):
    """Background management commands for welcome cards."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="backgrounds")
    @commands.has_permissions(administrator=True)
    async def backgrounds(self, ctx):
        """Manage welcome card backgrounds (admin only)."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a subcommand. Use `!backgrounds list` to see available backgrounds.")

    @backgrounds.command(name="list")
    async def list_bg(self, ctx):
        """List all available backgrounds."""        
        backgrounds_list = list_backgrounds()
        
        if not backgrounds_list:
            await ctx.send("No backgrounds available. Add backgrounds with `!backgrounds add <name> <url>`")
            return
        
        embed = discord.Embed(
            title="Welcome Card Backgrounds", 
            description=f"Total backgrounds: {len(backgrounds_list)}", 
            color=discord.Color.blue()
        )
        
        for bg in backgrounds_list:
            name = bg["name"]
            status = "✅ Default" if bg["is_default"] else ""
            embed.add_field(name=f"{name} {status}", value=f"Use: `!welcome {name}`", inline=True)
        
        embed.set_footer(text="Use !backgrounds preview <name> to see a preview")
        await ctx.send(embed=embed)

    @backgrounds.command(name="add")
    async def add_bg(self, ctx, name: str, url: str = None):
        """
        Add a new background from URL or attachment.
        
        Usage:
        !backgrounds add <name> <url> - Add background from URL
        !backgrounds add <name> - Add background from attachment
        """
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
            if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                await ctx.send("Attachment must be an image file (PNG, JPG, JPEG, GIF, WEBP).")
                return
            
            # Download the attachment
            try:
                attachment_data = await attachment.read()
                print(f"Successfully read attachment: {len(attachment_data)} bytes")
            except Exception as e:
                await ctx.send(f"Error reading attachment: {str(e)}")
                return
        
        # Show typing indicator while processing
        async with ctx.typing():
            try:
                success = await add_background(name, url, attachment_data)
                
                if success:
                    # Create a preview
                    preview = await create_background_preview(name)
                    
                    embed = discord.Embed(
                        title="Background Added", 
                        description=f"Successfully added background: `{name}`", 
                        color=discord.Color.green()
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
            except Exception as e:
                await ctx.send(f"Error adding background: {str(e)}")
                import traceback
                traceback.print_exc()

    @backgrounds.command(name="remove")
    async def remove_bg(self, ctx, name: str):
        """Remove a background."""        
        success = remove_background(name)
        
        if success:
            await ctx.send(f"Successfully removed background: `{name}`")
        else:
            await ctx.send(f"Failed to remove background `{name}`. It may not exist.")

    @backgrounds.command(name="set-default")
    async def set_default_bg(self, ctx, name: str):
        """Set the default background."""        
        success = set_default_background(name)
        
        if success:
            await ctx.send(f"Successfully set `{name}` as the default background!")
        else:
            await ctx.send(f"Failed to set default background. `{name}` may not exist.")

    @backgrounds.command(name="preview")
    async def preview_bg(self, ctx, name: str):
        """Preview a background."""        
        preview = await create_background_preview(name)
        
        if preview:
            await ctx.send(
                content=f"Background preview for: `{name}`",
                file=discord.File(fp=preview, filename="preview.png")
            )
        else:
            await ctx.send(f"Background `{name}` not found.")

    @backgrounds.command(name="help")
    async def help_bg(self, ctx):
        """Show help information for background commands."""        
        embed = discord.Embed(
            title="Background Management Commands",
            description="Commands for managing welcome card backgrounds",
            color=discord.Color.blue()
        )
        
        commands = [
            ("list", "List all available backgrounds", "!backgrounds list"),
            ("add", "Add a new background", "!backgrounds add <name> [url]"),
            ("remove", "Remove a background", "!backgrounds remove <name>"),
            ("set-default", "Set the default background", "!backgrounds set-default <name>"),
            ("preview", "Preview a background", "!backgrounds preview <name>")
        ]
        
        for name, desc, usage in commands:
            embed.add_field(name=name, value=f"{desc}\nUsage: `{usage}`", inline=False)
            
        embed.set_footer(text="Note: These commands require administrator permissions")
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Set up the cog with the bot."""    
    await bot.add_cog(BackgroundsCog(bot))
