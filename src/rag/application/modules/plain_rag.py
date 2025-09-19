import dspy

from rag.application.signatures.command_generator import CommandGenerator


class PlainRAG(dspy.Module):
    def __init__(self, context: str):
        super().__init__()

        self._context = context

        self.statement = dspy.ChainOfThought(CommandGenerator)

    def forward(self, instruction: str):
        return self.statement(context=self._context, instruction=instruction)
