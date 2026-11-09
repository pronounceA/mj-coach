from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://redis:6379/0"

    llm_provider: str = "ollama"
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"

    class Config:
        env_file = ".env"


settings = Settings()
