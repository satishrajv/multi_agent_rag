"""
Initialize logging for the application
Run this before starting the application
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.logging_config import setup_logging
import logging


def main():
    """Initialize logging system"""

    print("Initializing logging system...")

    # Setup logging
    setup_logging(
        log_level="INFO",
        log_dir="logs",
        enable_console=True,
        enable_file=True,
        enable_json=True,
        max_bytes=10 * 1024 * 1024,  # 10MB per file
        backup_count=5  # Keep 5 backup files
    )

    # Test logging
    logger = logging.getLogger(__name__)

    logger.debug("Debug message - testing logging")
    logger.info("Info message - logging initialized successfully")
    logger.warning("Warning message - this is a test")

    # Test structured logging
    logger.info(
        "Test structured log",
        extra={
            'user_id': 'test_user',
            'request_id': '12345',
            'duration_ms': 100
        }
    )

    # Test error logging
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        logger.error("Caught test exception", exc_info=True)

    print("\nLogging initialized!")
    print("\nLog files created:")
    print("  - logs/application.log      (Human-readable application logs)")
    print("  - logs/error.log            (Errors only)")
    print("  - logs/application.json     (Structured JSON logs)")
    print("  - logs/performance.log      (Performance metrics)")
    print("  - logs/user_activity.log    (User actions)")
    print("\nAll log files rotate at 10MB with 5 backups retained.")


if __name__ == "__main__":
    main()
