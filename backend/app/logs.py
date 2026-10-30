"""JSON logs, one object per line, tagged with the id of the request being served."""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime

request_id: ContextVar[str] = ContextVar("request_id", default="-")
log = logging.getLogger("http")


class JsonFormatter(logging.Formatter):
    """Format a record as JSON; fields passed as `extra={"fields": {...}}` are merged in."""

    def format(self, record: logging.LogRecord) -> str:
        """One line: time, level, logger, message, request id, extra fields, traceback."""
        line = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id.get(),
            **getattr(record, "fields", {}),
        }
        if record.exc_info:
            line["error"] = self.formatException(record.exc_info)
        return json.dumps(line, ensure_ascii=False, default=str)


def setup_logging() -> None:
    """Send every logger, uvicorn's included, through one JSON handler on stderr."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("httpx").setLevel(logging.WARNING)


class RequestLogMiddleware:
    """Give each HTTP request an id (X-Request-ID) and log one line when it answers.

    The line is written when the response starts, so for a stream `ms` is the time
    to the first byte."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Docker probes /api/health every 10 seconds; logging it would bury the rest.
        if scope["type"] != "http" or scope["path"] == "/api/health":
            return await self.app(scope, receive, send)
        rid = uuid.uuid4().hex[:12]
        token = request_id.set(rid)
        start = time.monotonic()

        async def send_with_id(message):
            if message["type"] == "http.response.start":
                message["headers"] = [
                    *message.get("headers", []),
                    (b"x-request-id", rid.encode()),
                ]
                ms = round((time.monotonic() - start) * 1000)
                log.info(
                    "request",
                    extra={
                        "fields": {
                            "method": scope["method"],
                            "path": scope["path"],
                            "status": message["status"],
                            "ms": ms,
                        }
                    },
                )
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            request_id.reset(token)
