"""
Generate synthetic data for testing the multi-agent RAG system
"""
import pandas as pd
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.database import db_manager


def generate_opportunities(n=100):
    """Generate synthetic sales opportunities"""

    companies = [
        "Jupiter Computing", "TechCorp EMEA", "Alpha Systems", "Beta Industries",
        "Gamma Solutions", "Delta Enterprises", "Epsilon Tech", "Zeta Corp",
        "Theta Innovations", "Iota Systems", "Kappa Holdings", "Lambda Inc",
        "Mu Technologies", "Nu Partners", "Xi Corporation", "Omicron Group",
        "Pi Ventures", "Rho Industries", "Sigma Solutions", "Tau Systems"
    ]

    stages = ["Discovery", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]

    opportunities = []

    for i in range(n):
        opp_id = f"OPP-{2024}-{i+1:03d}"
        company = random.choice(companies)
        stage = random.choice(stages[:-2])  # Exclude closed stages for active opps

        # Generate realistic data
        days_in_stage = random.randint(1, 45)
        last_activity_days_ago = random.randint(0, 21)
        last_activity_date = datetime.now() - timedelta(days=last_activity_days_ago)
        contacts_engaged = random.randint(1, 7)
        deal_value = random.randint(50, 5000) * 1000
        expected_close_days = random.randint(7, 120)
        expected_close_date = datetime.now() + timedelta(days=expected_close_days)

        opportunities.append({
            "opportunity_id": opp_id,
            "company": company,
            "stage": stage,
            "days_in_stage": days_in_stage,
            "last_activity_date": last_activity_date.strftime("%Y-%m-%d"),
            "contacts_engaged": contacts_engaged,
            "deal_value": deal_value,
            "expected_close_date": expected_close_date.strftime("%Y-%m-%d"),
            "outcome": None
        })

    # Convert to DataFrame and save
    df = pd.DataFrame(opportunities)
    output_path = Path(__file__).parent.parent / "data" / "raw" / "opportunities.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Generated {n} opportunities -> {output_path}")
    return opportunities


def generate_projects(n=50):
    """Generate synthetic delivery projects"""

    project_names = [
        "Silver River Project", "Golden Gate Initiative", "Azure Sky Platform",
        "Crimson Wave System", "Emerald Forest Solution", "Sapphire Ocean Project",
        "Diamond Peak Platform", "Ruby Valley Initiative", "Pearl Harbor System",
        "Jade Mountain Solution", "Amber Sunset Project", "Coral Reef Platform",
        "Onyx Shadow Initiative", "Topaz Dawn System", "Opal Cloud Solution"
    ]

    statuses = ["Green", "Yellow", "Red"]

    projects = []

    for i in range(n):
        proj_id = f"PROJ-{2024}-{i+1:03d}"
        project_name = f"{random.choice(project_names)} {i+1}"
        status = random.choice(statuses)

        # Generate realistic data based on status
        if status == "Green":
            progress_pct = random.uniform(30, 95)
            overdue_tasks = random.randint(0, 2)
            client_response_gap = random.randint(0, 3)
        elif status == "Yellow":
            progress_pct = random.uniform(20, 70)
            overdue_tasks = random.randint(1, 5)
            client_response_gap = random.randint(2, 7)
        else:  # Red
            progress_pct = random.uniform(10, 60)
            overdue_tasks = random.randint(5, 15)
            client_response_gap = random.randint(5, 14)

        end_days = random.randint(3, 90)
        end_date = datetime.now() + timedelta(days=end_days)
        last_update_days_ago = random.randint(0, 10)
        last_update_date = datetime.now() - timedelta(days=last_update_days_ago)

        projects.append({
            "project_id": proj_id,
            "project_name": project_name,
            "status": status,
            "progress_pct": round(progress_pct, 2),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "overdue_tasks": overdue_tasks,
            "last_update_date": last_update_date.strftime("%Y-%m-%d"),
            "client_response_gap_days": client_response_gap
        })

    # Save as JSON
    output_path = Path(__file__).parent.parent / "data" / "raw" / "projects.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(projects, f, indent=2)

    print(f"Generated {n} projects -> {output_path}")
    return projects


def generate_initial_playbooks():
    """Generate initial playbook library"""

    playbooks = [
        {
            "playbook_id": "PB-001",
            "title": "Multi-threading Strategy for Stalled Proposals",
            "category": "sales",
            "content": """
When to use: Opportunities stalled in Proposal stage with single-threaded engagement

Recommended Actions:
1. Identify decision-making unit (CFO, CTO, Risk Lead, Business Owner)
2. Research each stakeholder's priorities via LinkedIn and company news
3. Send personalized outreach to each stakeholder highlighting their specific concerns
4. Schedule multi-party discovery call within 5 business days
5. Create stakeholder map and track engagement breadth

Success Factors:
- Engaging 3+ stakeholders increases win rate by 35%
- CFO involvement critical in deals > $1M
- Technical champions need executive sponsorship

Common Pitfalls:
- Sending generic emails to all stakeholders
- Not researching individual priorities
- Skipping the CTO in technical deals
            """,
            "success_rate": 0.78,
            "num_cases": 11
        },
        {
            "playbook_id": "PB-002",
            "title": "Reactivation Strategy for Dormant Deals",
            "category": "sales",
            "content": """
When to use: No activity in 7+ days, any stage

Recommended Actions:
1. Review last touchpoint and identify blocker
2. Send 2-option value email (not just "checking in")
3. Offer specific business insights or competitive intelligence
4. Propose concrete next step with calendar invite
5. If no response in 3 days, loop in their manager

Success Factors:
- Providing value in every outreach (not just asking for updates)
- Specific calendar invites get 3x more responses
- Industry insights increase engagement by 42%

Common Pitfalls:
- Generic "just checking in" emails
- Not offering tangible value
- Waiting too long before escalating
            """,
            "success_rate": 0.65,
            "num_cases": 18
        },
        {
            "playbook_id": "PB-003",
            "title": "Cap Table Sensitivity Messaging for APAC",
            "category": "sales",
            "content": """
When to use: APAC deals in Negotiation stage with pricing concerns

Recommended Actions:
1. Frame solution as revenue enabler, not cost center
2. Show ROI calculation with region-specific benchmarks
3. Offer flexible payment terms (annual vs quarterly)
4. Provide reference customers in same industry/region
5. Highlight compliance benefits for local regulations

Success Factors:
- ROI messaging increased conversion by 28% in APAC
- Local references critical (global references less effective)
- Flexible terms unlock 40% of stalled deals

Common Pitfalls:
- Using Western pricing justifications
- Ignoring local compliance drivers
- Not offering payment flexibility
            """,
            "success_rate": 0.82,
            "num_cases": 8
        },
        {
            "playbook_id": "PB-004",
            "title": "Red to Green Project Recovery - Manager Huddle",
            "category": "delivery",
            "content": """
When to use: Projects in Red status with <7 days to deadline

Recommended Actions:
1. Start 15-minute daily huddle with delivery manager
2. Identify top 3 critical blockers
3. Escalate client response gaps to account team
4. Re-scope non-essential items to Phase 2
5. Get written confirmation on revised scope within 24 hours

Success Factors:
- Daily huddles have 85% success rate in Red → Green transitions
- Scope re-alignment critical (trying to do everything fails)
- Client escalation by sales team speeds responses 3x

Common Pitfalls:
- Trying to recover without rescoping
- Not involving sales team for client escalation
- Weekly vs daily check-ins (too slow)
            """,
            "success_rate": 0.85,
            "num_cases": 14
        },
        {
            "playbook_id": "PB-005",
            "title": "Overdue Task Triage Protocol",
            "category": "delivery",
            "content": """
When to use: 5+ overdue tasks, any project status

Recommended Actions:
1. Categorize overdue tasks: client-blocked vs team-blocked vs scope creep
2. For client-blocked: escalate via account manager
3. For team-blocked: reassign or pair-program
4. For scope creep: flag as Phase 2, get approval
5. Update project plan with revised timeline

Success Factors:
- Categorization prevents wasted effort
- 60% of overdue tasks are client-blocked (need escalation)
- Pair programming resolves 70% of team blockers in <1 day

Common Pitfalls:
- Treating all overdue tasks equally
- Not escalating client blockers fast enough
- Accepting scope creep without re-planning
            """,
            "success_rate": 0.73,
            "num_cases": 22
        }
    ]

    # Save to database
    for pb in playbooks:
        db_manager.insert_playbook(pb)

    # Also save as markdown files
    playbooks_dir = Path(__file__).parent.parent / "data" / "playbooks"
    playbooks_dir.mkdir(parents=True, exist_ok=True)

    for pb in playbooks:
        pb_path = playbooks_dir / f"{pb['playbook_id']}.md"
        with open(pb_path, 'w') as f:
            f.write(f"# {pb['title']}\n\n")
            f.write(f"**Category:** {pb['category']}\n")
            f.write(f"**Success Rate:** {pb['success_rate']:.1%}\n")
            f.write(f"**Cases:** {pb['num_cases']}\n\n")
            f.write(pb['content'])

    print(f"Generated {len(playbooks)} playbooks")
    return playbooks


def load_data_to_database():
    """Load generated data into PostgreSQL"""

    # Load opportunities
    opp_file = Path(__file__).parent.parent / "data" / "raw" / "opportunities.csv"
    if opp_file.exists():
        df = pd.read_csv(opp_file)
        for _, row in df.iterrows():
            db_manager.insert_opportunity(row.to_dict())
        print(f"Loaded {len(df)} opportunities to database")

    # Load projects
    proj_file = Path(__file__).parent.parent / "data" / "raw" / "projects.json"
    if proj_file.exists():
        with open(proj_file, 'r') as f:
            projects = json.load(f)
        for proj in projects:
            db_manager.insert_project(proj)
        print(f"Loaded {len(projects)} projects to database")


if __name__ == "__main__":
    print("Generating synthetic data...")

    # Generate data files
    generate_opportunities(100)
    generate_projects(50)
    generate_initial_playbooks()

    # Load to database
    print("\nLoading data to PostgreSQL...")
    try:
        load_data_to_database()
        print("\nData generation complete!")
    except Exception as e:
        print(f"\nNote: Database loading failed (this is OK if DB is not running yet): {e}")
        print("Run docker-compose up first, then run this script again.")
