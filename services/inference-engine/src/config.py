# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    """
    Defines and validates application settings loaded from environment variables.
    """
    model_name: str = "default_model.gguf"
    
    # This tells Pydantic to load variables from a .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Create a single, importable instance of the settings
settings = AppSettings()