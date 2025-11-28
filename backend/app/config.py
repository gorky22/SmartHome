from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_file: str = "smarthome.db"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    sensors_api_keys: str = ""  # comma separated keys

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
