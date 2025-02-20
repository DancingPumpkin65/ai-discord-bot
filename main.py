from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message, Attachment
from responses import get_response

# Load the environment variables
load_dotenv()

TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Set up the bot
intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

# Message event
async def send_message(message: Message, user_message: str = None, image_file: str = None, image_format: str = None) -> None:
    if not user_message and not image_file:
        print('User message is empty because intents were not enabled properly.')
        return
    
    if user_message and user_message[0] == '?':
        is_private = True
        user_message = user_message[1:]
    else:
        is_private = False
    
    try:
        response: str = await get_response(user_message or "", image_file, image_format)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

# Handling the startups for our bot
@client.event
async def on_ready() -> None:
    print(f'{client.user} has connected to Discord!')

# Handling incoming messages
@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: {user_message}')

    image_file = None
    image_format = None

    if message.attachments:
        attachment: Attachment = message.attachments[0]
        image_file = attachment.filename
        image_format = attachment.filename.split('.')[-1]
        await attachment.save(image_file)

    await send_message(message, user_message, image_file, image_format)

# Main entry point
def main() -> None:
    client.run(TOKEN)

if __name__ == '__main__':
    main()