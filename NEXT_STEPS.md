# Next Steps - Complete Action Plan

## Quick Start (30 Minutes Total)

Follow these steps in order to get your RAG system running:

---

## ✅ Step 1: Test RAG Pipeline (10 min)

**Goal**: Verify Weaviate + OpenAI + Playbooks are working

```bash
cd C:\Users\Yashvi\Desktop\PMC\multi_agent_rag

# Activate virtual environment
venv\Scripts\activate

# Initialize logging
python scripts\init_logging.py

# Test RAG retrieval
python scripts\test_rag_simple.py
```

**Expected Output**:
```
✓ Step 1: Loading playbooks from data/playbooks/
✓ Step 2: Testing OpenAI embeddings
✓ Step 3: Storing in Weaviate cloud
✓ Step 4: Testing semantic search
  Result 1: Multi-threading Strategy (0.92)
  Result 2: Reactivation Strategy (0.78)
```

**If this works** ✅ → Move to Step 2
**If this fails** ❌ → Check:
- OpenAI API key in `.env`
- Weaviate cluster credentials in `.env`
- Internet connection

---

## ✅ Step 2: Start Database (5 min)

**Goal**: Start PostgreSQL and Redis services

```bash
# Start Docker containers
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Expected Output**:
```
NAME                    STATUS
postgres                Up
redis                   Up
```

**If this fails** ❌ → Install Docker Desktop for Windows

---

## ✅ Step 3: Load Sample Data (5 min)

**Goal**: Load sample PitchBook opportunities and projects into database

```bash
# Load sample opportunities and projects
python scripts\load_sample_data.py
```

**Expected Output**:
```
Loading opportunities from data/raw/sample_pitchbook_opportunities.csv...
  ✓ Loaded OPP-2024-001: TechVenture AI
  ✓ Loaded OPP-2024-002: CloudScale Systems
  ...
✓ Loaded 10 opportunities successfully

Loading projects from data/raw/sample_pitchbook_projects.csv...
  ✓ Loaded PROJ-2024-001: TechVenture AI Platform Implementation
  ...
✓ Loaded 10 projects successfully
```

---

## ✅ Step 4: Test Sales Agent (5 min)

**Goal**: Analyze a sample opportunity with RAG

```bash
# Test Sales Agent on at-risk deal
python -c "from src.agents.sales_agent import SalesAgent; agent = SalesAgent(); result = agent.analyze_opportunity('OPP-2024-001'); import json; print(json.dumps(result, indent=2))"
```

**Expected Output**:
```json
{
  "opportunity_id": "OPP-2024-001",
  "company": "TechVenture AI",
  "status": "AT RISK",
  "risk_score": 0.87,
  "risk_factors": [
    "No activity in 21 days",
    "Single-threaded engagement (only 1 contact)",
    "Deal value $2.5M > $500K threshold"
  ],
  "recommended_actions": [
    {
      "playbook": "Multi-threading Strategy",
      "success_rate": "78%",
      "action": "Identify decision-making unit: CFO, CTO, Risk Lead..."
    }
  ],
  "draft_email": {
    "subject": "Quick thought on TechVenture AI's analytics goals",
    "body": "Hi [CFO Name], I've been working with..."
  }
}
```

---

## ✅ Step 5: Test Delivery Agent (5 min)

**Goal**: Analyze a sample red project with RAG

```bash
# Test Delivery Agent on red project
python -c "from src.agents.delivery_agent import DeliveryAgent; agent = DeliveryAgent(); result = agent.analyze_project('PROJ-2024-001'); import json; print(json.dumps(result, indent=2))"
```

**Expected Output**:
```json
{
  "project_id": "PROJ-2024-001",
  "project_name": "TechVenture AI Platform Implementation",
  "status": "Red",
  "classification": "TRUE RISK",
  "risk_factors": [
    "Progress 22% vs deadline in 3 days",
    "8 overdue tasks (23% of total)",
    "Client response gap: 5 days"
  ],
  "recommended_actions": [
    {
      "playbook": "Red to Green Project Recovery",
      "success_rate": "85%",
      "action": "Start daily 15-min huddles..."
    }
  ]
}
```

---

## ✅ Step 6: Launch UI Dashboard (Optional - 5 min)

**Goal**: View results in Streamlit web interface

```bash
# Start Streamlit dashboard
streamlit run ui\streamlit_app.py
```

**Opens**: http://localhost:8501

**UI Features**:
- View all opportunities
- Analyze individual deals
- See recommendations
- Provide feedback (accept/reject)

---

## After Testing: Next Development Steps

### Option A: Add More Playbooks

Create additional playbooks in `data/playbooks/`:

**Suggested playbooks**:
1. `PB-005-competitor-displacement.txt` - Handling competitive deals
2. `PB-006-pricing-objections.txt` - Overcoming pricing concerns
3. `PB-007-scope-management.txt` - Preventing scope creep
4. `PB-008-stakeholder-escalation.txt` - Escalation strategies

**Template**:
```
Title: [Strategy Name]
Category: sales | delivery
Success Rate: XX%
Number of Cases: XX

When to Use:
- Trigger 1
- Trigger 2

Recommended Actions:
1. Action 1
2. Action 2

Success Factors:
- Factor 1

Common Pitfalls:
- Pitfall 1
```

### Option B: Integrate Real PitchBook Data

1. **Export from PitchBook**:
   - Companies → Filter → Export CSV
   - Include: company_name, deal_value, funding_date, contacts

2. **Add your tracking fields** (Excel/Sheets):
   - stage (Discovery, Proposal, Negotiation)
   - contacts_engaged
   - last_activity_date
   - expected_close_date

3. **Replace sample data**:
   ```
   data/raw/pitchbook_opportunities.csv
   ```

4. **Load into system**:
   ```bash
   python scripts\load_sample_data.py
   ```

### Option C: Set Up Auto-Training

**Enable weekly model retraining**:

1. Collect 20+ feedback interactions
2. Run manual training:
   ```bash
   python scripts\run_auto_training.py
   ```

3. Set up Windows Task Scheduler (weekly Sunday 2 AM):
   ```
   Task: Run python scripts\run_auto_training.py
   Trigger: Weekly, Sunday, 2:00 AM
   ```

### Option D: Production Deployment

**Deploy to cloud**:

1. **AWS Option**:
   - EC2: t3.large instance
   - RDS: PostgreSQL 16
   - ElastiCache: Redis
   - EventBridge: Weekly auto-training

2. **Azure Option**:
   - App Service
   - Azure Database for PostgreSQL
   - Azure Cache for Redis
   - Logic Apps: Scheduled training

3. **Environment variables**:
   ```bash
   # Set in production
   export DATABASE_URL="postgresql://..."
   export REDIS_URL="redis://..."
   export OPENAI_API_KEY="sk-..."
   export WEAVIATE_CLUSTER_URL="https://..."
   ```

---

## Troubleshooting

### Issue: "Module not found"
```bash
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Database connection failed"
```bash
# Check Docker is running
docker-compose ps

# Restart services
docker-compose restart postgres redis
```

### Issue: "Weaviate connection error"
```bash
# Check .env file has correct credentials
cat .env | findstr WEAVIATE

# Test connection
python scripts\test_weaviate_config.py
```

### Issue: "OpenAI API error"
```bash
# Check API key
cat .env | findstr OPENAI

# Test connection
python scripts\test_openai_config.py
```

---

## Success Criteria

You'll know the system is working when:

✅ RAG retrieves correct playbooks for queries
✅ Sales Agent identifies at-risk deals (risk_score > 0.85)
✅ Delivery Agent classifies TRUE RISK vs HOUSEKEEPING
✅ Recommendations match opportunity/project context
✅ Draft emails are generated automatically
✅ Feedback is logged to database
✅ Logs show operations in `logs/application.log`

---

## Your Current Status

| Component | Status | Next Action |
|-----------|--------|-------------|
| Playbooks | ✅ Ready | Add more (optional) |
| RAG Pipeline | ✅ Ready | Test with Step 1 |
| Weaviate | ✅ Connected | Verify in Step 1 |
| OpenAI | ✅ Connected | Verify in Step 1 |
| Sample Data | ✅ Created | Load in Step 3 |
| Database | ⚠️ Not started | Start in Step 2 |
| Agents | ✅ Code ready | Test in Steps 4-5 |
| UI | ✅ Code ready | Launch in Step 6 |

---

## Timeline

**Today (30 min)**:
- Steps 1-5: Core testing

**This Week**:
- Add 2-3 more playbooks
- Test with different scenarios
- Review recommendations quality

**Next Week**:
- Integrate real PitchBook data
- Train team on using the system
- Collect initial feedback

**Week 3+**:
- Enable auto-training (need 20+ interactions)
- Deploy to production
- Set up monitoring

---

## Questions?

Common questions:

**Q: Can I test without Docker?**
A: For Step 1 (RAG only), yes! Steps 3-5 need PostgreSQL.

**Q: How much does this cost to run?**
A: Local: Free (except OpenAI API ~$5-10/month)
   Cloud: ~$100/month (EC2 + RDS + Redis)

**Q: How do I add my team's data?**
A: Export from PitchBook → CSV → `data/raw/` → `python scripts\load_sample_data.py`

**Q: When will auto-training start working?**
A: After 20+ user feedback interactions (accept/reject recommendations)

---

**🚀 START HERE: Step 1 - Test RAG Pipeline**

```bash
cd C:\Users\Yashvi\Desktop\PMC\multi_agent_rag
venv\Scripts\activate
python scripts\test_rag_simple.py
```
