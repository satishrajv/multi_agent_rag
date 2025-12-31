# Weaviate Cloud Configuration Guide

## Configuration Summary

Your system is now configured to use **Weaviate Cloud** for vector storage instead of local ChromaDB.

| Setting | Value |
|---------|-------|
| **Vector Store** | Weaviate Cloud |
| **Cluster Name** | wvb-emb |
| **REST Endpoint** | https://wdrd8zyt4ewlcqwk0661w.c0.us-west3.gcp.weaviate.cloud |
| **gRPC Endpoint** | grpc-wdrd8zyt4ewlcqwk0661w.c0.us-west3.gcp.weaviate.cloud |
| **Region** | us-west3 (Google Cloud) |

## What Changed

### 1. Environment Variables (.env)
```bash
VECTOR_STORE_TYPE=weaviate                                  # Changed from 'chromadb'
WEAVIATE_CLUSTER_URL=https://wdrd8zyt4ewlcqwk0...          # Your cluster URL
WEAVIATE_GRPC_URL=grpc-wdrd8zyt4ewlcqwk0...                # gRPC endpoint
WEAVIATE_API_KEY=NlBmR0ZsWVNu...                           # Your API key
WEAVIATE_CLUSTER_NAME=wvb-emb                              # Cluster name
```

### 2. Docker Compose Updated
- ✅ Removed ChromaDB service (no longer needed)
- ✅ Kept PostgreSQL and Redis
- ✅ Vector store now in cloud (managed by Weaviate)

### 3. New Files Created

**src/rag/vector_store_weaviate.py** - Weaviate cloud integration:
- Connects to your Weaviate cloud cluster
- Manages collections (schema)
- Handles embeddings and search
- Compatible with existing code

**scripts/test_weaviate_config.py** - Test script:
- Validates Weaviate connection
- Tests document insertion
- Tests vector search
- Verifies custom vector store class

### 4. Updated Files

**requirements.txt**:
```bash
weaviate-client>=4.4.0  # Added Weaviate Python client
```

**src/config.py**:
- Added Weaviate configuration fields
- Added 'weaviate' to vector_store_type options

**src/rag/vector_store.py**:
- Added factory pattern to switch between ChromaDB and Weaviate
- Auto-selects based on VECTOR_STORE_TYPE

---

## Benefits of Weaviate Cloud

### vs Local ChromaDB

| Feature | Weaviate Cloud | Local ChromaDB |
|---------|----------------|----------------|
| **Deployment** | Cloud-hosted (managed) | Docker container (self-managed) |
| **Scalability** | Auto-scaling | Manual scaling |
| **Reliability** | 99.9% SLA | Depends on host |
| **Backups** | Automated | Manual |
| **Access** | From anywhere | Local only |
| **Cost** | Pay-as-you-go | Infrastructure costs |

### Key Advantages

1. **No Infrastructure Management**
   - No Docker containers to maintain
   - No disk space concerns
   - Automatic backups

2. **Production Ready**
   - High availability
   - Automatic failover
   - Monitoring included

3. **Scalability**
   - Handles millions of vectors
   - Auto-scales based on load
   - No manual configuration

4. **Global Access**
   - Access from any machine
   - Team collaboration
   - Multi-environment support (dev/staging/prod)

---

## How It Works

### Architecture with Weaviate

```
User Query →
  Generate Query Embedding (OpenAI) →
    Search Weaviate Cloud (vector similarity) →
      Retrieve Top-K Documents →
        Rerank Results (local cross-encoder) →
          Return to Agent
```

### Data Flow

1. **Indexing** (Setup):
   ```
   Playbook Text →
     Generate Embedding (OpenAI) →
       Store in Weaviate Cloud (text + vector + metadata)
   ```

2. **Searching** (Runtime):
   ```
   User Query →
     Generate Embedding →
       Weaviate: Find similar vectors →
         Return documents + scores →
           Rerank locally →
             Return top results
   ```

### What's Stored in Weaviate

Each document has:
- **Text**: The playbook content (chunk)
- **Vector**: 1536-dimensional embedding (from OpenAI)
- **Metadata**:
  - playbook_id
  - title
  - category (sales/delivery)
  - success_rate
  - num_cases
  - chunk_id

---

## Testing Your Configuration

### Step 1: Install Weaviate Client

```bash
pip install weaviate-client>=4.4.0
```

### Step 2: Test Connection

```bash
python scripts/test_weaviate_config.py
```

**Expected Output**:
```
==============================================================
Weaviate Cloud Configuration Test
==============================================================

Configuration:
  Vector Store Type: weaviate
  Cluster Name: wvb-emb
  Cluster URL: https://wdrd8zyt4ewlcqwk0...
  API Key: NlBmR0ZsWVNu...

Test 1: Connecting to Weaviate cloud...
✓ Connected to Weaviate cloud successfully
✓ Weaviate cluster is ready

Test 2: Checking collections...
✓ Found 0 collection(s)

Test 3: Creating test collection...
✓ Created test collection: TestCollection

Test 4: Inserting test document...
✓ Inserted test document
  Embedding dimension: 1536

Test 5: Testing vector search...
✓ Search successful
  Similarity: 0.9245

Test 6: Testing custom Weaviate vector store...
✓ Custom vector store works

==============================================================
✓ All tests passed! Weaviate configuration is working.
==============================================================
```

---

## Quick Start

### 1. Test Configuration

```bash
# Test Weaviate connection
python scripts/test_weaviate_config.py

# Test OpenAI + Weaviate together
python scripts/test_openai_config.py
```

### 2. Start Local Services

```bash
# Only PostgreSQL and Redis now (no ChromaDB)
docker-compose up -d
```

### 3. Initialize System

```bash
# Generate data
python scripts/setup_data.py

# Initialize Weaviate with playbooks
python scripts/initialize_vector_store.py
```

This will:
- Create "Playbooks" collection in Weaviate
- Generate embeddings with OpenAI
- Upload ~50-100 chunks to Weaviate cloud

### 4. Launch Dashboard

```bash
streamlit run ui/streamlit_app.py
```

---

## Weaviate Dashboard

Access your Weaviate cloud dashboard:
- **URL**: https://console.weaviate.cloud
- **Cluster**: wvb-emb
- **Features**:
  - View collections
  - Monitor queries
  - Check usage
  - Manage backups
  - View logs

---

## Usage & Costs

### Weaviate Cloud Pricing

**Free Tier** (Sandbox):
- 1 cluster
- Limited storage
- Good for development/testing

**Serverless** (Pay-as-you-go):
- $0.095 per 1M vector dimensions stored/month
- $0.040 per 1M vector dimensions read

**Example Cost** (100 playbooks × 1536 dimensions):
- Storage: ~0.15M dimensions = **$0.014/month**
- Queries (1000/day): ~1.5M reads = **$0.06/month**
- **Total**: ~**$0.07/month** (extremely low!)

**Serverless Deployment** (Production):
- Starts at $25/month
- Includes SLA, backups, support
- Auto-scaling

### Cost Comparison

| Service | Monthly Cost |
|---------|-------------|
| Weaviate Cloud (development) | ~$0.07 |
| OpenAI Embeddings | ~$0.03 |
| OpenAI GPT-4 (100 req/day) | ~$90 |
| **Total** | **~$90/month** |

**Note**: Vector storage is extremely cheap compared to LLM API calls!

---

## Switching Between Vector Stores

### Back to ChromaDB (Local)

Edit `.env`:
```bash
VECTOR_STORE_TYPE=chromadb
```

Restart:
```bash
docker-compose up -d
python scripts/initialize_vector_store.py  # Re-index locally
```

### To Weaviate Cloud

Edit `.env`:
```bash
VECTOR_STORE_TYPE=weaviate
```

No restart needed! Just re-initialize:
```bash
python scripts/initialize_vector_store.py
```

---

## Troubleshooting

### Error: "Connection refused"

**Solution**:
1. Check cluster URL is correct in `.env`
2. Verify cluster is running in Weaviate console
3. Check API key is valid

```bash
# Test connection
curl https://wdrd8zyt4ewlcqwk0661w.c0.us-west3.gcp.weaviate.cloud/v1/.well-known/ready
```

### Error: "Authentication failed"

**Solution**:
1. Check API key in `.env` (no extra spaces)
2. Regenerate API key in Weaviate console if needed
3. Verify key has correct permissions

### Error: "Collection not found"

**Solution**:
```bash
# Re-initialize vector store
python scripts/initialize_vector_store.py
```

### Slow queries

**Solution**:
1. Check cluster region (should be close to you)
2. Reduce TOP_K_RETRIEVAL in `.env`
3. Upgrade to serverless deployment for better performance

### High costs

**Solution**:
1. Weaviate costs are minimal (~$0.07/month)
2. Main cost is OpenAI API (~$90/month for GPT-4)
3. Switch to GPT-3.5-Turbo to reduce LLM costs

---

## Advanced Configuration

### Using Weaviate's Built-in Vectorizer

Weaviate can generate embeddings automatically. To use this:

1. Edit `src/rag/vector_store_weaviate.py`:
```python
# Change vectorizer config
vectorizer_config=Configure.Vectorizer.text2vec_openai(
    model="text-embedding-3-small"
)
```

2. Weaviate will call OpenAI directly (no local embedding generation)

**Pros**: Simpler code, less local processing
**Cons**: Weaviate needs your OpenAI key, slightly higher latency

### Multi-tenancy

Create separate collections for different teams/projects:

```python
sales_store = WeaviateVectorStore(collection_name="SalesPlaybooks")
delivery_store = WeaviateVectorStore(collection_name="DeliveryPlaybooks")
```

### Hybrid Search in Weaviate

Weaviate supports built-in hybrid search (BM25 + vector):

```python
# Use Weaviate's hybrid search
response = collection.query.hybrid(
    query="multi-threading strategy",
    alpha=0.7,  # 0.7 = 70% vector, 30% BM25
    limit=5
)
```

---

## Security Best Practices

### API Key Management

1. **Never commit API keys to Git**
   - Already in `.gitignore` ✅
   - Use environment variables

2. **Rotate keys regularly**
   - Generate new keys in Weaviate console
   - Update `.env` file
   - Revoke old keys

3. **Use read-only keys for clients**
   - Create separate keys for different environments
   - Limit permissions where possible

### Network Security

1. **HTTPS only**
   - All connections encrypted ✅
   - TLS 1.3 supported

2. **IP Allowlisting** (Enterprise)
   - Restrict access by IP
   - Available in paid plans

### Data Privacy

1. **Regional deployment**
   - Your cluster is in us-west3 (GCP)
   - Choose region based on data residency requirements

2. **Encryption at rest**
   - Enabled by default ✅
   - AES-256 encryption

---

## Monitoring & Maintenance

### Check Cluster Status

```python
import weaviate

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://wdrd8zyt4ewlcqwk0...",
    auth_credentials=weaviate.auth.AuthApiKey("your-key")
)

if client.is_ready():
    print("Cluster is healthy")

# Get collection stats
collection = client.collections.get("Playbooks")
count = collection.aggregate.over_all(total_count=True).total_count
print(f"Documents: {count}")

client.close()
```

### View Logs

1. Go to: https://console.weaviate.cloud
2. Select your cluster
3. Click "Logs" tab
4. Filter by level (error, warn, info)

### Backups

**Automatic** (Weaviate Cloud):
- Daily backups (retained 7 days)
- Point-in-time recovery
- No configuration needed

**Manual** (if needed):
```python
# Export all data
client.backup.create(
    backup_id="manual_backup_20250129",
    backend="gcs",  # or "s3"
    include_collections=["Playbooks"]
)
```

---

## Summary

### What You Have Now

✅ **Weaviate Cloud**: Production-ready vector database
✅ **OpenAI Embeddings**: High-quality text-embedding-3-small
✅ **No Local Vector DB**: No Docker container to manage
✅ **Global Access**: Vector store accessible from anywhere
✅ **Auto-scaling**: Handles growth automatically

### Next Steps

1. **Test Configuration**:
   ```bash
   python scripts/test_weaviate_config.py
   ```

2. **Initialize System**:
   ```bash
   docker-compose up -d  # PostgreSQL + Redis only
   python scripts/setup_data.py
   python scripts/initialize_vector_store.py
   ```

3. **Launch Dashboard**:
   ```bash
   streamlit run ui/streamlit_app.py
   ```

4. **Monitor Usage**:
   - Check Weaviate console: https://console.weaviate.cloud
   - Check OpenAI usage: https://platform.openai.com/usage

---

## Support

### Weaviate Resources
- Documentation: https://weaviate.io/developers/weaviate
- Console: https://console.weaviate.cloud
- Python Client: https://weaviate.io/developers/weaviate/client-libraries/python
- Community: https://forum.weaviate.io

### Project Documentation
- Main README: `README.md`
- OpenAI Setup: `OPENAI_SETUP.md`
- Quick Start: `QUICKSTART.md`

---

**Status**: ✅ Weaviate Cloud Configuration Complete

Your system now uses Weaviate Cloud for vector storage with OpenAI embeddings!

Run the test script to verify:
```bash
python scripts/test_weaviate_config.py
```
