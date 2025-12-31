"""
Production-grade logging configuration
"""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json
import sys


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Build colored message
        message = f"{log_color}[{record.levelname}]{reset_color} {timestamp} - {record.name} - {record.getMessage()}"

        # Add exception if present
        if record.exc_info:
            message += '\n' + self.formatException(record.exc_info)

        return message


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Setup production-grade logging

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_json: Enable JSON structured logging
        max_bytes: Max size of each log file before rotation
        backup_count: Number of backup files to keep
    """

    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console Handler (colored, human-readable)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        root_logger.addHandler(console_handler)

    # Application Log File (human-readable)
    if enable_file:
        app_log_file = log_path / "application.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.DEBUG)
        app_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app_handler.setFormatter(app_formatter)
        root_logger.addHandler(app_handler)

    # Error Log File (errors only)
    if enable_file:
        error_log_file = log_path / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n%(exc_info)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)

    # JSON Log File (structured, machine-readable)
    if enable_json:
        json_log_file = log_path / "application.json"
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)

    # Performance Log File (for timing and metrics)
    performance_log_file = log_path / "performance.log"
    performance_handler = logging.handlers.RotatingFileHandler(
        performance_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    performance_handler.setLevel(logging.INFO)
    performance_handler.addFilter(lambda record: hasattr(record, 'duration_ms'))
    performance_formatter = logging.Formatter(
        '%(asctime)s - %(message)s - Duration: %(duration_ms)dms',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    performance_handler.setFormatter(performance_formatter)
    root_logger.addHandler(performance_handler)

    # User Activity Log File (track user actions)
    activity_log_file = log_path / "user_activity.log"
    activity_handler = logging.handlers.RotatingFileHandler(
        activity_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    activity_handler.setLevel(logging.INFO)
    activity_handler.addFilter(lambda record: hasattr(record, 'user_action'))
    activity_formatter = logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    activity_handler.setFormatter(activity_formatter)
    root_logger.addHandler(activity_handler)

    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('weaviate').setLevel(logging.WARNING)

    logging.info(f"Logging configured: level={log_level}, dir={log_dir}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Context managers for tracking operations

class LogContext:
    """Context manager for logging operations with timing"""

    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.extra = kwargs
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.operation}", extra=self.extra)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds() * 1000

        if exc_type is None:
            self.logger.info(
                f"Completed: {self.operation}",
                extra={**self.extra, 'duration_ms': int(duration)}
            )
        else:
            self.logger.error(
                f"Failed: {self.operation} - {exc_val}",
                extra={**self.extra, 'duration_ms': int(duration)},
                exc_info=True
            )

        return False  # Don't suppress exceptions


# Helper functions for common logging patterns

def log_api_request(logger: logging.Logger, endpoint: str, method: str, status_code: int, duration_ms: int):
    """Log API request"""
    logger.info(
        f"API {method} {endpoint}",
        extra={
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration_ms
        }
    )


def log_user_action(logger: logging.Logger, user_id: str, action: str, details: dict = None):
    """Log user action"""
    message = f"User {user_id} performed {action}"
    if details:
        message += f" - {details}"

    logger.info(
        message,
        extra={
            'user_id': user_id,
            'user_action': action,
            'details': details or {}
        }
    )


def log_performance(logger: logging.Logger, operation: str, duration_ms: int, details: dict = None):
    """Log performance metrics"""
    message = f"Performance: {operation}"
    if details:
        message += f" - {details}"

    logger.info(
        message,
        extra={
            'operation': operation,
            'duration_ms': duration_ms,
            'details': details or {}
        }
    )


def log_error_with_context(logger: logging.Logger, error: Exception, context: dict = None):
    """Log error with additional context"""
    logger.error(
        f"Error: {str(error)}",
        extra={'context': context or {}},
        exc_info=True
    )
