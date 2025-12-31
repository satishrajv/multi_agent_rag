# Quick Start with Virtual Environment

## 🚀 Get Started in 5 Minutes

### Step 1: Create Virtual Environment (30 seconds)

```cmd
cd C:\Users\Yashvi\Desktop\PMC\multi_agent_rag
python -m venv venv
venv\Scripts\activate
```

✅ You should see `(venv)` at the start of your command line

---

### Step 2: Install Dependencies (2-3 minutes)

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

✅ Installs OpenAI, Weaviate, Streamlit, and all other packages

---

### Step 3: Test RAG System (1-2 minutes)

```cmd
# Test OpenAI connection
python scripts\test_openai_config.py

# Test Weaviate connection
python scripts\test_weaviate_config.py

# Test RAG pipeline with files (no SQL needed!)
python scripts\test_rag_simple.py
```

✅ All tests should pass!

**Cost**: ~$0.01 for embedding generation

---

## What You Can Test Right Now

### ✅ WITHOUT SQL Database:

1. **RAG Pipeline**
   - Load text files from `data/playbooks/`
   - Generate embeddings with OpenAI
   - Store in Weaviate Cloud
   - Search for relevant content
   - Test with your own questions

2. **Test Files Included**:
   - `PB-001-sales-multithreading.txt` - Multi-threading strategy
   - `PB-002-sales-reactivation.txt` - Reactivation playbook
   - `PB-003-delivery-red-to-green.txt` - Project recovery
   - `PB-004-delivery-overdue-tasks.txt` - Task triage

3. **Add Your Own**:
   - Create `.txt` files in `data/playbooks/`
   - Run `python scripts\test_rag_simple.py`
   - Test searches with your content

---

## Test Sequence

### Test 1: OpenAI

```cmd
python scripts\test_openai_config.py
```

**Checks**:
- ✅ API key valid
- ✅ Can generate embeddings
- ✅ Can call GPT-4

**Expected**: All tests pass ✓

---

### Test 2: Weaviate

```cmd
python scripts\test_weaviate_config.py
```

**Checks**:
- ✅ Cluster connection works
- ✅ Can create collections
- ✅ Can insert/search vectors

**Expected**: All tests pass ✓

---

### Test 3: RAG Pipeline (File-Based)

```cmd
python scripts\test_rag_simple.py
```

**What it does**:
1. Loads 4 playbook files from `data/playbooks/`
2. Chunks them into smaller pieces
3. Generates embeddings (OpenAI)
4. Stores in Weaviate Cloud
5. Tests search queries
6. Tests reranking

**Expected Output**:
```
Step 1: Loading playbook files...
✓ Found 4 playbook file(s)

Step 2: Reading file contents...
✓ Successfully loaded 4 playbook(s)

Step 3: Testing text chunking...
✓ Total chunks created: 20

Step 4: Testing embedding generation...
✓ Generated embedding (dimension: 1536)

Step 5: Testing vector store...
✓ Added 20 chunks to vector store

Step 6: Testing vector search...
  Query: 'How to handle stalled sales deals?'
  ✓ Found 2 result(s)

✓ ALL RAG TESTS PASSED!
```

---

## Custom Testing

### Test Your Own Query

Create a file `test_query.py`:

```python
from src.rag.vector_store import vector_store

# Your question
query = "How do I recover a red project?"

# Search
results = vector_store.similarity_search(query, top_k=3)

# Print results
for i, result in enumerate(results, 1):
    print(f"\n{i}. Score: {result['score']:.4f}")
    print(f"   Playbook: {result['metadata']['playbook_id']}")
    print(f"   Category: {result['metadata']['category']}")
    print(f"   Text: {result['document'][:200]}...\n")
```

Run it:
```cmd
python test_query.py
```

---

## Add Your Own Playbooks

### Create a new file:

`data/playbooks/PB-005-your-topic.txt`

**Format**:
```
Title: Your Playbook Title

Category: sales (or delivery, or other)
Success Rate: 80%
Number of Cases: 10

When to Use:
- Situation 1
- Situation 2

Recommended Actions:
1. First action
   - Details here
   - More details

2. Second action
   - Implementation steps

Success Factors:
- What makes this work
- Key metrics

Common Pitfalls:
- What to avoid
- Mistakes to prevent
```

### Test it:

```cmd
python scripts\test_rag_simple.py
```

Your new playbook will be included!

---

## Troubleshooting

### "python not found"

**Solution**:
```cmd
# Check Python installation
python --version
# or
python3 --version

# If not installed: https://www.python.org/downloads/
```

### "pip not found"

**Solution**:
```cmd
python -m pip --version
```

### "Cannot activate venv on PowerShell"

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

### "OpenAI API error"

**Solution**:
```cmd
# Check .env file
type .env | findstr OPENAI_API_KEY

# Verify at: https://platform.openai.com/api-keys
# Check billing: https://platform.openai.com/account/billing
```

### "Weaviate connection failed"

**Solution**:
```cmd
# Check .env file
type .env | findstr WEAVIATE

# Verify cluster: https://console.weaviate.cloud
```

---

## Next Steps

### After Tests Pass:

**Option 1**: Continue with file-based testing
- Add more playbooks
- Test different queries
- Refine your content

**Option 2**: Set up full system (with SQL)
```cmd
docker-compose up -d
python scripts\setup_data.py
streamlit run ui\streamlit_app.py
```

**Option 3**: Test agents directly
```python
# Simple agent test (no SQL needed)
from src.rag.vector_store import vector_store

query = "enterprise deal stalled"
results = vector_store.similarity_search(query, top_k=3)

for r in results:
    print(f"Playbook: {r['metadata']['playbook_id']}")
    print(f"Score: {r['score']:.4f}\n")
```

---

## Summary

### ✅ What's Set Up:

1. **Virtual Environment** - Isolated Python environment
2. **Dependencies** - OpenAI, Weaviate, all libraries
3. **Test Files** - 4 sample playbooks ready
4. **Test Scripts** - 3 test scripts to verify everything

### ✅ What Works Without SQL:

- OpenAI embeddings and LLM
- Weaviate cloud vector storage
- Text chunking
- Similarity search
- Reranking
- Custom queries

### ❌ What Requires SQL:

- Sales opportunities data
- Delivery projects data
- Full dashboard
- Auto-training pipeline

### 💰 Current Costs:

- Testing RAG: ~$0.01 per test run
- Vector storage (Weaviate): ~$0.07/month
- Production usage: ~$90/month (or $1.80 with GPT-3.5)

---

## Quick Reference

```cmd
# Setup (one time)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Test (every time)
python scripts\test_openai_config.py
python scripts\test_weaviate_config.py
python scripts\test_rag_simple.py

# Deactivate when done
deactivate
```

---

**Start Here**:
1. Create venv
2. Install packages
3. Run the 3 test scripts
4. Add your own playbooks
5. Test custom queries

**Everything is file-based - no SQL needed for RAG testing!** 🚀
