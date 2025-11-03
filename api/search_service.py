"""
Search service wrapper for API

Provides clean interface to search_engine.py for FastAPI
"""

import sys
import os
from pathlib import Path
import torch
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import time

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, SparseVector, Range
from FlagEmbedding import BGEM3FlagModel

from api.models import SearchResult, SearchFilters, SearchMode, GroupedResults


class SearchService:
    """
    Search service that wraps search_engine functionality for API use.

    Handles model caching, error handling, and structured responses.
    """

    def __init__(
        self,
        qdrant_url: str,
        qdrant_api_key: str,
        collection_name: str,
        model_name: str,
        device: str = "cpu"
    ):
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.collection_name = collection_name
        self.model_name = model_name
        self.device = device

        # Model will be loaded once and cached
        self.model: Optional[BGEM3FlagModel] = None

    def load_model(self):
        """Load BGE-M3 model (called once at startup)"""
        if self.model is None:
            use_fp16 = self.device in ['cuda', 'mps']
            self.model = BGEM3FlagModel(self.model_name, use_fp16=use_fp16, device=self.device)

    def search(
        self,
        query: str,
        filters: SearchFilters
    ) -> tuple[List[SearchResult] | List[GroupedResults], float]:
        """
        Execute search and return structured results.

        Supports multiple search modes:
        - VECTOR: Standard hybrid vector search
        - RECOMMEND: Find similar with positive/negative examples
        - ORDER_BY: Sort by field instead of relevance
        - MMR: Maximal Marginal Relevance for diversity
        - GROUPS: Group results by field

        Args:
            query: Search query text
            filters: Search filters

        Returns:
            Tuple of (results list, execution_time_ms)
        """
        start_time = time.time()

        # Dispatch to appropriate search method based on mode
        if filters.search_mode == SearchMode.RECOMMEND:
            return self._search_recommend(query, filters, start_time)
        elif filters.search_mode == SearchMode.ORDER_BY:
            return self._search_order_by(query, filters, start_time)
        elif filters.search_mode == SearchMode.MMR:
            return self._search_mmr(query, filters, start_time)
        elif filters.search_mode == SearchMode.GROUPS:
            return self._search_groups(query, filters, start_time)
        else:  # VECTOR mode (default)
            return self._search_vector(query, filters, start_time)

    def _search_vector(
        self,
        query: str,
        filters: SearchFilters,
        start_time: float
    ) -> tuple[List[SearchResult], float]:
        """
        Standard hybrid vector search (dense + sparse).

        Args:
            query: Search query text
            filters: Search filters
            start_time: Start time for execution tracking

        Returns:
            Tuple of (results list, execution_time_ms)
        """
        # Encode query into vectors
        query_dense, query_sparse = self._encode_query(query)
        query_filter = self._build_filter(filters)

        # Connect to Qdrant
        client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=60,
            prefer_grpc=False,
        )

        try:
            # Dense search
            dense_results = client.query_points(
                collection_name=self.collection_name,
                query=query_dense.tolist(),
                using="dense",
                query_filter=query_filter,
                limit=filters.limit,
                with_payload=True,
            ).points

            # Sparse search
            sparse_results = client.query_points(
                collection_name=self.collection_name,
                query=query_sparse,
                using="sparse",
                query_filter=query_filter,
                limit=filters.limit,
                with_payload=True,
            ).points

            # Combine and re-rank results
            combined_results = {result.id: result for result in dense_results}
            for result in sparse_results:
                if result.id not in combined_results:
                    combined_results[result.id] = result

            # Sort by score (descending)
            sorted_results = sorted(combined_results.values(), key=lambda r: r.score, reverse=True)[:filters.limit]

            # Convert to SearchResult models
            results = self._convert_to_search_results(sorted_results)
            execution_time_ms = (time.time() - start_time) * 1000
            return results, execution_time_ms

        finally:
            client.close()

    def _build_filter(self, filters: SearchFilters) -> Optional[Filter]:
        """Build Qdrant filter from SearchFilters"""
        filter_conditions = []

        if filters.platform:
            filter_conditions.append(FieldCondition(
                key="platform",
                match=MatchValue(value=filters.platform)
            ))

        if filters.with_interpretations:
            filter_conditions.append(FieldCondition(
                key="has_interpretations",
                match=MatchValue(value=True)
            ))

        if filters.date_from:
            gte_val = self._parse_date(filters.date_from)
            filter_conditions.append(FieldCondition(
                key="timestamp",
                range=Range(gte=gte_val)
            ))

        if filters.date_to:
            lte_val = self._parse_date(filters.date_to)
            filter_conditions.append(FieldCondition(
                key="timestamp",
                range=Range(lte=lte_val)
            ))

        if filters.metadata_filter:
            key, value = filters.metadata_filter.split(":", 1)
            filter_conditions.append(FieldCondition(
                key=f"payload.{key}",
                match=MatchValue(value=value)
            ))

        return Filter(must=filter_conditions) if filter_conditions else None

    def _encode_query(self, query: str) -> tuple:
        """Encode query into dense and sparse vectors"""
        if self.model is None:
            self.load_model()

        output = self.model.encode(
            [query],
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False
        )

        # Handle dense vector
        dense_vec = output['dense_vecs'][0]
        if isinstance(dense_vec, torch.Tensor):
            query_dense = dense_vec.cpu().numpy()
        else:
            query_dense = np.asarray(dense_vec)

        # Handle sparse vector
        query_sparse_weights = output['lexical_weights'][0]
        if isinstance(query_sparse_weights, dict):
            sparse_indices = [int(idx) for idx in query_sparse_weights.keys()]
            sparse_values = list(query_sparse_weights.values())
        else:
            if isinstance(query_sparse_weights, torch.Tensor):
                arr = query_sparse_weights.cpu().numpy()
            else:
                arr = np.asarray(query_sparse_weights)
            nonzero = np.nonzero(arr)[0]
            sparse_indices = nonzero.tolist()
            sparse_values = arr[nonzero].tolist()

        query_sparse = SparseVector(indices=sparse_indices, values=sparse_values)
        return query_dense, query_sparse

    def _convert_to_search_results(self, qdrant_points, start_index: int = 0) -> List[SearchResult]:
        """Convert Qdrant points to SearchResult models"""
        results = []
        for i, result in enumerate(qdrant_points, start=start_index):
            payload = result.payload if result.payload is not None else {}

            # Convert timestamp to ISO format string if it's a float
            timestamp = payload.get('timestamp')
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

            results.append(SearchResult(
                id=i,
                score=round(result.score, 4),
                platform=payload.get('platform', 'unknown'),
                conversation_title=payload.get('conversation_title', 'Untitled'),
                timestamp=timestamp,
                turn_number=payload.get('turn_number', 0),
                user_message=payload.get('user_message', ''),
                assistant_message=payload.get('assistant_message', ''),
                has_interpretations=payload.get('has_interpretations', False),
                about_user=payload.get('about_user'),
                about_model=payload.get('about_model'),
                user_message_type=payload.get('user_message_type'),
                assistant_message_type=payload.get('assistant_message_type'),
                assistant_model=payload.get('assistant_model')
            ))
        return results

    def _search_recommend(
        self,
        query: str,
        filters: SearchFilters,
        start_time: float
    ) -> tuple[List[SearchResult], float]:
        """
        Recommend search - find similar using positive/negative examples.

        Uses Qdrant's recommend API to find points similar to positive examples
        and dissimilar to negative examples.
        """
        client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=60,
            prefer_grpc=False,
        )

        try:
            query_filter = self._build_filter(filters)

            # Build positive and negative point IDs
            positive = filters.positive_ids if filters.positive_ids else []
            negative = filters.negative_ids if filters.negative_ids else []

            if not positive:
                raise ValueError("Recommend mode requires at least one positive_id")

            # Perform recommendation
            results = client.recommend(
                collection_name=self.collection_name,
                positive=positive,
                negative=negative,
                query_filter=query_filter,
                limit=filters.limit,
                with_payload=True,
            )

            search_results = self._convert_to_search_results(results)
            execution_time_ms = (time.time() - start_time) * 1000
            return search_results, execution_time_ms

        finally:
            client.close()

    def _search_order_by(
        self,
        query: str,
        filters: SearchFilters,
        start_time: float
    ) -> tuple[List[SearchResult], float]:
        """
        Order by search - sort by field instead of relevance.

        Performs vector search but re-sorts results by specified field.
        """
        # First perform vector search
        results, _ = self._search_vector(query, filters, time.time())

        # Re-sort by specified field
        if filters.order_by_field:
            reverse = (filters.order_direction == "desc")
            results = sorted(
                results,
                key=lambda r: getattr(r, filters.order_by_field, ''),
                reverse=reverse
            )

        execution_time_ms = (time.time() - start_time) * 1000
        return results, execution_time_ms

    def _search_mmr(
        self,
        query: str,
        filters: SearchFilters,
        start_time: float
    ) -> tuple[List[SearchResult], float]:
        """
        MMR (Maximal Marginal Relevance) search - diverse results.

        Re-ranks results to maximize both relevance and diversity.
        """
        query_dense, query_sparse = self._encode_query(query)
        query_filter = self._build_filter(filters)

        client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=60,
            prefer_grpc=False,
        )

        try:
            # Use Qdrant's query API with MMR
            from qdrant_client.models import QueryRequest, NearestQuery

            diversity_lambda = filters.mmr_diversity if filters.mmr_diversity else 0.5

            # Search with MMR enabled (need vectors for similarity calculation)
            results = client.query_points(
                collection_name=self.collection_name,
                query=query_dense.tolist(),
                using="dense",
                query_filter=query_filter,
                limit=filters.limit * 2,  # Get more results for diversity selection
                with_payload=True,
                with_vectors=True,  # Required for MMR similarity calculations
            ).points

            # Apply MMR re-ranking
            if len(results) > 0:
                selected = []
                remaining = list(results)

                # Select first result (most relevant)
                selected.append(remaining.pop(0))

                # Select remaining results using MMR formula
                while remaining and len(selected) < filters.limit:
                    best_score = -float('inf')
                    best_idx = 0

                    for idx, candidate in enumerate(remaining):
                        # Relevance score
                        relevance = candidate.score

                        # Get candidate vector
                        candidate_vec = np.array(candidate.vector['dense']) if hasattr(candidate, 'vector') and candidate.vector else None

                        # Max similarity to selected documents
                        if candidate_vec is not None and len(selected) > 0:
                            max_sim = max([
                                self._cosine_similarity(
                                    candidate_vec,
                                    np.array(selected[i].vector['dense']) if hasattr(selected[i], 'vector') and selected[i].vector else np.zeros_like(candidate_vec)
                                )
                                for i in range(len(selected))
                            ])
                        else:
                            max_sim = 0

                        # MMR score: λ * relevance - (1-λ) * max_similarity
                        mmr_score = diversity_lambda * relevance - (1 - diversity_lambda) * max_sim

                        if mmr_score > best_score:
                            best_score = mmr_score
                            best_idx = idx

                    selected.append(remaining.pop(best_idx))

                search_results = self._convert_to_search_results(selected)
            else:
                search_results = []

            execution_time_ms = (time.time() - start_time) * 1000
            return search_results, execution_time_ms

        finally:
            client.close()

    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        if len(vec1) == 0 or len(vec2) == 0:
            return 0
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def _search_groups(
        self,
        query: str,
        filters: SearchFilters,
        start_time: float
    ) -> tuple[List[GroupedResults], float]:
        """
        Group search - results grouped by field.

        Groups results by specified field (e.g., platform, conversation_id).
        """
        query_dense, query_sparse = self._encode_query(query)
        query_filter = self._build_filter(filters)

        if not filters.group_by:
            raise ValueError("Groups mode requires group_by field")

        client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=60,
            prefer_grpc=False,
        )

        try:
            # Use Qdrant's search groups API
            from qdrant_client.models import NamedVector
            results = client.search_groups(
                collection_name=self.collection_name,
                query_vector=NamedVector(name="dense", vector=query_dense.tolist()),
                group_by=filters.group_by,
                limit=filters.limit,  # Number of groups
                group_size=filters.group_size,  # Results per group
                query_filter=query_filter,
                with_payload=True,
            )

            # Convert to GroupedResults
            grouped_results = []
            for group in results.groups:
                group_hits = self._convert_to_search_results(group.hits)
                grouped_results.append(GroupedResults(
                    group_key=str(group.id),
                    hits=group_hits
                ))

            execution_time_ms = (time.time() - start_time) * 1000
            return grouped_results, execution_time_ms

        finally:
            client.close()

    def _parse_date(self, date_str: str) -> float:
        """Parse date string to Unix timestamp"""
        try:
            if isinstance(date_str, (int, float)):
                return float(date_str)
            else:
                try:
                    return float(date_str)
                except ValueError:
                    ds = date_str
                    if ds.endswith("Z"):
                        ds = ds.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(ds)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt.timestamp()
        except Exception as e:
            raise ValueError(f"Invalid date value: {date_str}") from e

    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        model_loaded = self.model is not None
        qdrant_connected = False

        try:
            client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key,
                timeout=5,
                prefer_grpc=False,
            )
            try:
                client.get_collections()
                qdrant_connected = True
            finally:
                client.close()
        except Exception:
            pass

        return {
            "model_loaded": model_loaded,
            "qdrant_connected": qdrant_connected
        }
