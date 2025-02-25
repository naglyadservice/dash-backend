from pydantic import Field
from pydantic_settings import BaseSettings as _BaseSettings
from pydantic_settings import SettingsConfigDict
from sqlalchemy import URL


class BaseSettings(_BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )


class DbConfig(BaseSettings, env_prefix="POSTGRES_"):
    host: str = Field(default=...)
    port: int = Field(default=...)
    user: str = Field(default=...)
    password: str = Field(default=...)
    db: str = Field(default=...)

    def build_dsn(self) -> str:
        url = URL.create(
            drivername="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.db,
        )
        return url.render_as_string(hide_password=False)


class RedisConfig(BaseSettings, env_prefix="REDIS_"):
    host: str = Field(default=...)
    port: int = Field(default=...)
    password: str = Field(default=...)


class AppConfig(BaseSettings):
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    reload: bool = Field(default=True)


class Config(BaseSettings):
    db: DbConfig = DbConfig()
    redis: RedisConfig = RedisConfig()
    app: AppConfig = AppConfig()
