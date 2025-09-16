from pydantic_settings import BaseSettings
from typing import Optional, List
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./db/team_activity.db")

    # JIRA Configuration
    jira_server_url: Optional[str] = os.getenv("JIRA_SERVER_URL")
    jira_email: Optional[str] = os.getenv("JIRA_EMAIL")
    jira_api_token: Optional[str] = os.getenv("JIRA_API_TOKEN")
    
    # Legacy support for username (will be deprecated)
    jira_username: Optional[str] = None
    
    # GitHub Configuration
    github_token: Optional[str] = os.getenv("GITHUB_TOKEN")
    github_organization: Optional[str] = os.getenv("GITHUB_ORGANIZATION")
    github_repo_names: Optional[str] = os.getenv("GITHUB_REPO_NAMES")
    
    # OpenAI Configuration (for chatbot responses)
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Google Gemini Configuration
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
