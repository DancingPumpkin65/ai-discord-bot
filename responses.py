import os
import httpx
from random import choice
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
ai_client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("OPENAI_API_KEY"),
)

async def get_response(user_input: str) -> str:
    """
    Given user_input, use the AI API to generate a response.
    """
    # If the input is empty, return a specific message
    if not user_input.strip():
        return "Well you're awfully silent."
    
    try:
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

def fallback_response() -> str:
    """Return one of the default fallback responses."""
    return choice([
        "I don't know what you mean by that.",
        "I don't understand.",
        "I'm sorry, I don't know what you mean."
    ])