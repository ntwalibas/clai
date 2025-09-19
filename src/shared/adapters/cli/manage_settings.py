import click
from loguru import logger

from config import settings


@click.command(
    help="""Manage settings in ZenML secrets.

You can either export the local .env settings into ZenML secrets
or drop existing ZenML secrets. The options --export and --drop
are mutually exclusive — you must choose one.

Example:

    # Export settings to ZenML secrets
    uv run src/scripts/settings.py --export

    # Drop settings from ZenML secrets
    uv run src/scripts/settings.py --drop
"""
)
@click.option(
    "--export",
    is_flag=True,
    default=False,
    help="Exports settings in the local .env into ZenML secrets.",
)
@click.option(
    "--drop", is_flag=True, default=False, help="Deletes settings from ZenML secrets."
)
def manage_settings(export: bool, drop: bool):
    # Enforce mutual exclusivity
    if export and drop:
        raise click.UsageError(
            "Options --export and --drop are mutually exclusive. Please choose only one."
        )

    if export:
        logger.info("Exporting settings to ZenML secrets...")
        if settings.export():
            logger.success("Settings exported!")
        else:
            logger.warning(
                "Settings already exist in ZenML! Use --drop to remove them before recreating them."
            )

    elif drop:
        logger.info("Dropping settings from ZenML secrets...")
        if settings.drop():
            logger.success("Settings dropped!")
        else:
            logger.warning("Settings not found in ZenML!")

    else:
        click.echo("No action specified. Use --export or --drop.")


if __name__ == "__main__":
    manage_settings()
