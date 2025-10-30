#!/usr/bin/env python3
"""
Upload WillGPT conversations to Qdrant with BGE-M3 hybrid embeddings
"""

import sys
import os
from pathlib import Path
from tqdm import tqdm
from typing import List, Dict, Any
import torch
from dotenv import load_dotenv

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

from parsers import ConversationCollection
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    SparseVectorParams,
    SparseIndexParams,
)
from sentence_transformers import SentenceTransformer

# Configuration - hardcoded
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoyMDc3MTMyMDc2fQ.2kbNJ7tGunrcafxnldpZhmyPXgv689dlfyCQSZ1mYJo"
QDRANT_URL = "https://79582a58-07be-4684-b371-a80693088b0a.us-east-1-1.aws.cloud.qdrant.io:6333"
COLLECTION_NAME = "will-gpt"
EMBEDDING_MODE = "balanced"  # Options: balanced, user_focused, minimal, full
BATCH_SIZE = 8  # Reduced from 100 to avoid OOM

# BGE-M3 configuration
MODEL_NAME = "BAAI/bge-m3"
DEVICE = "cpu"  # Use CPU to avoid MPS OOM (M4 has limited GPU memory)


def setup_qdrant_collection(client: QdrantClient, collection_name: str, vector_size: int):
    """
    Create or recreate Qdrant collection with hybrid search support

    BGE-M3 produces:
    - Dense vectors (1024 dims for bge-m3)
    - Sparse vectors (lexical/keyword matching)
    """

    # Check if collection exists
    collections = client.get_collections().collections
    collection_exists = any(c.name == collection_name for c in collections)

    if collection_exists:
        print(f"\n⚠️  Collection '{collection_name}' already exists!")
        response = input("Delete and recreate? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborting. Use existing collection or choose different name.")
            sys.exit(0)

        print(f"Deleting existing collection '{collection_name}'...")
        client.delete_collection(collection_name)

    print(f"\nCreating collection '{collection_name}' with hybrid search...")

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            )
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(
                    on_disk=False,
                )
            )
        },
    )

    print(f"✅ Collection created successfully!")


def generate_bge_m3_embeddings(model: SentenceTransformer, texts: List[str]) -> tuple:
    """
    Generate BGE-M3 hybrid embeddings (dense + sparse)

    Returns:
        tuple: (dense_embeddings, sparse_embeddings)
    """

    # BGE-M3 encode method returns dict with 'dense_vecs' and 'lexical_weights'
    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        convert_to_tensor=True,
        batch_size=BATCH_SIZE,
    )

    # For BGE-M3, we get dense vectors directly
    # Sparse vectors require special encoding (lexical matching)
    # For now, we'll use dense only and add sparse later if needed

    return embeddings, None


def chunk_to_payload(chunk) -> Dict[str, Any]:
    """
    Convert UniversalChunk to Qdrant payload

    Stores structured data separately from embeddings for filtering/display
    """

    payload = {
        "conversation_id": chunk.conversation_id,
        "platform": chunk.platform,
        "timestamp": chunk.timestamp.isoformat() if chunk.timestamp else None,
        "conversation_title": chunk.conversation_title,
        "turn_number": chunk.turn_number,

        # The actual content
        "user_message": chunk.user_message,
        "assistant_message": chunk.assistant_message,
        "user_message_type": chunk.user_message_type,
        "assistant_message_type": chunk.assistant_message_type,
        "assistant_model": chunk.assistant_model,

        # AI interpretations - THE GOLD
        "has_interpretations": bool(chunk.ai_interpretations),
    }

    # Add ChatGPT-specific interpretations if present
    if chunk.platform == "chatgpt" and chunk.ai_interpretations:
        ucd = chunk.ai_interpretations.get('user_context_message_data', {})
        payload["about_user"] = ucd.get('about_user_message', '')
        payload["about_model"] = ucd.get('about_model_message', '')

    # Add metadata
    if chunk.system_context:
        payload["system_context"] = chunk.system_context

    if chunk.tool_usage:
        payload["has_tool_usage"] = True
        payload["tool_count"] = len(chunk.tool_usage)

    return payload


def upload_conversations_to_qdrant(
    collection_file: str,
    qdrant_url: str,
    collection_name: str,
    embedding_mode: str = "balanced",
    api_key: str = None,
):
    """
    Main upload function: Load conversations, generate embeddings, upload to Qdrant
    """

    print("="*70)
    print("WILLGPT → QDRANT HYBRID SEARCH UPLOAD")
    print("="*70)

    # Load conversations
    print(f"\n1. Loading conversations from {collection_file}...")
    collection = ConversationCollection.load_from_json(collection_file)
    print(f"   ✅ Loaded {len(collection.chunks)} conversation chunks")

    # Initialize BGE-M3 model
    print(f"\n2. Loading BGE-M3 model ({MODEL_NAME})...")
    print(f"   Device: {DEVICE}")
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)
    vector_size = model.get_sentence_embedding_dimension()
    print(f"   ✅ Model loaded (vector size: {vector_size})")

    # Connect to Qdrant
    print(f"\n3. Connecting to Qdrant...")
    print(f"   URL: {qdrant_url}")
    client = QdrantClient(
        url=qdrant_url,
        api_key=api_key,
        timeout=60,
        prefer_grpc=False,  # Use HTTP REST API
    )
    print(f"   ✅ Connected")

    # Setup collection
    setup_qdrant_collection(client, collection_name, vector_size)

    # Generate embeddings and upload in batches
    print(f"\n4. Generating embeddings and uploading (mode: {embedding_mode})...")
    print(f"   Batch size: {BATCH_SIZE}")

    points = []
    batch_texts = []
    batch_chunks = []

    for idx, chunk in enumerate(tqdm(collection.chunks, desc="Processing")):
        # Generate embedding text
        embedding_text = chunk.to_embedding_text(mode=embedding_mode)
        batch_texts.append(embedding_text)
        batch_chunks.append(chunk)

        # Process batch when full
        if len(batch_texts) >= BATCH_SIZE or idx == len(collection.chunks) - 1:
            # Generate embeddings
            embeddings, _ = generate_bge_m3_embeddings(model, batch_texts)

            # Create points
            for i, (emb, ch) in enumerate(zip(embeddings, batch_chunks)):
                point_id = len(points) + i

                point = PointStruct(
                    id=point_id,
                    vector={
                        "dense": emb.cpu().tolist() if isinstance(emb, torch.Tensor) else emb.tolist()
                    },
                    payload=chunk_to_payload(ch)
                )
                points.append(point)

            # Upload batch to Qdrant
            if len(points) >= BATCH_SIZE:
                client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                points = []

            # Reset batch
            batch_texts = []
            batch_chunks = []

    # Upload remaining points
    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )

    # Get collection info
    collection_info = client.get_collection(collection_name)

    print(f"\n{'='*70}")
    print("✅ UPLOAD COMPLETE!")
    print(f"{'='*70}")
    print(f"Collection: {collection_name}")
    print(f"Total points: {collection_info.points_count}")
    print(f"Vector size: {vector_size}")
    print(f"Embedding mode: {embedding_mode}")
    print(f"\n🔍 Ready for hybrid search!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload WillGPT conversations to Qdrant")
    parser.add_argument(
        "--collection-file",
        default="data/processed_conversations.json",
        help="Path to processed conversations JSON"
    )
    parser.add_argument(
        "--qdrant-url",
        default=QDRANT_URL,
        help="Qdrant server URL"
    )
    parser.add_argument(
        "--collection-name",
        default=COLLECTION_NAME,
        help="Qdrant collection name"
    )
    parser.add_argument(
        "--embedding-mode",
        default=EMBEDDING_MODE,
        choices=["balanced", "user_focused", "minimal", "full"],
        help="Embedding text generation mode"
    )
    parser.add_argument(
        "--api-key",
        default=QDRANT_API_KEY,
        help="Qdrant API key (or set QDRANT_API_KEY in .env)"
    )

    args = parser.parse_args()

    if not args.api_key:
        print("❌ Error: QDRANT_API_KEY not found in .env file or --api-key argument")
        print("   Add QDRANT_API_KEY to your .env file or pass --api-key")
        sys.exit(1)

    upload_conversations_to_qdrant(
        collection_file=args.collection_file,
        qdrant_url=args.qdrant_url,
        collection_name=args.collection_name,
        embedding_mode=args.embedding_mode,
        api_key=args.api_key,
    )
