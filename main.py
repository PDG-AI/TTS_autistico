"""
Discord TTS Bot - Main Entry Point
Spanish Text-to-Speech bot for Discord using edge-tts
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from bot import DiscordTTSBot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the Discord bot"""
    # Get bot token from environment variables
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        logger.error("Please create a .env file with your bot token")
        return
    
    # Create and start the bot
    bot = DiscordTTSBot()
    
    try:
        logger.info("Starting Discord TTS Bot...")
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
