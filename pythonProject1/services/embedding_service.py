"""Placeholder for embedding model integration."""
from typing import Protocol
from abc import abstractmethod


class EmbeddingModel(Protocol):
    """Interface for embedding model (for future integration)."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Convert text to embedding vector."""
        ...

    @abstractmethod
    async def find_similar(self, embedding: list[float], threshold: float = 0.8) -> float:
        """Find similarity with known author profiles."""
        ...

# TODO: Implement real embedding model here
# Current options:
# - sentence-transformers
# - OpenAI embeddings
# - HuggingFace embeddings