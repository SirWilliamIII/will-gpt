# WillGPT Search Examples

Comprehensive guide to searching your conversation history across ChatGPT, Claude, and Claude Projects.

## Table of Contents
- [Basic Search](#basic-search)
- [Limit Results](#limit-results)
- [Platform Filtering](#platform-filtering)
- [AI Interpretations](#ai-interpretations)
- [Metadata Filtering](#metadata-filtering)
- [Combined Filters](#combined-filters)
- [Interactive Mode](#interactive-mode)
- [Self-Effacing Pattern Detection](#self-effacing-pattern-detection)
- [Cross-Platform Analysis](#cross-platform-analysis)

---

## Basic Search

Search across all platforms without filters:

```bash
# Simple query
python retrieval/search_qdrant.py "kubernetes deployment"

# Multi-word query
python retrieval/search_qdrant.py "how to debug python errors"

# Technical concepts
python retrieval/search_qdrant.py "docker containers"
python retrieval/search_qdrant.py "neural networks"
python retrieval/search_qdrant.py "database optimization"

# Programming questions
python retrieval/search_qdrant.py "async await pattern"
python retrieval/search_qdrant.py "memory leak debugging"
```

---

## Limit Results

Control the number of search results with `--limit`:

```bash
# Get top 5 results (default is 10)
python retrieval/search_qdrant.py "authentication" --limit 5

# Get just the single best match
python retrieval/search_qdrant.py "SSH keys" --limit 1

# Get more comprehensive results
python retrieval/search_qdrant.py "machine learning" --limit 20

# Quick scan with minimal results
python retrieval/search_qdrant.py "git workflow" --limit 3
```

**Use Cases**:
- `--limit 1`: Quick lookup for best match
- `--limit 5`: Standard search
- `--limit 20`: Deep dive into topic
- `--limit 50`: Comprehensive analysis

---

## Platform Filtering

Search within specific AI platforms using `--platform`:

### ChatGPT Only

```bash
# ChatGPT conversations only
python retrieval/search_qdrant.py "typescript" --platform chatgpt

# Find ChatGPT-specific advice
python retrieval/search_qdrant.py "REST API design" --platform chatgpt --limit 10

# Search ChatGPT coding help
python retrieval/search_qdrant.py "python best practices" --platform chatgpt
```

### Claude Only

```bash
# Claude conversations only
python retrieval/search_qdrant.py "system design" --platform claude

# Find Claude-specific discussions
python retrieval/search_qdrant.py "database schema" --platform claude --limit 15

# Search Claude project help
python retrieval/search_qdrant.py "refactoring strategy" --platform claude
```

### Claude Projects Only

```bash
# Search project documentation and context
python retrieval/search_qdrant.py "project goals" --platform claude-projects

# Find project-specific instructions
python retrieval/search_qdrant.py "custom instructions" --platform claude-projects

# Search project knowledge base
python retrieval/search_qdrant.py "documentation" --platform claude-projects --limit 20
```

**Use Cases**:
- Compare how different AIs explained the same concept
- Find platform-specific features or advice
- Analyze project context and custom instructions

---

## AI Interpretations

Filter for conversations where the AI recorded interpretations about you with `--interpretations`:

```bash
# Find how AIs interpret your communication style
python retrieval/search_qdrant.py "communication" --interpretations

# See AI's understanding of your preferences
python retrieval/search_qdrant.py "preferences" --interpretations

# Find interpreted patterns
python retrieval/search_qdrant.py "approach to problem solving" --interpretations

# Search project contexts with interpretations
python retrieval/search_qdrant.py "project context" --platform claude-projects --interpretations

# Any query but only show results with AI interpretations
python retrieval/search_qdrant.py "debugging" --interpretations --limit 5
```

**Use Cases**:
- Discover how AIs model your communication style
- Find conversations with rich contextual metadata
- Analyze AI's interpretation evolution over time
- See project-level context and custom instructions

---

## Metadata Filtering

Filter by custom metadata fields with `--metadata-filter`:

```bash
# Filter by model version
python retrieval/search_qdrant.py "coding help" --metadata-filter "assistant_model:gpt-4o"

# Search specific conversation
python retrieval/search_qdrant.py "query" --metadata-filter "conversation_id:abc-123"

# Filter by message type
python retrieval/search_qdrant.py "images" --metadata-filter "user_message_type:multimodal_text"

# Find tool usage
python retrieval/search_qdrant.py "search" --metadata-filter "has_tool_usage:true"
```

**Available Metadata Fields**:
- `assistant_model`: e.g., "gpt-4o", "claude-3-opus"
- `conversation_id`: Specific conversation UUID
- `user_message_type`: "text", "multimodal_text"
- `assistant_message_type`: "text"
- `has_tool_usage`: "true" or "false"

---

## Combined Filters

Powerful searches combining multiple flags:

### Research and Analysis

```bash
# Find ChatGPT's best explanation of a concept
python retrieval/search_qdrant.py "async programming" --platform chatgpt --limit 3

# Deep dive into Claude conversations about architecture
python retrieval/search_qdrant.py "system architecture" --platform claude --limit 20

# Find interpreted conversations about specific topic
python retrieval/search_qdrant.py "debugging approach" --interpretations --limit 10

# Cross-platform comparison (run multiple searches)
python retrieval/search_qdrant.py "authentication" --platform chatgpt --limit 5
python retrieval/search_qdrant.py "authentication" --platform claude --limit 5
```

### Self-Effacing Pattern Detection

```bash
# Find self-deprecating language with ChatGPT interpretations
python retrieval/search_qdrant.py "I'm probably wrong" --platform chatgpt --interpretations

# Search for apologies across all platforms
python retrieval/search_qdrant.py "sorry" --limit 30

# Find uncertainty expressions in Claude conversations
python retrieval/search_qdrant.py "not sure if this makes sense" --platform claude --limit 15

# Search for mistake acknowledgments
python retrieval/search_qdrant.py "my mistake" --interpretations --limit 20
```

### Technical Deep Dives

```bash
# Comprehensive search on a technical topic
python retrieval/search_qdrant.py "kubernetes" --limit 30

# Find specific model's advice
python retrieval/search_qdrant.py "docker deployment" --platform chatgpt --metadata-filter "assistant_model:gpt-4" --limit 10

# Project-specific technical documentation
python retrieval/search_qdrant.py "API design" --platform claude-projects --limit 15
```

### Time-Based Analysis (Future Enhancement)

```bash
# These will work once date filtering is implemented
# python retrieval/search_qdrant.py "python" --date-from "2024-01-01" --date-to "2024-12-31"
# python retrieval/search_qdrant.py "machine learning" --date-from "2024-06-01"
```

---

## Interactive Mode

Launch interactive mode for exploratory search:

```bash
# Start interactive mode
python retrieval/search_qdrant.py

# Then use commands:
🔍 Query: kubernetes deployment

# Change platform filter
🔍 Query: /platform chatgpt
🔍 Query: kubernetes deployment

# Adjust result limit
🔍 Query: /limit 20
🔍 Query: kubernetes deployment

# Toggle interpretations filter
🔍 Query: /interpretations
🔍 Query: communication style

# Clear all filters
🔍 Query: /all

# Exit
🔍 Query: /quit
```

**Interactive Commands**:
- `/quit` - Exit interactive mode
- `/platform [chatgpt|claude|claude-projects]` - Set platform filter
- `/limit [number]` - Set result limit
- `/interpretations` - Toggle AI interpretations filter
- `/metadata <key>:<value>` - Set metadata filter
- `/all` - Clear all filters

---

## Self-Effacing Pattern Detection

Find conversations with self-effacing or self-deprecating language:

### Apologies and Mistakes

```bash
# Find apologies
python retrieval/search_qdrant.py "I apologize" --limit 20
python retrieval/search_qdrant.py "sorry about that" --limit 20
python retrieval/search_qdrant.py "my apologies" --limit 15

# Find mistake acknowledgments
python retrieval/search_qdrant.py "my mistake" --limit 20
python retrieval/search_qdrant.py "I was wrong" --limit 15
python retrieval/search_qdrant.py "that was dumb" --limit 10
```

### Uncertainty and Self-Doubt

```bash
# Find expressions of uncertainty
python retrieval/search_qdrant.py "I'm not sure" --limit 25
python retrieval/search_qdrant.py "probably wrong" --limit 20
python retrieval/search_qdrant.py "might be confused" --limit 15

# Find self-questioning
python retrieval/search_qdrant.py "does this make sense" --limit 20
python retrieval/search_qdrant.py "is this right" --limit 15
python retrieval/search_qdrant.py "did I understand correctly" --limit 15
```

### Minimizing Accomplishments

```bash
# Find self-minimization
python retrieval/search_qdrant.py "just a simple" --limit 15
python retrieval/search_qdrant.py "probably obvious" --limit 15
python retrieval/search_qdrant.py "might be a dumb question" --limit 10

# Find qualification language
python retrieval/search_qdrant.py "kind of" --limit 30
python retrieval/search_qdrant.py "sort of" --limit 30
```

### Cross-Platform Self-Effacing Analysis

```bash
# Compare self-effacing patterns across platforms
python retrieval/search_qdrant.py "I'm probably" --platform chatgpt --limit 15
python retrieval/search_qdrant.py "I'm probably" --platform claude --limit 15

# Find how different AIs responded to self-deprecation
python retrieval/search_qdrant.py "not good at" --interpretations --limit 20

# Temporal analysis (see how patterns changed over time)
python retrieval/search_qdrant.py "stupid mistake" --limit 50
```

---

## Cross-Platform Analysis

Compare how different AIs handled the same topics:

### Same Query, Different Platforms

```bash
# ChatGPT's approach
python retrieval/search_qdrant.py "system design patterns" --platform chatgpt --limit 10

# Claude's approach
python retrieval/search_qdrant.py "system design patterns" --platform claude --limit 10

# Compare responses side-by-side
```

### Topic Evolution Across Platforms

```bash
# Find all conversations about a topic
python retrieval/search_qdrant.py "authentication" --limit 50

# Then filter by platform to see differences
python retrieval/search_qdrant.py "authentication" --platform chatgpt --limit 20
python retrieval/search_qdrant.py "authentication" --platform claude --limit 20
```

### AI Interpretation Comparison

```bash
# See how ChatGPT interpreted your style
python retrieval/search_qdrant.py "coding style" --platform chatgpt --interpretations

# See how Claude interpreted your style
python retrieval/search_qdrant.py "coding style" --platform claude --interpretations

# Compare project-level interpretations
python retrieval/search_qdrant.py "preferences" --platform claude-projects --interpretations
```

---

## Advanced Use Cases

### Finding Specific Conversations

```bash
# Search by conversation title
python retrieval/search_qdrant.py "SSH key management" --limit 5

# Find recent discussions (sort by relevance)
python retrieval/search_qdrant.py "docker compose" --limit 10

# Deep technical dive
python retrieval/search_qdrant.py "database indexing strategies" --limit 30
```

### Pattern Recognition

```bash
# Find communication patterns
python retrieval/search_qdrant.py "let me know if" --limit 30
python retrieval/search_qdrant.py "does that help" --limit 20
python retrieval/search_qdrant.py "thanks for" --limit 25

# Find question patterns
python retrieval/search_qdrant.py "how do I" --limit 50
python retrieval/search_qdrant.py "what's the best way" --limit 40
python retrieval/search_qdrant.py "can you explain" --limit 30
```

### Research and Learning

```bash
# Find all discussions on a learning topic
python retrieval/search_qdrant.py "machine learning fundamentals" --limit 40

# Track learning progression
python retrieval/search_qdrant.py "neural networks" --limit 30
python retrieval/search_qdrant.py "deep learning" --limit 30
python retrieval/search_qdrant.py "transformers" --limit 20

# Find project documentation
python retrieval/search_qdrant.py "API documentation" --platform claude-projects --limit 15
```

---

## Tips and Best Practices

### Effective Query Writing

1. **Be specific**: "postgres connection pooling" > "database"
2. **Use natural language**: "how to debug memory leaks" works well
3. **Include context**: "python async await best practices"
4. **Try variations**: "kubernetes" vs "k8s" vs "container orchestration"

### Filter Strategy

1. **Start broad**: Search without filters first
2. **Narrow down**: Add platform filter if needed
3. **Find gold**: Use `--interpretations` for meta-insights
4. **Adjust limit**: Increase for comprehensive, decrease for quick lookup

### Interpreting Results

- **Scores > 0.6**: Highly relevant matches
- **Scores 0.4-0.6**: Good semantic matches
- **Scores < 0.4**: Weak matches, try different query

### Performance Tips

- Interactive mode reuses the model (faster for multiple searches)
- Single query mode reloads model each time (slower but fresh)
- Larger `--limit` values don't significantly slow down search
- Platform filters reduce search space and improve speed

---

## Quick Reference

```bash
# Basic
python retrieval/search_qdrant.py "query"

# With limit
python retrieval/search_qdrant.py "query" --limit 5

# Platform filter
python retrieval/search_qdrant.py "query" --platform chatgpt

# Interpretations only
python retrieval/search_qdrant.py "query" --interpretations

# Combined
python retrieval/search_qdrant.py "query" --platform claude --limit 20 --interpretations

# Interactive
python retrieval/search_qdrant.py
```

---

## Future Enhancements

Planned features for future versions:

```bash
# Date range filtering
python retrieval/search_qdrant.py "query" --date-from "2024-01-01" --date-to "2024-12-31"

# Export results to file
python retrieval/search_qdrant.py "query" --export results.json

# Aggregation and statistics
python retrieval/search_qdrant.py "query" --stats

# Conversation threading
python retrieval/search_qdrant.py "query" --show-context --context-turns 3
```

---

**Happy searching! 🔍**

For more information, see the main [README.md](README.md) and [CLAUDE.md](CLAUDE.md).
