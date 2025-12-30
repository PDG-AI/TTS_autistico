"""
Configuration settings for the Discord TTS Bot
"""

import os
from typing import List

class BotConfig:
    """Bot configuration class"""
    
    # Discord Bot Settings
    COMMAND_PREFIX = "T"
    
    # Target users for TTS (display names)
    TARGET_USERS: List[str] = [
        "Clara <3",
        "PDGadm",
        "azacgamer"
    ]
    
    # TTS Settings
    DEFAULT_VOICE: str = os.getenv('TTS_VOICE', 'es-ES-XimenaNeural')
    DEFAULT_RATE: str = os.getenv('TTS_RATE', '+0%')
    DEFAULT_VOLUME: str = os.getenv('TTS_VOLUME', '+0%')
    
    # Audio Settings
    MAX_MESSAGE_LENGTH: int = int(os.getenv('MAX_MESSAGE_LENGTH', '500'))
    AUDIO_TIMEOUT: int = int(os.getenv('AUDIO_TIMEOUT', '300'))  # 5 minutes
    
    # Voice Channel Settings
    AUTO_JOIN: bool = os.getenv('AUTO_JOIN', 'true').lower() == 'true'
    AUTO_LEAVE_TIMEOUT: int = int(os.getenv('AUTO_LEAVE_TIMEOUT', '600'))  # 10 minutes
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'bot.log')
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        if not cls.TARGET_USERS:
            raise ValueError("No target users configured")
        
        if cls.MAX_MESSAGE_LENGTH <= 0:
            raise ValueError("Invalid max message length")
        
        if cls.AUDIO_TIMEOUT <= 0:
            raise ValueError("Invalid audio timeout")
        
        return True
    
    @classmethod
    def get_target_users(cls) -> List[str]:
        """Get list of target users"""
        # Allow environment variable override
        env_users = os.getenv('TARGET_USERS')
        if env_users:
            return [user.strip() for user in env_users.split(',')]
        return cls.TARGET_USERS
    
    @classmethod
    def add_target_user(cls, username: str):
        """Add a new target user"""
        if username not in cls.TARGET_USERS:
            cls.TARGET_USERS.append(username)
    
    @classmethod
    def remove_target_user(cls, username: str):
        """Remove a target user"""
        if username in cls.TARGET_USERS:
            cls.TARGET_USERS.remove(username)
    
    @classmethod
    def print_config(cls):
        """Print current configuration (for debugging)"""
        print("=== Discord TTS Bot Configuration ===")
        print(f"Command Prefix: {cls.COMMAND_PREFIX}")
        print(f"Target Users: {', '.join(cls.TARGET_USERS)}")
        print(f"Default Voice: {cls.DEFAULT_VOICE}")
        print(f"Default Rate: {cls.DEFAULT_RATE}")
        print(f"Default Volume: {cls.DEFAULT_VOLUME}")
        print(f"Max Message Length: {cls.MAX_MESSAGE_LENGTH}")
        print(f"Audio Timeout: {cls.AUDIO_TIMEOUT}")
        print(f"Auto Join: {cls.AUTO_JOIN}")
        print(f"Auto Leave Timeout: {cls.AUTO_LEAVE_TIMEOUT}")
        print("=====================================")

# Validate configuration on import
BotConfig.validate_config()
