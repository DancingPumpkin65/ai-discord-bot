"""
AI Discord Bot - Welcome Cards Configuration Module

This module centralizes configuration settings for the welcome card system.
"""
import os

# --- Directory Structure ---
ASSETS_DIR = "assets"
FONTS_DIR = f"{ASSETS_DIR}/fonts"
BACKGROUNDS_DIR = f"{ASSETS_DIR}/backgrounds"
BACKGROUNDS_CONFIG = f"{BACKGROUNDS_DIR}/config.json"

# Create directory structure for assets
os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(BACKGROUNDS_DIR, exist_ok=True)

# --- Font Configuration ---
FONT_REGULAR = f"{FONTS_DIR}/Poppins-Regular.ttf"
FONT_BOLD = f"{FONTS_DIR}/Poppins-Bold.ttf"

# Fall back to None if fonts don't exist (will use default system fonts)
FONT_REGULAR = FONT_REGULAR if os.path.exists(FONT_REGULAR) else None
FONT_BOLD = FONT_BOLD if os.path.exists(FONT_BOLD) else None

# --- Color Scheme ---
PRIMARY_COLOR = (114, 137, 218)      # Discord blurple
SECONDARY_COLOR = (255, 255, 255)    # White
ACCENT_COLOR = (46, 204, 113)        # Green accent
DARK_BG = (35, 39, 42)               # Discord dark
LIGHT_TEXT = (255, 255, 255)         # White text
HIGHLIGHT_COLOR = (253, 203, 110)    # Warm yellow for highlights

# --- Card Dimensions ---
# Reduced dimensions for better display in Discord
CARD_WIDTH = 1000                    # Reduced from 1200
CARD_HEIGHT = 563                    # Reduced from 675 (16:9 aspect ratio)

# --- Avatar Settings ---
AVATAR_SIZE = 196                    # Increased from 180
AVATAR_BORDER_SIZE = AVATAR_SIZE + 12  # Increased border

# --- Typography ---
WELCOME_FONT_SIZE = 42               # Increased from 36
USERNAME_FONT_SIZE = 68              # Increased from 60
MESSAGE_FONT_SIZE = 32               # Increased from 28
COUNT_FONT_SIZE = 28                 # Increased from 24
