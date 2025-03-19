"""
AI Discord Bot - Welcome Cards Image Utilities

This module provides image processing functions for welcome cards.
"""
from typing import Optional, Tuple
import io
import time
import traceback
import re
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageOps
import tempfile
import os

async def download_image(url: str) -> Optional[bytes]:
    """
    Download an image from a URL with enhanced error handling and headers.
    
    Args:
        url: The URL of the image to download
        
    Returns:
        Bytes containing the image data, or None if download failed
    """
    try:
        # Handle uhdpaper.com URLs specifically
        if "uhdpaper.com" in url:
            print(f"Detected uhdpaper.com URL, using specialized method")
            return await download_uhdpaper_image(url)
            
        # Add timeout to prevent hanging on slow connections
        timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
        
        # Set professional headers to avoid getting blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://discord.com/',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'Trailers',
        }
        
        start_time = time.time()
        print(f"Starting download from {url}")
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status == 200:
                    data = await response.read()
                    elapsed = time.time() - start_time
                    print(f"Download successful: {len(data)} bytes in {elapsed:.2f} seconds")
                    
                    # Verify the downloaded data is an image (do a quick check)
                    try:
                        img_test = Image.open(io.BytesIO(data))
                        img_format = img_test.format
                        img_size = f"{img_test.width}x{img_test.height}"
                        print(f"Verified image data: {img_format} format, {img_size}")
                        return data
                    except Exception as img_err:
                        print(f"Downloaded data is not a valid image: {img_err}")
                        
                        # Debug: Print first 100 bytes to see what we got
                        content_preview = data[:100]
                        if b"<!DOCTYPE" in content_preview or b"<html" in content_preview:
                            print("Received HTML content instead of image data")
                            # Try alternative specialized approach
                            return await download_image_with_selenium(url)
                        
                        traceback.print_exc()
                        return None
                else:
                    print(f"Failed to download image: HTTP {response.status}")
                    print(f"Response headers: {response.headers}")
                    
                    # Try alternative approach for certain sites
                    if any(site in url for site in ["uhdpaper.com", "wallpaper", "wallhaven"]):
                        print("Detected wallpaper site, trying alternative download approach...")
                        return await download_image_with_session(url)
                        
                    return None
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        traceback.print_exc()
        
        # Try alternative method for problematic URLs
        if "uhdpaper.com" in url or "wallpaper" in url:
            print("Trying alternative download method for wallpaper site...")
            return await download_uhdpaper_image(url)
            
        return None

async def download_image_with_session(url: str) -> Optional[bytes]:
    """
    Alternative download method for problematic URLs.
    Uses a session with different settings and browsers simulation.
    
    Args:
        url: The URL of the image to download
        
    Returns:
        Bytes containing the image data, or None if download failed
    """
    try:
        # Create a session with different settings
        timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout
        
        # Use more browser-like headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="96", " Not A;Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        
        print(f"Using alternative download method for: {url}")
        
        # Create a ClientSession that looks more like a browser
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # First make a HEAD request to check content type
            async with session.head(url, headers=headers, allow_redirects=True) as head_resp:
                print(f"HEAD response: {head_resp.status}")
                
            # Now make the actual GET request
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status == 200:
                    # Check content type
                    content_type = response.headers.get('Content-Type', '')
                    print(f"Content-Type: {content_type}")
                    
                    if 'image' in content_type or 'octet-stream' in content_type:
                        data = await response.read()
                        print(f"Alternative download successful: {len(data)} bytes")
                        
                        # Verify the downloaded data is an image
                        try:
                            img_test = Image.open(io.BytesIO(data))
                            print(f"Image format: {img_test.format}, Size: {img_test.width}x{img_test.height}")
                            return data
                        except Exception as e:
                            print(f"Downloaded data is not a valid image: {e}")
                            return None
                    else:
                        print(f"Content is not an image: {content_type}")
                        return None
                else:
                    print(f"Alternative download failed: HTTP {response.status}")
                    return None
    except Exception as e:
        print(f"Error in alternative download: {str(e)}")
        traceback.print_exc()
        return None

async def download_uhdpaper_image(url: str) -> Optional[bytes]:
    """
    Specialized method for downloading images from uhdpaper.com
    Handles their URL structure and content delivery approach.
    
    Args:
        url: The URL of the image to download
        
    Returns:
        Bytes containing the image data, or None if download failed
    """
    try:
        print(f"Using specialized uhdpaper downloader for: {url}")
        
        # Extract resolution and image ID from URL
        # Format is typically: .../wallpaper/TITLE-RESOLUTION-uhdpaper.com-ID@X@d.jpg
        # We need to convert it to their direct download format
        
        # Extract ID and resolution
        pattern = r".*-(\d+x\d+)-uhdpaper\.com-(\d+)@\d+@.*\.jpg"
        match = re.search(pattern, url)
        
        if not match:
            print("Could not parse UHD Paper URL format")
            return None
        
        resolution = match.group(1)
        image_id = match.group(2)
        
        # Construct direct download URL
        direct_url = f"https://images.uhdpaper.com/wallpaper/{image_id}@{resolution}.jpg"
        print(f"Constructed direct download URL: {direct_url}")
        
        # Use enhanced session with more browser-like headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.uhdpaper.com/',
            'sec-ch-ua': '"Chromium";v="96", " Not A;Brand";v="99"',
        }
        
        # Create a ClientSession that looks more like a browser
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(direct_url, headers=headers, allow_redirects=True) as response:
                if response.status == 200:
                    data = await response.read()
                    print(f"UHD Paper download successful: {len(data)} bytes")
                    
                    # Save to temp file first to verify it's an image
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        temp_file.write(data)
                        temp_path = temp_file.name
                    
                    try:
                        # Try to open the image to verify it's valid
                        img = Image.open(temp_path)
                        img.verify()  # Verify it's an actual image
                        print(f"Valid image downloaded: {img.format} {img.width}x{img.height}")
                        
                        # Read the verified data
                        with open(temp_path, 'rb') as f:
                            verified_data = f.read()
                        
                        # Clean up
                        os.unlink(temp_path)
                        return verified_data
                    except Exception as e:
                        print(f"Downloaded file is not a valid image: {e}")
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        return None
                else:
                    print(f"Direct download failed: HTTP {response.status}")
                    # Try scraping the image from the website instead
                    return await scrape_image_from_page(url)
    except Exception as e:
        print(f"Error in UHD Paper download: {str(e)}")
        traceback.print_exc()
        return None

async def scrape_image_from_page(url: str) -> Optional[bytes]:
    """
    Scrape image URL from page HTML and download the image.
    
    Args:
        url: The URL of the page containing the image
        
    Returns:
        Bytes containing the image data, or None if download failed
    """
    try:
        print(f"Attempting to scrape image from page: {url}")
        
        # Use a simulated browser session to get the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for image URLs in the HTML
                    # This is a simplified approach - may need adjustment for specific sites
                    img_patterns = [
                        r'<img[^>]+src="([^"]+\.(jpg|jpeg|png))"',
                        r'<meta[^>]+content="([^"]+\.(jpg|jpeg|png))"',
                        r'background-image: url\("([^"]+\.(jpg|jpeg|png))"\)',
                    ]
                    
                    all_matches = []
                    for pattern in img_patterns:
                        matches = re.findall(pattern, html)
                        if matches:
                            all_matches.extend(m[0] if isinstance(m, tuple) else m for m in matches)
                    
                    # Filter to find likely high-res images
                    candidates = [m for m in all_matches if any(term in m for term in ["large", "hd", "original", "download", "wallpaper"])]
                    
                    if not candidates and all_matches:
                        candidates = all_matches  # Use all matches if no filtered candidates
                    
                    if candidates:
                        print(f"Found {len(candidates)} image candidates, trying first one")
                        
                        # Try to download the first candidate
                        img_url = candidates[0]
                        # Handle relative URLs
                        if img_url.startswith('/'):
                            base_url = '/'.join(url.split('/')[:3])  # http(s)://domain.com
                            img_url = base_url + img_url
                            
                        print(f"Trying to download image from: {img_url}")
                        
                        # Simple download of the image
                        async with session.get(img_url, headers={'User-Agent': headers['User-Agent']}) as img_resp:
                            if img_resp.status == 200:
                                data = await img_resp.read()
                                print(f"Downloaded image data: {len(data)} bytes")
                                
                                # Verify it's an image
                                try:
                                    img_test = Image.open(io.BytesIO(data))
                                    print(f"Successfully scraped image: {img_test.format} {img_test.width}x{img_test.height}")
                                    return data
                                except Exception as e:
                                    print(f"Scraped data is not a valid image: {e}")
                
                print("Could not find valid image in page content")
                return None
    except Exception as e:
        print(f"Error scraping image: {str(e)}")
        traceback.print_exc()
        return None

# ---  Alternative download method for last resort ---
async def download_image_with_selenium(url: str) -> Optional[bytes]:
    """
    Download image using Selenium for sites that require JavaScript.
    Note: This requires selenium and appropriate webdriver to be installed.
    
    Args:
        url: The URL of the image to download
        
    Returns:
        Bytes containing the image data, or None if download failed
    """
    print("Selenium download method requested but not implemented.")
    print("To add this functionality, install selenium and appropriate webdriver.")
    
    # This is a placeholder - implementing Selenium would require additional dependencies
    # that might not be available on all systems where the bot runs.
    return None

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

def create_circular_image(image: Image.Image, size: int, bg_color=None) -> Image.Image:
    """
    Create a circular image with optional background color.
    
    Args:
        image: The PIL Image to make circular
        size: The diameter of the circular image
        bg_color: Optional background color (RGB tuple)
        
    Returns:
        A circular PIL Image
    """
    # Resize the image to fit the circle
    image = image.resize((size, size), Image.LANCZOS)
    
    # Create mask for circular crop
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    # Apply mask to create circular image
    result = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    
    # Add background if specified
    if bg_color:
        bg = Image.new('RGBA', (size, size), bg_color)
        bg.paste(result, (0, 0), result)
        result = bg
        
    return result
