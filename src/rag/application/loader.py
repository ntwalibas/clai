import asyncio
import json

from config import settings
from rag.application.services.ingestor import IngestionService
from rag.domain.entities import Command
from rag.domain.policies.example_parser import ExampleParser
from rag.domain.services.context_builder import ContextBuilder
from rag.infrastructure.encoder import Encoder
from rag.infrastructure.qdrant_repository import QdrantRepository
from rag.infrastructure.utils import qdrant_client


async def ingest(contexts: list[str], payloads: list[Command]):
    encoder = Encoder(settings.QDRANT_EMBEDDING_MODEL)

    async with qdrant_client(encoder.size) as client:
        repository = QdrantRepository(client, settings.QDRANT_COLLECTION_NAME)
        ingestion_service = IngestionService(encoder, repository)
        await ingestion_service.run(contexts, payloads)


class CommandLoader:
    def load_one(self, doc_config: dict[str, str], command: Command) -> None:
        if doc_config["command"] == command.name and "trainset" in doc_config:
            command.trainset = [
                ExampleParser.parse(example)
                for example in json.loads(doc_config["trainset"])
            ]
        context = ContextBuilder.build(command)
        asyncio.run(ingest([context], [command]))

    def load_many(
        self, doc_configs: list[dict[str, str]], commands: list[Command]
    ) -> None:
        for command in commands:
            for doc_config in doc_configs:
                if doc_config["command"] == command.name and "trainset" in doc_config:
                    command.trainset = [
                        ExampleParser.parse(example)
                        for example in json.loads(doc_config["trainset"])
                    ]

        contexts = ContextBuilder.build(commands)
        asyncio.run(ingest(contexts, commands))
