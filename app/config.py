from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    model_name: str = "llama-3.1-8b-instant"
    port: int = 8000
    log_level: str = "INFO"
    llm_timeout: float = 8.0  # seconds — tight, protects p95 (<=5s) and the 30s hard limit

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
