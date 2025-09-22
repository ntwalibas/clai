import dspy

from rag.application.signatures.command_generator import CommandGenerator
from rag.domain.entities import Command


class PlainRAG(dspy.Module):
    def __init__(self, command: Command, context: str):
        super().__init__()

        self.command = command
        self._context = context

        self.statement = dspy.ChainOfThought(CommandGenerator)

    def forward(self, instruction: str):
        return self.statement(context=self._context, instruction=instruction)
