#!/usr/bin/env python3
"""
Upload WillGPT conversations to Qdrant with BGE-M3 hybrid embeddings
"""

import sys
import os
from pathlib import Path
from tqdm import tqdm
from typing import List, Dict, Any, Optional
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
    SparseVector,
)
from FlagEmbedding import BGEM3FlagModel

QDRANT_API_KEY=os.getenv('QDRANT_API_KEY')
QDRANT_URL=os.getenv('QDRANT_URL')
COLLECTION_NAME=os.getenv('COLLECTION_NAME')
MODEL_NAME=os.getenv('MODEL_NAME')
EMBEDDING_MODE = "balanced"
DEVICE = "cpu"
BATCH_SIZE= 4


def setup_qdrant_collection(client: QdrantClient, collection_name: str, vector_size: int, auto_confirm: bool = False):
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

        if not auto_confirm:
            response = input("Delete and recreate? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborting. Use existing collection or choose different name.")
                sys.exit(0)
        else:
            print("Auto-confirm enabled - deleting and recreating...")

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


def generate_bge_m3_embeddings(model: BGEM3FlagModel, texts: List[str]) -> tuple:
    """
    Generate BGE-M3 hybrid embeddings (dense + sparse)

    Returns:
        tuple: (dense_embeddings, sparse_embeddings_list)
            - dense_embeddings: numpy array of shape [batch_size, 1024]
            - sparse_embeddings_list: list of dicts with token_id: weight mappings
    """

    # BGE-M3 encode method returns dict with 'dense_vecs' and 'lexical_weights'
    output = model.encode(
        texts,
        return_dense=True,
        return_sparse=True,  # Enable sparse (lexical) vectors
        return_colbert_vecs=False,
        batch_size=BATCH_SIZE,
    )

    dense_vecs = output['dense_vecs']  # Shape: [batch_size, 1024]
    lexical_weights = output['lexical_weights']  # List of dicts: [{'token_id': weight, ...}]

    return dense_vecs, lexical_weights


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
    api_key: Optional[str] = None,
    auto_confirm: bool = False,
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
    if not MODEL_NAME:
        raise ValueError("❌ Error: MODEL_NAME is not set. Please set MODEL_NAME in your .env file or environment.")
    print(f"\n2. Loading BGE-M3 model ({MODEL_NAME})...")
    print(f"   Device: {DEVICE}")
    use_fp16 = DEVICE in ['cuda', 'mps']  # Use FP16 for GPU, FP32 for CPU
    model = BGEM3FlagModel(MODEL_NAME, use_fp16=use_fp16, device=DEVICE)
    vector_size = 1024  # BGE-M3 dense vector dimension
    print(f"   ✅ Model loaded (vector size: {vector_size}, FP16: {use_fp16})")

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
    setup_qdrant_collection(client, collection_name, vector_size, auto_confirm=auto_confirm)

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
            # Generate embeddings (dense + sparse)
            dense_embeddings, sparse_embeddings = generate_bge_m3_embeddings(model, batch_texts)

            # Create points
            for i, (dense_emb, sparse_weights, ch) in enumerate(zip(dense_embeddings, sparse_embeddings, batch_chunks)):
                point_id = len(points) + i

                # Convert sparse weights to Qdrant SparseVector format
                if sparse_weights:
                    # sparse_weights is a dict like {token_id: weight, ...}
                    indices = list(sparse_weights.keys())
                    values = list(sparse_weights.values())
                    sparse_vector = SparseVector(indices=indices, values=values)
                else:
                    sparse_vector = SparseVector(indices=[], values=[])

                point = PointStruct(
                    id=point_id,
                    vector={
                        "dense": dense_emb.tolist() if hasattr(dense_emb, 'tolist') else dense_emb,
                        "sparse": sparse_vector
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
        default="data/processed/processed_conversations.json",
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
