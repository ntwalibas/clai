from qdrant_client import AsyncQdrantClient, models

from rag.domain.entities import Command


class QdrantRepository:
    def __init__(self, client: AsyncQdrantClient, collection_name: str):
        self._client = client
        self._collection_name = collection_name

    async def save_one(self, vector: list[float], payload: Command) -> bool:
        res = await self._client.upsert(
            collection_name=self._collection_name,
            points=[
                {
                    "id": str(payload.id),
                    "vector": vector,
                    "payload": payload.model_dump(),
                }
            ],
        )
        return res.status == models.UpdateStatus.COMPLETED

    async def save_many(
        self, vectors: list[list[float]], payloads: list[Command]
    ) -> None:
        res = await self._client.upsert(
            collection_name=self._collection_name,
            points=[
                {
                    "id": str(payload.id),
                    "vector": vector,
                    "payload": payload.model_dump(),
                }
                for vector, payload in zip(vectors, payloads, strict=False)
            ],
        )
        return res.status == models.UpdateStatus.COMPLETED

    async def get(self, query: list[float], limit: int = 10) -> list[(float, Command)]:
        response = await self._client.query_points(
            collection_name=self._collection_name,
            query=query,
            limit=limit,
        )

        hits = response.points
        if not hits:
            return []

        return [(hit.score, Command.model_validate(hit.payload)) for hit in hits]
