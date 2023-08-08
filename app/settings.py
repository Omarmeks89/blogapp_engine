from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    app_run_path: str
    reloading: bool
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            )


class TestDBSettings(BaseSettings):
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            )
    TEST_DIALECT: str = ""
    TEST_DB_DRIVER: str = ""
    TEST_LOGIN: str = ""
    TEST_PASSWD: str = ""
    TEST_HOST: str = ""
    TEST_PORT: int = 5432
    TEST_DB_NAME: str = ""
    TEST_ECHO_POOL: str = ""
    TEST_POOL_PREPING: bool = True
    TEST_POOL_SZ: int = 8
    TEST_POOL_OWF: int = 8
    TEST_POOL_RECL: int = 3600
    TEST_AUTOCM: bool = False
    TEST_AUTOFL: bool = False
    TEST_DB_URL: str = ""

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
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            )
    SMTP_PASWD: str = "oaexmxckmxvxrlyb"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_LOGIN: str = "r5railmodels@gmail.com"
