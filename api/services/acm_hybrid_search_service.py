"""Hybrid Search Service for ACM Records

Combines BM25 full-text search with vector similarity search
using Reciprocal Rank Fusion (RRF).

Story: E11-S2 Hybrid Search Service
"""

from typing import Optional

from loguru import logger

from open_notebook.database.repository import repo_query


class HybridSearchService:
    """Hybrid search combining BM25 and vector similarity."""

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    async def bm25_search(
        self,
        query: str,
        source_id: Optional[str] = None,
        building_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Full-text BM25 search using SurrealDB SEARCH operator."""
        filters = []
        params: dict = {"query": query, "limit": limit}

        if source_id:
            filters.append("source_id = $source_id")
            params["source_id"] = source_id
        if building_id:
            filters.append("building_id = $building_id")
            params["building_id"] = building_id

        where_clause = " AND ".join(filters) if filters else ""
        if where_clause:
            where_clause = f"AND {where_clause}"

        surql = (
            "SELECT *, search::score(1) AS bm25_score "
            "FROM acm_record "
            "WHERE (product @1@ $query OR material_description @1@ $query "
            "OR location @1@ $query OR hygienist_recommendations @1@ $query) "
            f"{where_clause} "
            "ORDER BY bm25_score DESC "
            "LIMIT $limit"
        )

        try:
            results = await repo_query(surql, params)
            return results or []
        except Exception as e:
            logger.warning(f"BM25 search failed (index may not exist yet): {e}")
            return []

    async def vector_search(
        self,
        query_embedding: list[float],
        source_id: Optional[str] = None,
        building_id: Optional[str] = None,
        limit: int = 50,
        threshold: float = 0.5,
    ) -> list[dict]:
        """Vector similarity search using cosine distance."""
        filters = ["embedding IS NOT NULL"]
        params: dict = {
            "query_embedding": query_embedding,
            "limit": limit,
        }

        if source_id:
            filters.append("source_id = $source_id")
            params["source_id"] = source_id
        if building_id:
            filters.append("building_id = $building_id")
            params["building_id"] = building_id

        where_clause = " AND ".join(filters)

        surql = (
            "SELECT *, vector::similarity::cosine(embedding, $query_embedding) AS similarity "
            f"FROM acm_record WHERE {where_clause} "
            "ORDER BY similarity DESC "
            "LIMIT $limit"
        )

        try:
            results = await repo_query(surql, params)
            return [r for r in (results or []) if r.get("similarity", 0) >= threshold]
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def reciprocal_rank_fusion(
        self,
        bm25_results: list[dict],
        vector_results: list[dict],
        limit: int = 10,
    ) -> list[dict]:
        """Combine results using Reciprocal Rank Fusion (RRF).

        RRF score = sum(1 / (k + rank_i)) for each result list.
        """
        scores: dict[str, float] = {}
        records: dict[str, dict] = {}

        for rank, result in enumerate(bm25_results):
            rid = str(result.get("id", ""))
            if not rid:
                continue
            scores[rid] = scores.get(rid, 0) + 1.0 / (self.rrf_k + rank + 1)
            records[rid] = result

        for rank, result in enumerate(vector_results):
            rid = str(result.get("id", ""))
            if not rid:
                continue
            scores[rid] = scores.get(rid, 0) + 1.0 / (self.rrf_k + rank + 1)
            if rid not in records:
                records[rid] = result

        # Sort by RRF score descending
        sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)

        results = []
        for rid in sorted_ids[:limit]:
            record = records[rid]
            record["rrf_score"] = scores[rid]
            # Preserve original scores
            record.setdefault("bm25_score", 0)
            record.setdefault("similarity", 0)
            results.append(record)

        return results

    async def search(
        self,
        query: str,
        query_embedding: Optional[list[float]] = None,
        source_id: Optional[str] = None,
        building_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.5,
        mode: str = "hybrid",
    ) -> list[dict]:
        """Run search with specified mode.

        Args:
            mode: "hybrid" (BM25 + vector + RRF), "vector", or "bm25"
        """
        if mode == "bm25":
            return await self.bm25_search(
                query, source_id=source_id, building_id=building_id, limit=limit
            )

        if mode == "vector":
            if not query_embedding:
                logger.warning("Vector search requires embedding; returning empty")
                return []
            return await self.vector_search(
                query_embedding,
                source_id=source_id,
                building_id=building_id,
                limit=limit * 3,
                threshold=threshold,
            )[:limit]

        # Hybrid mode
        bm25_results = await self.bm25_search(
            query, source_id=source_id, building_id=building_id, limit=limit * 3
        )

        vector_results = []
        if query_embedding:
            vector_results = await self.vector_search(
                query_embedding,
                source_id=source_id,
                building_id=building_id,
                limit=limit * 3,
                threshold=threshold,
            )

        if not bm25_results and not vector_results:
            return []

        if not vector_results:
            return bm25_results[:limit]

        if not bm25_results:
            return vector_results[:limit]

        return self.reciprocal_rank_fusion(bm25_results, vector_results, limit=limit)
