import time

import structlog
from asgi_correlation_id.context import correlation_id
from fastapi import Request, Response
from fastapi.responses import ORJSONResponse
from uvicorn.protocols.utils import get_path_with_query_string

access_logger = structlog.stdlib.get_logger("api.access")


def _get_client_ip(request: Request) -> str:
    # Try to get the X-Forwarded-For header (case-insensitive).
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # The header can contain multiple IPs. The first one is the original client.
        return x_forwarded_for.split(",")[0].strip()
    # Fall back to the default if the header is missing.
    return request.client.host


async def access_logs_middleware(request: Request, call_next) -> Response:
    structlog.contextvars.clear_contextvars()
    # These context vars will be added to all log entries emitted during the request
    request_id = correlation_id.get()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start_time = time.perf_counter_ns()
    # If the call_next raises an error, we still want to return our own 500 response,
    # so we can add headers to it (process time, request ID...)
    response = ORJSONResponse(
        content={"error": "Internal server error", "request_id": request_id},
        status_code=500,
    )
    try:
        response = await call_next(request)
    except Exception:
        # TODO: Validate that we don't swallow exceptions (unit test?)
        structlog.stdlib.get_logger("api.error").exception("Uncaught exception")
        raise
    finally:
        process_time = (time.perf_counter_ns() - start_time) / 10**6  # convert to ms
        status_code = response.status_code
        url = get_path_with_query_string(request.scope)  # type: ignore
        client_ip = _get_client_ip(request)
        client_port = request.client.port  # type: ignore
        http_method = request.method
        http_version = request.scope["http_version"]
        # Recreate the Uvicorn access log format, but add all parameters as structured information
        if url != "/api/health":
            access_logger.info(
                f"""{client_ip}:{client_port} - "{http_method} {url} HTTP/{http_version}" {status_code}""",
                http={
                    "url": str(request.url),
                    "status_code": status_code,
                    "method": http_method,
                    "request_id": request_id,
                    "version": http_version,
                },
                network={"client": {"ip": client_ip, "port": client_port}},
                duration=f"{process_time:.2f}ms",
            )
        response.headers["X-Process-Time"] = (
            f"{process_time / 10**3:.2f}"  # convert to seconds
        )

        return response
