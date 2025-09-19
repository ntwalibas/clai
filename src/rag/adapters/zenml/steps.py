from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from typing import Annotated

import dspy
import mlflow
from zenml import step

from config import settings
from rag.application.evaluators.evaluator import Evaluator
from rag.application.loader import CommandLoader
from rag.application.modules.simple_rag import SimpleRAG
from rag.application.parser import DocpageService
from rag.domain.entities import Command
from rag.domain.policies.eval_metric import EvalMetric
from rag.domain.services.context_builder import ContextBuilder
from rag.domain.value_objects import CommandInstance
from rag.infrastructure.materializers import (
    CommandMaterializer,
    ListCommandMaterializer,
    ListProgramMaterializer,
)
from rag.infrastructure.utils import configure_llm


@step(enable_cache=False, output_materializers={"parsed_content": CommandMaterializer})
def parse_content(docpage: dict[str, str]) -> Annotated[Command, "parsed_content"]:
    return DocpageService().parse_one(docpage["content"])


@step(
    enable_cache=False,
    output_materializers={"parsed_contents": ListCommandMaterializer},
)
def parse_contents(
    docpages: list[dict[str, str]],
) -> Annotated[list[Command], "parsed_contents"]:
    doc_contents = [docpage["content"] for docpage in docpages]
    return DocpageService().parse_many(doc_contents)


@step(enable_cache=False)
def load_command(
    doc_config: dict[str, str], command: Command
) -> Annotated[None, "loaded_command"]:
    CommandLoader().load_one(doc_config, command)


@step(enable_cache=False)
def load_commands(
    doc_configs: list[dict[str, str]], commands: list[Command]
) -> Annotated[None, "loaded_commands"]:
    CommandLoader().load_many(doc_configs, commands)


# @step(enable_cache=False)
# def load_simple_rag_program(command: Command) -> Annotated[dspy.Module, "loaded_program"]:
#     return SimpleRAG(command, ContextBuilder.build(command), command.trainset)


@step(
    enable_cache=False,
    output_materializers={"loaded_programs": ListProgramMaterializer},
)
def load_simple_rag_programs(
    commands: list[Command],
) -> Annotated[list[dspy.Module], "loaded_programs"]:
    return [
        SimpleRAG(command, ContextBuilder.build(command), command.trainset)
        for command in commands
    ]


@step(enable_cache=False, experiment_tracker="mlflow_docker")
def evaluate_programs(
    doc_configs: list[dict[str, str]], programs: list[dspy.Module]
) -> Annotated[list[dict[str, float]], "evaluation_results"]:
    mlflow.dspy.autolog()
    configure_llm(settings.LLM_NAME, settings.LLM_ENDPOINT)

    outputs = []

    metric = EvalMetric()
    with Evaluator(metric) as evaluator:
        tasks = []

        for doc_config in doc_configs:
            if "evalset" not in doc_config:
                continue

            evalset_j = json.loads(doc_config["evalset"])
            evalset = [
                dspy.Example(
                    instruction=example["instruction"],
                    command=CommandInstance.model_validate(example["command"]),
                ).with_inputs("instruction")
                for example in evalset_j
            ]

            for program in programs:
                if doc_config["command"] != program.command.name:
                    continue
                tasks.append((program, evalset, doc_config["command"]))

        with ThreadPoolExecutor() as step_executor:
            future_to_task = {
                step_executor.submit(
                    lambda p=program, e=evalset: ThreadPoolExecutor(max_workers=1)
                    .submit(lambda: evaluator.evaluate(p, e))
                    .result()
                ): (program, evalset, command)
                for program, evalset, command in tasks
            }

            for future in as_completed(future_to_task):
                _, _, command = future_to_task[future]
                # Blocks until DSPy threads finish
                results = future.result()
                outputs.append(
                    {
                        "command": command,
                        "score": results.score,
                    }
                )

    for output in outputs:
        mlflow.log_metric(f"Unoptimized/{output['command']}/score", output["score"])

    return outputs
