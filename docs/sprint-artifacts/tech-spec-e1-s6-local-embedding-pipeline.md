# Tech Spec: E1-S6 - Configure Local Embedding Pipeline

> **Story:** E1-S6
> **Epic:** ACM Data Extraction Pipeline
> **Status:** Drafted
> **Created:** 2025-12-19

---

## Overview

Configure local embedding models for ACM data vectorization using the existing Esperanto abstraction layer and Ollama integration. This enables semantic search without external API calls, meeting privacy requirements for sensitive compliance data.

---

## User Story

**As a** developer
**I want** to configure local embedding models for ACM data vectorization
**So that** semantic search works without external API calls (privacy requirement)

---

## Acceptance Criteria

- [ ] Local embedding model selected and configured (mxbai-embed-large via Ollama)
- [ ] Embedding pipeline integrated with ACM record creation
- [ ] Page content vectorized and stored in SurrealDB vector fields
- [ ] Semantic search API endpoint for ACM records
- [ ] Configuration option to choose between local and cloud embeddings
- [ ] Performance benchmarks documented (embedding speed, search latency)

---

## Technical Design

### 1. Existing Infrastructure (Already Available)

Open Notebook already has comprehensive embedding support via Esperanto:

#### ModelManager (`open_notebook/domain/models.py`)

```python
class ModelManager:
    async def get_embedding_model(self, **kwargs) -> Optional[EmbeddingModel]:
        """Get the default embedding model"""
        defaults = await self.get_defaults()
        model_id = defaults.default_embedding_model
        if model_id:
            model = await AIModel.get(model_id)
            if model:
                return self.create_embedding(model, **kwargs)
        return None
```

#### Ollama Embedding Support (`docs/features/ollama.md`)

Recommended embedding models:
| Model | Best For | Performance |
|-------|----------|-------------|
| **mxbai-embed-large** | General search | Excellent |
| **nomic-embed-text** | Document similarity | Good |

### 2. ACM Embedding Configuration

#### Environment Configuration

```bash
# .env additions for local embedding
OLLAMA_HOST=http://localhost:11434
DEFAULT_EMBEDDING_MODEL=ollama:mxbai-embed-large
ACM_EMBEDDING_BATCH_SIZE=50
ACM_EMBEDDING_ENABLED=true
```

#### ACM Settings Extension (`open_notebook/domain/acm.py`)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ACMEmbeddingConfig:
    """Configuration for ACM embedding pipeline"""
    enabled: bool = True
    model_id: Optional[str] = None  # Falls back to default embedding model
    batch_size: int = 50
    include_fields: list[str] = field(default_factory=lambda: [
        "location_in_building",
        "specific_location",
        "acm_item_description",
        "accessibility_score_notes",
        "condition_score_notes",
        "recommendations"
    ])
```

### 3. Embedding Integration with ACM Records

#### Update ACM Record Model

```python
# open_notebook/domain/acm.py - extend ACMRecord

class ACMRecord(BaseModel):
    # ... existing fields ...

    # New embedding fields
    embedding: Optional[list[float]] = None
    embedding_text: Optional[str] = None  # Combined text used for embedding
    embedding_model: Optional[str] = None
    embedded_at: Optional[datetime] = None

    def get_embedding_text(self) -> str:
        """Generate text for embedding from record fields"""
        parts = []
        for field in ACMEmbeddingConfig.include_fields:
            value = getattr(self, field, None)
            if value:
                parts.append(f"{field}: {value}")
        return "\n".join(parts)
```

#### SurrealDB Vector Field Migration

```sql
-- migrations/add_acm_embeddings.surql
DEFINE FIELD embedding ON TABLE acm_record TYPE option<array<float>>;
DEFINE FIELD embedding_text ON TABLE acm_record TYPE option<string>;
DEFINE FIELD embedding_model ON TABLE acm_record TYPE option<string>;
DEFINE FIELD embedded_at ON TABLE acm_record TYPE option<datetime>;

-- Create vector index for semantic search
DEFINE INDEX acm_embedding_idx ON TABLE acm_record
  FIELDS embedding MTREE DIMENSION 1024
  DIST COSINE TYPE F32;
```

### 4. Embedding Pipeline

#### Batch Embedding Service (`api/services/acm_embedding_service.py`)

```python
from open_notebook.domain.models import ModelManager
from open_notebook.domain.acm import ACMRecord, ACMEmbeddingConfig
from typing import List
import asyncio

class ACMEmbeddingService:
    def __init__(self, config: ACMEmbeddingConfig):
        self.config = config
        self.model_manager = ModelManager()

    async def embed_records(self, records: List[ACMRecord]) -> List[ACMRecord]:
        """Embed multiple ACM records in batches"""
        if not self.config.enabled:
            return records

        embedding_model = await self.model_manager.get_embedding_model()
        if not embedding_model:
            raise ValueError("No embedding model configured")

        # Process in batches
        for i in range(0, len(records), self.config.batch_size):
            batch = records[i:i + self.config.batch_size]
            texts = [r.get_embedding_text() for r in batch]

            # Use Esperanto's batch embedding
            embeddings = await embedding_model.embed_documents(texts)

            for record, embedding in zip(batch, embeddings):
                record.embedding = embedding
                record.embedding_text = record.get_embedding_text()
                record.embedding_model = embedding_model.model_id
                record.embedded_at = datetime.utcnow()

        return records

    async def embed_single(self, record: ACMRecord) -> ACMRecord:
        """Embed a single ACM record"""
        return (await self.embed_records([record]))[0]
```

### 5. Semantic Search API

#### Search Endpoint (`api/routers/acm.py`)

```python
@router.get("/acm/search")
async def semantic_search_acm(
    query: str,
    source_id: Optional[str] = None,
    building_id: Optional[str] = None,
    limit: int = 10,
    threshold: float = 0.7
):
    """
    Semantic search across ACM records.

    Args:
        query: Natural language search query
        source_id: Filter to specific source
        building_id: Filter to specific building
        limit: Maximum results to return
        threshold: Minimum similarity score (0-1)

    Returns:
        List of matching ACM records with similarity scores
    """
    embedding_service = ACMEmbeddingService(ACMEmbeddingConfig())
    embedding_model = await embedding_service.model_manager.get_embedding_model()

    # Embed the query
    query_embedding = await embedding_model.embed_query(query)

    # SurrealDB vector search
    filters = []
    if source_id:
        filters.append(f"source_id = '{source_id}'")
    if building_id:
        filters.append(f"building_id = '{building_id}'")

    where_clause = " AND ".join(filters) if filters else "true"

    results = await db.query(f"""
        SELECT *, vector::similarity::cosine(embedding, $query_embedding) AS score
        FROM acm_record
        WHERE {where_clause} AND embedding IS NOT NULL
        ORDER BY score DESC
        LIMIT {limit}
    """, {"query_embedding": query_embedding})

    return [r for r in results if r["score"] >= threshold]
```

### 6. Integration with ACM Extraction

#### Update Extraction Command (`commands/acm_commands.py`)

```python
async def handle_extract_acm(cmd: ExtractACMCommand):
    source = await Source.get(cmd.source_id)

    # ... existing extraction logic ...
    records = await acm_extraction_transform(source)

    # Embed records if enabled
    embedding_config = ACMEmbeddingConfig()
    if embedding_config.enabled:
        embedding_service = ACMEmbeddingService(embedding_config)
        records = await embedding_service.embed_records(records)

    # Save records with embeddings
    for record in records:
        await record.save()

    return {"status": "success", "count": len(records), "embedded": embedding_config.enabled}
```

---

## Configuration Options

### Model Selection in Settings UI

Add to Settings page (`frontend/src/app/(dashboard)/settings/page.tsx`):

```tsx
// Embedding model configuration section
<Card>
  <CardHeader>
    <CardTitle>Embedding Configuration</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label>Local Embeddings (Ollama)</Label>
        <Switch
          checked={useLocalEmbeddings}
          onCheckedChange={setUseLocalEmbeddings}
        />
      </div>
      <Select value={embeddingModel} onValueChange={setEmbeddingModel}>
        <SelectTrigger>
          <SelectValue placeholder="Select embedding model" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="ollama:mxbai-embed-large">
            mxbai-embed-large (Recommended)
          </SelectItem>
          <SelectItem value="ollama:nomic-embed-text">
            nomic-embed-text
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
  </CardContent>
</Card>
```

---

## File Changes

| File | Change |
|------|--------|
| `open_notebook/domain/acm.py` | Add embedding fields and config |
| `migrations/add_acm_embeddings.surql` | New migration for vector fields |
| `api/services/acm_embedding_service.py` | New embedding service |
| `api/routers/acm.py` | Add semantic search endpoint |
| `commands/acm_commands.py` | Integrate embedding in extraction |
| `frontend/.../settings/page.tsx` | Add embedding configuration UI |
| `.env.example` | Add embedding environment variables |

---

## Dependencies

- E1-S3: ACM Extraction Transformation (must be complete)
- E1-S4: ACM API Endpoints (must be complete)
- Ollama installed locally with mxbai-embed-large model

---

## Ollama Setup (One-time)

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull embedding model
ollama pull mxbai-embed-large

# Verify model is available
ollama list
```

---

## Testing

1. Configure Ollama embedding model in Settings
2. Upload a SAMP document with ACM extraction enabled
3. Verify embeddings are generated for ACM records
4. Test semantic search with natural language queries:
   - "high risk asbestos items"
   - "floor tiles in poor condition"
   - "accessible materials in corridors"
5. Verify vector search returns relevant results
6. Benchmark embedding speed and search latency

---

## Performance Benchmarks (Target)

| Metric | Target |
|--------|--------|
| Embedding speed | < 100ms per record |
| Batch embedding (50 records) | < 3 seconds |
| Search latency | < 200ms |
| Index size overhead | < 5KB per record |

---

## Estimated Complexity

**Medium** - Leverages existing Esperanto infrastructure, primary work is integration

---
