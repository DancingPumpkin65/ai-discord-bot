"""
AI Discord Bot - Welcome Card Module

This module handles the creation and management of welcome cards for new members.
It includes functions to create, customize, and manage background images for welcome cards.
"""
# Standard library imports
import os
import io
import json
import random
import asyncio
from typing import Tuple, Optional, List, Dict, Any, Union

# Third-party imports
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# --- Configuration Constants ---

# Directory structure
ASSETS_DIR = "assets"
FONTS_DIR = f"{ASSETS_DIR}/fonts"
BACKGROUNDS_DIR = f"{ASSETS_DIR}/backgrounds"
BACKGROUNDS_CONFIG = f"{BACKGROUNDS_DIR}/config.json"

# Create directory structure for assets
os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(BACKGROUNDS_DIR, exist_ok=True)

# Default font paths with fallbacks
FONT_REGULAR = f"{FONTS_DIR}/Poppins-Regular.ttf"
FONT_BOLD = f"{FONTS_DIR}/Poppins-Bold.ttf"
FONT_REGULAR = FONT_REGULAR if os.path.exists(FONT_REGULAR) else None
FONT_BOLD = FONT_BOLD if os.path.exists(FONT_BOLD) else None

# Default color scheme (RGB tuples)
PRIMARY_COLOR = (114, 137, 218)  # Discord blurple
SECONDARY_COLOR = (255, 255, 255)  # White
ACCENT_COLOR = (46, 204, 113)  # Green accent
DARK_BG = (35, 39, 42)  # Discord dark
LIGHT_TEXT = (255, 255, 255)  # White text

# Welcome card dimensions
CARD_WIDTH = 1200
CARD_HEIGHT = 675

# --- Background Configuration Management ---

def get_backgrounds_config() -> Dict[str, Any]:
    """
    Load the backgrounds configuration file or create default if not exists.
    
    Returns:
        Dict: The background configuration dictionary.
    """
    if os.path.exists(BACKGROUNDS_CONFIG):
        try:
            with open(BACKGROUNDS_CONFIG, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading backgrounds config: {e}")
    
    # Create default config if not exists
    default_config = {
        "default_background": None,
        "backgrounds": {}
    }
    save_backgrounds_config(default_config)
    return default_config

def save_backgrounds_config(config: Dict[str, Any]) -> None:
    """
    Save the backgrounds configuration to file.
    
    Args:
        config: The configuration dictionary to save.
    """
    try:
        with open(BACKGROUNDS_CONFIG, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving backgrounds config: {e}")

# --- Image Processing Utilities ---

def resize_image(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """
    Resize and crop image to fit target dimensions while maintaining aspect ratio.
    
    Args:
        image: The PIL Image object to resize
        target_width: The desired width in pixels
        target_height: The desired height in pixels
        
    Returns:
        A resized and cropped PIL Image
    """
    # Calculate aspect ratios
    img_ratio = image.width / image.height
    target_ratio = target_width / target_height
    
    if img_ratio > target_ratio:
        # Image is wider than target
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        # Image is taller than target
        new_width = target_width
        new_height = int(target_width / img_ratio)
    
    # Resize to maintain aspect ratio
    resized = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Center crop
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height
    
    return resized.crop((left, top, right, bottom))

async def download_image(url: str) -> Optional[bytes]:
    """
    Download an image from a URL.
    
    Args:
        url: The URL of the image to download
        
    Returns:
        Bytes containing the image data, or None if download failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                print(f"Failed to download image: HTTP {response.status}")
                return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

# --- Background Management Functions ---

async def add_background(name: str, url: str = None, attachment_data: bytes = None) -> bool:
    """
    Add a background to the collection from URL or attachment data.
    
    Args:
        name: The name for the background (used as identifier)
        url: Optional URL of the image to download
        attachment_data: Optional image data from an attachment
        
    Returns:
        True if adding was successful, False otherwise
    """
    config = get_backgrounds_config()
    
    # Check if name already exists
    if name in config["backgrounds"]:
        print(f"Background with name '{name}' already exists")
        return False
    
    file_path = f"{BACKGROUNDS_DIR}/{name}.png"
    
    try:
        # Get image data from URL or attachment data
        image_data = None
        if url:
            image_data = await download_image(url)
        elif attachment_data:
            image_data = attachment_data
            
        if not image_data:
            print("No valid image data provided")
            return False
        
        # Process and save the image
        image = Image.open(io.BytesIO(image_data)).convert("RGBA")
        
        # Resize to standard dimensions for consistency
        image = resize_image(image, CARD_WIDTH, CARD_HEIGHT)
        
        # Save the image
        image.save(file_path, "PNG")
        
        # Update config
        config["backgrounds"][name] = {
            "path": file_path,
            "added_at": str(asyncio.get_event_loop().time())
        }
        
        # Set as default if it's the first background
        if not config["default_background"]:
            config["default_background"] = name
            print(f"Set '{name}' as default background")
        
        save_backgrounds_config(config)
        print(f"Background '{name}' successfully added")
        return True
    
    except Exception as e:
        print(f"Error adding background: {e}")
        return False

def remove_background(name: str) -> bool:
    """
    Remove a background from the collection.
    
    Args:
        name: The name of the background to remove
        
    Returns:
        True if removal was successful, False otherwise
    """
    config = get_backgrounds_config()
    
    if name not in config["backgrounds"]:
        print(f"Background '{name}' not found")
        return False
    
    try:
        # Delete the file
        file_path = config["backgrounds"][name]["path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Update config
        del config["backgrounds"][name]
        
        # Update default if needed
        if config["default_background"] == name:
            if config["backgrounds"]:
                new_default = next(iter(config["backgrounds"]))
                config["default_background"] = new_default
                print(f"Changed default background to '{new_default}'")
            else:
                config["default_background"] = None
                print("No backgrounds left, cleared default")
        
        save_backgrounds_config(config)
        print(f"Background '{name}' successfully removed")
        return True
    except Exception as e:
        print(f"Error removing background: {e}")
        return False

def set_default_background(name: str) -> bool:
    """
    Set the default background.
    
    Args:
        name: The name of the background to set as default
        
    Returns:
        True if setting default was successful, False otherwise
    """
    config = get_backgrounds_config()
    
    if not name:
        # Clear default
        config["default_background"] = None
        save_backgrounds_config(config)
        print("Default background cleared")
        return True
    
    if name not in config["backgrounds"]:
        print(f"Background '{name}' not found")
        return False
    
    config["default_background"] = name
    save_backgrounds_config(config)
    print(f"Default background set to '{name}'")
    return True

def list_backgrounds() -> List[Dict[str, Any]]:
    """
    Get a list of all backgrounds with information.
    
    Returns:
        List of dictionaries containing background info
    """
    config = get_backgrounds_config()
    backgrounds = []
    
    for name, info in config["backgrounds"].items():
        backgrounds.append({
            "name": name,
            "path": info["path"],
            "is_default": name == config["default_background"]
        })
    
    return backgrounds

def get_random_background() -> Optional[str]:
    """
    Get a random background path.
    
    Returns:
        Path to a random background, or None if no backgrounds exist
    """
    backgrounds = list_backgrounds()
    if not backgrounds:
        return None
    
    bg = random.choice(backgrounds)
    return bg["path"]

def get_default_background() -> Optional[str]:
    """
    Get the default background path.
    
    Returns:
        Path to the default background, or None if no default is set
    """
    config = get_backgrounds_config()
    default = config["default_background"]
    
    if default and default in config["backgrounds"]:
        return config["backgrounds"][default]["path"]
    
    return None

# --- Welcome Card Creation Functions ---

async def create_welcome_card(
    username: str, 
    avatar_url: str, 
    server_name: str, 
    member_count: int, 
    background_url: Optional[str] = None,
    background_name: Optional[str] = None,
    use_random_bg: bool = False,
    accent_color: Tuple[int, int, int] = ACCENT_COLOR,
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
        card = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), DARK_BG)
        draw = ImageDraw.Draw(card)
        
        # Select background image based on priority:
        # 1. Specified background_name from library
        # 2. Specified background_url 
        # 3. Random background if use_random_bg is True
        # 4. Default background
        # 5. Keep solid color background if none available
        
        background_applied = False
        
        # Try to apply specified background from library
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
        
        # Try to apply background from URL if no background applied yet
        if not background_applied and background_url:
            bg_data = await download_image(background_url)
            if bg_data:
                background = Image.open(io.BytesIO(bg_data)).convert("RGBA")
                background = resize_image(background, CARD_WIDTH, CARD_HEIGHT)
                card = background.copy()
                draw = ImageDraw.Draw(card)
                background_applied = True
                print("Using background from URL")
        
        # Try to use random background if requested and no background applied yet
        if not background_applied and use_random_bg:
            bg_path = get_random_background()
            if bg_path and os.path.exists(bg_path):
                background = Image.open(bg_path).convert("RGBA")
                card = background.copy()
                draw = ImageDraw.Draw(card)
                background_applied = True
                print("Using random background")
        
        # Try to use default background if no background applied yet
        if not background_applied:
            bg_path = get_default_background()
            if bg_path and os.path.exists(bg_path):
                background = Image.open(bg_path).convert("RGBA")
                card = background.copy()
                draw = ImageDraw.Draw(card)
                background_applied = True
                print("Using default background")
        
        if not background_applied:
            print("Using solid color background")
        
        # Apply dark overlay for better text visibility
        overlay = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 110))  # Semi-transparent black
        card = Image.alpha_composite(card, overlay)
        draw = ImageDraw.Draw(card)
        
        # Add decorative elements
        # Top and bottom accent bars
        draw.rectangle([(0, 0), (CARD_WIDTH, 8)], fill=accent_color)  # Top bar
        draw.rectangle([(0, CARD_HEIGHT-8), (CARD_WIDTH, CARD_HEIGHT)], fill=accent_color)  # Bottom bar
        
        # Add a subtle gradient overlay
        gradient = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        for y in range(CARD_HEIGHT):
            # Create a gradient from top to bottom
            alpha = int(150 - (y / CARD_HEIGHT * 80))  # Fade from visible to less visible
            gradient_draw.line([(0, y), (CARD_WIDTH, y)], fill=(0, 0, 0, alpha))
        
        card = Image.alpha_composite(card, gradient)
        draw = ImageDraw.Draw(card)
        
        # Process avatar
        avatar = await process_avatar(avatar_url, username, accent_color)
        
        # Position avatar
        avatar_size = avatar.width
        avatar_pos_x = (CARD_WIDTH - avatar_size) // 2
        avatar_pos_y = 120  # From top
        
        # Place avatar with border on card
        card.paste(avatar, (avatar_pos_x, avatar_pos_y), avatar)
        
        # Load fonts with fallbacks
        try:
            username_font = ImageFont.truetype(FONT_BOLD, 60) if FONT_BOLD else ImageFont.load_default()
            title_font = ImageFont.truetype(FONT_BOLD, 36) if FONT_BOLD else ImageFont.load_default()
            subtitle_font = ImageFont.truetype(FONT_REGULAR, 28) if FONT_REGULAR else ImageFont.load_default()
            small_font = ImageFont.truetype(FONT_REGULAR, 24) if FONT_REGULAR else ImageFont.load_default()
        except Exception as e:
            print(f"Error loading fonts: {e} - Using default fonts")
            username_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Center position for text elements
        center_x = CARD_WIDTH // 2
        
        # Calculate positions for text elements
        welcome_y = avatar_pos_y + avatar_size + 30
        username_y = welcome_y + 50
        message_y = username_y + 70
        count_y = message_y + 60
        decoration_y = CARD_HEIGHT - 50
        
        # Use smaller font for long usernames
        if len(username) > 20:
            username_font = ImageFont.truetype(FONT_BOLD, 40) if FONT_BOLD else ImageFont.load_default()
        
        # Draw text elements
        draw.text((center_x, welcome_y), "WELCOME", fill=LIGHT_TEXT, font=title_font, anchor="mt")
        draw.text((center_x, username_y), username, fill=LIGHT_TEXT, font=username_font, anchor="mt")
        
        # Draw custom or default message
        message = custom_message or f"Welcome to {server_name}!"
        draw.text((center_x, message_y), message, fill=LIGHT_TEXT, font=subtitle_font, anchor="mt")
        
        # Calculate ordinal suffix for member count
        if 11 <= member_count % 100 <= 13:
            suffix = "th"  # 11th, 12th, 13th
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(member_count % 10, "th")
        
        # Draw member count
        draw.text(
            (center_x, count_y), 
            f"You are the {member_count}{suffix} member", 
            fill=SECONDARY_COLOR, 
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
        return None

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
    # Avatar settings
    avatar_size = 180
    border_size = avatar_size + 10
    final_size = border_size
    
    # Download avatar image
    avatar_data = await download_image(avatar_url)
    
    if not avatar_data:
        # Create placeholder if avatar can't be downloaded
        avatar = Image.new('RGBA', (256, 256), accent_color)
        avatar_draw = ImageDraw.Draw(avatar)
        try:
            avatar_font = ImageFont.truetype(FONT_BOLD, 100) if FONT_BOLD else ImageFont.load_default()
        except Exception:
            avatar_font = ImageFont.load_default()
            
        # Draw first character of username
        avatar_draw.text(
            (128, 128), 
            username[0].upper(), 
            fill=LIGHT_TEXT, 
            font=avatar_font, 
            anchor='mm'
        )
    else:
        # Process downloaded avatar
        avatar = Image.open(io.BytesIO(avatar_data)).convert("RGBA")
    
    # Resize avatar to desired size
    avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
    
    # Create circular mask
    mask = Image.new('L', (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
    
    # Apply circular mask to avatar
    avatar_circle = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
    avatar_circle.putalpha(mask)
    
    # Create a border
    avatar_with_border = Image.new('RGBA', (final_size, final_size), (0, 0, 0, 0))
    border = Image.new('RGBA', (final_size, final_size), accent_color)
    border_mask = Image.new('L', (final_size, final_size), 0)
    border_draw = ImageDraw.Draw(border_mask)
    border_draw.ellipse((0, 0, final_size, final_size), fill=255)
    border.putalpha(border_mask)
    
    # Combine border and avatar
    avatar_with_border = Image.alpha_composite(avatar_with_border, border)
    avatar_with_border.paste(
        avatar_circle, 
        ((final_size - avatar_size) // 2, (final_size - avatar_size) // 2), 
        avatar_circle
    )
    
    return avatar_with_border

async def create_background_preview(background_name: str) -> Optional[io.BytesIO]:
    """
    Create a preview image of a background.
    
    Args:
        background_name: Name of the background to preview
        
    Returns:
        BytesIO buffer containing the PNG preview, or None if creation failed
    """
    config = get_backgrounds_config()
    
    if background_name not in config["backgrounds"]:
        print(f"Background '{background_name}' not found")
        return None
    
    file_path = config["backgrounds"][background_name]["path"]
    
    try:
        # Load background
        background = Image.open(file_path).convert("RGBA")
        
        # Resize if needed
        background = resize_image(background, CARD_WIDTH, CARD_HEIGHT)
        
        # Add overlay to show how it would look
        overlay = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 110))
        preview = Image.alpha_composite(background, overlay)
        
        # Add text to show it's a preview
        draw = ImageDraw.Draw(preview)
        
        try:
            font = ImageFont.truetype(FONT_BOLD, 50) if FONT_BOLD else ImageFont.load_default()
            small_font = ImageFont.truetype(FONT_REGULAR, 24) if FONT_REGULAR else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            
        # Draw preview title
        center_x = CARD_WIDTH // 2
        center_y = CARD_HEIGHT // 2
        draw.text(
            (center_x, center_y), 
            f"BACKGROUND: {background_name}", 
            fill=LIGHT_TEXT, 
            font=font, 
            anchor="mm"
        )
        
        # Add info if it's the default
        if background_name == config["default_background"]:
            draw.text(
                (center_x, center_y + 60), 
                "(Default Background)", 
                fill=ACCENT_COLOR, 
                font=small_font, 
                anchor="mm"
            )
        
        # Save to buffer
        buffer = io.BytesIO()
        preview.save(buffer, format="PNG")
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        print(f"Error creating background preview: {e}")
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
