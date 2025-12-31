# Quick Start Guide

Get the Multi-Agent RAG system up and running in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- Docker Desktop installed and running
- 8GB RAM minimum

## Installation Steps

### 1. Set Up Python Environment

```bash
# Navigate to project directory
cd multi_agent_rag

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file (optional - defaults work fine for testing)
# If using OpenAI instead of Ollama:
# - Set LLM_PROVIDER=openai
# - Add your OPENAI_API_KEY=sk-...
```

### 3. Run Complete Setup

```bash
# This single script does everything:
# - Starts Docker services
# - Generates synthetic data
# - Initializes vector store
# - Verifies installation
python scripts/setup_system.py
```

Wait 2-3 minutes for setup to complete.

### 4. Launch Dashboard

```bash
streamlit run ui/streamlit_app.py
```

The dashboard opens at: **http://localhost:8501**

## Try It Out

### Test Sales Agent

1. Go to **Sales Agent** tab
2. Enter opportunity ID: `OPP-2024-001`
3. Click **Analyze Opportunity**
4. Review risk score and recommendations
5. Click **Accept** or **Dismiss** to provide feedback

### Test Delivery Agent

1. Go to **Delivery Agent** tab
2. Enter project ID: `PROJ-2024-001`
3. Click **Analyze Project**
4. Review classification and recommendations
5. Provide feedback on actions

## What's Happening Behind the Scenes?

1. **Risk Scoring**: XGBoost models calculate risk scores based on activity patterns
2. **RAG Retrieval**: Hybrid search (vector + BM25) finds relevant playbooks
3. **Reranking**: Cross-encoder reranks results for better accuracy
4. **LLM Generation**: Generates specific action recommendations and email drafts
5. **Feedback Collection**: Your clicks (accept/dismiss) are logged for training

## Auto-Training

The system improves over time through weekly auto-training:

```bash
# Run auto-training manually
python scripts/run_auto_training.py
```

This will:
- Retrain the reranker on your feedback
- Tune classification thresholds
- Set up A/B testing for new models

## Troubleshooting

### Docker Services Won't Start

```bash
# Check Docker Desktop is running
docker --version

# Restart services
docker-compose down
docker-compose up -d

# View logs
docker-compose logs -f
```

### "Module not found" errors

```bash
# Ensure virtual environment is activated
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### ChromaDB connection errors

```bash
# Restart ChromaDB
docker-compose restart chromadb

# Wait 10 seconds, then retry
```

### No playbooks found

```bash
# Re-initialize vector store
python scripts/initialize_vector_store.py
```

### LLM generation fails

If using Ollama (default):
```bash
# Install Ollama from https://ollama.ai
# Pull the model
ollama pull llama3.1

# Start Ollama server
ollama serve
```

If using OpenAI:
```bash
# Edit .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
```

## Next Steps

1. **Explore the Data**
   - Check `data/raw/opportunities.csv` for all opportunities
   - Check `data/raw/projects.json` for all projects
   - Review generated playbooks in `data/playbooks/`

2. **Customize Settings**
   - Edit `.env` to adjust risk thresholds
   - Try different embedding models
   - Switch between Ollama and OpenAI

3. **Add Your Own Data**
   - Replace synthetic data with real opportunities/projects
   - Add custom playbooks to database
   - Re-initialize vector store

4. **Set Up Production**
   - Configure weekly auto-training cron job
   - Set up monitoring and logging
   - Deploy to cloud infrastructure

## Architecture Overview

```
User (Streamlit UI)
    ↓
Agents (Sales / Delivery)
    ↓
RAG Pipeline (Hybrid Retrieval + Reranking)
    ↓
Vector Store (ChromaDB) + Database (PostgreSQL)
    ↓
Auto-Training (Weekly Retraining)
```

## Key Files

- `ui/streamlit_app.py` - Dashboard interface
- `src/agents/sales_agent.py` - Sales opportunity agent
- `src/agents/delivery_agent.py` - Delivery triage agent
- `src/rag/retrieval.py` - Hybrid retrieval system
- `src/feedback/auto_trainer.py` - Auto-training pipeline
- `scripts/setup_system.py` - Complete setup script

## Support

- Full documentation: See `README.md`
- Architecture details: See `README.md` → System Architecture
- Troubleshooting: See `README.md` → Troubleshooting section

## Example Workflow

```python
# In Python shell or script
from src.agents.sales_agent import sales_agent

# Analyze opportunity
result = sales_agent.analyze_opportunity("OPP-2024-001")
print(result['status'])  # "AT RISK" or "HEALTHY"
print(result['risk_score'])  # 0.87
print(result['recommended_actions'])  # List of actions

# Log feedback
sales_agent.log_feedback(
    opportunity_id="OPP-2024-001",
    query="Risk analysis",
    risk_score=result['risk_score'],
    retrieved_playbooks=result.get('recommended_actions', []),
    selected_playbook_id="PB-001",
    user_action="accepted"  # or "rejected"
)
```

Happy building! 🚀
