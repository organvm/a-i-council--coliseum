"""
Knowledge Base Module.

Provides Vector-backed RAG (Retrieval Augmented Generation) capabilities
using pgvector and LiteLLM embeddings.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import litellm
from sqlalchemy import select
from pgvector.sqlalchemy import Vector

from ..database import AsyncSessionLocal
from ..models import KnowledgeEntry as KnowledgeEntryModel

logger = logging.getLogger(__name__)
_warned_missing_embedding_keys_global = False

class KnowledgeBase:
    """RAG-enabled knowledge base using pgvector."""

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self._warned_missing_embedding_keys = False

    def _has_embedding_credentials(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))

    def _warn_missing_keys_once(self) -> None:
        global _warned_missing_embedding_keys_global
        if self._warned_missing_embedding_keys or _warned_missing_embedding_keys_global:
            return
        self._warned_missing_embedding_keys = True
        _warned_missing_embedding_keys_global = True
        logger.warning(
            "Knowledge base embeddings disabled: no OPENAI_API_KEY/ANTHROPIC_API_KEY configured; "
            "RAG add/search will use no-op fallback"
        )

    async def add_entry(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """Embed content and save to the vector database."""
        if not self._has_embedding_credentials():
            self._warn_missing_keys_once()
            return -1
        try:
            response = await litellm.aembedding(
                model=self.model_name,
                input=[content]
            )
            embedding = response.data[0]['embedding']

            async with AsyncSessionLocal() as db:
                entry = KnowledgeEntryModel(
                    content=content,
                    metadata_json=metadata or {},
                    embedding=embedding
                )
                db.add(entry)
                await db.commit()
                await db.refresh(entry)
                return entry.id
        except Exception as e:
            logger.error(f"Error adding knowledge entry: {e}")
            return -1

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform a vector similarity search."""
        if not self._has_embedding_credentials():
            self._warn_missing_keys_once()
            return []
        try:
            response = await litellm.aembedding(
                model=self.model_name,
                input=[query]
            )
            query_embedding = response.data[0]['embedding']

            async with AsyncSessionLocal() as db:
                # pgvector cosine distance search (<=>)
                stmt = select(KnowledgeEntryModel).order_by(
                    KnowledgeEntryModel.embedding.cosine_distance(query_embedding)
                ).limit(limit)
                
                result = await db.execute(stmt)
                entries = result.scalars().all()
                
                return [
                    {
                        "id": e.id,
                        "content": e.content,
                        "metadata": e.metadata_json,
                        "score": 1.0  # Cosine similarity could be calculated here
                    }
                    for e in entries
                ]
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
