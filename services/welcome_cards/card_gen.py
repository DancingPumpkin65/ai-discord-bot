"""
AI Discord Bot - Welcome Card Generation Module

This module handles the creation of welcome cards for new members.
"""
# Standard library imports
import os
import io
import textwrap
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
                
        # Apply a gradient overlay for better text visibility and aesthetic appeal
        gradient = Image.new('RGBA', (cfg.CARD_WIDTH, cfg.CARD_HEIGHT), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        
        # Create a dark gradient from bottom to top
        for y in range(cfg.CARD_HEIGHT):
            # Make the bottom darker than the top
            alpha = int(40 + (y / cfg.CARD_HEIGHT * 160))  # 40-200 alpha range
            gradient_draw.line([(0, y), (cfg.CARD_WIDTH, y)], fill=(0, 0, 0, alpha))
        
        card = Image.alpha_composite(card, gradient)
        
        # Add stylish side accent bars
        accent_width = 6
        draw = ImageDraw.Draw(card)
        draw.rectangle([(0, 0), (accent_width, cfg.CARD_HEIGHT)], fill=accent_color)  # Left bar
        draw.rectangle([(cfg.CARD_WIDTH-accent_width, 0), (cfg.CARD_WIDTH, cfg.CARD_HEIGHT)], fill=accent_color)  # Right bar
        
        # Process avatar with enhanced glow effect
        avatar = await process_avatar(avatar_url, username, accent_color)
        
        # Position avatar
        avatar_size = avatar.width
        avatar_pos_x = (cfg.CARD_WIDTH - avatar_size) // 2
        avatar_pos_y = 100  # Moved higher up from 120
        
        # Create subtle glow effect behind avatar
        glow_size = avatar_size + 20
        glow = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_color = (*accent_color, 60)  # Semi-transparent accent color
        for i in range(10, 0, -1):
            glow_draw.ellipse((i, i, glow_size - i, glow_size - i), fill=(*accent_color, 6))
        
        # Position and paste glow
        glow_pos_x = avatar_pos_x - 10
        glow_pos_y = avatar_pos_y - 10
        card.paste(glow, (glow_pos_x, glow_pos_y), glow)
        
        # Place avatar on card
        card.paste(avatar, (avatar_pos_x, avatar_pos_y), avatar)
        
        # Load fonts with enhanced sizes
        try:
            username_font = ImageFont.truetype(cfg.FONT_BOLD, cfg.USERNAME_FONT_SIZE) if cfg.FONT_BOLD else ImageFont.load_default()
            title_font = ImageFont.truetype(cfg.FONT_BOLD, cfg.WELCOME_FONT_SIZE) if cfg.FONT_BOLD else ImageFont.load_default()
            subtitle_font = ImageFont.truetype(cfg.FONT_REGULAR, cfg.MESSAGE_FONT_SIZE) if cfg.FONT_REGULAR else ImageFont.load_default()
            small_font = ImageFont.truetype(cfg.FONT_REGULAR, cfg.COUNT_FONT_SIZE) if cfg.FONT_REGULAR else ImageFont.load_default()
        except Exception as e:
            print(f"Error loading fonts: {e} - Using default fonts")
            username_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Center position for text elements
        center_x = cfg.CARD_WIDTH // 2
        
        # Calculate updated positions for text elements
        welcome_y = avatar_pos_y + avatar_size + 26  # Reduced space
        username_y = welcome_y + 46  # Reduced space
        message_y = username_y + 64  # Reduced space
        count_y = message_y + 50  # Reduced space
        
        # Use smaller font for long usernames
        if len(username) > 20:
            username_font = ImageFont.truetype(cfg.FONT_BOLD, 48) if cfg.FONT_BOLD else ImageFont.load_default()
        
        # Add a subtle text shadow effect for better readability
        def draw_text_with_shadow(x, y, text, font, fill, anchor="mt", shadow_color=(0,0,0,120), shadow_offset=2):
            # Draw shadow first
            draw.text((x+shadow_offset, y+shadow_offset), text, font=font, fill=shadow_color, anchor=anchor)
            # Draw main text
            draw.text((x, y), text, font=font, fill=fill, anchor=anchor)
        
        # Draw text elements with shadows
        draw_text_with_shadow(center_x, welcome_y, "WELCOME", title_font, cfg.HIGHLIGHT_COLOR)
        draw_text_with_shadow(center_x, username_y, username, username_font, cfg.LIGHT_TEXT)
        
        # Draw custom or default message (with word wrap for long server names)
        message = custom_message or f"Welcome to {server_name}!"
        # Wrap text if too long
        if len(message) > 40:
            message = "\n".join(textwrap.wrap(message, width=40, break_long_words=False))
        draw_text_with_shadow(center_x, message_y, message, subtitle_font, cfg.LIGHT_TEXT)
        
        # Calculate ordinal suffix for member count
        if 11 <= member_count % 100 <= 13:
            suffix = "th"  # 11th, 12th, 13th
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(member_count % 10, "th")
        
        # Create a highlight box for member count
        count_text = f"You are the {member_count}{suffix} member"
        count_width = center_x * 0.7  # 70% of center_x
        count_height = 40
        count_rect_x = center_x - count_width // 2
        count_rect_y = count_y - 5
        
        # Draw semi-transparent background
        draw.rectangle(
            [(count_rect_x, count_rect_y), (count_rect_x + count_width, count_rect_y + count_height)],
            fill=(0, 0, 0, 100),
            outline=accent_color
        )
        
        # Draw member count with highlighting
        draw_text_with_shadow(
            center_x, count_y + count_height//2 - 2,
            count_text, small_font, cfg.LIGHT_TEXT,
            anchor="mm"  # Middle-middle anchor
        )
        
        # Add decorative accent at the bottom
        decoration_y = cfg.CARD_HEIGHT - 40
        draw.text((center_x, decoration_y), "• • •", fill=accent_color, font=subtitle_font, anchor="mm")
        
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