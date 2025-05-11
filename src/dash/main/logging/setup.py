import logging
import sys
from datetime import timedelta
from typing import Literal
from uuid import UUID

import ddtrace
import orjson
import structlog
from ddtrace.trace import tracer
from structlog.types import EventDict, Processor

LoggingLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _serializer(*args, **kwargs):
    return orjson.dumps(*args, **kwargs).decode()


# https://github.com/hynek/structlog/issues/35#issuecomment-591321744
def rename_event_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Log entries keep the text message in the `event` field, but Datadog
    uses the `message` field. This processor moves the value from one field to
    the other.
    See https://github.com/hynek/structlog/issues/35#issuecomment-591321744
    """
    event_dict["message"] = event_dict.pop("event")
    return event_dict


def tracer_injection(_, __, event_dict: EventDict) -> EventDict:
    span = tracer.current_span()
    trace_id, span_id = (span.trace_id, span.span_id) if span else (None, None)

    # add ids to structlog event dictionary
    event_dict["dd.trace_id"] = str(trace_id or 0)
    event_dict["dd.span_id"] = str(span_id or 0)

    # add the env, service, and version configured for the tracer
    event_dict["dd.env"] = ddtrace.config.env or ""
    event_dict["dd.service"] = ddtrace.config.service or ""
    event_dict["dd.version"] = ddtrace.config.version or ""

    return event_dict


def convert_uuid_keys(_, __, event_dict: EventDict) -> EventDict:
    return {str(k) if isinstance(k, UUID) else k: v for k, v in event_dict.items()}


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


def convert_timedelta(_, __, event_dict: EventDict) -> EventDict:
    return {
        k: human_readable_timedelta(v) if isinstance(v, timedelta) else v
        for k, v in event_dict.items()
    }


def human_readable_timedelta(td: timedelta) -> str:
    """
    Convert a timedelta to a human-readable string like "2 days, 3 hours, 5 minutes".
    """
    # Total seconds in the interval
    total_seconds = int(td.total_seconds())
    if total_seconds == 0:
        return "0 seconds"

    periods = [
        ("day", 60 * 60 * 24),
        ("hour", 60 * 60),
        ("min", 60),
        ("sec", 1),
    ]

    parts = []
    for name, seconds_per_unit in periods:
        value, total_seconds = divmod(total_seconds, seconds_per_unit)
        if value:
            unit = name if value == 1 else name + "s"
            parts.append(f"{value} {unit}")

    return ", ".join(parts)


def configure_logging(
    level: LoggingLevel = "INFO", json_logs: bool = False, colorize: bool = False
) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        drop_color_message_key,
        tracer_injection,
        timestamper,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        # We rename the `event` key to `message` only in JSON logs, as Datadog looks for the
        # `message` key but the pretty ConsoleRenderer looks for `event`
        shared_processors.append(rename_event_key)
        # Format the exception only for JSON logs, as we want to pretty-print them when
        # using the ConsoleRenderer
        shared_processors.append(structlog.processors.format_exc_info)
        shared_processors.append(convert_timedelta)
    else:
        shared_processors.append(convert_uuid_keys)
        shared_processors.append(convert_timedelta)

    structlog.configure(
        processors=shared_processors
        + [
            # Prepare event dict for `ProcessorFormatter`.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log_renderer: structlog.types.Processor
    if json_logs:
        log_renderer = structlog.processors.JSONRenderer(serializer=_serializer)
    else:
        log_renderer = structlog.dev.ConsoleRenderer(
            colors=colorize, exception_formatter=structlog.dev.plain_traceback
        )

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            # Remove _record & _from_structlog.
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            log_renderer,
        ],
    )

    handler = logging.StreamHandler()
    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    for _log in ["uvicorn", "uvicorn.error"]:
        # Clear the log handlers for uvicorn loggers, and enable propagation
        # so the messages are caught by our root logger and formatted correctly
        # by structlog
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = True

    # Since we re-create the access logs ourselves, to add all information
    # in the structured log (see the `logging_middleware` in main.py), we clear
    # the handlers and prevent the logs to propagate to a logger higher up in the
    # hierarchy (effectively rendering them silent).
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False

    def handle_exception(exc_type, exc_value, exc_traceback):
        """
        Log any uncaught exception instead of letting it be printed by Python
        (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
        See https://stackoverflow.com/a/16993115/3641865
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        root_logger.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception
