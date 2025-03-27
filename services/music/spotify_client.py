"""
AI Discord Bot - Spotify API Client

This module handles Spotify API interactions, primarily extracting tracks from playlists.
"""
import os
import re
from typing import List, Dict, Any, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Spotify credentials from environment variables
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

class SpotifyClient:
    """Client for interacting with the Spotify API."""
    
    def __init__(self):
        """Initialize the Spotify client with API credentials."""
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            raise ValueError("Spotify API credentials not found in environment variables")
            
        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
        )
    
    @staticmethod
    def is_spotify_url(url: str) -> bool:
        """Check if the given URL is a Spotify URL."""
        return bool(re.match(r'https?://open\.spotify\.com/(playlist|album|track)', url))
    
    @staticmethod
    def extract_spotify_id(url: str) -> Optional[str]:
        """Extract Spotify ID from a Spotify URL."""
        match = re.search(r'spotify\.com/(?:playlist|album|track)/([a-zA-Z0-9]+)', url)
        return match.group(1) if match else None
    
    @staticmethod
    def get_spotify_type(url: str) -> Optional[str]:
        """Get the Spotify resource type (playlist, album, track) from URL."""
        match = re.search(r'spotify\.com/(playlist|album|track)', url)
        return match.group(1) if match else None
    
    def get_playlist_tracks(self, playlist_url: str) -> List[Dict[str, Any]]:
        """
        Get tracks from a Spotify playlist.
        
        Args:
            playlist_url: Spotify playlist URL
            
        Returns:
            List of track data with name, artists, and duration
        """
        playlist_id = self.extract_spotify_id(playlist_url)
        if not playlist_id:
            return []
            
        results = []
        offset = 0
        limit = 100  # Maximum allowed by Spotify API
        
        while True:
            response = self.spotify.playlist_tracks(
                playlist_id, 
                offset=offset,
                limit=limit,
                fields='items(track(name,artists(name),duration_ms)),total'
            )
            
            if not response or 'items' not in response:
                break
                
            items = response['items']
            if not items:
                break
                
            for item in items:
                if 'track' in item and item['track']:
                    track = item['track']
                    results.append({
                        'name': track['name'],
                        'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                        'duration': track['duration_ms'],
                        'search_query': f"{track['name']} {track['artists'][0]['name'] if track['artists'] else ''}"
                    })
            
            offset += len(items)
            if len(results) >= response.get('total', 0):
                break
                
        return results
    
    def get_album_tracks(self, album_url: str) -> List[Dict[str, Any]]:
        """
        Get tracks from a Spotify album.
        
        Args:
            album_url: Spotify album URL
            
        Returns:
            List of track data with name, artists, and duration
        """
        album_id = self.extract_spotify_id(album_url)
        if not album_id:
            return []
            
        results = []
        
        try:
            response = self.spotify.album_tracks(album_id)
            
            if not response or 'items' not in response:
                return []
                
            for track in response['items']:
                results.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                    'duration': track['duration_ms'],
                    'search_query': f"{track['name']} {track['artists'][0]['name'] if track['artists'] else ''}"
                })
                
        except Exception as e:
            print(f"Error fetching album tracks: {e}")
            
        return results
    
    def get_track_info(self, track_url: str) -> Optional[Dict[str, Any]]:
        """
        Get info for a single Spotify track.
        
        Args:
            track_url: Spotify track URL
            
        Returns:
            Track data with name, artists, and duration
        """
        track_id = self.extract_spotify_id(track_url)
        if not track_id:
            return None
            
        try:
            track = self.spotify.track(track_id)
            
            if not track:
                return None
                
            return {
                'name': track['name'],
                'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                'duration': track['duration_ms'],
                'search_query': f"{track['name']} {track['artists'][0]['name'] if track['artists'] else ''}"
            }
            
        except Exception as e:
            print(f"Error fetching track info: {e}")
            
        return None
        
    def get_tracks_from_url(self, url: str) -> List[Dict[str, Any]]:
        """
        Get tracks from any Spotify URL (playlist, album, or track).
        
        Args:
            url: Spotify URL (playlist, album, or track)
            
        Returns:
            List of track data
        """
        if not self.is_spotify_url(url):
            return []
            
        resource_type = self.get_spotify_type(url)
        
        if resource_type == 'playlist':
            return self.get_playlist_tracks(url)
        elif resource_type == 'album':
            return self.get_album_tracks(url)
        elif resource_type == 'track':
            track = self.get_track_info(url)
            return [track] if track else []
        
        return []
