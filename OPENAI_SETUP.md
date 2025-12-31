# OpenAI API Configuration Guide

## Configuration Summary

Your system is now configured to use **OpenAI API** with the following settings:

| Setting | Value |
|---------|-------|
| **LLM Provider** | OpenAI |
| **LLM Model** | gpt-4 |
| **Embedding Model** | text-embedding-3-small |
| **Embedding Dimension** | 1536 |

## What Changed

### 1. Environment Variables (.env)
```bash
LLM_PROVIDER=openai                    # Changed from 'ollama' to 'openai'
LLM_MODEL=gpt-4                        # Using GPT-4 (GPT-5 nano not available yet)
OPENAI_API_KEY=sk-proj-...            # Your API key configured
EMBEDDING_MODEL=text-embedding-3-small # Using OpenAI embeddings
EMBEDDING_DIMENSION=1536               # OpenAI's embedding dimension
```

### 2. Embedding Generator Updated
The `src/rag/embedding.py` module now:
- ✅ Detects OpenAI embedding models automatically
- ✅ Uses OpenAI Embeddings API for `text-embedding-*` models
- ✅ Falls back to sentence-transformers for other models
- ✅ Supports batch embedding with OpenAI

## Important Notes

### GPT-5 Nano Availability
⚠️ **Note**: As of now, "GPT-5 nano" is not a publicly available model. I've configured the system to use **GPT-4** instead, which is the latest widely available model.

If GPT-5 becomes available, simply update the `.env` file:
```bash
LLM_MODEL=gpt-5-nano  # or whatever the official name is
```

### Available OpenAI Models

**LLM Models** (for text generation):
- `gpt-4` - Most capable, higher cost
- `gpt-4-turbo` - Faster GPT-4 variant
- `gpt-3.5-turbo` - Fast, cost-effective
- `gpt-4o` - Latest optimized model

**Embedding Models**:
- `text-embedding-3-small` - 1536 dimensions (recommended) ✅ **Currently configured**
- `text-embedding-3-large` - 3072 dimensions (higher quality)
- `text-embedding-ada-002` - 1536 dimensions (previous generation)

## Testing Your Configuration

Run the test script to verify everything works:

```bash
python scripts/test_openai_config.py
```

This will test:
1. ✅ OpenAI client initialization
2. ✅ Embedding generation
3. ✅ LLM chat completion
4. ✅ Custom embedding generator
5. ✅ Custom LLM client

## Expected Output

```
==============================================================
OpenAI Configuration Test
==============================================================

Configuration:
  LLM Provider: openai
  LLM Model: gpt-4
  Embedding Model: text-embedding-3-small
  Embedding Dimension: 1536
  API Key: sk-proj-UiQxGLb6pMvL...PQiIA

Test 1: Initializing OpenAI client...
✓ Client initialized successfully

Test 2: Testing embedding generation...
✓ Embedding generated successfully
  Embedding dimension: 1536
  Expected dimension: 1536
✓ Dimension matches configuration

Test 3: Testing LLM chat completion...
✓ LLM response received
  Response: Configuration test successful!

Test 4: Testing custom embedding generator...
✓ Custom embedding generator works
  Generated embedding dimension: 1536

Test 5: Testing custom LLM client...
✓ Custom LLM client works
  Response: 4

==============================================================
✓ All tests passed! OpenAI configuration is working.
==============================================================
```

## Cost Estimates

### Per 1000 Requests (Approximate)

**GPT-4**:
- Input: $0.03 per 1K tokens
- Output: $0.06 per 1K tokens
- Average request (~500 tokens in, ~300 out): **~$0.03 per request**
- 100 requests/day: ~**$3/day** or **$90/month**

**GPT-3.5-Turbo** (Cost-Effective Alternative):
- Input: $0.0005 per 1K tokens
- Output: $0.0015 per 1K tokens
- Average request: **~$0.0006 per request**
- 100 requests/day: ~**$0.06/day** or **$1.80/month**

**Embeddings (text-embedding-3-small)**:
- $0.00002 per 1K tokens
- 100 documents/day (avg 500 tokens each): **~$0.001/day** or **$0.03/month**

### Optimization Tips

1. **Use GPT-3.5-Turbo for development/testing**:
   ```bash
   LLM_MODEL=gpt-3.5-turbo
   ```

2. **Cache results** (already implemented):
   - Redis caching reduces duplicate API calls
   - Semantic caching for similar queries

3. **Batch embeddings** (already implemented):
   - System batches multiple texts in single API call

4. **Monitor usage**:
   - Check OpenAI dashboard: https://platform.openai.com/usage

## Switching Between Models

### To Use GPT-3.5-Turbo (Cheaper)

Edit `.env`:
```bash
LLM_MODEL=gpt-3.5-turbo
```

### To Use Local Ollama (Free)

Edit `.env`:
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

Then restart services.

## Troubleshooting

### Error: "Invalid API Key"
- Check your API key in `.env` file
- Verify key is active at: https://platform.openai.com/api-keys
- Ensure no extra spaces in the key

### Error: "Model not found"
- Update `LLM_MODEL` to a valid model (e.g., `gpt-4` or `gpt-3.5-turbo`)
- Check available models at: https://platform.openai.com/docs/models

### Error: "Rate limit exceeded"
- You've hit OpenAI's rate limits
- Wait a few minutes or upgrade your plan
- Reduce request frequency

### Error: "Insufficient quota"
- Add credits to your OpenAI account
- Check billing at: https://platform.openai.com/account/billing

### High API Costs
- Switch to `gpt-3.5-turbo` for development
- Reduce `TOP_K_RETRIEVAL` in `.env` (fewer playbooks retrieved)
- Increase cache TTL for longer caching

## Current Configuration Files

### .env (Active Configuration)
```bash
# Located at: multi_agent_rag/.env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

### Modified Files
1. ✅ `.env` - Updated with your API key and OpenAI settings
2. ✅ `src/rag/embedding.py` - Added OpenAI embedding support
3. ✅ `src/utils/llm_client.py` - Already supports OpenAI (via LangChain)

## Next Steps

1. **Test Configuration**:
   ```bash
   python scripts/test_openai_config.py
   ```

2. **Run Setup** (if not already done):
   ```bash
   python scripts/setup_system.py
   ```

3. **Launch Dashboard**:
   ```bash
   streamlit run ui/streamlit_app.py
   ```

4. **Try an Analysis**:
   - Sales Agent tab → Enter `OPP-2024-001`
   - Watch OpenAI generate recommendations!

## API Key Security

⚠️ **Important Security Notes**:

1. **Never commit .env to Git**:
   - Already in `.gitignore` ✅
   - Never share publicly

2. **Rotate keys regularly**:
   - Generate new keys at: https://platform.openai.com/api-keys
   - Revoke old keys

3. **Monitor usage**:
   - Set spending limits in OpenAI dashboard
   - Enable email alerts

4. **Use environment-specific keys**:
   - Different keys for dev/staging/production
   - Restrict key permissions if possible

## Support

### OpenAI Resources
- API Documentation: https://platform.openai.com/docs
- API Keys: https://platform.openai.com/api-keys
- Usage Dashboard: https://platform.openai.com/usage
- Pricing: https://openai.com/pricing
- Rate Limits: https://platform.openai.com/account/rate-limits

### Project Documentation
- Main README: `README.md`
- Quick Start: `QUICKSTART.md`
- Troubleshooting: See README.md → Troubleshooting section

---

**Status**: ✅ OpenAI Configuration Complete

Your system is now configured to use OpenAI's GPT-4 for text generation and text-embedding-3-small for embeddings!

Run the test script to verify everything works:
```bash
python scripts/test_openai_config.py
```
