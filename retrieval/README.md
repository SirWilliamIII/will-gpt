# WillGPT Retrieval System

Hybrid search for your AI conversations using BGE-M3 embeddings and Qdrant.

## Setup

```bash
# Install dependencies (if not already installed)
pip install qdrant-client sentence-transformers torch tqdm python-dotenv

# Create .env file in project root with:
# QDRANT_API_KEY='your-api-key-here'
# QDRANT_COLLECTION_NAME='will-gpt'
```

The scripts automatically load credentials from `.env` file.

## Upload Conversations to Qdrant

```bash
# Upload with default settings (balanced mode, ~400 tokens avg)
python retrieval/upload_to_qdrant.py

# Upload with specific embedding mode
python retrieval/upload_to_qdrant.py --embedding-mode user_focused

# Upload with custom collection name
python retrieval/upload_to_qdrant.py --collection-name my-conversations
```

**Embedding Modes:**
- `balanced` (default): User + truncated assistant + interpretations (~400 tokens)
- `user_focused`: User message + AI interpretations only (~117 tokens)
- `minimal`: User message only (~61 tokens)
- `full`: Everything including full responses (~410 tokens)

**Expected Upload Time:**
- 13,139 chunks with BGE-M3 embeddings
- On M4 Mac (MPS): ~10-15 minutes
- On CPU: ~30-45 minutes
- On GPU: ~5-10 minutes

## Search

### Interactive Mode (Recommended)

```bash
python retrieval/search_qdrant.py
```

**Commands:**
```
🔍 Query: self-effacing patterns
🔍 Query: /platform chatgpt
🔍 Query: /limit 5
🔍 Query: /interpretations
🔍 Query: programming challenges
🔍 Query: /all
🔍 Query: /quit
```

### Single Query Mode

```bash
# Basic search
python retrieval/search_qdrant.py "self-effacing behavior"

# Search with filters
python retrieval/search_qdrant.py "programming mistakes" --limit 5 --interpretations

# Platform-specific search
python retrieval/search_qdrant.py "customer engineering" --platform chatgpt
```

## Architecture

```
Conversations → BGE-M3 → Qdrant
                ├─ Dense vectors (1024 dims, semantic similarity)
                └─ Sparse vectors (lexical/keyword matching)
```

### What Gets Stored

Each conversation chunk in Qdrant contains:

**Vectors:**
- Dense embedding (1024 dims from BGE-M3)
- Sparse embedding (lexical matching, future enhancement)

**Payload:**
```python
{
    "conversation_id": "...",
    "platform": "chatgpt",
    "timestamp": "2025-10-27T12:06:28",
    "conversation_title": "Clean ~/.ssh folder",
    "turn_number": 5,

    # Content
    "user_message": "...",
    "assistant_message": "...",
    "assistant_model": "gpt-4o",

    # AI Interpretations
    "has_interpretations": true,
    "about_user": "Preferred name: don't do it in a negative tone...",
    "about_model": "consistency -- sometimes...",

    # Metadata
    "system_context": {...},
    "has_tool_usage": true,
    "tool_count": 3
}
```

## Example Queries

**Finding Self-Effacing Patterns:**
```bash
python retrieval/search_qdrant.py "I probably made a mistake"
python retrieval/search_qdrant.py "not sure if this is the right approach"
python retrieval/search_qdrant.py "stupid error" --interpretations
```

**Topic-Based:**
```bash
python retrieval/search_qdrant.py "kubernetes deployment issues"
python retrieval/search_qdrant.py "SSH key management"
```

**AI Interpretation Analysis:**
```bash
python retrieval/search_qdrant.py "customer engineering" --interpretations
```

## Performance

**Collection Stats:**
- Total points: 13,139
- Vector size: 1024 (BGE-M3)
- Average embedding size: ~400 tokens (balanced mode)
- Storage: ~150MB (vectors + payloads)

**Search Speed:**
- Query encoding: ~50ms (M4 Mac)
- Qdrant search: ~10-50ms
- Total: ~100ms per query

## Next Steps

1. **Upload your conversations**:
   ```bash
   python retrieval/upload_to_qdrant.py
   ```

2. **Try some searches**:
   ```bash
   python retrieval/search_qdrant.py
   ```

3. **Add Claude data** when you get fresh exports

4. **Build web interface** (FastAPI + React) for Phase 4

5. **Implement cross-platform comparison** queries
