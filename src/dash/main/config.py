from typing import Literal

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


class MqttConfig(BaseSettings, env_prefix="MQTT_"):
    host: str = Field(default=...)
    port: int = Field(default=...)
    username: str = Field(default=...)
    password: str = Field(default=...)
    client_id: str | None = Field(default=None)


class AppConfig(BaseSettings):
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    reload: bool = Field(default=True)
    allowed_origins: list[str] = Field(default=...)


class MonopayConfig(BaseSettings, env_prefix="MONOPAY_"):
    webhook_url: str = Field(default=...)
    redirect_url: str = Field(default=...)


class LiqpayConfig(BaseSettings, env_prefix="LIQPAY_"):
    webhook_url: str = Field(default=...)
    redirect_url: str = Field(default=...)


class JWTConfig(BaseSettings, env_prefix="JWT_"):
    access_secret: str = Field(default=...)
    access_algorithm: str = Field(default=...)
    access_expire_minutes: int = Field(default=...)
    refresh_secret: str = Field(default=...)
    refresh_algorithm: str = Field(default=...)
    refresh_expire_days: int = Field(default=...)


LoggingLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LoggingConfig(BaseSettings, env_prefix="LOG_"):
    level: LoggingLevel = Field(default=...)
    json_mode: bool = Field(default=...)
    colorize: bool = Field(default=...)


class Config(BaseSettings):
    db: DbConfig = DbConfig()
    redis: RedisConfig = RedisConfig()
    app: AppConfig = AppConfig()
    mqtt: MqttConfig = MqttConfig()
    monopay: MonopayConfig = MonopayConfig()
    liqpay: LiqpayConfig = LiqpayConfig()
    logging: LoggingConfig = LoggingConfig()
    jwt: JWTConfig = JWTConfig()
