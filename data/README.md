# WillGPT - Data Directory

This directory contains conversation exports and processed data.

## Structure

```
data/
├── raw/                    # Original export files
│   ├── chatgpt_export.json
│   ├── claude_export.json
│   └── other_exports/
├── processed/              # Parsed conversation chunks
│   ├── processed_conversations.json
│   ├── conversation_stats.json
│   └── cross_platform_analysis.json
└── embeddings/             # Generated embeddings
    ├── dense_embeddings/
    ├── sparse_embeddings/
    └── metadata/
```

## File Types

- **Raw exports**: Original JSON files from each LLM platform
- **Processed conversations**: Unified UniversalChunk format
- **Embeddings**: Vector representations for retrieval
- **Stats**: Analysis and metadata about the conversations

## Usage

1. Place your export files in `raw/`
2. Run the parser to generate processed data
3. Generate embeddings for retrieval
4. Analyze patterns and insights

## Privacy Note

All conversation data should be treated as highly sensitive personal information.
Keep this directory secure and do not commit raw conversation data to version control.
