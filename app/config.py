"""
Configuration management using environment variables
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""
    
    # API Authentication
    API_KEY: str = os.getenv("API_KEY", "your-secret-api-key-here")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_SESSION_TTL: int = int(os.getenv("REDIS_SESSION_TTL", "86400"))  # 24 hours
    
    # GUVI Callback Configuration
    GUVI_CALLBACK_URL: str = os.getenv(
        "GUVI_CALLBACK_URL",
        "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    )
    CALLBACK_TIMEOUT: int = int(os.getenv("CALLBACK_TIMEOUT", "30"))
    CALLBACK_MAX_RETRIES: int = int(os.getenv("CALLBACK_MAX_RETRIES", "3"))
    
    # Agent Behavior Configuration
    MIN_MESSAGES_FOR_CALLBACK: int = int(os.getenv("MIN_MESSAGES_FOR_CALLBACK", "1"))
    MIN_INTELLIGENCE_ITEMS: int = int(os.getenv("MIN_INTELLIGENCE_ITEMS", "1"))
    
    # Scam Detection Configuration
    SCAM_DETECTION_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("SCAM_DETECTION_CONFIDENCE_THRESHOLD", "0.7")
    )
    
    # Application Settings
    APP_NAME: str = "Agentic Honey-Pot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        errors = []
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        if not cls.API_KEY or cls.API_KEY == "your-secret-api-key-here":
            errors.append("API_KEY must be set to a secure value")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    @classmethod
    def get_redis_config(cls) -> dict:
        """Get Redis connection configuration"""
        return {
            "url": cls.REDIS_URL,
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        }


# Create global config instance
config = Config()
