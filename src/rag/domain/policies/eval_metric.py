from collections import Counter

import dspy

from rag.domain.value_objects import CommandInstance, FlagInstance


class EvalMetric:
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

        self._flags = {flag.name for flag in expected_command.flags}

        # 1. If the expected command name doesn't match the predicted command name
        # there is no need to calculate the metric any further
        if expected_command.name != predicted_command.name:
            return 0.0
        else:
            command_name_score = 1.0

        # 2. Calculate the score for the command arguments
        command_args_score = (
            1.0
            if sorted(expected_command.args) == sorted(predicted_command.args)
            else 0.0
        )

        # 3. Calculate the score for the command flags
        command_flags_score = self._flags_metric(
            expected_command.flags, predicted_command.flags
        )

        return (command_name_score + command_args_score + command_flags_score) / 3.0

    def _flags_metric(
        self, expected_flags: FlagInstance, predicted_flags: FlagInstance
    ) -> float:
        expected_set = {flag.name for flag in expected_flags}

        duplicates = {
            flag
            for flag, count in Counter(
                [predicted_flag.name for predicted_flag in predicted_flags]
            ).items()
            if count > 1
        }

        buckets = {"valid_flags": set(), "invalid_flags": set(), "unknown_flags": set()}

        for predicted_flag in predicted_flags:
            if predicted_flag.name in self._flags:
                buckets["valid_flags"].add(predicted_flag.name)
            else:
                key = (
                    "unknown_flags"
                    if predicted_flag.name.startswith("--")
                    else "invalid_flags"
                )
                buckets[key].add(predicted_flag.name)

        valid_flags = buckets["valid_flags"]

        tp = 0
        for expected_flag in expected_flags:
            if expected_flag.name in valid_flags:
                predicted_flag = next(
                    (
                        flag
                        for flag in predicted_flags
                        if flag.name == expected_flag.name
                    ),
                    None,
                )
                if predicted_flag:
                    if sorted(expected_flag.args) == sorted(predicted_flag.args):
                        tp += 1

        fp = len(valid_flags - expected_set)
        fn = len(expected_set - valid_flags)

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1_score = (
            (2 * precision * recall / (precision + recall))
            if (precision + recall)
            else (1.0 if not expected_set else 0.0)
        )

        denom = max(1, len(expected_flags))
        penalty = (
            0.50 * len(buckets["unknown_flags"])
            + 0.35 * len(buckets["invalid_flags"])
            + 0.15 * len(duplicates)
        ) / denom

        return max(0.0, min(1.0, f1_score - penalty))
