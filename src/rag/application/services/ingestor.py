import asyncio

from loguru import logger

from rag.domain.entities import Command
from rag.infrastructure.encoder import Encoder
from rag.infrastructure.qdrant_repository import QdrantRepository

BATCH_SIZE = 64
QUEUE_SIZE = 5


class IngestionService:
    def __init__(
        self,
        encoder: Encoder,
        repository: QdrantRepository,
        batch_size: int = BATCH_SIZE,
        queue_size: int = QUEUE_SIZE,
    ):
        self.encoder = encoder
        self.repository = repository
        self.batch_size = batch_size
        self.queue_size = queue_size

    async def run(self, contexts: list[str], payloads: list[Command]):
        queue = asyncio.Queue(maxsize=self.queue_size)

        async def producer():
            for i in range(0, len(contexts), self.batch_size):
                batched_contexts = contexts[i : i + self.batch_size]

                # Encode batch in thread pool to avoid blocking
                vectors = await asyncio.to_thread(
                    self.encoder.encode_many, batched_contexts
                )

                await queue.put((vectors, payloads))
            await queue.put(None)

        async def consumer():
            while True:
                batch = await queue.get()
                if batch is None:
                    break
                vectors, payloads = batch
                success = await self.repository.save_many(vectors, payloads)
                if not success:
                    logger.warning("batch upsert failed!")

        await asyncio.gather(producer(), consumer())
