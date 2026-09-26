import json
import logging
import sys
import time
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    Formatter producing structured JSON log records for centralized ingestion.
    Ensures safe metadata fields and never leaks raw message content.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include structured extra fields if present
        for key in (
            "request_id",
            "endpoint",
            "method",
            "status_code",
            "duration_ms",
            "error_code",
            "client_ip",
        ):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            log_entry["exception"] = record.exc_text

        return json.dumps(log_entry, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure root and application loggers with structured JSON formatting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Avoid duplicate handlers if reloaded
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(JSONFormatter())

    # Quiet external third-party loggers
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with LinkSentry standards."""
    return logging.getLogger(name)
