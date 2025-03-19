"""
AI Discord Bot - Welcome Cards Background Management

This module handles the management of background images for welcome cards.
"""
import os
import io
import json
import random
import asyncio
import tempfile
import traceback
from typing import List, Dict, Any, Optional

from PIL import Image, ImageDraw, ImageFont
from . import config as cfg
from .image_utils import download_image, resize_image

def get_backgrounds_config() -> Dict[str, Any]:
    """
    Load the backgrounds configuration file or create default if not exists.
    
    Returns:
        Dict: The background configuration dictionary.
    """
    if os.path.exists(cfg.BACKGROUNDS_CONFIG):
        try:
            with open(cfg.BACKGROUNDS_CONFIG, 'r') as f:
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
        with open(cfg.BACKGROUNDS_CONFIG, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving backgrounds config: {e}")

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
    print(f"Adding background '{name}' - URL provided: {bool(url)}, Attachment provided: {bool(attachment_data)}")
    
    # Ensure backgrounds directory exists
    os.makedirs(cfg.BACKGROUNDS_DIR, exist_ok=True)
    
    config = get_backgrounds_config()
    
    # Check if name already exists
    if name in config["backgrounds"]:
        print(f"Background with name '{name}' already exists")
        return False
    
    file_path = f"{cfg.BACKGROUNDS_DIR}/{name}.png"
    temp_file = None
    
    try:
        # Get image data
        image_data = None
        if url:
            print(f"Downloading image from URL: {url}")
            image_data = await download_image(url)
            if not image_data:
                print("Failed to download image from URL")
                return False
            
            print(f"Successfully downloaded {len(image_data)} bytes")
            
            # For large images, use a temporary file to avoid memory issues
            if len(image_data) > 5 * 1024 * 1024:  # If larger than 5MB
                print("Large image detected, using temporary file")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.img')
                temp_file.write(image_data)
                temp_file.close()
                
                # Open image from the temp file
                try:
                    image = Image.open(temp_file.name).convert("RGBA")
                    print(f"Opened large image from temp file: {image.width}x{image.height}")
                except Exception as e:
                    print(f"Failed to open large image: {e}")
                    traceback.print_exc()
                    return False
            else:
                # Use BytesIO for smaller images
                image_stream = io.BytesIO(image_data)
                image_stream.seek(0)
                
                try:
                    image = Image.open(image_stream).convert("RGBA")
                    print(f"Opened image from BytesIO: {image.width}x{image.height}")
                except Exception as e:
                    print(f"Failed to open image from BytesIO: {e}")
                    traceback.print_exc()
                    return False
        elif attachment_data:
            print(f"Processing attachment data of {len(attachment_data)} bytes")
            
            # For large attachments, use a temporary file
            if len(attachment_data) > 5 * 1024 * 1024:  # If larger than 5MB
                print("Large attachment detected, using temporary file")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.img')
                temp_file.write(attachment_data)
                temp_file.close()
                
                # Open image from the temp file
                try:
                    image = Image.open(temp_file.name).convert("RGBA")
                    print(f"Opened large attachment from temp file: {image.width}x{image.height}")
                except Exception as e:
                    print(f"Failed to open large attachment: {e}")
                    traceback.print_exc()
                    return False
            else:
                # Use BytesIO for smaller attachments
                image_stream = io.BytesIO(attachment_data)
                image_stream.seek(0)
                
                try:
                    image = Image.open(image_stream).convert("RGBA")
                    print(f"Opened attachment from BytesIO: {image.width}x{image.height}")
                except Exception as e:
                    print(f"Failed to open attachment from BytesIO: {e}")
                    traceback.print_exc()
                    return False
        else:
            print("No valid image data provided")
            return False
        
        # Process and save the image    
        try:
            # Resize to standard dimensions for consistency
            print(f"Resizing image to {cfg.CARD_WIDTH}x{cfg.CARD_HEIGHT}...")
            image = resize_image(image, cfg.CARD_WIDTH, cfg.CARD_HEIGHT)
            print("Resizing successful")
            
            # Save the image
            print(f"Saving image to {file_path}")
            image.save(file_path, "PNG")
            print("Image saved successfully")
            
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
            print(f"Error processing image: {e}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"Error adding background: {e}")
        traceback.print_exc()
        return False
    finally:
        # Clean up any temporary files
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
                print(f"Removed temporary file: {temp_file.name}")
            except Exception as e:
                print(f"Failed to remove temporary file: {e}")

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
        background = resize_image(background, cfg.CARD_WIDTH, cfg.CARD_HEIGHT)
        
        # Add overlay to show how it would look
        overlay = Image.new('RGBA', (cfg.CARD_WIDTH, cfg.CARD_HEIGHT), (0, 0, 0, 110))
        preview = Image.alpha_composite(background, overlay)
        
        # Add text to show it's a preview
        draw = ImageDraw.Draw(preview)
        
        try:
            font = ImageFont.truetype(cfg.FONT_BOLD, 50) if cfg.FONT_BOLD else ImageFont.load_default()
            small_font = ImageFont.truetype(cfg.FONT_REGULAR, 24) if cfg.FONT_REGULAR else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            
        # Draw preview title
        center_x = cfg.CARD_WIDTH // 2
        center_y = cfg.CARD_HEIGHT // 2
        draw.text(
            (center_x, center_y), 
            f"BACKGROUND: {background_name}", 
            fill=cfg.LIGHT_TEXT, 
            font=font, 
            anchor="mm"
        )
        
        # Add info if it's the default
        if background_name == config["default_background"]:
            draw.text(
                (center_x, center_y + 60), 
                "(Default Background)", 
                fill=cfg.ACCENT_COLOR, 
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
