"""
ACM Embedding Service

Provides embedding functionality for ACM records to enable semantic search.
Uses the existing Esperanto abstraction for multi-provider embedding support.
"""

from datetime import UTC, datetime
from typing import List, Optional

from loguru import logger

from open_notebook.domain.acm import ACMEmbeddingConfig, ACMRecord
from open_notebook.domain.models import model_manager


class ACMEmbeddingService:
    """
    Service for embedding ACM records for semantic search.

    Supports batch embedding with configurable batch sizes and
    leverages the existing model_manager for embedding model provisioning.
    """

    def __init__(self, config: Optional[ACMEmbeddingConfig] = None):
        """
        Initialize the ACM embedding service.

        Args:
            config: Optional embedding configuration. Uses defaults if not provided.
        """
        self.config = config or ACMEmbeddingConfig()

    async def embed_records(self, records: List[ACMRecord]) -> List[ACMRecord]:
        """
        Embed multiple ACM records in batches.

        Args:
            records: List of ACMRecord instances to embed.

        Returns:
            List of ACMRecord instances with embedding fields populated.

        Raises:
            ValueError: If no embedding model is configured.
        """
        if not self.config.enabled:
            logger.debug("ACM embedding is disabled, skipping")
            return records

        if not records:
            logger.debug("No records to embed")
            return records

        # Get the embedding model
        embedding_model = await model_manager.get_embedding_model()
        if not embedding_model:
            raise ValueError(
                "No embedding model configured. Please configure one in the Models section."
            )

        model_name = str(embedding_model)
        logger.info(
            f"Starting ACM embedding for {len(records)} records using {model_name}"
        )

        embedded_count = 0
        batch_size = self.config.batch_size

        # Process records in batches
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(records) + batch_size - 1) // batch_size

            logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")

            # Generate embedding text for each record
            texts = [r.get_embedding_text() for r in batch]

            # Filter out empty texts
            valid_indices = [idx for idx, text in enumerate(texts) if text]
            valid_texts = [texts[idx] for idx in valid_indices]

            if not valid_texts:
                logger.warning(f"Batch {batch_num}: No valid texts to embed")
                continue

            try:
                # Use Esperanto's batch embedding (aembed for async)
                embeddings = await embedding_model.aembed(valid_texts)

                # Assign embeddings to records
                now = datetime.now(UTC)
                for idx, embedding in zip(valid_indices, embeddings):
                    record = batch[idx]
                    record.embedding = embedding
                    record.embedding_text = texts[idx]
                    record.embedding_model = model_name
                    record.embedded_at = now
                    embedded_count += 1

                logger.debug(
                    f"Batch {batch_num}: Embedded {len(valid_texts)} records"
                )

            except Exception as e:
                logger.error(f"Batch {batch_num} embedding failed: {e}")
                # Continue with other batches even if one fails
                continue

        logger.info(f"ACM embedding complete: {embedded_count}/{len(records)} records embedded")
        return records

    async def embed_single(self, record: ACMRecord) -> ACMRecord:
        """
        Embed a single ACM record.

        Args:
            record: ACMRecord instance to embed.

        Returns:
            ACMRecord instance with embedding fields populated.
        """
        results = await self.embed_records([record])
        return results[0] if results else record

    async def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        Get embedding for a search query.

        Args:
            query: The search query text.

        Returns:
            The embedding vector for the query, or None if embedding fails.

        Raises:
            ValueError: If no embedding model is configured.
        """
        embedding_model = await model_manager.get_embedding_model()
        if not embedding_model:
            raise ValueError(
                "No embedding model configured. Please configure one in the Models section."
            )

        try:
            embeddings = await embedding_model.aembed([query])
            return embeddings[0] if embeddings else None
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise


# Global service instance for convenience
acm_embedding_service = ACMEmbeddingService()
