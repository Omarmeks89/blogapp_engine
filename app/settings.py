from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    app_run_path: str
    reloading: bool
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            )
