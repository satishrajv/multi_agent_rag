"""
Load sample PitchBook data (opportunities and projects) into PostgreSQL
"""
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.database import db_manager


def load_opportunities():
    """Load sample opportunities from CSV"""

    csv_path = Path(__file__).parent.parent / "data" / "raw" / "sample_pitchbook_opportunities.csv"

    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        return

    print(f"Loading opportunities from {csv_path}...")
    df = pd.read_csv(csv_path)

    print(f"Found {len(df)} opportunities")

    # Transform to match database schema
    for _, row in df.iterrows():
        opportunity = {
            "opportunity_id": row['opportunity_id'],
            "company": row['company_name'],
            "stage": row['stage'],
            "days_in_stage": row['days_in_stage'],
            "last_activity_date": row['last_activity_date'],
            "contacts_engaged": row['contacts_engaged'],
            "deal_value": row['deal_value'],
            "expected_close_date": row['expected_close_date']
        }

        try:
            db_manager.insert_opportunity(opportunity)
            print(f"  ✓ Loaded {opportunity['opportunity_id']}: {opportunity['company']}")
        except Exception as e:
            print(f"  ✗ Error loading {opportunity['opportunity_id']}: {e}")

    print(f"\n✓ Loaded {len(df)} opportunities successfully")


def load_projects():
    """Load sample projects from CSV"""

    csv_path = Path(__file__).parent.parent / "data" / "raw" / "sample_pitchbook_projects.csv"

    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        return

    print(f"\nLoading projects from {csv_path}...")
    df = pd.read_csv(csv_path)

    print(f"Found {len(df)} projects")

    # Transform to match database schema
    for _, row in df.iterrows():
        project = {
            "project_id": row['project_id'],
            "project_name": row['project_name'],
            "status": row['status'],
            "progress_pct": row['progress_pct'],
            "end_date": row['end_date'],
            "overdue_tasks": row['overdue_tasks'],
            "last_update_date": row['last_update_date'],
            "client_response_gap_days": row['client_response_gap_days']
        }

        try:
            db_manager.insert_project(project)
            print(f"  ✓ Loaded {project['project_id']}: {project['project_name']}")
        except Exception as e:
            print(f"  ✗ Error loading {project['project_id']}: {e}")

    print(f"\n✓ Loaded {len(df)} projects successfully")


def main():
    """Main function"""

    print("=" * 60)
    print("Loading Sample PitchBook Data into PostgreSQL")
    print("=" * 60)

    # Load opportunities
    load_opportunities()

    # Load projects
    load_projects()

    print("\n" + "=" * 60)
    print("✓ Data loading complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test Sales Agent: python -c \"from src.agents.sales_agent import SalesAgent; agent = SalesAgent(); print(agent.analyze_opportunity('OPP-2024-001'))\"")
    print("2. Test Delivery Agent: python -c \"from src.agents.delivery_agent import DeliveryAgent; agent = DeliveryAgent(); print(agent.analyze_project('PROJ-2024-001'))\"")


if __name__ == "__main__":
    main()
