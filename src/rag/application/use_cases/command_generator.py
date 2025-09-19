from rag.application.modules.simple_rag import SimpleRAG
from rag.domain.policies.command_formatter import CommandFormatter
from rag.domain.policies.command_selector import CommandSelector, ThresholdStrategy
from rag.domain.services.context_builder import ContextBuilder
from rag.infrastructure.encoder import Encoder
from rag.infrastructure.qdrant_repository import QdrantRepository


class CommandGenerator:
    def __init__(
        self,
        qdrant_repo: QdrantRepository,
        encoder: Encoder,
        formatter: CommandFormatter,
    ):
        self._qdrant_repo = qdrant_repo
        self._encoder = encoder
        self._formatter = formatter

    async def generate(self, instruction: str) -> str:
        query = self._encoder.encode_one(instruction)
        candidates = await self._qdrant_repo.get(query)
        command = CommandSelector.select(candidates, ThresholdStrategy(0.0))

        # If no good candidate command could be found in Qdrant, there is no point running RAG
        if not command:
            return ""

        program = SimpleRAG(command, ContextBuilder.build(command), command.trainset)
        return self._formatter.format(program(instruction).command)
