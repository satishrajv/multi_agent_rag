# RAG Chunking Strategy - Complete Guide

## Overview

Your system uses **RecursiveCharacterTextSplitter** to break playbooks into optimal chunks for storage in Weaviate.

---

## Current Configuration

From `.env`:
```bash
CHUNK_SIZE=500          # Maximum characters per chunk
CHUNK_OVERLAP=50        # Overlap between chunks (preserves context)
```

---

## How Chunking Works

### **Input: Full Playbook Document**

```
Title: Multi-threading Strategy for Stalled Sales

Category: sales
Success Rate: 78%
Number of Cases: 11

When to Use:
- Sales opportunities stalled in Proposal stage
- Single-threaded engagement (only 1 contact)
- Deal value > $500K
- No activity in 7+ days

Recommended Actions:
1. Identify the decision-making unit (DMU)
   - CFO (budget holder)
   - CTO (technical decision maker)
   - Risk Lead (compliance/security)
   - Business Owner (champion)

2. Research each stakeholder on LinkedIn
   - Review their posts and interests
   - Identify their key priorities
   - Find common connections

3. Send personalized outreach to each stakeholder
   - Tailor message to their role
   - Highlight their specific concerns
   - Provide relevant case studies
...
[Total: ~1,800 characters]
```

---

### **Output: 4 Chunks with Overlap**

The chunker splits this into **4 chunks** (500 chars each, 50 char overlap):

---

#### **Chunk 0** (Characters 0-500)

```
Title: Multi-threading Strategy for Stalled Sales

Category: sales
Success Rate: 78%
Number of Cases: 11

When to Use:
- Sales opportunities stalled in Proposal stage
- Single-threaded engagement (only 1 contact)
- Deal value > $500K
- No activity in 7+ days

Recommended Actions:
1. Identify the decision-making unit (DMU)
   - CFO (budget holder)
   - CTO (technical decision maker)
   - Risk Lead (compliance/security)
   - Business Owner (champion)

2. Research each stakeholder on LinkedIn
   - Review their posts and interests
```

**Metadata stored with chunk:**
```json
{
  "playbook_id": "PB-001",
  "title": "Multi-threading Strategy for Stalled Sales",
  "category": "sales",
  "success_rate": 0.78,
  "num_cases": 11,
  "chunk_id": 0
}
```

---

#### **Chunk 1** (Characters 450-950) - Note 50 char overlap

```
   - Review their posts and interests    ← Overlap with Chunk 0
   - Identify their key priorities
   - Find common connections

3. Send personalized outreach to each stakeholder
   - Tailor message to their role
   - Highlight their specific concerns
   - Provide relevant case studies

4. Schedule multi-party discovery call within 5 business days
   - Include all key stakeholders
   - Prepare customized agenda
   - Assign roles to your team

5. Create stakeholder engagement map
   - Track interactions with each person
```

**Metadata stored with chunk:**
```json
{
  "playbook_id": "PB-001",
  "title": "Multi-threading Strategy for Stalled Sales",
  "category": "sales",
  "success_rate": 0.78,
  "num_cases": 11,
  "chunk_id": 1
}
```

---

#### **Chunk 2** (Characters 900-1400) - Note 50 char overlap

```
   - Track interactions with each person    ← Overlap with Chunk 1
   - Monitor relationship strength
   - Identify gaps in coverage

Success Factors:
- Engaging 3+ stakeholders increases win rate by 35%
- CFO involvement is critical in deals over $1M
- Technical champions need executive sponsorship
- Multi-threading reduces risk of single-point failure

Common Pitfalls to Avoid:
- Sending generic emails to all stakeholders
- Not researching individual priorities beforehand
- Skipping the CTO in technical deals
```

**Metadata stored with chunk:**
```json
{
  "playbook_id": "PB-001",
  "title": "Multi-threading Strategy for Stalled Sales",
  "category": "sales",
  "success_rate": 0.78,
  "num_cases": 11,
  "chunk_id": 2
}
```

---

#### **Chunk 3** (Characters 1350-1800) - Note 50 char overlap

```
- Skipping the CTO in technical deals    ← Overlap with Chunk 2
- Relying solely on one champion
- Not documenting stakeholder engagement

Expected Timeline:
- Research phase: 1-2 days
- Outreach: 2-3 days
- First multi-party call: Within 1 week
- Follow-up cadence: Every 3-4 days

Metrics to Track:
- Number of stakeholders engaged
- Response rate to outreach
- Time to first multi-party meeting
- Win rate improvement
```

**Metadata stored with chunk:**
```json
{
  "playbook_id": "PB-001",
  "title": "Multi-threading Strategy for Stalled Sales",
  "category": "sales",
  "success_rate": 0.78,
  "num_cases": 11,
  "chunk_id": 3
}
```

---

## Why This Chunking Strategy Works

### **1. Chunk Size: 500 Characters**

**Why 500?**
- ✅ Small enough to be semantically focused
- ✅ Large enough to contain complete thoughts
- ✅ Fits within embedding model context (1536 dimensions handles this well)
- ✅ Retrieves precise sections (not entire document)

**Too Small (100 chars):**
```
❌ "Title: Multi-threading Strategy for Stalled Sales

Category: sales
Success Rate: 78%"
```
- Not enough context
- Fragments sentences
- More chunks = slower retrieval

**Too Large (2000 chars):**
```
❌ [Entire playbook in 1 chunk]
```
- Too much irrelevant info
- LLM gets confused with too much context
- Loses precision in retrieval

---

### **2. Chunk Overlap: 50 Characters**

**Why overlap?**

Without overlap:
```
Chunk 0: "...Research each stakeholder on LinkedIn"
Chunk 1: "3. Send personalized outreach..."
                ↑ Context lost! User doesn't know what "outreach" refers to
```

With 50-char overlap:
```
Chunk 0: "...Research each stakeholder on LinkedIn
          - Review their posts and interests"
                                    ↓
Chunk 1: "- Review their posts and interests    ← Preserved context!
          - Identify their key priorities
          3. Send personalized outreach..."
```

**Benefits:**
- ✅ Preserves context across chunk boundaries
- ✅ Sentences aren't cut mid-thought
- ✅ Better semantic understanding
- ✅ More accurate retrieval

---

### **3. Recursive Separators**

The splitter tries to break on natural boundaries:

```python
separators=["\n\n", "\n", ". ", " ", ""]
```

**Priority order:**
1. **`\n\n`** (double newline) - Paragraph breaks ← Best
2. **`\n`** (single newline) - Line breaks
3. **`. `** (sentence end) - Sentence boundaries
4. **` `** (space) - Word boundaries
5. **`""`** (character) - Last resort

**Example:**

```
Chunk reaching 500 chars at position: "...CFO involvement is critical|in deals over $1M..."
                                                    ↑ char 500

Separator priority:
1. Look back for "\n\n" → Found at char 485 ✓ Break here!
   Result: Clean paragraph break

If no "\n\n" found:
2. Look back for "\n" → Break at line
3. Look back for ". " → Break at sentence
4. Look back for " " → Break at word
5. Break at char 500 (worst case)
```

**Result:** Clean, meaningful chunks!

---

## Storage in Weaviate

### **Each Chunk Becomes a Vector**

```python
# Chunk 0 processing:
text = "Title: Multi-threading Strategy... [500 chars]"

# 1. Generate embedding
embedding = openai.embeddings.create(
    model="text-embedding-3-small",
    input=text
)
# Returns: [0.023, -0.041, 0.089, ..., 0.012]  (1536 dimensions)

# 2. Store in Weaviate
weaviate.add_object(
    class_name="Playbook",
    properties={
        "text": text,
        "playbook_id": "PB-001",
        "title": "Multi-threading Strategy",
        "category": "sales",
        "success_rate": 0.78,
        "num_cases": 11,
        "chunk_id": 0
    },
    vector=embedding
)
```

### **Weaviate Schema**

```
Collection: Playbooks
├── Vector: [1536 dimensions]
└── Properties:
    ├── text (string) - The actual chunk text
    ├── playbook_id (string) - "PB-001"
    ├── title (string) - "Multi-threading Strategy"
    ├── category (string) - "sales" or "delivery"
    ├── success_rate (number) - 0.78
    ├── num_cases (number) - 11
    └── chunk_id (number) - 0, 1, 2, 3...
```

---

## Retrieval Flow

### **User Query:**
```
"How to handle stalled deal with only one contact?"
```

### **Step 1: Query Embedding**
```python
query_embedding = openai.embeddings.create(
    model="text-embedding-3-small",
    input="How to handle stalled deal with only one contact?"
)
# Returns: [0.019, -0.038, 0.091, ..., 0.015]
```

### **Step 2: Vector Search in Weaviate**
```python
results = weaviate.query.near_vector(
    vector=query_embedding,
    limit=5
)
```

**Weaviate compares:**
```
Query vector:     [0.019, -0.038, 0.091, ..., 0.015]
                         ↓ Cosine Similarity
Chunk 0 (PB-001): [0.023, -0.041, 0.089, ..., 0.012] → 0.92 ✓ Very similar!
Chunk 1 (PB-001): [0.015, -0.025, 0.078, ..., 0.010] → 0.87 ✓ Similar
Chunk 0 (PB-002): [0.030, -0.050, 0.095, ..., 0.018] → 0.81 ✓ Somewhat similar
Chunk 2 (PB-003): [0.005, -0.010, 0.020, ..., 0.003] → 0.45 ✗ Not similar
```

### **Step 3: Return Top Results**
```json
[
  {
    "text": "Title: Multi-threading Strategy... When to Use: stalled... single-threaded engagement...",
    "playbook_id": "PB-001",
    "similarity": 0.92,
    "chunk_id": 0
  },
  {
    "text": "...Identify the decision-making unit (DMU)... CFO, CTO, Risk Lead...",
    "playbook_id": "PB-001",
    "similarity": 0.87,
    "chunk_id": 1
  }
]
```

---

## Hybrid Search (Dense + Sparse)

Your system combines **2 search methods**:

### **1. Dense Vector Search (70% weight)**
```
Query: "stalled deal one contact"
Embedding: [0.019, -0.038, 0.091, ...]
Finds: Semantically similar chunks (understands meaning)
```

### **2. BM25 Sparse Search (30% weight)**
```
Query: "stalled deal one contact"
Keywords: ["stalled", "deal", "one", "contact"]
Finds: Keyword matches (exact term overlap)
```

### **Combined Results:**
```python
# Dense search results:
dense_results = [
  {"chunk_id": "PB-001-0", "score": 0.92},
  {"chunk_id": "PB-002-1", "score": 0.85}
]

# Sparse search results:
sparse_results = [
  {"chunk_id": "PB-001-0", "score": 0.88},  # "stalled" mentioned 3x
  {"chunk_id": "PB-001-1", "score": 0.75}   # "contact" mentioned 2x
]

# Hybrid combination (70% dense + 30% sparse):
final_scores = {
  "PB-001-0": 0.92 * 0.7 + 0.88 * 0.3 = 0.908 ← Top result!
  "PB-002-1": 0.85 * 0.7 + 0.00 * 0.3 = 0.595
  "PB-001-1": 0.00 * 0.7 + 0.75 * 0.3 = 0.225
}
```

---

## Reranking (Final Step)

After hybrid search, **cross-encoder reranks** top 5 results:

```python
# Top 5 from hybrid search
candidates = [
  {"text": "...", "score": 0.908},
  {"text": "...", "score": 0.595},
  {"text": "...", "score": 0.225},
  {"text": "...", "score": 0.189},
  {"text": "...", "score": 0.145}
]

# Cross-encoder re-scores (query + document pairs)
reranked = cross_encoder.rerank(
    query="How to handle stalled deal with only one contact?",
    documents=candidates
)

# New scores (more accurate):
reranked_results = [
  {"text": "...", "score": 0.95},  # PB-001-0 (improved!)
  {"text": "...", "score": 0.72},  # PB-001-1
  {"text": "...", "score": 0.51},  # PB-002-1 (dropped)
]
```

**Why rerank?**
- Cross-encoders see query + document together (more context)
- Bi-encoders (embeddings) see them separately (less context)
- Reranking corrects false positives from initial retrieval

---

## Alternative Chunking Strategies

### **Option 1: Semantic Chunking** (NOT currently used)

Break on semantic boundaries (sections):

```
Chunk 0: Title + Category + When to Use
Chunk 1: Recommended Actions 1-3
Chunk 2: Recommended Actions 4-5
Chunk 3: Success Factors + Pitfalls
Chunk 4: Timeline + Metrics
```

**Pros:**
- Complete logical sections
- Better context preservation

**Cons:**
- Variable chunk sizes (50-800 chars)
- Some chunks too large, some too small
- More complex to implement

---

### **Option 2: Fixed Chunking** (NOT recommended)

Break every 500 chars exactly:

```
Chunk 0: chars 0-500
Chunk 1: chars 500-1000
Chunk 2: chars 1000-1500
```

**Pros:**
- Simple, predictable

**Cons:**
- ❌ Breaks mid-sentence
- ❌ No context preservation
- ❌ Poor retrieval quality

---

### **Option 3: Sentence-Level Chunking**

Break on sentences, combine until 500 chars:

```
Chunk 0: [Sentence 1] + [Sentence 2] + [Sentence 3] = 480 chars
Chunk 1: [Sentence 4] + [Sentence 5] = 510 chars
```

**Pros:**
- Clean sentence boundaries

**Cons:**
- Some chunks too short
- Sentences can be very long (>500 chars)

---

## Current Strategy: Best for Your Use Case ✅

**RecursiveCharacterTextSplitter with 500/50** is optimal because:

1. ✅ **Playbooks are structured** (clear sections)
2. ✅ **Moderate length** (~1,800 chars) → 3-4 chunks
3. ✅ **Complete thoughts** (overlap preserves context)
4. ✅ **Fast retrieval** (not too many chunks)
5. ✅ **Good precision** (retrieves relevant sections, not entire doc)
6. ✅ **Works with LLM context** (GPT-4 gets focused, relevant info)

---

## Example: Full Retrieval Flow

```
User: "My $2M deal has been stuck for 3 weeks with 1 contact"
         ↓
1. Generate query embedding: [0.019, -0.038, 0.091, ...]
         ↓
2. Hybrid search (dense 70% + sparse 30%)
   → Finds: PB-001-0 (score: 0.908)
         ↓
3. Rerank with cross-encoder
   → Top result: PB-001-0 (score: 0.95)
         ↓
4. Retrieve chunk:
   "Title: Multi-threading Strategy for Stalled Sales

    When to Use:
    - Sales opportunities stalled in Proposal stage
    - Single-threaded engagement (only 1 contact)
    - Deal value > $500K
    - No activity in 7+ days

    Recommended Actions:
    1. Identify the decision-making unit (DMU)
       - CFO (budget holder)
       - CTO (technical decision maker)..."
         ↓
5. Feed to GPT-4:
   Context: [Opportunity data] + [Chunk text]
   Generate: Personalized recommendations
```

---

## Configuration Tuning

### **Current Settings:**
```bash
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### **When to Adjust:**

**Increase CHUNK_SIZE to 800** if:
- Playbooks are longer (3000+ chars)
- LLM needs more context per retrieval
- Want fewer chunks (faster search)

**Decrease CHUNK_SIZE to 300** if:
- Want more precise retrieval
- Playbooks have many short sections
- LLM gets confused with too much context

**Increase OVERLAP to 100** if:
- Context frequently lost at boundaries
- Sentences/paragraphs break awkwardly

**Decrease OVERLAP to 20** if:
- Chunks are duplicating too much
- Storage cost is concern

---

## Summary

✅ **Your current chunking strategy is excellent for playbook RAG:**

| Setting | Value | Why |
|---------|-------|-----|
| **Chunk Size** | 500 chars | Focused sections, complete thoughts |
| **Overlap** | 50 chars | Preserves context, smooth boundaries |
| **Separators** | `\n\n`, `\n`, `. ` | Natural breaks (paragraphs, sentences) |
| **Result** | 3-4 chunks per playbook | Fast retrieval, good precision |

**No changes needed** - this is production-ready! 🚀
