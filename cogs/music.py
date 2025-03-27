"""
Music Cog

This cog implements music playback commands using Lavalink.
"""
import os
import asyncio
import re
import datetime
import discord
from discord.ext import commands
import wavelink

from services.music import MusicService

# Load environment variables or use defaults for Lavalink
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "127.0.0.1")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

class MusicCog(commands.Cog, name="Music"):
    """Music playback commands through Lavalink."""
    
    def __init__(self, bot):
        """Initialize the music cog with a bot instance."""
        self.bot = bot
        self.music_service = MusicService(
            bot=bot, 
            lavalink_host=LAVALINK_HOST,
            lavalink_port=LAVALINK_PORT,
            lavalink_password=LAVALINK_PASSWORD
        )
        
    async def cog_load(self):
        """Set up the music service when the cog loads."""
        await self.music_service.setup()
        
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node):
        """Event triggered when wavelink node is ready."""
        print(f'Lavalink node {node.identifier} is ready!')
        
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player, track, reason):
        """Event triggered when a track finishes playing."""
        # Only auto-advance if the track actually ended (not paused, etc.)
        if reason == "FINISHED" or reason == "LOAD_FAILED":
            await self.music_service.play_next(player, player.guild.id)
            
    @commands.command(name="join")
    async def join(self, ctx):
        """Join your voice channel."""
        player = await self.music_service.join_voice(ctx)
        if player:
            await ctx.send(f"Joined {player.channel.mention}")
            
    @commands.command(name="leave")
    async def leave(self, ctx):
        """Leave the voice channel."""
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
            
        guild_id = ctx.guild.id
        controller = self.music_service.get_controller(guild_id)
        
        # Clear the queue before leaving
        controller.clear_queue()
        controller.current_track = None
        
        # Cancel any scheduled disconnects
        controller.cancel_disconnect()
        
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel.")
            
    @commands.command(name="play")
    async def play(self, ctx, *, query: str = None):
        """
        Play a song or add it to the queue.
        
        You can provide a YouTube URL, Spotify URL, or search terms.
        """
        # Handle case when no query is provided
        if not query:
            if not ctx.message.attachments:
                await ctx.send("Please provide a song to play!")
                return
            # Try to use attachment as song if available
            query = ctx.message.attachments[0].url
            
        # Join the user's voice channel
        player = await self.music_service.join_voice(ctx)
        if not player:
            return
            
        # Get controller for this guild
        guild_id = ctx.guild.id
        controller = self.music_service.get_controller(guild_id)
        
        # Cancel any disconnect timers
        controller.cancel_disconnect()
            
        # Send a loading message for feedback
        loading_msg = await ctx.send("🔍 Searching...")
            
        try:
            # Search for tracks based on the query
            tracks = await self.music_service.get_tracks_from_url(query, ctx)
            
            if not tracks:
                await loading_msg.edit(content="❌ No songs found matching that query!")
                return
                
            # Add tracks to queue
            track_objects = controller.add_tracks(tracks, requester=ctx.author)
            first_track = track_objects[0] if track_objects else None
                
            # Update the loading message with success info
            if len(tracks) > 1:
                await loading_msg.edit(content=f"✅ Added {len(tracks)} songs to the queue")
            else:
                await loading_msg.edit(content=f"✅ Added **{tracks[0].title}** to the queue")
                
            # If nothing is currently playing, start playing
            if not player.is_playing():
                next_track = controller.skip()  # Get first track
                if next_track:
                    controller.current_track = next_track
                    next_track.mark_playing()
                    await player.play(next_track.track)
                    await ctx.send(f"🎵 Now playing: **{next_track.track.title}**")
                    
        except Exception as e:
            await loading_msg.edit(content=f"❌ Error: {str(e)}")
            print(f"Error playing music: {e}")
            
    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pause the current song."""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("Nothing is playing right now!")
            return
            
        await ctx.voice_client.pause()
        await ctx.send("⏸️ Paused the music")
        
    @commands.command(name="resume")
    async def resume(self, ctx):
        """Resume the current song."""
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
            
        if not ctx.voice_client.is_paused():
            await ctx.send("The music is not paused!")
            return
            
        await ctx.voice_client.resume()
        await ctx.send("▶️ Resumed the music")
        
    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skip the current song."""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("Nothing is playing right now!")
            return
            
        guild_id = ctx.guild.id
        controller = self.music_service.get_controller(guild_id)
        
        # Get current track for the message
        current_track = controller.current_track
        current_title = current_track.track.title if current_track else "Unknown"
        
        await ctx.voice_client.stop()
        await ctx.send(f"⏭️ Skipped **{current_title}**")
        
    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stop playing and clear the queue."""
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
            
        guild_id = ctx.guild.id
        controller = self.music_service.get_controller(guild_id)
        
        # Clear queue and stop playing
        controller.clear_queue()
        controller.current_track = None
        
        await ctx.voice_client.stop()
        await ctx.send("⏹️ Stopped playing and cleared the queue")
        
        # Schedule a disconnect if no new commands come in
        controller.schedule_disconnect(ctx.voice_client)
        
    @commands.command(name="queue")
    async def queue(self, ctx):
        """Show the current music queue."""
        guild_id = ctx.guild.id
        controller = self.music_service.get_controller(guild_id)
        
        if not controller.current_track and not controller.queue:
            await ctx.send("The queue is empty!")
            return
            
        # Create an embed for better formatting
        embed = discord.Embed(
            title="🎵 Music Queue",
            color=discord.Color.blurple()
        )
        
        # Add the current track
        if controller.current_track:
            track = controller.current_track.track
            requester = controller.current_track.requester
            duration = str(datetime.timedelta(seconds=track.duration // 1000))
            
            embed.add_field(
                name="Now Playing",
                value=f"**{track.title}** [{duration}]\nRequested by: {requester.mention if requester else 'Unknown'}",
                inline=False
            )
        
        # Add upcoming tracks
        if controller.queue:
            queue_description = ""
            for i, track_obj in enumerate(controller.queue[:10]):  # Limit to first 10 tracks
                track = track_obj.track
                requester = track_obj.requester
                duration = str(datetime.timedelta(seconds=track.duration // 1000))
                
                queue_description += f"`{i+1}.` **{track.title}** [{duration}] - {requester.mention if requester else 'Unknown'}\n"
                
            if len(controller.queue) > 10:
                queue_description += f"\n... and {len(controller.queue) - 10} more songs"
                
            embed.add_field(name="Up Next", value=queue_description or "No songs in queue", inline=False)
            
        # Add total tracks and duration info
        total_songs = len(controller.queue) + (1 if controller.current_track else 0)
        embed.set_footer(text=f"{total_songs} songs in queue")
        
        await ctx.send(embed=embed)
        
    @commands.command(name="np", aliases=["playing", "now"])
    async def now_playing(self, ctx):
        """Show the currently playing song."""
        guild_id = ctx.guild.id
        controller = self.music_service.get_controller(guild_id)
        
        if not controller.current_track:
            await ctx.send("Nothing is playing right now!")
            return
            
        track = controller.current_track.track
        requester = controller.current_track.requester
        
        # Create a nicely formatted embed
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{track.title}**",
            color=discord.Color.green()
        )
        
        # Add track info
        duration = str(datetime.timedelta(seconds=track.duration // 1000))
        embed.add_field(name="Duration", value=duration, inline=True)
        
        if requester:
            embed.add_field(name="Requested by", value=requester.mention, inline=True)
            
        # Add YouTube link if available
        if hasattr(track, 'uri'):
            embed.add_field(name="Link", value=f"[YouTube]({track.uri})", inline=True)
        
        await ctx.send(embed=embed)
        
    @commands.command(name="shuffle")
    async def shuffle_queue(self, ctx):
        """Shuffle the music queue."""
        guild_id = ctx.guild.id
        controller = self.music_service.get_controller(guild_id)
        
        if not controller.queue or len(controller.queue) < 2:
            await ctx.send("Not enough songs in the queue to shuffle!")
            return
            
        controller.shuffle()
        await ctx.send(f"🔀 Shuffled the queue ({len(controller.queue)} songs)")
        
    @commands.command(name="volume")
    async def volume(self, ctx, volume: int = None):
        """Set the player volume (0-100)."""
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel!")
            return
            
        if volume is None:
            # Just show current volume
            current_vol = ctx.voice_client.volume
            await ctx.send(f"🔊 Current volume: {current_vol}%")
            return
            
        # Make sure volume is within range
        volume = max(0, min(150, volume))
        
        # Update controller volume and player
        controller = self.music_service.get_controller(ctx.guild.id)
        controller.volume = volume
        await ctx.voice_client.set_volume(volume / 100)
        
        await ctx.send(f"🔊 Volume set to {volume}%")

    @commands.command(name="loop")
    async def loop(self, ctx):
        """Toggle looping for the current song."""
        guild_id = ctx.guild.id
        controller = self.music_service.get_controller(guild_id)
        
        controller.loop = not controller.loop
        
        if controller.loop:
            await ctx.send("🔁 Looping enabled for current song")
        else:
            await ctx.send("▶️ Looping disabled")

async def setup(bot):
    """Set up the cog with the bot."""
    await bot.add_cog(MusicCog(bot))
