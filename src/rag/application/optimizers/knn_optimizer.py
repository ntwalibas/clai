from collections.abc import Callable
import math

import dspy
from dspy.teleprompt import KNNFewShot
from sentence_transformers import SentenceTransformer

from config import settings


class KNNOptimizer:
    def __init__(
        self,
        metric: Callable,
        k: int,
        max_labeled_demos: int | None = None,
        max_bootstrapped_demos: int | None = None,
    ):
        self._metric = metric
        self._k = k
        self._max_labeled_demos = max_labeled_demos
        self._max_bootstrapped_demos = max_bootstrapped_demos
        self._vectorizer = dspy.Embedder(
            SentenceTransformer(settings.QDRANT_EMBEDDING_MODEL).encode
        )

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

        few_shot_bootstrap_args = {
            "metric": self._metric,
            "metric_threshold": 1.0,
            "max_labeled_demos": self._max_labeled_demos,
            "max_bootstrapped_demos": self._max_bootstrapped_demos,
            "max_rounds": max_rounds,
        }

        optimizer = KNNFewShot(
            self._k,
            [example.to_dspy() for example in program.command.trainset],
            self._vectorizer,
            **few_shot_bootstrap_args,
        )

        return optimizer.compile(program)
