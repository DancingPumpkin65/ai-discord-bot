"""
AI Discord Bot - Music Controller

This module handles the core music playback functionality using Wavelink/Lavalink.
"""
import asyncio
import re
import time
from typing import List, Dict, Any, Optional, Callable, Coroutine
import discord
import wavelink
from wavelink.ext import spotify
from .spotify_client import SpotifyClient

class Track:
    """Represents a playable track with metadata."""
    
    def __init__(self, wavelink_track, requester=None):
        """Initialize a track with its wavelink track and requester."""
        self.track = wavelink_track
        self.requester = requester
        self.start_time = 0
        
    @property
    def is_playing(self) -> bool:
        """Check if the track is currently playing."""
        return self.start_time > 0
        
    def mark_playing(self) -> None:
        """Mark the track as playing now."""
        self.start_time = time.time()

class GuildMusicController:
    """Controls music playback for a specific guild."""
    
    def __init__(self, guild_id: int):
        """Initialize the music controller for a guild."""
        self.guild_id = guild_id
        self.queue = []  # List of Track objects
        self.current_track = None  # Current Track
        self.volume = 100  # Default volume (0-1000)
        self.loop = False  # Repeat current track
        self._disconnect_task = None
        self._disconnect_timeout = 180  # 3 minutes
        
    @property
    def is_playing(self) -> bool:
        """Check if music is currently playing."""
        return self.current_track is not None and self.current_track.is_playing
    
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty and nothing is playing."""
        return len(self.queue) == 0 and not self.is_playing
        
    def add_track(self, track, requester=None) -> Track:
        """Add a track to the queue."""
        track_obj = Track(track, requester)
        self.queue.append(track_obj)
        return track_obj
        
    def add_tracks(self, tracks, requester=None) -> List[Track]:
        """Add multiple tracks to the queue."""
        track_objects = []
        for track in tracks:
            track_obj = self.add_track(track, requester)
            track_objects.append(track_obj)
        return track_objects
        
    def skip(self) -> Optional[Track]:
        """Skip the current track and return the next track."""
        self.current_track = None
        if not self.queue:
            return None
        return self.queue.pop(0)
        
    def clear_queue(self) -> None:
        """Clear the entire queue."""
        self.queue = []
        
    def shuffle(self) -> None:
        """Shuffle the queue."""
        import random
        random.shuffle(self.queue)
        
    def cancel_disconnect(self) -> None:
        """Cancel the scheduled disconnect."""
        if self._disconnect_task and not self._disconnect_task.done():
            self._disconnect_task.cancel()
            self._disconnect_task = None
            
    def schedule_disconnect(self, player, timeout: int = None) -> None:
        """Schedule a disconnect if no activity for the specified timeout."""
        self.cancel_disconnect()
        
        if timeout is None:
            timeout = self._disconnect_timeout
            
        async def disconnect_task():
            await asyncio.sleep(timeout)
            await player.disconnect()
            print(f"Automatically disconnected from guild {self.guild_id} due to inactivity")
            
        self._disconnect_task = asyncio.create_task(disconnect_task())

class MusicService:
    """Global service for managing music playback across guilds."""
    
    def __init__(self, bot, lavalink_host, lavalink_port, lavalink_password):
        """Initialize the music service with Lavalink connection details."""
        self.bot = bot
        self.lavalink_host = lavalink_host
        self.lavalink_port = lavalink_port
        self.lavalink_password = lavalink_password
        self.controllers = {}  # guild_id -> GuildMusicController
        self.spotify_client = SpotifyClient()
        
    def get_controller(self, guild_id: int) -> GuildMusicController:
        """Get or create a music controller for a guild."""
        if guild_id not in self.controllers:
            self.controllers[guild_id] = GuildMusicController(guild_id)
        return self.controllers[guild_id]
        
    async def setup(self) -> None:
        """Set up the wavelink client and connect to Lavalink server."""
        # Initialize Wavelink nodes
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=self.lavalink_host,
            port=self.lavalink_port,
            password=self.lavalink_password,
            spotify_client=spotify.SpotifyClient(
                client_id=SpotifyClient.SPOTIFY_CLIENT_ID,
                client_secret=SpotifyClient.SPOTIFY_CLIENT_SECRET
            )
        )
            
    async def search_track(self, query: str) -> Optional[wavelink.Track]:
        """Search for a track on YouTube."""
        tracks = await wavelink.YouTubeTrack.search(query=query)
        if not tracks:
            return None
        return tracks[0]
    
    async def get_tracks_from_url(self, url: str, ctx=None) -> List[wavelink.Track]:
        """Get tracks from a URL (Spotify or direct YouTube URL)."""
        if "spotify.com" in url:
            # Handle Spotify URL
            spotify_tracks = self.spotify_client.get_tracks_from_url(url)
            tracks = []
            
            if ctx:
                await ctx.send(f"Found {len(spotify_tracks)} tracks in the Spotify link. This may take a moment to process...")
                
            for i, track_data in enumerate(spotify_tracks):
                query = track_data['search_query']
                track = await self.search_track(query)
                
                if track:
                    # Add artist and title metadata from Spotify
                    tracks.append(track)
                    
                # Give updates for long playlists
                if ctx and i > 0 and i % 10 == 0:
                    await ctx.send(f"Processed {i}/{len(spotify_tracks)} tracks...")
                    
            return tracks
            
        elif "youtube.com" in url or "youtu.be" in url:
            # Handle YouTube URL directly
            tracks = await wavelink.YouTubeTrack.search(url)
            return tracks if isinstance(tracks, list) else [tracks]
            
        else:
            # Search as a regular query
            track = await self.search_track(url)
            return [track] if track else []
            
    async def join_voice(self, ctx) -> Optional[wavelink.Player]:
        """Join a voice channel."""
        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel to use this command!")
            return None
            
        channel = ctx.author.voice.channel
        
        # Create or get player
        player = ctx.voice_client or await channel.connect(cls=wavelink.Player)
        
        # Make sure player is in the right channel
        if player.channel.id != channel.id:
            await player.move_to(channel)
            
        # Set up player event listeners
        player.guild_id = ctx.guild.id
        
        return player
        
    async def play_next(self, player: wavelink.Player, guild_id: int) -> None:
        """Play the next track in the queue."""
        controller = self.get_controller(guild_id)
        
        # Cancel any pending disconnects
        controller.cancel_disconnect()
        
        # Get the next track or re-queue current if looping
        next_track = None
        if controller.loop and controller.current_track:
            next_track = controller.current_track
            # Reset playing status for accurate tracking
            controller.current_track.start_time = 0
        else:
            if controller.queue:
                next_track = controller.queue.pop(0)
            controller.current_track = next_track
            
        # Play the track if we have one
        if next_track:
            next_track.mark_playing()
            await player.play(next_track.track)
            return
            
        # No tracks left, schedule disconnect
        controller.current_track = None
        controller.schedule_disconnect(player)
