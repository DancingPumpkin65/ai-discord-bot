"""
AI Discord Bot - AI Services Module

This module handles the interaction with the AI model to generate responses.
It includes functions to process text and image inputs and generate responses.
"""
import os
import base64
import traceback
from typing import Optional, AsyncGenerator, Tuple, List, Dict
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

# --- Multi-turn Conversation Types ---

# Define a type for message in a conversation
Message = Dict[str, str]  # {"role": "...", "content": "..."}

# --- Core Response Functions ---

async def get_response_with_history(
    user_input: str, 
    conversation_history: List[Message] = None, 
    image_file: str = None, 
    image_format: str = None
) -> Tuple[str, List[Message]]:
    """
    Generate a response using the AI API based on user input, conversation history, and optional image.

    Args:
        user_input: The text input from the user.
        conversation_history: Optional list of previous messages in the conversation.
        image_file: Optional path to an image file.
        image_format: Optional format of the image file.

    Returns:
        A tuple containing (response_text, updated_conversation_history)
    """
    # Return a default message if input is empty and no image is provided
    if not user_input.strip() and not image_file:
        return "Well you're awfully silent.", conversation_history or []
    
    try:
        # Start with system message
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        if image_file and image_format:
            image_data_url = get_image_data_url(image_file, image_format)
            if not image_data_url:
                return "Could not read the image file.", conversation_history or []
                
            # Process with image
            print(f"Generating AI response for image and text with history: {user_input[:30] if user_input else ''}...")
            
            # Add user message with image
            messages.append({
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
                ]
            })
            
            # Create a text-only version of the message for history
            user_message = {"role": "user", "content": user_input or "What's in this image? [Image attached]"}
        else:
            # Process text only
            print(f"Generating AI response for text input with history: {user_input[:30]}...")
            user_message = {"role": "user", "content": user_input}
            messages.append(user_message)
        
        # Call the API
        response = ai_client.chat.completions.create(
            messages=messages,
            model=model_name,
            temperature=1,
            max_tokens=4096,
            top_p=1
        )
        
        # Extract content from response
        if hasattr(response, 'choices') and response.choices:
            if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                response_text = response.choices[0].message.content
                
                # Create assistant message for history
                assistant_message = {"role": "assistant", "content": response_text}
                
                # Update conversation history
                new_history = (conversation_history or []).copy()
                new_history.append(user_message)
                new_history.append(assistant_message)
                
                # Return response and updated history
                return response_text, new_history
                
        # Handle unexpected response format
        print("Received unexpected response format from API")
        return "I couldn't generate a proper response. Please try again.", conversation_history or []
        
    except Exception as e:
        # Log the full error for debugging
        print(f"AI API exception occurred: {e}")
        traceback.print_exc()
        
        # Return a fallback response and unchanged history
        fallback = choice([
            "I don't know what you mean by that.",
            "I don't understand.",
            "I'm sorry, I don't know what you mean."
        ])
        return fallback, conversation_history or []

async def stream_response_with_history(
    user_input: str, 
    conversation_history: List[Message] = None, 
    image_file: str = None, 
    image_format: str = None
) -> AsyncGenerator[Tuple[str, List[Message]], None]:
    """
    Stream AI response with conversation history.

    Args:
        user_input: The text input from the user.
        conversation_history: Optional list of previous messages in the conversation.
        image_file: Optional path to an image file.
        image_format: Optional format of the image file.

    Yields:
        Tuples containing (response_chunk, updated_conversation_history)
    """
    # Return a default message if input is empty and no image is provided
    if not user_input.strip() and not image_file:
        yield "Well you're awfully silent.", conversation_history or []
        return

    try:
        # Start with system message
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        if image_file and image_format:
            image_data_url = get_image_data_url(image_file, image_format)
            if not image_data_url:
                yield "Could not read the image file.", conversation_history or []
                return
                
            # Process with image
            print(f"Streaming AI response for image and text with history: {user_input[:30] if user_input else ''}...")
            
            # Add user message with image
            messages.append({
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
                ]
            })
            
            # Create a text-only version of the message for history
            user_message = {"role": "user", "content": user_input or "What's in this image? [Image attached]"}
        else:
            # Process text only
            print(f"Streaming AI response for text input with history: {user_input[:30]}...")
            user_message = {"role": "user", "content": user_input}
            messages.append(user_message)
        
        # Call the API with streaming enabled
        response_stream = ai_client.chat.completions.create(
            messages=messages,
            model=model_name,
            temperature=1,
            max_tokens=4096,
            top_p=1,
            stream=True
        )
        
        # Process the streaming response
        full_response = ""
        for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                
                # Create partial assistant message for history
                assistant_message = {"role": "assistant", "content": full_response}
                
                # Update conversation history
                new_history = (conversation_history or []).copy()
                new_history.append(user_message)
                new_history.append(assistant_message)
                
                yield content, new_history
                
        # If no content was received, yield an error message
        if not full_response:
            fallback = "I couldn't generate a proper response. Please try again."
            yield fallback, conversation_history or []
                
    except Exception as e:
        # Log the full error for debugging
        print(f"AI API streaming exception occurred: {e}")
        traceback.print_exc()
        
        # Return a fallback response and unchanged history
        fallback = choice([
            "I don't know what you mean by that.",
            "I don't understand.",
            "I'm sorry, I don't know what you mean."
        ])
        yield fallback, conversation_history or []

# Keep original functions for backward compatibility
async def get_response(user_input: str, image_file: str = None, image_format: str = None) -> str:
    """
    Generate a complete non-streaming response using the AI API (without history).
    
    Args:
        user_input (str): The text input from the user.
        image_file (str, optional): Path to an image file.
        image_format (str, optional): Format of the image file.

    Returns:
        str: The AI-generated response or a fallback message.
    """
    response_text, _ = await get_response_with_history(user_input, None, image_file, image_format)
    return response_text

async def stream_response(user_input: str, image_file: str = None, image_format: str = None) -> AsyncGenerator[str, None]:
    """
    Stream AI response using the OpenAI API with streaming enabled (without history).

    Args:
        user_input (str): The text input from the user.
        image_file (str, optional): Path to an image file.
        image_format (str, optional): Format of the image file.

    Yields:
        Chunks of the AI-generated response as they become available.
    """
    async for content, _ in stream_response_with_history(user_input, None, image_file, image_format):
        yield content
