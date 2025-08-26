import os
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

# Printing all environment variables
for key, value in os.environ.items():
    print(f"{key}={value}")


class PostgresConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    db: str

    def build_dsn(self) -> str:
        # import here to avoid import sqlalchemy before datadog integration
        from sqlalchemy import URL

        url = URL.create(
            drivername="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.db,
        )
        return url.render_as_string(hide_password=False)


class RedisConfig(BaseModel):
    host: str
    port: int
    password: str | None = None


class MqttConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    client_id: str | None = Field(default=None)


class AppConfig(BaseModel):
    host: str
    port: int
    allowed_origins: list[str]
    proxy_headers: bool = False
    forwarded_allow_ips: str = "127.0.0.1"
    enable_datadog: bool
    enable_debugpy: bool
    timezone: ZoneInfo

    @field_validator("timezone", mode="before")
    @classmethod
    def zone_info_validator(cls, v: str) -> ZoneInfo:
        return ZoneInfo(v)


class MonopayConfig(BaseModel):
    webhook_url: str
    redirect_url: str


class LiqpayConfig(BaseModel):
    webhook_url: str
    redirect_url: str


class JWTConfig(BaseModel):
    access_secret: str
    access_algorithm: str
    access_expire_minutes: int
    refresh_secret: str
    refresh_algorithm: str
    refresh_expire_days: int


LoggingLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LoggingConfig(BaseModel):
    level: LoggingLevel
    json_mode: bool
    colorize: bool


class SMSConfig(BaseModel):
    api_key: str


class S3Config(BaseModel):
    bucket_name: str


class Config(BaseSettings):
    # Mock init to avoid lint error when creating config from env
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    postgres: PostgresConfig
    redis: RedisConfig
    app: AppConfig
    mqtt: MqttConfig
    monopay: MonopayConfig
    liqpay: LiqpayConfig
    logging: LoggingConfig
    jwt: JWTConfig
    sms: SMSConfig
    s3: S3Config

    model_config = {
        "arbitrary_types_allowed": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "env_nested_delimiter": "__",
    }
