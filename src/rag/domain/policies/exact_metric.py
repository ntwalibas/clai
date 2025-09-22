import dspy

from rag.domain.value_objects import CommandInstance


class ExactMetric:
    def __init__(self):
        self._flags = set()

    def __call__(
        self,
        example: dspy.Example,
        predicted: dspy.Prediction,
        trace=None,
    ) -> float:
        expected_command: CommandInstance = example.command
        predicted_command: CommandInstance = predicted.command

        return expected_command.model_dump() == predicted_command.model_dump()
