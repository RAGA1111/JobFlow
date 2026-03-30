"""Configuration settings for WhatsApp Job Agent."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Groq API
    GROQ_API_KEY: str
    
    # Twilio credentials
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/jobs.db"
    
    # Application settings
    MAX_APPLICATIONS_PER_SESSION: int = 10
    MIN_FIT_SCORE_THRESHOLD: int = 70
    DEFAULT_RESUME_PATH: Path = DATA_DIR / "resume.pdf"
    
    # Scraping settings
    SCRAPER_DELAY_MIN: int = 2
    SCRAPER_DELAY_MAX: int = 4
    SCRAPER_PAGES_PER_BOARD: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Initialize settings
settings = Settings()

# Groq model configurations
GROQ_MODELS = {
    "profile_parsing": "llama-3.1-8b-instant",
    "job_scoring": "llama-3.1-8b-instant",
    "cover_letter": "llama-3.3-70b-versatile",
    "intent_parsing": "llama-3.1-8b-instant",
    "agent_orchestration": "llama-3.1-8b-instant",
}

# Job board URLs
JOB_BOARDS = {
    "naukri": "https://www.naukri.com",
    "indeed": "https://in.indeed.com",
}
