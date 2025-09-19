import dspy
from dspy.teleprompt import LabeledFewShot

from rag.application.signatures.command_generator import CommandGenerator
from rag.domain.entities import Command


class SimpleRAG(dspy.Module):
    def __init__(
        self,
        command: Command,
        context: str,
        trainset: list[dspy.Example],
        trainset_size: int = -1,
    ):
        super().__init__()

        self.command = command
        self._context = context
        self._trainset = trainset
        if trainset_size > 0:
            assert trainset_size <= len(trainset), (
                "Trainset size must be less than or equal to the number of examples in the trainset."
            )
            self._trainset_size = trainset_size
        else:
            self._trainset_size = len(trainset)

        self.statement = LabeledFewShot(k=self._trainset_size).compile(
            student=dspy.ChainOfThought(CommandGenerator),
            trainset=self._trainset,
            sample=True,
        )

    def forward(self, instruction: str):
        return self.statement(context=self._context, instruction=instruction)
