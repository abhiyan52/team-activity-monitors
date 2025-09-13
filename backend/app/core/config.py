from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./team_activity.db"
    
    # JIRA Configuration
    jira_server_url: Optional[str] = None
    jira_username: Optional[str] = None
    jira_api_token: Optional[str] = None
    
    # GitHub Configuration
    github_token: Optional[str] = None
    github_organization: Optional[str] = None
    
    # OpenAI Configuration (for chatbot responses)
    openai_api_key: Optional[str] = None
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
