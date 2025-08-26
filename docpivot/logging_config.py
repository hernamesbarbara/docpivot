"""Logging configuration for DocPivot.

This module provides standardized logging setup and configuration for DocPivot
components. It ensures consistent log formatting, levels, and output across
all modules.
"""

import logging
import logging.config
import sys
from typing import Dict, Any, Optional


# Default logging configuration
DEFAULT_LOGGING_CONFIG: Dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s - %(name)s - %(message)s'
        },
        'performance': {
            'format': '%(asctime)s - %(name)s - PERF - %(message)s - Duration: %(duration)sms',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'detailed_console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        },
        'error_console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'stream': 'ext://sys.stderr'
        }
    },
    'loggers': {
        'docpivot': {
            'level': 'INFO',
            'handlers': ['console', 'error_console'],
            'propagate': False
        },
        'docpivot.io.readers': {
            'level': 'INFO',
            'handlers': ['console', 'error_console'],
            'propagate': False
        },
        'docpivot.io.serializers': {
            'level': 'INFO',
            'handlers': ['console', 'error_console'],
            'propagate': False
        },
        'docpivot.workflows': {
            'level': 'INFO',
            'handlers': ['console', 'error_console'],
            'propagate': False
        },
        'docpivot.validation': {
            'level': 'INFO',
            'handlers': ['console', 'error_console'],
            'propagate': False
        }
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['error_console']
    }
}


def setup_logging(
    level: str = "INFO",
    detailed: bool = False,
    config_dict: Optional[Dict[str, Any]] = None
) -> None:
    """Set up logging configuration for DocPivot.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        detailed: Whether to use detailed formatting with file/line info
        config_dict: Optional custom logging configuration dictionary
    """
    # Use custom config if provided, otherwise use default
    config = config_dict or DEFAULT_LOGGING_CONFIG.copy()
    
    # Override level if specified
    if level.upper() in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
        for logger_name in config['loggers']:
            config['loggers'][logger_name]['level'] = level.upper()
    
    # Switch to detailed formatting if requested
    if detailed:
        for handler_name in config['handlers']:
            if handler_name != 'error_console':  # Error console is already detailed
                config['handlers'][handler_name]['formatter'] = 'detailed'
                config['handlers'][handler_name]['level'] = 'DEBUG'
    
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


class PerformanceLogger:
    """Logger for performance metrics and timing information."""
    
    def __init__(self, logger: logging.Logger):
        """Initialize performance logger.
        
        Args:
            logger: Base logger to use for performance logging
        """
        self.logger = logger
        
    def log_operation_time(
        self, 
        operation: str, 
        duration_ms: float,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log operation timing information.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            context: Optional context information
        """
        context_str = ""
        if context:
            context_items = [f"{k}={v}" for k, v in context.items()]
            context_str = f" [{', '.join(context_items)}]"
            
        self.logger.info(
            f"Performance: {operation} completed in {duration_ms:.2f}ms{context_str}"
        )
        
    def log_file_processing(
        self,
        file_path: str,
        operation: str,
        duration_ms: float,
        file_size_bytes: Optional[int] = None
    ) -> None:
        """Log file processing performance.
        
        Args:
            file_path: Path to the processed file
            operation: Operation performed (read, write, transform, etc.)
            duration_ms: Duration in milliseconds
            file_size_bytes: Optional file size in bytes
        """
        context = {"file": file_path, "operation": operation}
        if file_size_bytes is not None:
            context["size_bytes"] = file_size_bytes
            
        self.log_operation_time(f"File {operation}", duration_ms, context)


class ProgressLogger:
    """Logger for progress tracking in long-running operations."""
    
    def __init__(self, logger: logging.Logger, total_items: int):
        """Initialize progress logger.
        
        Args:
            logger: Base logger to use for progress logging
            total_items: Total number of items to process
        """
        self.logger = logger
        self.total_items = total_items
        self.processed_items = 0
        
    def log_progress(self, increment: int = 1, message: Optional[str] = None) -> None:
        """Log progress update.
        
        Args:
            increment: Number of items processed since last update
            message: Optional additional message
        """
        self.processed_items += increment
        percentage = (self.processed_items / self.total_items) * 100
        
        progress_msg = f"Progress: {self.processed_items}/{self.total_items} ({percentage:.1f}%)"
        if message:
            progress_msg += f" - {message}"
            
        self.logger.info(progress_msg)
        
    def log_completion(self, message: Optional[str] = None) -> None:
        """Log operation completion.
        
        Args:
            message: Optional completion message
        """
        completion_msg = f"Completed: {self.processed_items}/{self.total_items} items processed"
        if message:
            completion_msg += f" - {message}"
            
        self.logger.info(completion_msg)


def create_error_context_logger(base_logger: logging.Logger) -> logging.Logger:
    """Create a logger adapter that includes error context information.
    
    Args:
        base_logger: Base logger to wrap
        
    Returns:
        logging.Logger: Logger with error context capabilities
    """
    class ErrorContextAdapter(logging.LoggerAdapter):
        """Adapter that adds error context to log messages."""
        
        def process(self, msg, kwargs):
            """Process log message to include context."""
            extra = kwargs.get('extra', {})
            
            # Add error context if available
            if 'error_context' in extra:
                context = extra['error_context']
                if isinstance(context, dict):
                    context_items = [f"{k}={v}" for k, v in context.items()]
                    msg = f"{msg} [Context: {', '.join(context_items)}]"
                    
            return msg, kwargs
            
    return ErrorContextAdapter(base_logger, {})


def log_exception_with_context(
    logger: logging.Logger,
    exception: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR
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
        exc_info=True
    )


# Initialize default logging configuration
setup_logging()