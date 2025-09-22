from collections.abc import Callable
import math

import dspy
from dspy.teleprompt import BootstrapFewShot


class BootstrapOptimizer:
    def __init__(
        self,
        metric: Callable,
        metric_threshold: float | None = None,
        max_labeled_demos: int | None = None,
        max_bootstrapped_demos: int | None = None,
    ):
        self._metric = metric
        self._metric_threshold = metric_threshold
        self._max_labeled_demos = max_labeled_demos
        self._max_bootstrapped_demos = max_bootstrapped_demos

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def optimize(self, program: dspy.Module) -> dspy.Module:
        if not self._max_labeled_demos:
            self._max_labeled_demos = len(program.command.trainset)

        if not self._max_bootstrapped_demos:
            self._max_bootstrapped_demos = int(self._max_labeled_demos * 1.6)

        max_rounds = 1.6
        if self._max_labeled_demos > 1:
            max_rounds *= math.log10(self._max_labeled_demos)
        max_rounds = math.ceil(max_rounds)

        optimizer = BootstrapFewShot(
            metric=self._metric,
            metric_threshold=self._metric_threshold,
            max_labeled_demos=self._max_labeled_demos,
            max_bootstrapped_demos=self._max_bootstrapped_demos,
            max_rounds=max_rounds,
        )

        return optimizer.compile(
            student=program,
            trainset=[example.to_dspy() for example in program.command.trainset],
        )
