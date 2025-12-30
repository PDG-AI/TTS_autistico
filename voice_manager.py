"""
Voice Manager - Discord Voice Channel Management
Handles voice channel connections and audio playback
"""

import discord
import asyncio
import io
import logging
from typing import Optional, Dict
import tempfile
import os

logger = logging.getLogger(__name__)

class VoiceManager:
    """Manages Discord voice connections and audio playback"""
    
    def __init__(self, bot):
        self.bot = bot
        self.audio_queue: Dict[int, asyncio.Queue] = {}  # Guild ID -> Queue
        self.playing: Dict[int, bool] = {}  # Guild ID -> Playing status
        
    async def join_channel(self, channel: discord.VoiceChannel) -> Optional[discord.VoiceClient]:
        """Join a voice channel (robust, safe, no index errors)"""
        try:
            guild = channel.guild
            voice_client = guild.voice_client  # ← EL MÉTODO CORRECTO

            # Caso 1: Ya conectado al mismo canal
            if voice_client and voice_client.is_connected():
                if voice_client.channel.id == channel.id:
                    logger.info(f"Already connected to {channel.name}")
                    return voice_client

                # Caso 2: Conectado a otro canal → mover
                await voice_client.move_to(channel)
                logger.info(f"Moved to {channel.name}")
                return voice_client

            # Caso 3: No está conectado → conectar limpio
            voice_client = await channel.connect()
            logger.info(f"Connected to voice channel: {channel.name}")

            # Inicializar cola
            if guild.id not in self.audio_queue:
                self.audio_queue[guild.id] = asyncio.Queue()
                self.playing[guild.id] = False

            # Iniciar procesador de audio si no estaba activo
            if guild.id not in self.playing or not self.playing[guild.id]:
                asyncio.create_task(self._process_audio_queue(guild.id))

            return voice_client

        except Exception as e:
            logger.error(f"Error joining voice channel: {e}")
            return None
    
    async def leave_channel(self, guild: discord.Guild):
        """Leave voice channel in a guild"""
        try:
            voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
            
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
                logger.info(f"Disconnected from voice channel in {guild.name}")
                
                # Clean up queue
                if guild.id in self.audio_queue:
                    # Clear the queue
                    while not self.audio_queue[guild.id].empty():
                        try:
                            self.audio_queue[guild.id].get_nowait()
                        except asyncio.QueueEmpty:
                            break
                    
                    del self.audio_queue[guild.id]
                    del self.playing[guild.id]
                
                # Clean up text channel association
                if hasattr(self.bot, 'voice_text_channels') and guild.id in self.bot.voice_text_channels:
                    del self.bot.voice_text_channels[guild.id]
            
        except Exception as e:
            logger.error(f"Error leaving voice channel: {e}")
            raise e
    
    async def play_audio(self, channel, audio_data, username):
        """Add audio to queue for playback"""
        try:
            guild = channel.guild
            
            # Asegurar que el bot esté conectado al canal
            voice_client = guild.voice_client
            if not voice_client or not voice_client.is_connected():
                logger.warning(f"Bot not connected to voice channel, attempting to connect...")
                voice_client = await channel.connect()
            
            # Si está conectado a otro canal, moverlo
            if voice_client.channel.id != channel.id:
                await voice_client.move_to(channel)
            
            # Inicializar cola si no existe
            if guild.id not in self.audio_queue:
                self.audio_queue[guild.id] = asyncio.Queue()
                self.playing[guild.id] = False
                # Iniciar procesador de audio
                asyncio.create_task(self._process_audio_queue(guild.id))
                logger.info(f"Initialized audio queue for guild {guild.id}")
            
            # Agregar audio a la cola
            audio_item = {
                'data': audio_data,
                'source': username
            }
            await self.audio_queue[guild.id].put(audio_item)
            logger.info(f"Added audio to queue for {username} (queue size: {self.audio_queue[guild.id].qsize()})")
            return True

        except Exception as e:
            logger.error(f"Error adding audio to queue: {e}")
            return False

    async def _play(self, audio_data, voice_client):
        """Play audio data from bytes"""
        try:
            # Create temporary file for audio (edge-tts generates MP3)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Check if the file has valid content
                file_size = os.path.getsize(temp_file_path)
                logger.info(f"Audio file created: {temp_file_path}, size: {file_size} bytes")
                
                if file_size == 0:
                    logger.error("Audio file is empty")
                    return False
                
                # Create FFmpeg audio source 
                audio_source = discord.FFmpegPCMAudio(
                    temp_file_path,
                    before_options='-nostdin',
                    options='-vn -filter:a "volume=0.8"'
                )
                
                # Play audio with error callback
                def after_playing(error):
                    if error:
                        logger.error(f"Player error: {error}")
                    else:
                        logger.info("Successfully played audio")
                
                voice_client.play(audio_source, after=after_playing)
                
                # Wait for playback to finish with timeout
                max_wait = 30  # Maximum 30 seconds
                wait_time = 0
                while voice_client.is_playing() and wait_time < max_wait:
                    await asyncio.sleep(0.1)
                    wait_time += 0.1
                
                if wait_time >= max_wait:
                    logger.warning("Audio playback timed out")
                    voice_client.stop()
                
                logger.info("Finished playing TTS audio")
                return True
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
                    
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
    
    
    async def _process_audio_queue(self, guild_id: int):
        """Process audio queue for a guild"""
        logger.info(f"Started audio queue processor for guild {guild_id}")
        
        while guild_id in self.audio_queue:
            try:
                # Wait for audio item (with reasonable timeout)
                try:
                    audio_item = await asyncio.wait_for(
                        self.audio_queue[guild_id].get(),
                        timeout=300  # 5 minutes timeout
                    )
                except asyncio.TimeoutError:
                    logger.info(f"Audio queue timeout for guild {guild_id} - no items for 5 minutes")
                    # Check if we should continue or stop
                    if guild_id in self.audio_queue and self.audio_queue[guild_id].empty():
                        # Wait a bit more before stopping
                        await asyncio.sleep(10)
                        if guild_id in self.audio_queue and self.audio_queue[guild_id].empty():
                            logger.info(f"Stopping audio queue processor for guild {guild_id} - queue empty")
                            break
                    continue
                
                # Get voice client
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    logger.warning(f"Guild {guild_id} not found")
                    continue
                
                voice_client = guild.voice_client
                if not voice_client or not voice_client.is_connected():
                    logger.warning(f"Voice client not connected for guild {guild_id}")
                    # Put item back in queue
                    await self.audio_queue[guild_id].put(audio_item)
                    await asyncio.sleep(2)
                    continue
                
                # Wait if already playing (shouldn't happen often, but just in case)
                while voice_client.is_playing():
                    logger.debug("Voice client is playing, waiting...")
                    await asyncio.sleep(0.5)
                
                # Play the audio (this will wait until it finishes)
                await self._play_audio_data(voice_client, audio_item)
                
            except Exception as e:
                logger.error(f"Error processing audio queue: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        logger.info(f"Audio queue processor stopped for guild {guild_id}")
    
    async def _play_audio_data(self, voice_client: discord.VoiceClient, audio_item: dict):
        """Play audio data through voice client"""
        try:
            source_name = audio_item['source']
            audio_data = audio_item['data']
            
            logger.info(f"Playing TTS audio for {source_name}")
            
            # Create temporary file for audio (edge-tts generates MP3)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Check if the file has valid content
                file_size = os.path.getsize(temp_file_path)
                logger.info(f"Audio file created: {temp_file_path}, size: {file_size} bytes")
                
                if file_size == 0:
                    logger.error("Audio file is empty")
                    return
                
                # Create FFmpeg audio source 
                audio_source = discord.FFmpegPCMAudio(
                    temp_file_path,
                    before_options='-nostdin',
                    options='-vn -filter:a "volume=0.8"'
                )
                
                # Use an event to wait for playback to finish
                playback_done = asyncio.Event()
                
                # Play audio with error callback
                def after_playing(error):
                    if error:
                        logger.error(f"Player error: {error}")
                    else:
                        logger.info(f"Successfully played audio for {source_name}")
                    # Signal that playback is done
                    playback_done.set()
                
                voice_client.play(audio_source, after=after_playing)
                
                # Wait for playback to finish with timeout
                try:
                    await asyncio.wait_for(playback_done.wait(), timeout=60)  # 60 seconds max
                except asyncio.TimeoutError:
                    logger.warning("Audio playback timed out")
                    voice_client.stop()
                    playback_done.set()  # Set anyway to continue
                
                logger.info(f"Finished playing TTS audio for {source_name}")
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
                
        except Exception as e:
            logger.error(f"Error playing audio data: {e}")
    
    async def stop_audio(self, guild: discord.Guild):
        """Stop current audio playback"""
        try:
            voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
            
            if voice_client and voice_client.is_playing():
                voice_client.stop()
                logger.info("Stopped audio playback")
                
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
    
    def get_queue_size(self, guild_id: int) -> int:
        """Get current queue size for a guild"""
        if guild_id in self.audio_queue:
            return self.audio_queue[guild_id].qsize()
        return 0
    
    def is_playing(self, guild: discord.Guild) -> bool:
        """Check if audio is currently playing"""
        voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
        return voice_client and voice_client.is_playing()
