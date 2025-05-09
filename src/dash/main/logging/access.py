import time

import structlog
from fastapi import Request, Response
from fastapi.responses import ORJSONResponse
from uvicorn.protocols.utils import get_path_with_query_string

logger = structlog.stdlib.get_logger("api.access")


async def access_logger(request: Request, call_next) -> Response:
    structlog.contextvars.clear_contextvars()
    # These context vars will be added to all log entries emitted during the request

    start_time = time.perf_counter_ns()
    # If the call_next raises an error, we still want to return our own 500 response,
    # so we can add headers to it (process time, request ID...)
    response = ORJSONResponse(
        content={"error": "Internal server error"}, status_code=500
    )
    try:
        response = await call_next(request)
    except Exception:
        structlog.stdlib.get_logger("api.error").exception("Uncaught exception")
        raise
    finally:
        process_time = (time.perf_counter_ns() - start_time) / 10**6  # convert to ms
        status_code = response.status_code
        url = get_path_with_query_string(request.scope)  # type: ignore
        client_host = request.client.host  # type: ignore
        client_port = request.client.port  # type: ignore
        http_method = request.method
        http_version = request.scope["http_version"]
        # Recreate the Uvicorn access log format, but add all parameters as structured information, ignore health check
        if url != "/api/health":
            logger.info(
                f"""{client_host}:{client_port} - "{http_method} {url} HTTP/{http_version}" {status_code}""",
                http={
                    "url": str(request.url),
                    "status_code": status_code,
                    "method": http_method,
                },
                network={"client": {"ip": client_host, "port": client_port}},
                duration=f"{process_time:.2f}ms",
            )

        response.headers["X-Process-Time"] = (
            f"{process_time / 10**3:.2f}"  # convert to seconds
        )
        return response
