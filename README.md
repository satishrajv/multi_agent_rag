# Multi-Agent RAG System with Auto-Training

A production-ready multi-agent RAG (Retrieval Augmented Generation) system with continuous feedback loops and automated model training. Features specialized AI agents that share common RAG infrastructure and improve over time through user feedback.

## Key Features

- **Multi-Agent Architecture**: Specialized agents for Sales and Delivery workflows
- **Advanced RAG Pipeline**: Hybrid retrieval (dense + BM25) with cross-encoder reranking
- **Continuous Learning**: Weekly auto-training based on user feedback
- **Auto-Threshold Tuning**: Classification thresholds adjust automatically based on false positive/negative rates
- **A/B Testing**: Compare model versions in production
- **Feedback Loops**: User interactions feed back into model training
- **Pattern Mining**: Background agent extracts successful patterns from historical data (optional)

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                      │
│           (User interactions + Feedback collection)         │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
    ┌─────────▼─────────┐       ┌────────▼────────┐
    │   Sales Agent     │       │  Delivery Agent  │
    │  (Risk Scoring)   │       │   (Triage)       │
    └─────────┬─────────┘       └────────┬─────────┘
              │                          │
              └──────────┬───────────────┘
                         │
              ┌──────────▼───────────┐
              │   RAG Pipeline       │
              │ ┌──────────────────┐ │
              │ │ Hybrid Retrieval │ │
              │ │  (Dense + BM25)  │ │
              │ └──────────────────┘ │
              │ ┌──────────────────┐ │
              │ │   Reranker       │ │
              │ │ (Cross-encoder)  │ │
              │ └──────────────────┘ │
              └──────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼─────┐   ┌─────▼──────┐   ┌────▼────┐
   │ChromaDB  │   │PostgreSQL  │   │  Redis  │
   │(Vectors) │   │(Data+Meta) │   │ (Cache) │
   └──────────┘   └────────────┘   └─────────┘
                        │
              ┌─────────▼────────────┐
              │  Auto-Trainer        │
              │  (Weekly retraining) │
              └──────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- 8GB+ RAM recommended

### Installation

1. **Clone the repository**
```bash
cd multi_agent_rag
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your settings (OpenAI API key if using OpenAI)
```

5. **Start infrastructure services**
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- ChromaDB (port 8000)

6. **Generate synthetic data**
```bash
python scripts/setup_data.py
```

This creates:
- 100 sample opportunities
- 50 sample projects
- 5 initial playbooks

7. **Initialize vector store**
```bash
python scripts/initialize_vector_store.py
```

8. **Launch Streamlit dashboard**
```bash
streamlit run ui/streamlit_app.py
```

The dashboard will open at `http://localhost:8501`

## Usage

### Sales Agent

Analyzes sales opportunities and recommends actions:

```python
from src.agents.sales_agent import sales_agent

# Analyze opportunity
result = sales_agent.analyze_opportunity("OPP-2024-001")

print(result)
# {
#   "opportunity_id": "OPP-2024-001",
#   "company": "Jupiter Computing",
#   "status": "AT RISK",
#   "risk_score": 0.87,
#   "risk_factors": ["No activity in 7 days", ...],
#   "recommended_actions": [...],
#   "draft_email": {...}
# }

# Log user feedback
sales_agent.log_feedback(
    opportunity_id="OPP-2024-001",
    query="Risk analysis",
    risk_score=0.87,
    retrieved_playbooks=[...],
    selected_playbook_id="PB-003",
    user_action="accepted"
)
```

### Delivery Agent

Triages project risks (true risk vs housekeeping):

```python
from src.agents.delivery_agent import delivery_agent

# Analyze project
result = delivery_agent.analyze_project("PROJ-2024-001")

print(result)
# {
#   "project_id": "PROJ-2024-001",
#   "classification": "TRUE RISK",
#   "risk_factors": ["Progress 22% vs end date in 3 days", ...],
#   "recommended_actions": [...]
# }
```

### Auto-Training

Run weekly auto-training manually:

```bash
python scripts/run_auto_training.py
```

Or set up as cron job (Linux/Mac):
```bash
# Add to crontab (every Sunday at 2 AM)
0 2 * * 0 /path/to/venv/bin/python /path/to/scripts/run_auto_training.py
```

## Project Structure

```
multi_agent_rag/
├── data/
│   ├── raw/                    # Input CSV/JSON files
│   ├── processed/              # Cleaned data
│   ├── vector_store/           # ChromaDB persistence
│   └── playbooks/              # Playbook markdown files
├── src/
│   ├── agents/
│   │   ├── sales_agent.py      # Sales opportunity agent
│   │   ├── delivery_agent.py   # Delivery triage agent
│   │   └── pattern_miner.py    # Pattern mining (optional)
│   ├── rag/
│   │   ├── chunking.py         # Text chunking
│   │   ├── embedding.py        # Embedding generation
│   │   ├── retrieval.py        # Hybrid retrieval
│   │   ├── reranker.py         # Cross-encoder reranking
│   │   └── vector_store.py     # Vector DB interface
│   ├── models/
│   │   ├── risk_classifier.py  # XGBoost risk scoring
│   │   └── threshold_tuner.py  # Auto-threshold optimization
│   ├── feedback/
│   │   └── auto_trainer.py     # Weekly retraining pipeline
│   ├── utils/
│   │   ├── database.py         # PostgreSQL interface
│   │   ├── redis_cache.py      # Redis caching
│   │   └── llm_client.py       # LLM API wrapper
│   └── config.py               # Configuration
├── ui/
│   └── streamlit_app.py        # Dashboard UI
├── scripts/
│   ├── setup_data.py           # Generate synthetic data
│   ├── initialize_vector_store.py  # Initialize vector store
│   └── run_auto_training.py    # Weekly auto-training job
├── models/                     # Saved model files
├── mlruns/                     # MLflow tracking
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## Configuration

Edit `.env` file to customize:

```bash
# LLM Provider
LLM_PROVIDER=ollama          # or 'openai'
LLM_MODEL=llama3.1           # or 'gpt-4'
OPENAI_API_KEY=your_key_here

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG Settings
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5
HYBRID_DENSE_WEIGHT=0.7
HYBRID_SPARSE_WEIGHT=0.3

# Agent Thresholds
SALES_RISK_THRESHOLD=0.85
DELIVERY_RISK_THRESHOLD=0.80

# Auto-Training
AUTO_TRAINING_ENABLED=true
AB_TEST_PERCENTAGE=0.1       # 10% traffic to new models
```

## Auto-Training Pipeline

The system continuously improves through:

1. **Feedback Collection**: Every user interaction (accept/reject) is logged
2. **Weekly Retraining**:
   - Retrains cross-encoder reranker on user-selected playbooks
   - Tunes classification thresholds based on false positive/negative rates
   - Registers new model versions
3. **A/B Testing**: New models serve 10% of traffic for evaluation
4. **Threshold Optimization**: Automatically adjusts risk thresholds to minimize errors

### Auto-Training Process

```python
# Runs automatically every Sunday at 2 AM
from src.feedback.auto_trainer import auto_trainer

summary = auto_trainer.run_weekly_training(days_lookback=7)

# Output:
# {
#   "reranker": {
#     "status": "success",
#     "samples": 45,
#     "version": "v_20241229_020000"
#   },
#   "sales_threshold": {
#     "old_threshold": 0.85,
#     "new_threshold": 0.90,
#     "reasoning": "Reducing false positives (18% → target <15%)"
#   },
#   "delivery_threshold": {...}
# }
```

## Key Components

### Hybrid Retrieval

Combines dense (vector) and sparse (BM25) retrieval:

```python
from src.rag.retrieval import hybrid_retriever

results = hybrid_retriever.hybrid_search(
    query="Multi-threading strategy for stalled deals",
    top_k=5,
    filter_dict={"category": "sales"}
)

# Returns: Weighted combination of:
# - 70% dense vector similarity
# - 30% BM25 keyword matching
```

### Reranking

Cross-encoder reranks retrieved results:

```python
from src.rag.reranker import reranker

reranked = reranker.rerank(
    query="How to recover red projects?",
    documents=retrieval_results,
    top_k=3
)

# Returns: Top-3 documents scored by cross-encoder
```

### Threshold Tuning

Automatically adjusts classification thresholds:

```python
from src.models.threshold_tuner import sales_threshold_tuner

result = sales_threshold_tuner.tune_threshold(
    feedback_data=feedback_df,
    current_threshold=0.85
)

# Result:
# {
#   "old_threshold": 0.85,
#   "new_threshold": 0.90,
#   "changed": True,
#   "reasoning": "Reducing false positives (18% → target <15%)",
#   "metrics": {
#     "precision": 0.82,
#     "recall": 0.76,
#     "f1_score": 0.79
#   }
# }
```

## Success Metrics

Track these metrics to demonstrate improvement:

### Retrieval Quality
- **Top-1 Accuracy**: % of times user selects top-ranked playbook (target: >70%)
- **Top-3 Accuracy**: % of times user selects from top-3 (target: >90%)

### Classification Accuracy
- **Precision**: True positives / (TP + FP) (target: >85%)
- **Recall**: True positives / (TP + FN) (target: >80%)

### User Satisfaction
- **Acceptance Rate**: % of recommendations accepted (target: >80%)

### Auto-Training Impact
- Compare week 1 vs week 4 metrics
- Show improvement trajectory

## Database Schema

### Opportunities
```sql
opportunity_id | company | stage | days_in_stage | last_activity_date |
contacts_engaged | deal_value | expected_close_date | outcome
```

### Projects
```sql
project_id | project_name | status | progress_pct | end_date |
overdue_tasks | last_update_date | client_response_gap_days
```

### Feedback Log
```sql
id | timestamp | agent_name | entity_id | query | risk_score |
retrieved_playbooks | selected_playbook_id | user_action | outcome
```

### Playbooks
```sql
playbook_id | title | content | category | success_rate | num_cases
```

## Development

### Run Tests
```bash
pytest tests/
```

### Add New Playbooks
```python
from src.utils.database import db_manager

playbook = {
    "playbook_id": "PB-999",
    "title": "New Playbook",
    "content": "Playbook content...",
    "category": "sales",
    "success_rate": 0.75,
    "num_cases": 10
}

db_manager.insert_playbook(playbook)
```

### Query Feedback Data
```python
from src.utils.database import db_manager

feedback = db_manager.get_feedback_for_training(days=7, agent_name="sales_agent")
print(feedback)
```

## Troubleshooting

### ChromaDB Connection Error
```bash
# Restart ChromaDB container
docker-compose restart chromadb
```

### PostgreSQL Connection Error
```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres
```

### LLM Generation Errors
```bash
# If using Ollama, ensure it's running
ollama serve

# Pull the model
ollama pull llama3.1
```

### Vector Store Empty
```bash
# Re-initialize vector store
python scripts/initialize_vector_store.py
```

## Future Enhancements

- [ ] Pattern Miner agent (automatic playbook generation)
- [ ] MLflow integration for experiment tracking
- [ ] Multi-tenancy support
- [ ] API endpoints for programmatic access
- [ ] Real-time model monitoring dashboard
- [ ] Advanced A/B testing framework
- [ ] Integration with CRM systems (Salesforce, HubSpot)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License

## Contact

For questions or support, please open an issue on GitHub.

---

**Built with**: Python, LangChain, ChromaDB, PostgreSQL, Redis, XGBoost, Sentence Transformers, Streamlit
