# WillGPT: Multi-Platform Self-Effacing RAG System

A comprehensive retrieval system for analyzing personal AI conversation patterns across multiple platforms.

## Project Goals

- Extract self-effacing patterns and surprising insights from years of AI conversations
- Build cross-platform analysis of how different AIs interpreted the user
- Create a retrieval system that knows the user better than they know themselves

## Data Sources

- ChatGPT conversations (69.5MB+ current export)
- Claude conversations (pending fresh export)
- Additional platforms as needed

## Architecture

### Phase 1: Requirements & Data Discovery ✅
- [x] Data source inventory
- [x] Export format analysis
- [x] Scale estimation

### Phase 2: Data Harmonization Pipeline (Current)
- [ ] Universal parser framework
- [ ] Platform-specific parsers (ChatGPT, Claude)
- [ ] Cross-platform conversation standardization
- [ ] Metadata extraction and enrichment

### Phase 3: Embedding Architecture
- [ ] Multi-vector embedding strategy
- [ ] BGE-M3 model testing and fine-tuning
- [ ] Colab processing pipeline
- [ ] Sparse embedding integration

### Phase 4: Retrieval System
- [ ] Local vector database (Qdrant)
- [ ] Hybrid retrieval (dense + sparse)
- [ ] Multi-agent retrieval system
- [ ] Web interface

### Phase 5: Advanced Analytics
- [ ] Personal conversation model training
- [ ] Cross-platform analysis
- [ ] Temporal pattern detection
- [ ] AI interpretation comparison

## Technical Stack

- **Processing**: Python, Google Colab (GPU), Mac M4 (local)
- **Embeddings**: BGE-M3, custom fine-tuned models
- **Storage**: Qdrant vector database
- **Interface**: FastAPI + React
- **Analytics**: PyTorch, NetworkX

## Project Structure

```
willGPT/
├── parsers/           # Platform-specific conversation parsers
├── embeddings/        # Embedding generation and models
├── retrieval/         # Vector DB and search logic
├── analytics/         # Pattern analysis and insights
├── interface/         # Web UI and API
├── data/             # Raw exports and processed data
└── notebooks/        # Colab processing notebooks
```

## Getting Started

1. Request fresh exports from all platforms
2. Set up development environment
3. Process initial data with universal parser
4. Generate embeddings using Colab
5. Build local retrieval system

---

*"There is so much info in my chat logs I would love to explore"*
