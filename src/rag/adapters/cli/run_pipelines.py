from datetime import datetime as dt

import click
from loguru import logger

from rag.adapters.zenml.pipelines import docpage_rag


@click.command(
    help="""Run the RAG pipeline to retrieve docpages and save them in Qdrant.

Example:

     uv run src/rag/adapters/cli/zenml.py --no-cache --config /path/to/config.yaml
"""
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable cache (default: cache enabled).",
)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
    help="Path to the configuration file.",
)
def run_rag(no_cache: bool, config: str):
    logger.info("Starting RAG pipeline...")

    pipeline_args = {
        "enable_cache": not no_cache,
    }

    run_args_rag = {}
    pipeline_args["config_path"] = config
    pipeline_args["run_name"] = (
        f"docpage_rag_run_{dt.now().strftime('%Y_%m_%d:%H_%M_%S')}"
    )
    docpage_rag.with_options(**pipeline_args)(**run_args_rag)

    logger.info("RAG pipeline finished running.")


if __name__ == "__main__":
    run_rag()
