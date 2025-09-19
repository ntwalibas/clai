from contextlib import asynccontextmanager

import dspy
from qdrant_client import AsyncQdrantClient, models

from config import settings


@asynccontextmanager
async def qdrant_client(vectors_size: int):
    client = AsyncQdrantClient(url=settings.QDRANT_CLIENT_URL)
    collection_name = settings.QDRANT_COLLECTION_NAME

    if not await client.collection_exists(collection_name):
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vectors_size,
                distance=models.Distance.COSINE,
            ),
        )

    try:
        yield client
    finally:
        await client.close()


def configure_llm(model_name: str, endpoint: str, temperature: float = 0.0):
    model = dspy.LM(model_name, api_base=endpoint, temperature=temperature)
    dspy.configure(lm=model)
