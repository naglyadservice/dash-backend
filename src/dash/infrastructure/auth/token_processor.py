from datetime import UTC, datetime, timedelta

from jose import ExpiredSignatureError, JWTError, jwt

from dash.infrastructure.auth.errors import JWTTokenError
from dash.main.config import JWTConfig


class JWTTokenProcessor:
    def __init__(self, config: JWTConfig) -> None:
        self.config = config

    def _create_token(
        self,
        sub: str,
        expire_delta: timedelta,
        algorithm: str,
        secret: str,
    ) -> str:
        to_encode = {
            "sub": sub,
            "exp": datetime.now(UTC) + expire_delta,
        }
        return jwt.encode(claims=to_encode, key=secret, algorithm=algorithm)

    def _decode_token(
        self,
        token: str,
        secret: str,
        algorithm: str,
    ) -> int:
        try:
            payload = jwt.decode(token=token, key=secret, algorithms=[algorithm])
        except ExpiredSignatureError:
            raise JWTTokenError("Token has expired")
        except JWTError:
            raise JWTTokenError("Invalid token")
        try:
            return int(payload["sub"])
        except (ValueError, KeyError):
            raise JWTTokenError("Invalid token")

    def create_access_token(self, user_id: int) -> str:
        return self._create_token(
            sub=str(user_id),
            expire_delta=timedelta(minutes=self.config.access_expire_minutes),
            algorithm=self.config.access_algorithm,
            secret=self.config.access_secret,
        )

    def create_refresh_token(self, user_id: int) -> str:
        return self._create_token(
            sub=str(user_id),
            expire_delta=timedelta(days=self.config.refresh_expire_days),
            algorithm=self.config.refresh_algorithm,
            secret=self.config.refresh_secret,
        )

    def validate_access_token(self, token: str) -> int:
        return self._decode_token(
            token=token,
            secret=self.config.access_secret,
            algorithm=self.config.access_algorithm,
        )

    def validate_refresh_token(self, token: str) -> int:
        return self._decode_token(
            token=token,
            secret=self.config.refresh_secret,
            algorithm=self.config.refresh_algorithm,
        )
