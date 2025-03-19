"""
AI Discord Bot - Welcome Card Generation Module

This module handles the creation of welcome cards for new members.
"""
# Standard library imports
import os
import io
from typing import Tuple, Optional

# Third-party imports
from PIL import Image, ImageDraw, ImageFont

# Local imports
from . import config as cfg
from .image_utils import download_image, create_circular_image, resize_image
from .backgrounds import (
    get_backgrounds_config, get_default_background, 
    get_random_background
)

async def process_avatar(
    avatar_url: str, 
    username: str, 
    accent_color: Tuple[int, int, int]
) -> Image.Image:
    """
    Process avatar image: download, create circular mask, and add border.
    
    Args:
        avatar_url: URL of the avatar image
        username: Username (used for placeholder if avatar can't be downloaded)
        accent_color: RGB tuple for avatar border color
        
    Returns:
        Processed PIL Image with the avatar
    """
    avatar_size = cfg.AVATAR_SIZE
    border_size = cfg.AVATAR_BORDER_SIZE
    
    # Download avatar image
    avatar_data = await download_image(avatar_url)
    
    if not avatar_data:
        # Create placeholder if avatar can't be downloaded
        avatar = Image.new('RGBA', (256, 256), accent_color)
        avatar_draw = ImageDraw.Draw(avatar)
        try:
            avatar_font = ImageFont.truetype(cfg.FONT_BOLD, 100) if cfg.FONT_BOLD else ImageFont.load_default()
        except Exception:
            avatar_font = ImageFont.load_default()
            
        # Draw first character of username
        avatar_draw.text(
            (128, 128), 
            username[0].upper(), 
            fill=cfg.LIGHT_TEXT, 
            font=avatar_font, 
            anchor='mm'
        )
    else:
        # Process downloaded avatar
        avatar = Image.open(io.BytesIO(avatar_data)).convert("RGBA")
    
    # Create circular avatar
    avatar_circle = create_circular_image(avatar, avatar_size)
    
    # Create border
    final_size = border_size
    result = Image.new('RGBA', (final_size, final_size), (0, 0, 0, 0))
    border = create_circular_image(
        Image.new('RGBA', (final_size, final_size), accent_color),
        final_size
    )
    
    # Combine border and avatar
    result = Image.alpha_composite(result, border)
    
    # Calculate position to center avatar on border
    pos_x = (final_size - avatar_size) // 2
    pos_y = (final_size - avatar_size) // 2
    
    # Paste avatar onto border
    result.paste(avatar_circle, (pos_x, pos_y), avatar_circle)
    
    return result

async def create_welcome_card(
    username: str, 
    avatar_url: str, 
    server_name: str, 
    member_count: int, 
    background_url: Optional[str] = None,
    background_name: Optional[str] = None,
    use_random_bg: bool = False,
    accent_color: Tuple[int, int, int] = cfg.ACCENT_COLOR,
    custom_message: Optional[str] = None
) -> Optional[io.BytesIO]:
    """
    Create a stylish welcome card for new members.
    
    Args:
        username: The username to display
        avatar_url: URL of the user's avatar
        server_name: Name of the server
        member_count: The current member count
        background_url: Optional URL for a custom background
        background_name: Optional name of a stored background
        use_random_bg: Whether to use a random background
        accent_color: RGB tuple for accent color
        custom_message: Custom welcome message
        
    Returns:
        BytesIO buffer containing the PNG image, or None if creation failed
    """
    try:
        # Create base image with dark background
        card = Image.new('RGBA', (cfg.CARD_WIDTH, cfg.CARD_HEIGHT), cfg.DARK_BG)
        draw = ImageDraw.Draw(card)
        
        # Apply background following the priority order
        background_applied = False
        
        # 1. Try specified background from library
        if background_name:
            config = get_backgrounds_config()
            if background_name in config["backgrounds"]:
                bg_path = config["backgrounds"][background_name]["path"]
                if os.path.exists(bg_path):
                    background = Image.open(bg_path).convert("RGBA")
                    card = background.copy()
                    draw = ImageDraw.Draw(card)
                    background_applied = True
                    print(f"Using specified background: {background_name}")
        
        # 2. Try background from URL
        if not background_applied and background_url:
            bg_data = await download_image(background_url)
            if bg_data:
                background = Image.open(io.BytesIO(bg_data)).convert("RGBA")
                background = resize_image(background, cfg.CARD_WIDTH, cfg.CARD_HEIGHT)
                card = background.copy()
                draw = ImageDraw.Draw(card)
                background_applied = True
                print("Using background from URL")
        
        # 3. Try random background
        if not background_applied and use_random_bg:
            bg_path = get_random_background()
            if bg_path and os.path.exists(bg_path):
                background = Image.open(bg_path).convert("RGBA")
                card = background.copy()
                draw = ImageDraw.Draw(card)
                background_applied = True
                print("Using random background")
        
        # 4. Try default background
        if not background_applied:
            bg_path = get_default_background()
            if bg_path and os.path.exists(bg_path):
                background = Image.open(bg_path).convert("RGBA")
                card = background.copy()
                draw = ImageDraw.Draw(card)
                background_applied = True
                print("Using default background")
            else:
                print("Using solid color background")
        
        # Apply dark overlay for better text visibility
        overlay = Image.new('RGBA', (cfg.CARD_WIDTH, cfg.CARD_HEIGHT), (0, 0, 0, 110))
        card = Image.alpha_composite(card, overlay)
        draw = ImageDraw.Draw(card)
        
        # Add decorative elements
        # Top and bottom accent bars
        draw.rectangle([(0, 0), (cfg.CARD_WIDTH, 8)], fill=accent_color)  # Top bar
        draw.rectangle([(0, cfg.CARD_HEIGHT-8), (cfg.CARD_WIDTH, cfg.CARD_HEIGHT)], fill=accent_color)  # Bottom bar
        
        # Add a subtle gradient overlay
        gradient = Image.new('RGBA', (cfg.CARD_WIDTH, cfg.CARD_HEIGHT), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        for y in range(cfg.CARD_HEIGHT):
            # Create a gradient from top to bottom
            alpha = int(150 - (y / cfg.CARD_HEIGHT * 80))  # Fade from visible to less visible
            gradient_draw.line([(0, y), (cfg.CARD_WIDTH, y)], fill=(0, 0, 0, alpha))
        
        card = Image.alpha_composite(card, gradient)
        draw = ImageDraw.Draw(card)
        
        # Process avatar
        avatar = await process_avatar(avatar_url, username, accent_color)
        
        # Position avatar
        avatar_size = avatar.width
        avatar_pos_x = (cfg.CARD_WIDTH - avatar_size) // 2
        avatar_pos_y = 120  # From top
        
        # Place avatar with border on card
        card.paste(avatar, (avatar_pos_x, avatar_pos_y), avatar)
        
        # Rest of the function continues as before...
        # Load fonts with fallbacks
        try:
            username_font = ImageFont.truetype(cfg.FONT_BOLD, 60) if cfg.FONT_BOLD else ImageFont.load_default()
            title_font = ImageFont.truetype(cfg.FONT_BOLD, 36) if cfg.FONT_BOLD else ImageFont.load_default()
            subtitle_font = ImageFont.truetype(cfg.FONT_REGULAR, 28) if cfg.FONT_REGULAR else ImageFont.load_default()
            small_font = ImageFont.truetype(cfg.FONT_REGULAR, 24) if cfg.FONT_REGULAR else ImageFont.load_default()
        except Exception as e:
            print(f"Error loading fonts: {e} - Using default fonts")
            username_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Center position for text elements
        center_x = cfg.CARD_WIDTH // 2
        
        # Calculate positions for text elements
        welcome_y = avatar_pos_y + avatar_size + 30
        username_y = welcome_y + 50
        message_y = username_y + 70
        count_y = message_y + 60
        decoration_y = cfg.CARD_HEIGHT - 50
        
        # Use smaller font for long usernames
        if len(username) > 20:
            username_font = ImageFont.truetype(cfg.FONT_BOLD, 40) if cfg.FONT_BOLD else ImageFont.load_default()
        
        # Draw text elements
        draw.text((center_x, welcome_y), "WELCOME", fill=cfg.LIGHT_TEXT, font=title_font, anchor="mt")
        draw.text((center_x, username_y), username, fill=cfg.LIGHT_TEXT, font=username_font, anchor="mt")
        
        # Draw custom or default message
        message = custom_message or f"Welcome to {server_name}!"
        draw.text((center_x, message_y), message, fill=cfg.LIGHT_TEXT, font=subtitle_font, anchor="mt")
        
        # Calculate ordinal suffix for member count
        if 11 <= member_count % 100 <= 13:
            suffix = "th"  # 11th, 12th, 13th
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(member_count % 10, "th")
        
        # Draw member count
        draw.text(
            (center_x, count_y), 
            f"You are the {member_count}{suffix} member", 
            fill=cfg.SECONDARY_COLOR, 
            font=small_font, 
            anchor="mt"
        )
        
        # Draw decorative element at bottom
        draw.text((center_x, decoration_y), "• • •", fill=accent_color, font=subtitle_font, anchor="mt")
        
        # Save to buffer
        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        print(f"Error creating welcome card: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_welcome_embed(username: str, server_name: str, member_count: int, user_id: int):
    """
    Create a welcome embed to accompany the welcome card.
    
    Args:
        username: The username to display
        server_name: Name of the server
        member_count: The current member count
        user_id: Discord user ID
        
    Returns:
        Discord Embed object
    """
    from discord import Embed
    
    embed = Embed(
        title=f"Welcome to {server_name}!",
        description=f"We're happy to have you here, {username}!",
        color=0x2ecc71
    )
    
    embed.set_footer(text=f"Member #{member_count} • ID: {user_id}")
    
    # Add some helpful information
    embed.add_field(name="Getting Started", value="Check out <#CHANNEL_ID> to get started!", inline=False)
    embed.add_field(name="Rules", value="Please read our rules in <#CHANNEL_ID>", inline=False)
    
    return embed