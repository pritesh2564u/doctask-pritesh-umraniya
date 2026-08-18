from abc import ABC, abstractmethod
import hashlib
import math


class EmbeddingProvider(ABC):

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(text) for text in texts]


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic embeddings for tests.

    The same text always produces the same vector.
    No API key or network connection is required.
    """

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        values: list[float] = []

        for index in range(self.dimensions):
            digest = hashlib.sha256(
                f"{text}:{index}".encode("utf-8")
            ).digest()

            integer = int.from_bytes(digest[:8], "big")

            # Convert to a deterministic value between -1 and 1.
            value = (integer / (2**64 - 1)) * 2 - 1

            values.append(value)

        # Normalize vector
        magnitude = math.sqrt(
            sum(value * value for value in values)
        )

        if magnitude == 0:
            return values

        return [
            value / magnitude
            for value in values
        ]