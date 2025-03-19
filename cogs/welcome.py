"""
Welcome Cog

This cog handles welcome messages and welcome card generation for new members.
"""
import discord
from discord.ext import commands
import config
from services.welcome_cards import create_welcome_card, create_welcome_embed

class WelcomeCog(commands.Cog, name="Welcome"):
    """Welcome card and new member events."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when a new member joins the server."""
        if config.WELCOME_CHANNEL_ID == 0:
            print("WARNING: No welcome channel ID set. Skipping welcome message.")
            return
        
        try:
            welcome_channel = self.bot.get_channel(config.WELCOME_CHANNEL_ID)
            if not welcome_channel:
                print(f"ERROR: Could not find welcome channel with ID {config.WELCOME_CHANNEL_ID}")
                return
                
            # Generate welcome card
            card_buffer = await create_welcome_card(
                username=member.display_name,
                avatar_url=member.display_avatar.url,
                server_name=member.guild.name,
                member_count=member.guild.member_count,
                background_url=config.WELCOME_BACKGROUND_URL,
                use_random_bg=config.USE_RANDOM_BACKGROUNDS
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

    @commands.command(name='welcome')
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx, background: str = None):
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
                    background_url=config.WELCOME_BACKGROUND_URL if not bg_name else None,
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

async def setup(bot):
    """Set up the cog with the bot."""
    await bot.add_cog(WelcomeCog(bot))
