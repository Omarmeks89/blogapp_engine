from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    app_run_path: str = ""
    app_api_v: str = ""
    reloading: bool = True
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",  # compability with 1.x
            )


class TestDBSettings(BaseSettings):
    TEST_DIALECT: str = ""
    TEST_DB_DRIVER: str = ""
    TEST_LOGIN: str = ""
    TEST_PASSWD: str = ""
    TEST_HOST: str = ""
    TEST_PORT: int = 5432
    TEST_DB_NAME: str = "postgres"
    TEST_ECHO_POOL: str = ""
    TEST_POOL_PREPING: str = ""
    TEST_POOL_SZ: int = 10
    TEST_POOL_OWF: int = 6
    TEST_POOL_RECL: int = 3600
    TEST_AUTOCM: bool = False
    TEST_AUTOFL: bool = False
    TEST_DB_URL: str = "{}+{}://{}:{}@{}:{}/{}"
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",  # compability with 1.x
            )

    def get_db_url(self) -> str:
        return self.TEST_DB_URL.format(
                self.TEST_DIALECT,
                self.TEST_DB_DRIVER,
                self.TEST_LOGIN,
                self.TEST_PASSWD,
                self.TEST_HOST,
                self.TEST_PORT,
                self.TEST_DB_NAME,
                )


class SMTPSettings(BaseSettings):
    SMTP_PASSWD: str = "oaexmxckmxvxrlyb"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_LOGIN: str = "r5railmodels@gmail.com"
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",  # compability with 1.x
            )


class CacheSettings(BaseSettings):
    """base preset for redis caching."""
    CHOST: str = ""
    CPORT: int = 6381
    DEFDBNO: int = 0
    RESP_DEC: bool = False
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",  # compability with 1.x
            )
