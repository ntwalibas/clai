from collections.abc import Callable
import os

import dspy
from dspy.evaluate import Evaluate
from dspy.evaluate.evaluate import EvaluationResult


class Evaluator:
    def __init__(self, metric: Callable, display_progress=True, num_threads: int = -1):
        self._metric = metric
        self._display_progress = display_progress
        self._executor = None  # Optional, if you want to hold onto it
        if num_threads <= 0:
            self._num_threads = os.cpu_count()
        else:
            self._num_threads = num_threads

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def evaluate(
        self, program: dspy.Module, devset: list[dspy.Example]
    ) -> EvaluationResult:
        evaluate = Evaluate(
            devset=devset,
            num_threads=self._num_threads,
            display_progress=self._display_progress,
            provide_traceback=True,
        )
        return evaluate(program, metric=self._metric)
