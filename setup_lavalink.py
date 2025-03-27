"""
Lavalink Setup Script

This script downloads the latest version of Lavalink.jar and sets up the directory structure.
"""
import os
import sys
import requests
import json
from pathlib import Path
import shutil
import zipfile
import platform

LAVALINK_DIR = "lavalink"
LAVALINK_RELEASES_API = "https://api.github.com/repos/lavalink-devs/Lavalink/releases/latest"

def print_step(step):
    """Print a step with formatting."""
    print(f"\n{'='*10} {step} {'='*10}")

def check_java():
    """Check if Java is installed and the version is sufficient."""
    print_step("Checking Java installation")
    
    try:
        import subprocess
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        
        # Java will output version to stderr
        output = result.stderr
        
        if "version" in output:
            print("✓ Java is installed!")
            
            # Check version
            if "1.8" in output or "11" in output or "13" in output or "17" in output or "21" in output:
                print("✓ Java version is sufficient (needs Java 11+)")
                return True
            else:
                print("✗ Java version may be too old. Lavalink requires Java 11 or newer.")
                print(f"  Detected: {output.splitlines()[0]}")
                return False
    except Exception as e:
        print(f"✗ Error checking Java: {e}")
        print("✗ Java does not appear to be installed or is not in your PATH.")
        print("  Please install Java 11 or newer from: https://adoptium.net/")
        return False

def download_lavalink():
    """Download the latest Lavalink release."""
    print_step("Downloading Lavalink")
    
    # Create lavalink directory if it doesn't exist
    os.makedirs(LAVALINK_DIR, exist_ok=True)
    
    # Get the latest release info
    try:
        response = requests.get(LAVALINK_RELEASES_API)
        response.raise_for_status()
        release_data = response.json()
        
        # Find the Lavalink.jar asset
        assets = release_data.get("assets", [])
        jar_asset = None
        
        for asset in assets:
            if asset["name"].endswith(".jar"):
                jar_asset = asset
                break
        
        if not jar_asset:
            print("✗ Could not find Lavalink.jar in the latest release.")
            return False
        
        # Download the jar file
        jar_url = jar_asset["browser_download_url"]
        jar_path = os.path.join(LAVALINK_DIR, "Lavalink.jar")
        
        print(f"Downloading from: {jar_url}")
        print(f"Saving to: {jar_path}")
        
        with requests.get(jar_url, stream=True) as r:
            r.raise_for_status()
            with open(jar_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print(f"✓ Downloaded Lavalink.jar v{release_data['tag_name']}")
        return True
        
    except Exception as e:
        print(f"✗ Error downloading Lavalink: {e}")
        return False

def setup_logs_directory():
    """Create logs directory for Lavalink."""
    logs_dir = os.path.join(LAVALINK_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    print(f"✓ Created logs directory: {logs_dir}")

def print_startup_instructions():
    """Print instructions for starting Lavalink."""
    print_step("Startup Instructions")
    
    if platform.system() == "Windows":
        print("To start Lavalink, run these commands:")
        print("cd lavalink")
        print("java -jar Lavalink.jar")
    else:
        print("To start Lavalink, run these commands:")
        print("cd lavalink")
        print("java -jar Lavalink.jar")
    
    print("\nThen in another terminal, start your bot:")
    print("python main.py")

if __name__ == "__main__":
    print("Lavalink Setup Script")
    print("This script will download and set up Lavalink for your AI Discord Bot.")
    
    # Check Java installation
    if not check_java():
        print("\nWarning: Java check failed. Continuing anyway, but Lavalink may not run.")
    
    # Download Lavalink
    if download_lavalink():
        # Set up logs directory
        setup_logs_directory()
        
        # Print startup instructions
        print_startup_instructions()
    else:
        print("\nSetup failed. Please try again or download Lavalink manually.")
        print("Manual download: https://github.com/lavalink-devs/Lavalink/releases")
