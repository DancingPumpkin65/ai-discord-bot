"""
AI Commands Cog

This cog contains AI-related commands like the lumos conversation command.
"""
import os
import asyncio
import discord
from discord.ext import commands
import config
from core.ai_services import stream_response_with_history

class AICog(commands.Cog, name="AI"):
    """AI interaction commands."""
    
    def __init__(self, bot):
        self.bot = bot
        # Initialize conversation history storage
        self.conversations = {}  # User ID -> list of conversation turns (dicts with role and content)
    
    @commands.command(name="lumos")
    async def lumos(self, ctx, *, user_message: str = None):
        """
        Interact with the AI model.
        
        Usage: !lumos <your message>
        You can also attach an image with your message.
        The bot will remember your conversation history.
        """
        # Check for message or attachment
        if not user_message and not ctx.message.attachments:
            await ctx.send(f"Please provide a message or attach an image. Type `{config.DEFAULT_PREFIX}help lumos` for usage examples.")
            return
            
        try:
            # Show typing indicator while processing
            async with ctx.typing():
                image_file = None
                image_format = None

                # Process attached image if present
                if ctx.message.attachments:
                    attachment = ctx.message.attachments[0]
                    image_file = attachment.filename
                    image_format = attachment.filename.split('.')[-1].lower()
                    
                    # Validate image format
                    valid_formats = ['png', 'jpg', 'jpeg', 'gif', 'webp']
                    if image_format not in valid_formats:
                        await ctx.send(f"Unsupported image format. Supported formats: {', '.join(valid_formats)}")
                        return
                    
                    # Save the image temporarily
                    await attachment.save(image_file)

                # Get user's conversation history
                user_id = str(ctx.author.id)
                if user_id not in self.conversations:
                    self.conversations[user_id] = []
                
                # Limited history (keep last N exchanges)
                max_history_length = config.MAX_MEMORY_LENGTH 
                if len(self.conversations[user_id]) > max_history_length * 2:  # Each exchange is 2 messages
                    self.conversations[user_id] = self.conversations[user_id][-max_history_length * 2:]
                
                # Use streaming response with conversation history
                placeholder_msg = await ctx.send("Thinking...")
                accumulated_response = ""
                update_counter = 0
                update_threshold = 15  # Update message every ~15 tokens
                
                async for response_chunk, updated_history in stream_response_with_history(
                    user_message or "", 
                    self.conversations[user_id], 
                    image_file, 
                    image_format
                ):
                    accumulated_response += response_chunk
                    update_counter += 1
                    
                    # Update conversation history
                    self.conversations[user_id] = updated_history
                    
                    # Update the message periodically to show progress
                    if update_counter >= update_threshold:
                        # If response is getting too long, we need to split it
                        if len(accumulated_response) > 1900:
                            await placeholder_msg.edit(content=accumulated_response[:1900] + "...")
                            placeholder_msg = await ctx.send("...")
                            accumulated_response = accumulated_response[1900:]
                        else:
                            await placeholder_msg.edit(content=accumulated_response)
                        update_counter = 0
                        await asyncio.sleep(0.5)  # Brief pause to avoid rate limits
                
                # Send the final message with any remaining content
                if accumulated_response:
                    # Handle potential length limitations
                    response_chunks = [accumulated_response[i:i+2000] for i in range(0, len(accumulated_response), 2000)]
                    
                    # Edit the placeholder with the first chunk
                    if response_chunks:
                        await placeholder_msg.edit(content=response_chunks[0])
                    
                    # Send any additional chunks as new messages
                    for chunk in response_chunks[1:]:
                        await ctx.send(chunk)
                    
                # Clean up temporarily saved image
                if image_file and os.path.exists(image_file):
                    try:
                        os.remove(image_file)
                    except Exception as e:
                        print(f"Failed to delete temporary file {image_file}: {e}")
                
        except Exception as e:
            print(f"Error in lumos command: {str(e)}")
            await ctx.send("Sorry, I encountered an error while processing your request. Please try again later.")
    
    @commands.command(name="memory")
    async def memory(self, ctx, action: str = "show"):
        """
        View or clear your conversation history with the bot.
        
        Usage:
        !memory show - Show your conversation history
        !memory clear - Clear your conversation history
        """
        user_id = str(ctx.author.id)
        
        # Check if user has conversation history
        if user_id not in self.conversations or not self.conversations[user_id]:
            await ctx.send("You don't have any conversation history with me yet.")
            return
        
        # Process action
        action = action.lower()
        if action == "clear":
            self.conversations[user_id] = []
            await ctx.send("Your conversation history has been cleared.")
        elif action == "show":
            # Create embed with conversation history
            embed = discord.Embed(title="Your Conversation History", color=config.COLORS['info'])
            
            # Add last few conversations (limited to avoid huge embeds)
            history = self.conversations[user_id]
            total_exchanges = len(history) // 2
            
            # Show only the last 5 exchanges
            start_idx = max(0, len(history) - 10)
            display_history = history[start_idx:]
            
            # Group by exchanges (user-assistant pairs)
            for i in range(0, len(display_history), 2):
                if i+1 < len(display_history):  # Make sure we have both user and assistant message
                    exchange_num = (start_idx + i) // 2 + 1
                    user_msg = display_history[i]["content"]
                    bot_msg = display_history[i+1]["content"]
                    
                    # Truncate long messages
                    if len(user_msg) > 100:
                        user_msg = user_msg[:97] + "..."
                    if len(bot_msg) > 100:
                        bot_msg = bot_msg[:97] + "..."
                    
                    embed.add_field(
                        name=f"Exchange {exchange_num}/{total_exchanges}",
                        value=f"**You:** {user_msg}\n**Bot:** {bot_msg}",
                        inline=False
                    )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Unknown action. Use `{config.DEFAULT_PREFIX}memory show` or `{config.DEFAULT_PREFIX}memory clear`.")

async def setup(bot):
    """Set up the cog with the bot."""
    await bot.add_cog(AICog(bot))
