"""Document search tools for LangGraph chat agents.

These tools enable chat agents to search PDF document content via vector
similarity search and BM25 full-text search on the source_embedding,
source_insight, and note tables in SurrealDB.
"""

import asyncio
import json
from typing import Optional

from langchain_core.tools import tool
from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.graphs.chat_tools.acm_tools import (
    _build_vars,
    _get_scope,
    _run_async,
)


@tool
def search_documents(query: str, limit: int = 10) -> str:
    """Search document content using semantic similarity (vector search).

    Use this tool to find relevant passages from PDF documents, source content,
    and AI-generated insights. Good for questions about document content,
    policies, procedures, recommendations, or any text in the original documents.

    Args:
        query: Natural language search query
        limit: Maximum number of results (default 10)
    """
    source_id, notebook_id = _get_scope()

    async def _query():
        from open_notebook.domain.models import model_manager

        embedding_model = await model_manager.get_embedding_model()
        query_embedding = embedding_model.embed_query(query)

        # Build source filter for scoping
        source_filter = ""
        notebook_sources_subquery = ""
        if source_id:
            source_filter = f"AND source = {ensure_record_id(source_id)}"
        elif notebook_id:
            notebook_sources_subquery = f"AND source IN (SELECT out FROM reference WHERE in = {ensure_record_id(notebook_id)})"
            source_filter = notebook_sources_subquery

        # Search source_embedding (document chunks)
        chunks_query = f"""
            SELECT
                id, source as parent_id, content,
                vector::similarity::cosine(embedding, $query_embedding) as similarity,
                'chunk' as result_type
            FROM source_embedding
            WHERE embedding IS NOT NONE
            AND array::len(embedding) = array::len($query_embedding)
            AND vector::similarity::cosine(embedding, $query_embedding) >= 0.3
            {source_filter}
            ORDER BY similarity DESC
            LIMIT $limit
        """

        # Search source_insight (AI insights)
        insights_query = f"""
            SELECT
                id, source as parent_id, content, insight_type,
                vector::similarity::cosine(embedding, $query_embedding) as similarity,
                'insight' as result_type
            FROM source_insight
            WHERE embedding IS NOT NONE
            AND array::len(embedding) = array::len($query_embedding)
            AND vector::similarity::cosine(embedding, $query_embedding) >= 0.3
            {source_filter}
            ORDER BY similarity DESC
            LIMIT $limit
        """

        chunks_result = await repo_query(
            chunks_query, {"query_embedding": query_embedding, "limit": limit}
        )
        insights_result = await repo_query(
            insights_query, {"query_embedding": query_embedding, "limit": limit}
        )

        # Merge and sort by similarity
        all_results = chunks_result + insights_result
        all_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return all_results[:limit]

    try:
        results = _run_async(_query())
        formatted = []
        for r in results:
            content = r.get("content", "")
            if len(content) > 300:
                content = content[:300] + "..."
            formatted.append(
                {
                    "id": str(r.get("id", "")),
                    "parent_id": str(r.get("parent_id", "")),
                    "type": r.get("result_type", "chunk"),
                    "content": content,
                    "similarity": round(r.get("similarity", 0), 3),
                    "insight_type": r.get("insight_type"),
                }
            )

        return json.dumps(
            {
                "tool": "search_documents",
                "query": query,
                "results": formatted,
                "showing": len(formatted),
            }
        )
    except Exception as e:
        logger.error(f"search_documents error: {e}")
        return json.dumps({"error": str(e), "results": []})


@tool
def text_search_documents(query: str, limit: int = 10) -> str:
    """Search document content using keyword/text search (BM25).

    Use this tool for exact keyword or phrase matching in documents.
    Better than semantic search when looking for specific terms, names,
    reference numbers, or exact phrases.

    Args:
        query: Text keywords or phrase to search for
        limit: Maximum number of results (default 10)
    """
    source_id, notebook_id = _get_scope()

    async def _query():
        source_filter = ""
        if source_id:
            source_filter = f"AND source = {ensure_record_id(source_id)}"
        elif notebook_id:
            source_filter = f"AND source IN (SELECT out FROM reference WHERE in = {ensure_record_id(notebook_id)})"

        # Search source full_text
        source_query = f"""
            SELECT
                id, id as parent_id, title,
                search::highlight('<b>', '</b>', 1) as highlight,
                search::score(1) as score,
                'source' as result_type
            FROM source
            WHERE full_text @1@ $query_text
            {source_filter.replace("source =", "id =").replace("source IN", "id IN")}
            ORDER BY score DESC
            LIMIT $limit
        """

        # Search source_embedding content
        chunks_query = f"""
            SELECT
                id, source as parent_id, content,
                search::highlight('<b>', '</b>', 1) as highlight,
                search::score(1) as score,
                'chunk' as result_type
            FROM source_embedding
            WHERE content @1@ $query_text
            {source_filter}
            ORDER BY score DESC
            LIMIT $limit
        """

        source_results = await repo_query(
            source_query, {"query_text": query, "limit": limit}
        )
        chunk_results = await repo_query(
            chunks_query, {"query_text": query, "limit": limit}
        )

        # Merge and sort by score
        all_results = source_results + chunk_results
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_results[:limit]

    try:
        results = _run_async(_query())
        formatted = []
        for r in results:
            content = r.get("highlight") or r.get("content") or r.get("title") or ""
            if len(content) > 300:
                content = content[:300] + "..."
            formatted.append(
                {
                    "id": str(r.get("id", "")),
                    "parent_id": str(r.get("parent_id", "")),
                    "type": r.get("result_type", "chunk"),
                    "content": content,
                    "score": round(r.get("score", 0), 3),
                }
            )

        return json.dumps(
            {
                "tool": "text_search_documents",
                "query": query,
                "results": formatted,
                "showing": len(formatted),
            }
        )
    except Exception as e:
        logger.error(f"text_search_documents error: {e}")
        return json.dumps({"error": str(e), "results": []})
