import asyncio
import time
from typing import Literal

from redis.asyncio import Redis
from redis.exceptions import ResponseError
from structlog import get_logger


logger = get_logger()


class TooManyRequestsError(Exception):
    def __init__(self, retry_after_secs: int) -> None:
        self.retry_after_secs = retry_after_secs


class RateLimiter:
    _LUA_TOKEN_BUCKET = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local rate = tonumber(ARGV[2])
    local capacity = tonumber(ARGV[3])

    local bucket = redis.call('HMGET', key, 'tokens', 'ts')
    local tokens = tonumber(bucket[1])
    local ts = tonumber(bucket[2])

    if tokens == nil then
      tokens = capacity
      ts = now
    end

    local delta = now - ts
    if delta > 0 then
      local refill = (delta / 1000.0) * rate
      tokens = math.min(capacity, tokens + refill)
      ts = now
    end

    local allowed = 0
    local retry_after = 0.0
    if tokens >= 1.0 then
      tokens = tokens - 1.0
      allowed = 1
    else
      local missing = 1.0 - tokens
      retry_after = missing / rate
    end

    redis.call('HMSET', key, 'tokens', tokens, 'ts', ts)
    redis.call('EXPIRE', key, 60)

    return {allowed, retry_after, tokens, capacity}
    """

    ACTION_LIMITS = {
        "tg_send": {"rate": 25.0, "capacity": 25},
    }

    def __init__(self, redis: Redis):
        self._redis = redis
        self._script_sha: str | None = None

    async def _load_script(self) -> None:
        if self._script_sha is None:
            try:
                self._script_sha = await self._redis.script_load(self._LUA_TOKEN_BUCKET)
            except Exception as e:
                logger.error("rate_limiter.lua_script_load_failed", error=e)
                self._script_sha = None

    async def _eval_token_bucket(
        self,
        action: str,
        identifier: str,
    ) -> tuple[int, float, float, int]:
        cfg = self.ACTION_LIMITS[action]
        key = f"rl:{identifier}:{action}"
        now_ms = int(time.time() * 1000)

        if self._script_sha is None:
            await self._load_script()
            if self._script_sha is None:
                logger.warning("rate_limiter.fail_open.no_script")
                return 1, 0.0, cfg["capacity"], cfg["capacity"]

        try:
            res = await self._redis.evalsha(
                self._script_sha,
                1,
                key,
                str(now_ms),
                str(cfg["rate"]),
                str(cfg["capacity"]),
            )  # type: ignore
            return int(res[0]), float(res[1]), float(res[2]), int(res[3])

        except ResponseError as e:
            if "NOSCRIPT" in str(e):
                logger.warning("rate_limiter.redis_script_lost_reloading")
                self._script_sha = None

                await self._load_script()
                if self._script_sha:
                    res = await self._redis.evalsha(
                        self._script_sha,
                        1,
                        key,
                        str(now_ms),
                        str(cfg["rate"]),
                        str(cfg["capacity"]),
                    )  # type: ignore
                    return int(res[0]), float(res[1]), float(res[2]), int(res[3])

            logger.error("rate_limiter.evalsha_error", error=e)
            return 1, 0.0, cfg["capacity"], cfg["capacity"]

        except Exception as e:
            logger.error("rate_limiter.unknown_error", error=e)
            return 1, 0.0, cfg["capacity"], cfg["capacity"]

    async def enforce(
        self, action: Literal["tg_send"], identifier: str = "global"
    ) -> None:
        if action not in self.ACTION_LIMITS:
            return

        allowed, retry_after, _remaining, capacity = await self._eval_token_bucket(
            action, identifier
        )

        if allowed == 1:
            return

        retry_after_secs = max(1, int(retry_after + 0.999))
        raise TooManyRequestsError(retry_after_secs=retry_after_secs)

    async def enforce_with_retry(
        self, action: Literal["tg_send"], identifier: str = "global"
    ) -> None:
        while True:
            try:
                await self.enforce(action, identifier)
                return
            except TooManyRequestsError as e:
                logger.warning("rate_limiter.retry", retry_after=e.retry_after_secs)
                await asyncio.sleep(e.retry_after_secs)
