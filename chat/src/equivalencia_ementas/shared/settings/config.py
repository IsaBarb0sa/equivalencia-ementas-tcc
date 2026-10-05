from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_server: str
    db_name: str
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_trusted_connection: str = "yes"
    db_trust_server_certificate: str = "yes"
    db_echo: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
