"""
Master setup script - Initialize the entire Multi-Agent RAG system
"""
import sys
from pathlib import Path
import subprocess
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title):
    """Print formatted section header"""
    logger.info("\n" + "=" * 60)
    logger.info(f"  {title}")
    logger.info("=" * 60 + "\n")


def check_docker():
    """Check if Docker is running"""
    try:
        subprocess.run(
            ["docker", "ps"],
            check=True,
            capture_output=True
        )
        return True
    except Exception:
        return False


def start_services():
    """Start Docker services"""
    print_section("Starting Infrastructure Services")

    if not check_docker():
        logger.error("Docker is not running. Please start Docker and try again.")
        sys.exit(1)

    logger.info("Starting PostgreSQL, Redis, and ChromaDB...")

    try:
        subprocess.run(
            ["docker-compose", "up", "-d"],
            check=True
        )
        logger.info("✓ Services started successfully")

        # Wait for services to be ready
        logger.info("Waiting for services to initialize...")
        time.sleep(10)

    except Exception as e:
        logger.error(f"Failed to start services: {str(e)}")
        sys.exit(1)


def check_services():
    """Check if all services are healthy"""
    print_section("Checking Service Health")

    services = {
        "PostgreSQL": "postgres",
        "Redis": "redis",
        "ChromaDB": "chromadb"
    }

    all_healthy = True

    for name, container in services.items():
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "-q", container],
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                logger.info(f"✓ {name} is running")
            else:
                logger.error(f"✗ {name} is not running")
                all_healthy = False

        except Exception as e:
            logger.error(f"✗ {name} check failed: {str(e)}")
            all_healthy = False

    return all_healthy


def generate_data():
    """Generate synthetic data"""
    print_section("Generating Synthetic Data")

    script_path = Path(__file__).parent / "setup_data.py"

    try:
        subprocess.run(
            [sys.executable, str(script_path)],
            check=True
        )
        logger.info("✓ Data generation complete")

    except Exception as e:
        logger.error(f"Data generation failed: {str(e)}")
        sys.exit(1)


def initialize_vector_store():
    """Initialize vector store"""
    print_section("Initializing Vector Store")

    script_path = Path(__file__).parent / "initialize_vector_store.py"

    try:
        subprocess.run(
            [sys.executable, str(script_path)],
            check=True
        )
        logger.info("✓ Vector store initialized")

    except Exception as e:
        logger.error(f"Vector store initialization failed: {str(e)}")
        sys.exit(1)


def verify_installation():
    """Verify installation"""
    print_section("Verifying Installation")

    checks = []

    # Check Python packages
    try:
        import chromadb
        import sentence_transformers
        import xgboost
        import streamlit
        checks.append(("Python packages", True))
    except ImportError as e:
        checks.append(("Python packages", False))
        logger.error(f"Missing package: {str(e)}")

    # Check database connection
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from src.utils.database import db_manager

        # Try to query
        result = db_manager.execute_query("SELECT COUNT(*) FROM opportunities")
        count = result[0]['count'] if result else 0
        logger.info(f"Found {count} opportunities in database")
        checks.append(("Database connection", True))

    except Exception as e:
        checks.append(("Database connection", False))
        logger.error(f"Database check failed: {str(e)}")

    # Check Redis
    try:
        from src.utils.redis_cache import redis_cache
        if redis_cache.health_check():
            checks.append(("Redis connection", True))
        else:
            checks.append(("Redis connection", False))
    except Exception as e:
        checks.append(("Redis connection", False))
        logger.error(f"Redis check failed: {str(e)}")

    # Check vector store
    try:
        from src.rag.vector_store import vector_store
        count = vector_store.count()
        logger.info(f"Vector store contains {count} documents")
        checks.append(("Vector store", True if count > 0 else False))
    except Exception as e:
        checks.append(("Vector store", False))
        logger.error(f"Vector store check failed: {str(e)}")

    # Print summary
    logger.info("\nVerification Summary:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        logger.info(f"{status} {check_name}")
        if not passed:
            all_passed = False

    return all_passed


def print_next_steps():
    """Print next steps for user"""
    print_section("Setup Complete!")

    logger.info("""
Next Steps:

1. Launch the Streamlit dashboard:
   streamlit run ui/streamlit_app.py

2. The dashboard will open at http://localhost:8501

3. Try analyzing an opportunity:
   - Go to "Sales Agent" tab
   - Enter: OPP-2024-001
   - Click "Analyze Opportunity"

4. Try analyzing a project:
   - Go to "Delivery Agent" tab
   - Enter: PROJ-2024-001
   - Click "Analyze Project"

5. Provide feedback to train the models:
   - Click "Accept" or "Dismiss" on recommendations
   - Feedback is logged for weekly auto-training

6. Run auto-training manually:
   python scripts/run_auto_training.py

7. Set up weekly auto-training (optional):
   - Linux/Mac: Add to crontab
     0 2 * * 0 /path/to/venv/bin/python /path/to/scripts/run_auto_training.py
   - Windows: Use Task Scheduler

Configuration:
- Edit .env file to customize settings
- Switch LLM provider: LLM_PROVIDER=openai (requires API key)
- Adjust risk thresholds: SALES_RISK_THRESHOLD=0.85

Troubleshooting:
- View logs: docker-compose logs -f
- Restart services: docker-compose restart
- Re-initialize: docker-compose down && docker-compose up -d

Documentation:
- Full README: See README.md
- Architecture: See project structure in README.md

Enjoy using the Multi-Agent RAG System!
    """)


def main():
    """Main setup workflow"""
    print_section("Multi-Agent RAG System Setup")

    logger.info("This script will set up the entire system:")
    logger.info("1. Start Docker services (PostgreSQL, Redis, ChromaDB)")
    logger.info("2. Generate synthetic data")
    logger.info("3. Initialize vector store")
    logger.info("4. Verify installation")
    logger.info("")

    # Step 1: Start services
    start_services()

    # Step 2: Check services
    if not check_services():
        logger.error("Service health checks failed. Please check Docker logs.")
        logger.info("Run: docker-compose logs")
        sys.exit(1)

    # Step 3: Generate data
    generate_data()

    # Step 4: Initialize vector store
    initialize_vector_store()

    # Step 5: Verify
    if verify_installation():
        print_next_steps()
    else:
        logger.error("\nSome verification checks failed. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
