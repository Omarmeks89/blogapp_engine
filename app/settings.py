from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    app_run_path: str
    reloading: bool
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            )


class TestDBSetings(BaseSettings):
    TEST_DIALECT: str
    TEST_DB_DRIVER: str
    TEST_LOGIN: str
    TEST_PASSWD: str
    TEST_HOST: str
    TEST_POST: int
    TEST_DB_NAME: str
    TEST_ECHO_POOL: str
    TEST_POOL_PREPING: bool
    TEST_POOL_SZ: int
    TEST_POOL_OWF: int
    TEST_POOL_RECL: int
    TEST_AUTOCM: bool
    TEST_AUTOFL: bool
    TEST_DB_URL: str
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
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
    SMTP_PASWD: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_LOGIN: str
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            )
