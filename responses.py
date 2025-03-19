"""
AI Discord Bot - Response Module

This module handles the interaction with the AI model to generate responses.
It includes functions to process text and image inputs and generate responses.
"""
import os
import base64
import traceback
from typing import Optional
from random import choice
from openai import OpenAI
from dotenv import load_dotenv

# --- Initialization ---

load_dotenv()

# Configure endpoint and API key
endpoint = os.getenv("AZURE_ENDPOINT", "https://models.inference.ai.azure.com")
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("MODEL_NAME", "gpt-4o")

# Initialize OpenAI client
ai_client = OpenAI(
    base_url=endpoint,
    api_key=api_key,
)

# --- Helper Functions ---

def get_image_data_url(image_file: str, image_format: str) -> str:
    """
    Convert an image file to a data URL string.

    Args:
        image_file (str): The path to the image file.
        image_format (str): The format of the image file.

    Returns:
        str: The data URL of the image or empty string if file not found.
    """
    try:
        with open(image_file, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/{image_format};base64,{image_data}"
    except FileNotFoundError:
        print(f"Could not read '{image_file}'.")
        return ""

# --- Core Response Functions ---

async def get_response(user_input: str, image_file: str = None, image_format: str = None) -> str:
    """
    Generate a response using the AI API based on user input and optional image.

    Args:
        user_input (str): The text input from the user.
        image_file (str, optional): Path to an image file.
        image_format (str, optional): Format of the image file.

    Returns:
        str: The AI-generated response or a fallback message.
    """
    # Return a default message if input is empty and no image is provided
    if not user_input.strip() and not image_file:
        return "Well you're awfully silent."
    
    try:
        # Generate response based on input type
        if image_file and image_format:
            image_data_url = get_image_data_url(image_file, image_format)
            if not image_data_url:
                return "Could not read the image file."
                
            # Process with image
            print(f"Generating AI response for image and text: {user_input[:30] if user_input else ''}...")
            response = ai_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that describes images in detail.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_input or "What's in this image?",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url,
                                    "detail": "low"
                                },
                            },
                        ],
                    },
                ],
                model=model_name,
                temperature=1,
                max_tokens=4096,
                top_p=1
            )
        else:
            # Process text only
            print(f"Generating AI response for text input: {user_input[:30]}...")
            response = ai_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant.",
                    },
                    {
                        "role": "user",
                        "content": user_input,
                    }
                ],
                model=model_name,
                temperature=1,
                max_tokens=4096,
                top_p=1
            )
        
        # Extract content from response
        if hasattr(response, 'choices') and response.choices:
            if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                return response.choices[0].message.content
                
        # Handle unexpected response format
        print("Received unexpected response format from API")
        return "I couldn't generate a proper response. Please try again."
        
    except Exception as e:
        # Log the full error for debugging
        print(f"AI API exception occurred: {e}")
        traceback.print_exc()
        
        # Return a fallback response
        return choice([
            "I don't know what you mean by that.",
            "I don't understand.",
            "I'm sorry, I don't know what you mean."
        ])