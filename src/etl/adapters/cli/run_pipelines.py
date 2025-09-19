from datetime import datetime as dt

import click
from loguru import logger

from etl.adapters.zenml.pipelines import docpage_etl


@click.command(
    help="""Run the ETL pipeline to crawl docpages and save them to the database.

Example:

    uv run src/etl/adapters/cli/zenml.py --no-cache --config /path/to/config.yaml
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
def run_etl(no_cache: bool, config: str):
    logger.info("Starting ETL pipeline...")

    pipeline_args = {
        "enable_cache": not no_cache,
    }

    run_args_etl = {}
    pipeline_args["config_path"] = config
    pipeline_args["run_name"] = (
        f"docpage_etl_run_{dt.now().strftime('%Y_%m_%d:%H_%M_%S')}"
    )
    docpage_etl.with_options(**pipeline_args)(**run_args_etl)

    logger.info("ETL pipeline finished running.")


if __name__ == "__main__":
    run_etl()
