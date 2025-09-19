from zenml import pipeline

from etl.adapters.zenml.steps import retrieve_docs
from rag.adapters.zenml.steps import (
    evaluate_programs,
    load_commands,
    load_simple_rag_programs,
    parse_contents,
)


@pipeline(settings={"orchestrator": {"synchronous": False}})
def docpage_rag(doc_configs: list[dict[str, str]]) -> str:
    commands = [doc["command"] for doc in doc_configs]
    docpages = retrieve_docs(commands)
    commands = parse_contents(docpages)
    _ = load_commands(doc_configs, commands)
    programs = load_simple_rag_programs(commands)
    eval_results = evaluate_programs(doc_configs, programs)
    return eval_results
