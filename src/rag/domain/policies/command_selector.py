from abc import ABC, abstractmethod

from rag.domain.entities import Command


class CommandSelectionStrategy(ABC):
    @abstractmethod
    def select(self, candidates: list[(float, Command)]) -> Command:
        pass


class HighestScoreStrategy(CommandSelectionStrategy):
    """Pick the command with the highest score."""

    def select(self, candidates):
        if not candidates:
            return Command()  # empty command
        return max(candidates, key=lambda x: x[0])[1]


class ThresholdStrategy(CommandSelectionStrategy):
    """Pick only if score exceeds threshold, else return empty command."""

    def __init__(self, threshold: float):
        self.threshold = threshold

    def select(self, candidates):
        if not candidates:
            return Command()
        score, command = max(candidates, key=lambda x: x[0])
        return command if score > self.threshold else Command()


class CommandSelector:
    @staticmethod
    def select(
        candidates: list[(int, Command)], strategy: CommandSelectionStrategy
    ) -> Command:
        return strategy.select(candidates)
