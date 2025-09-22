from zenml import pipeline

from config import settings
from etl.adapters.zenml.steps import retrieve_docs
from rag.adapters.zenml.steps import (
    evaluate_programs,
    load_commands,
    load_plain_rag_programs,
    load_simple_rag_programs,
    optimize_programs,
    parse_contents,
)
from rag.infrastructure.utils import configure_llm


@pipeline(enable_cache=False, settings={"orchestrator": {"synchronous": False}})
def docpage_rag(doc_configs: list[dict[str, str]]) -> str:
    configure_llm(settings.LLM_NAME, settings.LLM_ENDPOINT)

    commands = [doc["command"] for doc in doc_configs]
    docpages = retrieve_docs(commands)
    commands = parse_contents(docpages)
    _ = load_commands(doc_configs, commands)

    simple_programs = load_simple_rag_programs(commands)
    _ = evaluate_programs("Simple-Unoptimized", doc_configs, simple_programs)
    optimized_simple_programs = optimize_programs(simple_programs)
    _ = evaluate_programs("Simple-Optimized", doc_configs, optimized_simple_programs)

    plain_programs = load_plain_rag_programs(commands)
    optimized_plain_programs = optimize_programs(plain_programs)
    _ = evaluate_programs("Plain-Optimized", doc_configs, optimized_plain_programs)
    return None
