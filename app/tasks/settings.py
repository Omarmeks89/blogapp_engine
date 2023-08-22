from pydantic_settings import BaseSettings, SettingsConfigDict


class SMTPSettings(BaseSettings):
    """for smtp server."""
    SMTP_PASSWD: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_LOGIN: str = ""
    model_config = SettingsConfigDict(
            env_file="../.env",
            env_file_encoding="utf-8",
            extra="ignore",  # compability with 1.x
            )


class ModerationAPISettings(BaseSettings):
    """api key for moderation servise."""
    api_user: str = ""
    api_secret: str = ""
    border_coeff: float = 0.3
    model_config = SettingsConfigDict(
            env_file="../.env",
            env_file_encoding="utf-8",
            extra="ignore",  # compability with 1.x
            )
