# WillGPT Search Quick Reference

One-page reference for all search commands.

---

## Basic Syntax

```bash
python retrieval/search_qdrant.py "query" [FLAGS]
```

---

## All Flags

| Flag | Values | Purpose | Example |
|------|--------|---------|---------|
| `--limit` | `1-100` | Number of results | `--limit 20` |
| `--platform` | `chatgpt`, `claude`, `claude-projects` | Filter by AI platform | `--platform chatgpt` |
| `--interpretations` | (boolean) | Only show results with AI interpretations | `--interpretations` |
| `--metadata-filter` | `key:value` | Filter by metadata field | `--metadata-filter "assistant_model:gpt-4o"` |
| `--api-key` | `string` | Qdrant API key | `--api-key "your-key"` |

---

## Common Examples

### Basic Search
```bash
# Simple query
python retrieval/search_qdrant.py "kubernetes"

# Get 5 best results
python retrieval/search_qdrant.py "docker containers" --limit 5
```

### Platform-Specific
```bash
# ChatGPT only
python retrieval/search_qdrant.py "python tips" --platform chatgpt

# Claude only
python retrieval/search_qdrant.py "system design" --platform claude

# Claude Projects only
python retrieval/search_qdrant.py "documentation" --platform claude-projects
```

### AI Interpretations
```bash
# Find conversations where AI recorded interpretations about you
python retrieval/search_qdrant.py "communication style" --interpretations

# Project contexts with interpretations
python retrieval/search_qdrant.py "preferences" --platform claude-projects --interpretations
```

### Combined Filters
```bash
# Multiple flags together
python retrieval/search_qdrant.py "debugging" --platform chatgpt --limit 10 --interpretations
```

---

## Self-Effacing Pattern Detection

```bash
# Apologies
python retrieval/search_qdrant.py "I apologize" --limit 20
python retrieval/search_qdrant.py "sorry" --limit 30

# Uncertainty
python retrieval/search_qdrant.py "I'm not sure" --limit 25
python retrieval/search_qdrant.py "probably wrong" --limit 20

# Self-doubt
python retrieval/search_qdrant.py "does this make sense" --limit 20
python retrieval/search_qdrant.py "stupid mistake" --limit 15

# Minimizing
python retrieval/search_qdrant.py "just a simple" --limit 15
python retrieval/search_qdrant.py "probably obvious" --limit 15
```

---

## Interactive Mode

```bash
# Start interactive mode
python retrieval/search_qdrant.py

# Commands in interactive mode
/quit                           # Exit
/platform [chatgpt|claude|...]  # Set platform filter
/limit [number]                 # Set result limit
/interpretations                # Toggle interpretations filter
/metadata <key>:<value>         # Set metadata filter
/all                            # Clear all filters
```

---

## Cross-Platform Analysis

```bash
# Compare same query across platforms
python retrieval/search_qdrant.py "authentication" --platform chatgpt --limit 10
python retrieval/search_qdrant.py "authentication" --platform claude --limit 10
python retrieval/search_qdrant.py "authentication" --platform claude-projects --limit 10
```

---

## Score Interpretation

- **> 0.6**: Highly relevant
- **0.4 - 0.6**: Good match
- **< 0.4**: Weak match (try different query)

---

## Tips

1. **Start broad**, then add filters
2. **Use natural language** queries
3. **Try variations** of search terms
4. **Interactive mode** is faster for multiple searches
5. **Combine flags** for precise results

---

## Metadata Fields

Available for `--metadata-filter`:
- `assistant_model` - e.g., "gpt-4o", "claude-3-opus"
- `conversation_id` - Specific conversation UUID
- `user_message_type` - "text", "multimodal_text"
- `has_tool_usage` - "true" or "false"

---

**Full documentation**: See [SEARCH_EXAMPLES.md](SEARCH_EXAMPLES.md)
