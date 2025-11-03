#!/usr/bin/env python3
"""
Core search engine for WillGPT conversations using BGE-M3 hybrid retrieval
"""

import os
import torch
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, SparseVector, Range
from FlagEmbedding import BGEM3FlagModel


# Environment variables
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')
MODEL_NAME = os.getenv('MODEL_NAME')

# Device detection
DEVICE = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"


def search_conversations(
    query: str,
    limit: int = 10,
    platform_filter: Optional[str] = None,
    with_interpretations_only: bool = False,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    metadata_filter: Optional[str] = None,
    api_key: Optional[str] = QDRANT_API_KEY,
):
    """
    Search conversations using BGE-M3 embeddings with hybrid retrieval.

    Args:
        query: Search query text
        limit: Number of results to return
        platform_filter: Filter by platform (chatgpt, claude, claude-projects)
        with_interpretations_only: Only return chunks with AI interpretations
        date_from: Filter by date (ISO format)
        date_to: Filter by date (ISO format)
        metadata_filter: Filter by metadata in format "key:value"
        api_key: Qdrant API key

    Returns:
        List of search results with scores and payloads
    """

    print("="*70)
    print("WILLGPT HYBRID SEARCH")
    print("="*70)
    print(f"\nQuery: '{query}'")
    print(f"Limit: {limit}")

    # Load model
    print(f"\nLoading BGE-M3 model...")
    use_fp16 = DEVICE in ['cuda', 'mps']
    if not MODEL_NAME:
        raise ValueError("MODEL_NAME environment variable is not set. Please set it in your .env file.")
    model = BGEM3FlagModel(MODEL_NAME, use_fp16=use_fp16, device=DEVICE)

    # Generate query embedding (dense + sparse)
    print(f"Generating hybrid query embedding...")
    output = model.encode(
        [query],
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False
    )

    # Handle both PyTorch tensor and numpy array cases
    dense_vec = output['dense_vecs'][0]
    if isinstance(dense_vec, torch.Tensor):
        query_dense = dense_vec.cpu().numpy()
    else:
        query_dense = np.asarray(dense_vec)
    query_sparse_weights = output['lexical_weights'][0]  # Get first (and only) sparse weights

    # Convert sparse weights to Qdrant format
    # lexical_weights may be a dict {idx: weight} or a numpy/torch array; handle both
    if isinstance(query_sparse_weights, dict):
        sparse_indices = [int(idx) for idx in query_sparse_weights.keys()]
        sparse_values = list(query_sparse_weights.values())
    else:
        # Support torch tensors and numpy arrays
        if isinstance(query_sparse_weights, torch.Tensor):
            arr = query_sparse_weights.cpu().numpy()
        else:
            arr = np.asarray(query_sparse_weights)
        nonzero = np.nonzero(arr)[0]
        sparse_indices = nonzero.tolist()
        sparse_values = arr[nonzero].tolist()

    query_sparse = SparseVector(indices=sparse_indices, values=sparse_values)

    # Connect to Qdrant
    print(f"Connecting to Qdrant...")
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=api_key,
        timeout=60,
        prefer_grpc=False,  # Use HTTP REST API
    )

    try:
        # Build filters
        filters = []

        if platform_filter:
            filters.append(FieldCondition(
                key="platform",
                match=MatchValue(value=platform_filter)
            ))

        if with_interpretations_only:
            filters.append(FieldCondition(
                key="has_interpretations",
                match=MatchValue(value=True)
            ))

        if date_from:
            # Convert ISO date or numeric string to UNIX timestamp (float) for Qdrant Range
            try:
                if isinstance(date_from, (int, float)):
                    gte_val = float(date_from)
                else:
                    # try numeric string first, then ISO8601 parsing (handle trailing 'Z')
                    try:
                        gte_val = float(date_from)
                    except ValueError:
                        ds = date_from
                        if ds.endswith("Z"):
                            ds = ds.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(ds)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        gte_val = dt.timestamp()
            except Exception:
                raise ValueError(f"Invalid date_from value: {date_from}")

            filters.append(FieldCondition(
                key="timestamp",
                range=Range(
                    gte=gte_val
                )
            ))

        if date_to:
            # Convert ISO date or numeric string to UNIX timestamp (float) for Qdrant Range
            try:
                if isinstance(date_to, (int, float)):
                    lte_val = float(date_to)
                else:
                    # try numeric string first, then ISO8601 parsing (handle trailing 'Z')
                    try:
                        lte_val = float(date_to)
                    except ValueError:
                        ds = date_to
                        if ds.endswith("Z"):
                            ds = ds.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(ds)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        lte_val = dt.timestamp()
            except Exception:
                raise ValueError(f"Invalid date_to value: {date_to}")

            filters.append(FieldCondition(
                key="timestamp",
                range=Range(
                    lte=lte_val
                )
            ))

        if metadata_filter:
            key, value = metadata_filter.split(":", 1)
            filters.append(FieldCondition(
                key=f"payload.{key}",
                match=MatchValue(value=value)
            ))

        query_filter = Filter(must=filters) if filters else None

        # Hybrid Search using two separate search calls
        print(f"Searching with hybrid (dense + sparse)...")

        if not COLLECTION_NAME:
            raise ValueError("COLLECTION_NAME environment variable is not set. Please set it in your .env file.")

        # Dense search
        dense_results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_dense.tolist(),
            using="dense",
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points

        # Sparse search
        sparse_results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_sparse,
            using="sparse",
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points

        # Combine and re-rank results (simple approach: combine and remove duplicates)
        combined_results = {result.id: result for result in dense_results}
        for result in sparse_results:
            if result.id not in combined_results:
                combined_results[result.id] = result

        # Sort by score (descending)
        results = sorted(combined_results.values(), key=lambda r: r.score, reverse=True)[:limit]

        # Display results
        print(f"\n{'='*70}")
        print(f"FOUND {len(results)} RESULTS")
        print(f"{'='*70}\n")

        for i, result in enumerate(results, 1):
            print(f"{'─'*70}")
            print(f"RESULT {i} (score: {result.score:.4f})")
            print(f"{'─'*70}")

            # Ensure payload is a dict to avoid calling .get on None
            payload = result.payload if result.payload is not None else {}
            print(f"Title: {payload.get('conversation_title', 'Untitled')}")
            print(f"Platform: {payload.get('platform', 'unknown')}")
            # Use ISO timestamp for display (more readable), fallback to float if needed
            timestamp_display = payload.get('timestamp_iso') or payload.get('timestamp', 'unknown')
            print(f"Date: {timestamp_display}")
            print(f"Turn: {payload.get('turn_number', 0)}")

            # User message
            user_msg = payload.get('user_message', '')
            if user_msg:
                print(f"\n💬 USER:")
                print(f"   {user_msg[:300]}{'...' if len(user_msg) > 300 else ''}")

            # Assistant message
            assistant_msg = payload.get('assistant_message', '')
            if assistant_msg:
                print(f"\n🤖 ASSISTANT:")
                print(f"   {assistant_msg[:300]}{'...' if len(assistant_msg) > 300 else ''}")

            # AI interpretations
            if payload.get('has_interpretations'):
                print(f"\n🧠 AI INTERPRETATION:")
                about_user = payload.get('about_user', '')
                if about_user:
                    print(f"   User: {about_user}")
                about_model = payload.get('about_model', '')
                if about_model:
                    print(f"   Model: {about_model}")

            print()

        return results

    finally:
        # Always close the client connection
        client.close()
