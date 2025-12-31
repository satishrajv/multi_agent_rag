"""
Weekly auto-training script
Run this as a cron job: 0 2 * * 0 (Every Sunday at 2 AM)
"""
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.feedback.auto_trainer import auto_trainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_training.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run weekly auto-training pipeline"""
    logger.info("Starting weekly auto-training job...")

    try:
        # Run training
        summary = auto_trainer.run_weekly_training(days_lookback=7)

        logger.info("\n" + "=" * 60)
        logger.info("TRAINING SUMMARY")
        logger.info("=" * 60)

        import json
        logger.info(json.dumps(summary, indent=2))

        logger.info("\nAuto-training completed successfully!")

    except Exception as e:
        logger.error(f"Auto-training failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
