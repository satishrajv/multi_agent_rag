# Step-by-Step Testing Guide

Test the RAG system incrementally without needing the full database setup.

---

## Prerequisites

### 1. Create Virtual Environment

```cmd
cd C:\Users\Yashvi\Desktop\PMC\multi_agent_rag

python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the start of your prompt.

### 2. Install Dependencies

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Time**: 2-3 minutes

### 3. Create .env File

The `.env` file already exists with your credentials:
- ✅ OpenAI API Key
- ✅ Weaviate Cloud credentials

**Verify**:
```cmd
type .env
```

You should see your API keys configured.

---

## Test Sequence

### Test 1: OpenAI Connection (30 seconds)

```cmd
python scripts\test_openai_config.py
```

**Expected Output**:
```
✓ Client initialized successfully
✓ Embedding generated successfully (dimension: 1536)
✓ LLM response received
✓ All tests passed!
```

**If it fails**:
- Check OpenAI API key in `.env`
- Verify billing at https://platform.openai.com/account/billing

---

### Test 2: Weaviate Connection (30 seconds)

```cmd
python scripts\test_weaviate_config.py
```

**Expected Output**:
```
✓ Connected to Weaviate cloud successfully
✓ Weaviate cluster is ready
✓ All tests passed!
```

**If it fails**:
- Check Weaviate cluster URL in `.env`
- Verify cluster is running at https://console.weaviate.cloud

---

### Test 3: Simple RAG Pipeline (1-2 minutes)

This is the NEW test that uses only text files (no SQL database needed):

```cmd
python scripts\test_rag_simple.py
```

**What it tests**:
1. ✅ Load playbook files from `data/playbooks/`
2. ✅ Chunk text into smaller pieces
3. ✅ Generate embeddings with OpenAI
4. ✅ Store in Weaviate cloud
5. ✅ Search for relevant chunks
6. ✅ Rerank results

**Expected Output**:
```
Step 1: Loading playbook files...
✓ Found 3 playbook file(s)

Step 2: Reading file contents...
✓ Successfully loaded 3 playbook(s)

Step 3: Testing text chunking...
✓ Total chunks created: 15

Step 4: Testing embedding generation...
✓ Generated embedding
  Embedding dimension: 1536

Step 5: Testing vector store...
✓ Added 15 chunks to vector store

Step 6: Testing vector search...
  Query: 'How to handle stalled sales deals?'
  ✓ Found 2 result(s)

Step 7: Testing reranking...
✓ Reranking successful

✓ ALL RAG TESTS PASSED!
```

**Cost**: ~$0.01 (OpenAI embeddings for 15 chunks)

---

## Test Input Files

I've created 3 simple playbook files for testing:

### File 1: Sales - Multi-threading
**Location**: `data/playbooks/PB-001-sales-multithreading.txt`

**Content**: Strategy for engaging multiple stakeholders in stalled deals

**Use case**: Test sales-related queries

### File 2: Sales - Reactivation
**Location**: `data/playbooks/PB-002-sales-reactivation.txt`

**Content**: How to re-engage dormant opportunities

**Use case**: Test reactivation strategies

### File 3: Delivery - Red to Green
**Location**: `data/playbooks/PB-003-delivery-red-to-green.txt`

**Content**: Project recovery from Red status

**Use case**: Test delivery/project queries

---

## Adding Your Own Test Files

### Create a new playbook file:

```
data/playbooks/PB-004-your-topic.txt
```

**Format** (plain text):
```
Title: Your Playbook Title

Category: sales
Success Rate: 80%
Number of Cases: 10

When to Use:
- Condition 1
- Condition 2

Recommended Actions:
1. First action
   - Details
   - More details

2. Second action
   - Details

Success Factors:
- Factor 1
- Factor 2

Common Pitfalls:
- Pitfall 1
- Pitfall 2
```

Then run the test again:
```cmd
python scripts\test_rag_simple.py
```

---

## Interactive Testing

### Test specific queries:

```python
# Create a test script: test_my_query.py
from src.rag.vector_store import vector_store

# Your question
query = "How do I handle a stalled enterprise deal?"

# Search
results = vector_store.similarity_search(query, top_k=3)

# Print results
for i, result in enumerate(results, 1):
    print(f"\nResult {i}:")
    print(f"Score: {result['score']:.4f}")
    print(f"Playbook: {result['metadata']['playbook_id']}")
    print(f"Text: {result['document'][:200]}...\n")
```

Run it:
```cmd
python test_my_query.py
```

---

## Troubleshooting

### Issue: "Module not found"

**Solution**:
```cmd
# Make sure venv is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "OpenAI API error"

**Solution**:
```cmd
# Check API key
type .env | findstr OPENAI_API_KEY

# Test connection
python scripts\test_openai_config.py
```

### Issue: "Weaviate connection failed"

**Solution**:
```cmd
# Check Weaviate URL
type .env | findstr WEAVIATE

# Verify cluster is running
# Go to: https://console.weaviate.cloud
```

### Issue: "No playbook files found"

**Solution**:
```cmd
# Check if files exist
dir data\playbooks\*.txt

# If empty, the 3 files should already be created:
# - PB-001-sales-multithreading.txt
# - PB-002-sales-reactivation.txt
# - PB-003-delivery-red-to-green.txt
```

---

## Next Steps

After all tests pass:

### Option 1: Test with Full System (with SQL)

```cmd
# Start PostgreSQL and Redis
docker-compose up -d

# Generate full synthetic data
python scripts\setup_data.py

# Initialize full vector store
python scripts\initialize_vector_store.py

# Launch dashboard
streamlit run ui\streamlit_app.py
```

### Option 2: Keep Testing RAG Only (no SQL)

Continue using the simple file-based approach:

1. Add more playbook `.txt` files to `data/playbooks/`
2. Run `python scripts\test_rag_simple.py`
3. Test different queries
4. Verify search quality

### Option 3: Test Agents Directly (Advanced)

```python
# Test script: test_agent.py
from src.agents.sales_agent import sales_agent

# Mock opportunity data (no SQL needed)
mock_opportunity = {
    'opportunity_id': 'TEST-001',
    'company': 'Test Company',
    'stage': 'Proposal',
    'days_in_stage': 14,
    'last_activity_date': '2025-01-20',
    'contacts_engaged': 1,
    'deal_value': 500000,
    'expected_close_date': '2025-02-15'
}

# Analyze (will use RAG to find playbooks)
result = sales_agent.analyze_opportunity('TEST-001')
print(result)
```

---

## Summary

### What You Can Test Now (No SQL Required):

✅ **OpenAI Connection** - API key and embeddings
✅ **Weaviate Connection** - Cloud vector database
✅ **Text Chunking** - Break documents into chunks
✅ **Embedding Generation** - Convert text to vectors
✅ **Vector Storage** - Store in Weaviate
✅ **Similarity Search** - Find relevant chunks
✅ **Reranking** - Improve result quality

### What Requires SQL Database:

❌ Sales opportunities data
❌ Delivery projects data
❌ Feedback logging
❌ Auto-training pipeline
❌ Full dashboard

### Recommended Testing Order:

1. ✅ Test OpenAI (scripts\test_openai_config.py)
2. ✅ Test Weaviate (scripts\test_weaviate_config.py)
3. ✅ Test RAG Pipeline (scripts\test_rag_simple.py)
4. ✅ Add your own playbook files
5. ✅ Test custom queries
6. ❌ (Optional) Set up full system with SQL

---

## Quick Reference

```cmd
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Test 1: OpenAI
python scripts\test_openai_config.py

# Test 2: Weaviate
python scripts\test_weaviate_config.py

# Test 3: RAG Pipeline (file-based, no SQL)
python scripts\test_rag_simple.py

# Clean up Weaviate (if needed)
# Go to https://console.weaviate.cloud
# Delete "Playbooks" collection
# Re-run test_rag_simple.py
```

---

**Start here**: Run the 3 test scripts in order to verify everything works!
