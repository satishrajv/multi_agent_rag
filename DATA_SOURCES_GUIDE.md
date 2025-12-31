# RAG System - Data Sources & Flow Guide

## Overview

Your Multi-Agent RAG system requires **TWO types of data**:

1. **Knowledge Base (Playbooks)** - What the system RETRIEVES to answer questions
2. **Operational Data (Opportunities & Projects)** - What the system ANALYZES

---

## 1. Knowledge Base: Playbooks ✅ READY

### Purpose
These are your **best practice strategies** that the RAG system retrieves to make recommendations.

### Location
```
data/playbooks/
├── PB-001-sales-multithreading.txt
├── PB-002-sales-reactivation.txt
├── PB-003-delivery-red-to-green.txt
└── PB-004-delivery-overdue-tasks.txt
```

### Structure
```
Title: [Playbook Name]
Category: sales | delivery
Success Rate: XX%
Number of Cases: XX

When to Use:
- Trigger condition 1
- Trigger condition 2

Recommended Actions:
1. Action step 1
2. Action step 2
...

Success Factors:
- Factor 1
- Factor 2

Common Pitfalls:
- Pitfall 1
- Pitfall 2
```

### Status
✅ **4 playbooks created and ready**

---

## 2. Operational Data: Opportunities (from PitchBook) ⚠️ SAMPLE DATA

### Purpose
These are **actual deals** from PitchBook that need analysis.

### Data Source
**PitchBook** provides:
- Company profiles
- Funding rounds
- Deal information
- Executive contacts
- Financial data

Reference:
- [PitchBook API Documentation](https://pitchbook.com/products/direct-access-data/api)
- [PitchBook Data Fields Guide](https://pitchbook.com/data)

### Sample Data Created
```
data/raw/sample_pitchbook_opportunities.csv
```

### Fields from PitchBook

| Field | Description | Example |
|-------|-------------|---------|
| **opportunity_id** | Unique deal identifier | OPP-2024-001 |
| **company_name** | Portfolio company name | TechVenture AI |
| **company_url** | Company website | https://techventure.ai |
| **year_founded** | Company founding year | 2021 |
| **employees** | Employee count | 45 |
| **latest_deal_type** | Funding round type | Series B, Growth Equity |
| **deal_value** | Funding amount ($) | 2500000 |
| **financing_status** | Current status | Active, Closed |
| **last_funding_date** | Last funding round date | 2024-11-15 |

### Additional Fields You Track

| Field | Source | Purpose |
|-------|--------|---------|
| **contacts_engaged** | Your CRM | Track multi-threading |
| **stage** | Your CRM | Discovery, Proposal, Negotiation |
| **days_in_stage** | Calculated | Identify stalled deals |
| **last_activity_date** | Your CRM | Track activity gaps |
| **expected_close_date** | Your CRM | Deadline tracking |
| **primary_contact** | PitchBook/Your CRM | Key stakeholder |
| **contact_role** | PitchBook/Your CRM | CTO, CFO, CEO, etc. |

### How Sales Agent Uses This

```python
# Sales Agent analyzes opportunities like:
opportunity = {
    "opportunity_id": "OPP-2024-001",
    "company_name": "TechVenture AI",
    "deal_value": 2500000,
    "stage": "Proposal",
    "days_in_stage": 21,
    "last_activity_date": "2024-12-09",
    "contacts_engaged": 1,  # Single-threaded!
    "expected_close_date": "2025-02-15"
}

# Agent identifies:
# ✅ Risk Score: 0.87 (AT RISK)
# ✅ Risk Factors:
#    - No activity in 21 days
#    - Single-threaded (only 1 contact)
#    - Deal value > $500K
# ✅ Retrieves Playbook: "Multi-threading Strategy" (78% success)
# ✅ Recommends: Engage CFO, CTO, Risk Lead
# ✅ Generates: Email draft to stakeholders
```

### Sample Data (10 opportunities created)
```csv
opportunity_id,company_name,deal_value,stage,days_in_stage,contacts_engaged
OPP-2024-001,TechVenture AI,2500000,Proposal,21,1        # AT RISK
OPP-2024-002,CloudScale Systems,8500000,Negotiation,12,3 # HEALTHY
OPP-2024-003,DataSync Solutions,15000000,Proposal,35,1   # AT RISK
...
```

---

## 3. Operational Data: Projects ⚠️ SAMPLE DATA

### Purpose
These are **active delivery projects** that need triage.

### Data Source
Your project management system (Jira, Asana, Monday.com, etc.)

### Sample Data Created
```
data/raw/sample_pitchbook_projects.csv
```

### Fields Required

| Field | Description | Example |
|-------|-------------|---------|
| **project_id** | Unique project identifier | PROJ-2024-001 |
| **project_name** | Project title | TechVenture AI Platform Implementation |
| **company_name** | Client company | TechVenture AI |
| **status** | Current status | Green, Yellow, Red |
| **progress_pct** | % complete | 22 |
| **start_date** | Project start | 2024-11-01 |
| **end_date** | Deadline | 2024-12-31 |
| **overdue_tasks** | # overdue tasks | 8 |
| **total_tasks** | Total task count | 35 |
| **last_update_date** | Last status update | 2024-12-28 |
| **client_response_gap_days** | Days since client responded | 5 |
| **project_manager** | PM name | Sarah Martinez |
| **deal_value** | Project value ($) | 2500000 |

### How Delivery Agent Uses This

```python
# Delivery Agent analyzes projects like:
project = {
    "project_id": "PROJ-2024-001",
    "project_name": "TechVenture AI Platform Implementation",
    "status": "Red",
    "progress_pct": 22,
    "end_date": "2024-12-31",  # 3 days away!
    "overdue_tasks": 8,
    "total_tasks": 35,
    "client_response_gap_days": 5
}

# Agent classifies:
# ✅ Classification: TRUE RISK (not just housekeeping)
# ✅ Risk Factors:
#    - Progress 22% vs deadline in 3 days
#    - 8 overdue tasks (23% of total)
#    - Client response gap: 5 days
# ✅ Retrieves Playbook: "Red to Green Project Recovery" (85% success)
# ✅ Recommends:
#    - Start daily 15-min huddles
#    - Escalate client blockers to sales team
#    - Re-scope non-essential items to Phase 2
```

### Sample Data (10 projects created)
```csv
project_id,project_name,status,progress_pct,end_date,overdue_tasks
PROJ-2024-001,TechVenture AI Platform,Red,22,2024-12-31,8      # TRUE RISK
PROJ-2024-002,CloudScale Migration,Green,85,2025-01-15,0      # HEALTHY
PROJ-2024-005,FinTech Payment Gateway,Red,35,2024-12-31,12    # TRUE RISK
...
```

---

## 4. How Data Flows Through RAG System

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: PitchBook Export (.csv)                              │
│ - Opportunities (deals, companies, funding)                 │
│ - Your tracking fields (stage, contacts, activity)          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Load into PostgreSQL                                │
│ - Parse CSV                                                  │
│ - Calculate derived fields (days_in_stage, activity_gap)    │
│ - Store in opportunities table                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Sales Agent Analyzes Opportunity                    │
│ - Fetch opportunity: OPP-2024-001                           │
│ - Extract features: deal_value, days_in_stage, contacts     │
│ - ML Risk Scoring: XGBoost → Risk Score: 0.87               │
│ - Classify: AT RISK (score >= 0.85 threshold)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: RAG Retrieval from Playbooks                        │
│                                                              │
│ Query: "Multi-threading for stalled $2.5M deal,             │
│         single contact, 21 days no activity"                │
│                                                              │
│         ┌───────────────────────────────┐                   │
│         │  Playbook Vector Store        │                   │
│         │  (Weaviate Cloud)             │                   │
│         │                               │                   │
│         │  PB-001: Multi-threading      │ ← Match! (score: 0.92)
│         │  PB-002: Reactivation         │ ← Match! (score: 0.78)
│         │  PB-003: Red-to-Green         │   (not relevant)
│         │  PB-004: Overdue Tasks        │   (not relevant)
│         └───────────────────────────────┘                   │
│                                                              │
│ Hybrid Search: 70% dense vector + 30% BM25 keyword          │
│ Reranking: Cross-encoder scores top results                 │
│ Top Result: PB-001 "Multi-threading Strategy"               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: LLM Generates Recommendations                       │
│                                                              │
│ Input to GPT-4:                                              │
│ - Opportunity context: TechVenture AI, $2.5M, 21 days stall │
│ - Risk factors: Single-threaded, no activity               │
│ - Playbook content: Multi-threading strategy steps          │
│                                                              │
│ Output:                                                      │
│ 1. Identify DMU: CFO, CTO, Risk Lead, Business Owner        │
│ 2. Research stakeholders on LinkedIn                        │
│ 3. Send personalized outreach (tailored by role)            │
│ 4. Schedule multi-party call within 5 days                  │
│                                                              │
│ Draft Email:                                                 │
│ Subject: Quick thought on TechVenture AI's analytics goals  │
│ Hi [CFO Name],                                              │
│ I've been working with [Primary Contact] on...              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: User Reviews & Provides Feedback                    │
│                                                              │
│ User Action:                                                 │
│ ☑ Accepts recommendation (logs as positive feedback)        │
│ ☐ Rejects recommendation (logs as negative feedback)        │
│ ☐ Selects different playbook (logs preference)             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Feedback Loop (Weekly Auto-Training)                │
│                                                              │
│ Every Sunday 2 AM:                                           │
│ - Collect last 7 days feedback                              │
│ - Positive examples: User accepted playbook                 │
│ - Negative examples: User rejected playbook                 │
│ - Retrain reranker model                                    │
│ - Tune risk threshold (if too many false positives)         │
│ - Deploy new model to 10% traffic (A/B test)                │
│                                                              │
│ Result: System gets smarter over time!                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Next Steps to Use Real Data

### Option A: Manual CSV Import (Easiest)

1. **Export from PitchBook**:
   ```
   Companies → Select fields → Export to CSV
   ```

2. **Add your tracking fields** (in Excel/Google Sheets):
   - stage (Discovery, Proposal, Negotiation)
   - contacts_engaged
   - last_activity_date
   - expected_close_date

3. **Save as**:
   ```
   data/raw/pitchbook_opportunities.csv
   ```

4. **Load into system**:
   ```bash
   python scripts/load_opportunities.py data/raw/pitchbook_opportunities.csv
   ```

### Option B: PitchBook API Integration (Advanced)

```python
# Create: scripts/sync_pitchbook.py

import requests
from src.utils.database import db_manager

# PitchBook API
api_key = "your_pitchbook_api_key"
endpoint = "https://api.pitchbook.com/v1/companies"

response = requests.get(endpoint, headers={"Authorization": f"Bearer {api_key}"})
deals = response.json()

# Transform and load
for deal in deals:
    opportunity = {
        "opportunity_id": f"OPP-{deal['id']}",
        "company_name": deal['name'],
        "deal_value": deal['latest_funding_amount'],
        # ... map other fields
    }
    db_manager.insert_opportunity(opportunity)
```

### Option C: CRM Integration (Recommended)

```
PitchBook → Export → Your CRM (Salesforce/HubSpot) → API → RAG System
```

---

## 6. Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **Playbooks** | ✅ Ready | 4 playbooks created |
| **RAG Pipeline** | ✅ Ready | Embeddings, retrieval, reranking configured |
| **Sales Agent** | ✅ Ready | Code complete, waiting for real data |
| **Delivery Agent** | ✅ Ready | Code complete, waiting for real data |
| **Weaviate Cloud** | ✅ Connected | Vector store configured |
| **OpenAI API** | ✅ Connected | GPT-4 + embeddings configured |
| **Sample Opportunities** | ✅ Created | 10 sample deals from PitchBook format |
| **Sample Projects** | ✅ Created | 10 sample delivery projects |
| **Real PitchBook Data** | ⚠️ Pending | Need your actual exports |

---

## 7. Test the System Now

You can test with the sample data I created:

```bash
# 1. Activate virtual environment
cd multi_agent_rag
venv\Scripts\activate

# 2. Initialize logging
python scripts/init_logging.py

# 3. Test RAG with playbooks
python scripts/test_rag_simple.py

# 4. Load sample opportunities (once database script is ready)
python scripts/load_sample_data.py

# 5. Test Sales Agent
python -c "
from src.agents.sales_agent import SalesAgent
agent = SalesAgent()
result = agent.analyze_opportunity('OPP-2024-001')
print(result)
"
```

---

## Sources

Data structure based on PitchBook's official documentation:
- [PitchBook API & Datafeed](https://pitchbook.com/products/direct-access-data)
- [PitchBook Data Overview](https://pitchbook.com/data)
- [Excel Plugin Data Fields](https://pitchbook.com/video-library/excel-plugin-finding-companies-data-fields)
- [PitchBook Features: Export Datasets](https://pitchbook.com/newsletter/pitchbook-features-four-new-ways-to-export-our-datasets-on-people-companies-debt-and-lps)

---

**Ready to develop the RAG system with your actual PitchBook data!** 🚀
