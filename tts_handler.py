"""
TTS Handler - Edge-TTS Integration
Handles text-to-speech conversion using Microsoft Edge TTS
"""

import edge_tts
import asyncio
import io
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

class TTSHandler:
    """Handles TTS generation using edge-tts"""
    
    def __init__(self):
        # Spanish voice configuration
        self.voice = "es-ES-ElviraNeural"  # Male Spanish voice
        self.rate = "+0%"  # Normal speed
        self.volume = "+0%"  # Normal volume
        
        # Alternative voices for variety
        self.voices = [
            "es-ES-AlvaroNeural",  # Male
            "es-ES-ElviraNeural",  # Female
            "es-ES-ManuelNeural",  # Male
            "es-ES-TeresaNeural"   # Female
        ]
        self.current_voice_index = 0
        
        logger.info(f"TTS Handler initialized with voice: {self.voice}")
    
    def clean_text(self, text: str) -> str:
        """Clean and prepare text for TTS"""
        # Remove Discord mentions and formatting
        text = re.sub(r'<@[!&]?\d+>', '', text)  # Remove user mentions
        text = re.sub(r'<#\d+>', '', text)  # Remove channel mentions
        text = re.sub(r'<:\w+:\d+>', '', text)  # Remove custom emojis
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Remove code blocks
        text = re.sub(r'`.*?`', '', text)  # Remove inline code
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold formatting
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Remove italic formatting
        text = re.sub(r'~~(.*?)~~', r'\1', text)  # Remove strikethrough
        text = re.sub(r'__(.*?)__', r'\1', text)  # Remove underline
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Clean up extra whitespace
        text = ' '.join(text.split())
        
        # Limit length (edge-tts has limits)
        if len(text) > 500:
            text = text[:500] + "..."
        
        return text.strip()
    
    async def generate_tts(self, text: str) -> Optional[bytes]:
        """Generate TTS audio from text"""
        try:
            # Clean the text
            clean_text = self.clean_text(text)
            
            if not clean_text:
                logger.warning("No text content after cleaning")
                return None
            
            logger.info(f"Generating TTS for: {clean_text[:100]}...")
            
            # Create TTS communication
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume
            )
            
            # Generate audio data
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            if not audio_data:
                logger.error("No audio data generated")
                return None
            
            logger.info(f"TTS audio generated successfully, size: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return None
    
    def rotate_voice(self):
        """Rotate to next voice for variety"""
        self.current_voice_index = (self.current_voice_index + 1) % len(self.voices)
        self.voice = self.voices[self.current_voice_index]
        logger.info(f"Rotated to voice: {self.voice}")
    
    async def get_available_voices(self) -> list:
        """Get list of available Spanish voices"""
        try:
            voices = await edge_tts.list_voices()
            
            # Spanish language codes and their variations
            spanish_locales = [
                'es-ES',    # Spain
                'es-MX',    # Mexico
                'es-AR',    # Argentina
                'es-CO',    # Colombia
                'es-PE',    # Peru
                'es-VE',    # Venezuela
                'es-CL',    # Chile
                'es-EC',    # Ecuador
                'es-GT',    # Guatemala
                'es-CR',    # Costa Rica
                'es-PA',    # Panama
                'es-CU',    # Cuba
                'es-BO',    # Bolivia
                'es-DO',    # Dominican Republic
                'es-HN',    # Honduras
                'es-PY',    # Paraguay
                'es-SV',    # El Salvador
                'es-NI',    # Nicaragua
                'es-PR',    # Puerto Rico
                'es-UY',    # Uruguay
                'es-GQ',    # Equatorial Guinea
            ]
            
            # Filter voices by Spanish locales
            spanish_voices = []
            for voice in voices:
                if voice['Locale'] in spanish_locales:
                    spanish_voices.append(voice)
            
            # Sort by locale and then by name for better organization
            spanish_voices.sort(key=lambda x: (x['Locale'], x['ShortName']))
            
            logger.info(f"Found {len(spanish_voices)} Spanish voices")
            return spanish_voices
            
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return []
    
    def set_voice(self, voice_name: str) -> bool:
        """Set specific voice"""
        # Update the voice directly - edge-tts will validate it
        self.voice = voice_name
        logger.info(f"Voice set to: {self.voice}")
        return True
    
    def set_speech_rate(self, rate: str):
        """Set speech rate (e.g., '+20%', '-10%', '+0%')"""
        self.rate = rate
        logger.info(f"Speech rate set to: {self.rate}")
    
    def set_volume(self, volume: str):
        """Set volume (e.g., '+20%', '-10%', '+0%')"""
        self.volume = volume
        logger.info(f"Volume set to: {self.volume}")
