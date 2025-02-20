import os
import base64
from random import choice
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
ai_client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("OPENAI_API_KEY"),
)

def get_image_data_url(image_file: str, image_format: str) -> str:
    """
    Helper function to convert an image file to a data URL string.

    Args:
        image_file (str): The path to the image file.
        image_format (str): The format of the image file.

    Returns:
        str: The data URL of the image.
    """
    try:
        with open(image_file, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"Could not read '{image_file}'.")
        return ""
    return f"data:image/{image_format};base64,{image_data}"

async def get_response(user_input: str, image_file: str = None, image_format: str = None) -> str:
    """
    Given user_input and optionally an image, use the AI API to generate a response.
    """
    # If the input is empty and no image is provided, return a specific message
    if not user_input.strip() and not image_file:
        return "Well you're awfully silent."
    
    try:
        if image_file and image_format:
            return await ai_image_response(user_input, image_file, image_format)
        else:
            return await ai_fallback_response(user_input)
    except Exception as e:
        print(f"Exception occurred: {e}")
        return fallback_response()

async def ai_fallback_response(user_input: str) -> str:
    """Use the AI API to generate a fallback response."""
    try:
        response = ai_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "",
                },
                {
                    "role": "user",
                    "content": user_input,
                }
            ],
            model="gpt-4o",
            temperature=1,
            max_tokens=4096,
            top_p=1
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI API exception occurred: {e}")
        return fallback_response()

async def ai_image_response(user_input: str, image_file: str, image_format: str) -> str:
    """Use the AI API to generate a response with an image input."""
    try:
        image_data_url = get_image_data_url(image_file, image_format)
        if not image_data_url:
            return "Could not read the image file."

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
                            "text": user_input,
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
            model="gpt-4o",
            temperature=1,
            max_tokens=4096,
            top_p=1
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI API exception occurred: {e}")
        return fallback_response()

def fallback_response() -> str:
    """Return one of the default fallback responses."""
    return choice([
        "I don't know what you mean by that.",
        "I don't understand.",
        "I'm sorry, I don't know what you mean."
    ])