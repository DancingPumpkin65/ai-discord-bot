"""
Welcome Cards package.

This package handles welcome card generation and background management.
"""
# Import and expose the main functions for external use
from .card_gen import create_welcome_card, create_welcome_embed
from .backgrounds import (
    add_background, remove_background, set_default_background,
    list_backgrounds, create_background_preview,
    get_backgrounds_config, get_default_background, get_random_background
)

# Define what gets imported with "from services.welcome_cards import *"
__all__ = [
    'create_welcome_card', 'create_welcome_embed',
    'add_background', 'remove_background', 'set_default_background',
    'list_backgrounds', 'create_background_preview',
    'get_backgrounds_config', 'get_default_background', 'get_random_background'
]
