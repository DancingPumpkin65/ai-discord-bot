from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os
import io
import json
import aiohttp
import asyncio
import random
from typing import Tuple, Optional, List, Dict

# Create directory structure for assets
os.makedirs("assets/fonts", exist_ok=True)
os.makedirs("assets/backgrounds", exist_ok=True)
BACKGROUNDS_CONFIG = "assets/backgrounds/config.json"

# Default font paths - you'll need to provide these fonts or use system fonts
FONT_REGULAR = "assets/fonts/Poppins-Regular.ttf"
FONT_BOLD = "assets/fonts/Poppins-Bold.ttf"

# Default colors using a nice color scheme
PRIMARY_COLOR = (114, 137, 218)  # Discord blurple
SECONDARY_COLOR = (255, 255, 255)  # White
ACCENT_COLOR = (46, 204, 113)  # Green accent
DARK_BG = (35, 39, 42)  # Discord dark
LIGHT_TEXT = (255, 255, 255)  # White text

# If the specified fonts don't exist, fall back to default system fonts
if not os.path.exists(FONT_REGULAR):
    FONT_REGULAR = None  # Will use default
if not os.path.exists(FONT_BOLD):
    FONT_BOLD = None  # Will use default

# Background management functions
def get_backgrounds_config() -> Dict:
    """Load the backgrounds configuration file"""
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

def save_backgrounds_config(config: Dict) -> None:
    """Save the backgrounds configuration file"""
    try:
        with open(BACKGROUNDS_CONFIG, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving backgrounds config: {e}")

async def add_background(name: str, url: str = None, attachment_data: bytes = None) -> bool:
    """Add a background to the collection"""
    config = get_backgrounds_config()
    
    # Check if name already exists
    if name in config["backgrounds"]:
        return False
    
    file_path = f"assets/backgrounds/{name}.png"
    
    try:
        # Save from URL or attachment data
        if url:
            image_data = await download_image(url)
            if not image_data:
                return False
        elif attachment_data:
            image_data = attachment_data
        else:
            return False
        
        # Process and save the image
        image = Image.open(io.BytesIO(image_data)).convert("RGBA")
        
        # Resize to standard dimensions (1200x675) for consistency
        image = resize_image(image, 1200, 675)
        
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
        
        save_backgrounds_config(config)
        return True
    
    except Exception as e:
        print(f"Error adding background: {e}")
        return False

def resize_image(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """Resize and crop image to fit target dimensions"""
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

def remove_background(name: str) -> bool:
    """Remove a background from the collection"""
    config = get_backgrounds_config()
    
    if name not in config["backgrounds"]:
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
                config["default_background"] = next(iter(config["backgrounds"]))
            else:
                config["default_background"] = None
        
        save_backgrounds_config(config)
        return True
    except Exception as e:
        print(f"Error removing background: {e}")
        return False

def set_default_background(name: str) -> bool:
    """Set the default background"""
    config = get_backgrounds_config()
    
    if not name:
        # Clear default
        config["default_background"] = None
        save_backgrounds_config(config)
        return True
    
    if name not in config["backgrounds"]:
        return False
    
    config["default_background"] = name
    save_backgrounds_config(config)
    return True

def list_backgrounds() -> List[Dict]:
    """Get list of all backgrounds with info"""
    config = get_backgrounds_config()
    backgrounds = []
    
    for name, info in config["backgrounds"].items():
        backgrounds.append({
            "name": name,
            "path": info["path"],
            "is_default": name == config["default_background"]
        })
    
    return backgrounds

def get_random_background() -> str:
    """Get a random background path"""
    backgrounds = list_backgrounds()
    if not backgrounds:
        return None
    
    bg = random.choice(backgrounds)
    return bg["path"]

def get_default_background() -> str:
    """Get the default background path"""
    config = get_backgrounds_config()
    default = config["default_background"]
    
    if default and default in config["backgrounds"]:
        return config["backgrounds"][default]["path"]
    
    return None

async def download_image(url: str) -> Optional[bytes]:
    """Download an image from a URL"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

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
    """Create a stylish welcome card for new members"""
    try:
        # Card dimensions (16:9 aspect ratio - looks good in Discord)
        width, height = 1200, 675
        
        # Create base image with dark background
        card = Image.new('RGBA', (width, height), DARK_BG)
        draw = ImageDraw.Draw(card)
        
        # Load background image based on priority:
        # 1. Specified background_name from library
        # 2. Specified background_url 
        # 3. Random background if use_random_bg is True
        # 4. Default background
        # 5. Keep solid color background if none available
        
        if background_name:
            # Use specified background from library
            config = get_backgrounds_config()
            if background_name in config["backgrounds"]:
                bg_path = config["backgrounds"][background_name]["path"]
                if os.path.exists(bg_path):
                    background = Image.open(bg_path).convert("RGBA")
                    card = background.copy()
                    draw = ImageDraw.Draw(card)
        
        elif background_url:
            # Use background from URL
            bg_data = await download_image(background_url)
            if bg_data:
                background = Image.open(io.BytesIO(bg_data)).convert("RGBA")
                # Resize and crop to fit our card dimensions
                background = resize_image(background, width, height)
                card = background.copy()
                draw = ImageDraw.Draw(card)
        
        elif use_random_bg:
            # Use random background from library
            bg_path = get_random_background()
            if bg_path and os.path.exists(bg_path):
                background = Image.open(bg_path).convert("RGBA")
                card = background.copy()
                draw = ImageDraw.Draw(card)
        
        else:
            # Use default background if available
            bg_path = get_default_background()
            if bg_path and os.path.exists(bg_path):
                background = Image.open(bg_path).convert("RGBA")
                card = background.copy()
                draw = ImageDraw.Draw(card)
        
        # Apply dark overlay for better text visibility
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 110))  # Semi-transparent black
        card = Image.alpha_composite(card, overlay)
        draw = ImageDraw.Draw(card)
        
        # Add decorative elements
        # Top and bottom accent bars
        draw.rectangle([(0, 0), (width, 8)], fill=accent_color)  # Top bar
        draw.rectangle([(0, height-8), (width, height)], fill=accent_color)  # Bottom bar
        
        # Add a subtle gradient overlay
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        for y in range(height):
            # Create a gradient from top to bottom
            alpha = int(150 - (y / height * 80))  # Fade from visible to less visible
            gradient_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
        
        card = Image.alpha_composite(card, gradient)
        draw = ImageDraw.Draw(card)
        
        # Download and process avatar
        avatar_data = await download_image(avatar_url)
        if not avatar_data:
            # If avatar can't be downloaded, create a placeholder
            avatar = Image.new('RGBA', (256, 256), accent_color)
            avatar_draw = ImageDraw.Draw(avatar)
            avatar_draw.text((128, 128), username[0].upper(), fill=LIGHT_TEXT, anchor='mm',
                           font=ImageFont.truetype(FONT_BOLD, 100) if FONT_BOLD else ImageFont.load_default())
        else:
            avatar = Image.open(io.BytesIO(avatar_data)).convert("RGBA")
        
        # Resize avatar to desired size
        avatar_size = 180
        avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
        
        # Create circular mask for avatar
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        
        # Apply circular mask to avatar
        avatar_circle = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        avatar_circle.putalpha(mask)
        
        # Create a slightly larger circle for the avatar border
        border_size = avatar_size + 10
        avatar_border = Image.new('RGBA', (border_size, border_size), accent_color)
        border_mask = Image.new('L', (border_size, border_size), 0)
        border_draw = ImageDraw.Draw(border_mask)
        border_draw.ellipse((0, 0, border_size, border_size), fill=255)
        avatar_border.putalpha(border_mask)
        
        # Center the avatar on the border
        avatar_with_border = avatar_border.copy()
        avatar_with_border.paste(avatar_circle, (5, 5), avatar_circle)
        
        # Position for the avatar
        avatar_pos_x = (width - border_size) // 2
        avatar_pos_y = 120  # From top
        
        # Place avatar with border on card
        card.paste(avatar_with_border, (avatar_pos_x, avatar_pos_y), avatar_with_border)
        
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
        
        # Calculate positions
        center_x = width // 2
        
        # Add welcome text
        welcome_y = avatar_pos_y + border_size + 30
        draw.text((center_x, welcome_y), "WELCOME", fill=LIGHT_TEXT, font=title_font, anchor="mt")
        
        # Add username (with proper text wrapping if too long)
        username_y = welcome_y + 50
        if len(username) > 20:
            username_font = ImageFont.truetype(FONT_BOLD, 40) if FONT_BOLD else ImageFont.load_default()
        draw.text((center_x, username_y), username, fill=LIGHT_TEXT, font=username_font, anchor="mt")
        
        # Add custom message or default message
        message = custom_message or f"Welcome to {server_name}!"
        message_y = username_y + 70
        draw.text((center_x, message_y), message, fill=LIGHT_TEXT, font=subtitle_font, anchor="mt")
        
        # Add member count with a nice label
        count_y = message_y + 60
        draw.text((center_x, count_y), f"You are the {member_count}{'th' if member_count % 10 != 1 else 'st'} member", 
                 fill=SECONDARY_COLOR, font=small_font, anchor="mt")
        
        # Add decorative element at bottom
        decoration_y = height - 50
        draw.text((center_x, decoration_y), "• • •", fill=accent_color, font=subtitle_font, anchor="mt")
        
        # Save to buffer
        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        print(f"Error creating welcome card: {e}")
        return None

# Create a background preview card
async def create_background_preview(background_name: str) -> Optional[io.BytesIO]:
    """Create a preview image of a background"""
    config = get_backgrounds_config()
    
    if background_name not in config["backgrounds"]:
        return None
    
    file_path = config["backgrounds"][background_name]["path"]
    
    try:
        # Load background
        background = Image.open(file_path).convert("RGBA")
        
        # Resize if needed
        width, height = 1200, 675
        background = resize_image(background, width, height)
        
        # Add overlay to show how it would look
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 110))
        preview = Image.alpha_composite(background, overlay)
        
        # Add text to show it's a preview
        draw = ImageDraw.Draw(preview)
        
        try:
            font = ImageFont.truetype(FONT_BOLD, 50) if FONT_BOLD else ImageFont.load_default()
            small_font = ImageFont.truetype(FONT_REGULAR, 24) if FONT_REGULAR else ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            
        # Draw text
        draw.text((width//2, height//2), f"BACKGROUND: {background_name}", 
                  fill=LIGHT_TEXT, font=font, anchor="mm")
        
        # Add info if it's the default
        if background_name == config["default_background"]:
            draw.text((width//2, height//2 + 60), "(Default Background)", 
                      fill=ACCENT_COLOR, font=small_font, anchor="mm")
        
        # Save to buffer
        buffer = io.BytesIO()
        preview.save(buffer, format="PNG")
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        print(f"Error creating background preview: {e}")
        return None

def create_welcome_embed(username, server_name, member_count, user_id):
    """Create a welcome embed to accompany the welcome card"""
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
