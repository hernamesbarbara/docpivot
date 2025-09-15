"""Simplified logging configuration for DocPivot."""

import logging
import logging.config
from typing import Dict, Any, Optional


# Simple logging configuration
DEFAULT_LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s - %(name)s - %(message)s"},
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "docpivot": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
    "root": {"level": "WARNING", "handlers": ["console"]},
}


def setup_logging(
    level: str = "INFO",
    detailed: bool = False,
) -> None:
    """Set up logging configuration for DocPivot.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        detailed: Whether to use detailed formatting with file/line info
    """
    config = DEFAULT_LOGGING_CONFIG.copy()

    # Override level if specified
    if level.upper() in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        config["loggers"]["docpivot"]["level"] = level.upper()
        config["handlers"]["console"]["level"] = level.upper()

    # Switch to detailed formatting if requested
    if detailed:
        config["handlers"]["console"]["formatter"] = "detailed"

    # Apply logging configuration
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified module.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def log_exception_with_context(
    logger: logging.Logger,
    exception: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR,
) -> None:
    """Log exception with operation context.

    Args:
        logger: Logger to use
        exception: Exception to log
        operation: Operation that was being performed
        context: Optional context information
        level: Logging level to use
    """
    context_str = ""
    if context:
        context_items = [f"{k}={v}" for k, v in context.items()]
        context_str = f" [Context: {', '.join(context_items)}]"

    logger.log(
        level,
        f"Exception during {operation}: {type(exception).__name__}: {exception}{context_str}",
        exc_info=True,
    )


# Initialize default logging configuration
setup_logging()