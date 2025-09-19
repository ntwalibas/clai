import asyncio
from typing import Annotated

from loguru import logger
from zenml import get_step_context, step

from etl.application.cleaner import DocCleaner
from etl.application.crawler import DocCrawler
from etl.application.loader import DocLoader
from etl.infrastructure.http_repository import HttpRepository
from etl.infrastructure.mongo_repository import MongoRepository


@step(enable_cache=False)
def fetch_doc(source: str) -> Annotated[str | None, "raw_doc"]:
    try:
        crawler = DocCrawler(HttpRepository())
        content = asyncio.run(crawler.crawl_one(source))

        step_context = get_step_context()
        step_context.add_output_metadata(
            output_name="raw_doc", metadata=_get_metadata_for_one(source, content)
        )

        return content
    except RuntimeError as err:
        logger.opt(exception=err).error(
            f"Failed to crawl the documentation from source: '{source}'"
        )
        return None


@step(enable_cache=False)
def fetch_docs(
    sources: list[str],
) -> Annotated[list[str] | None, "raw_docs"]:
    try:
        crawler = DocCrawler(HttpRepository())
        contents = asyncio.run(crawler.crawl_many(sources))

        step_context = get_step_context()
        step_context.add_output_metadata(
            output_name="raw_docs",
            metadata=_get_metadata_for_many(zip(sources, contents, strict=True)),
        )

        return contents
    except RuntimeError as err:
        logger.opt(exception=err).error(
            "Failed to crawl one of many documentation pages"
        )
        return None


def _get_metadata_for_one(source: str, content: str) -> dict:
    return {"source": source, "content": content}


def _get_metadata_for_many(pages: list[tuple[str, str]]) -> dict:
    return {
        "pages": [{"source": source, "content": content} for source, content in pages],
    }


@step(enable_cache=False)
def clean_doc(
    raw_doc: str,
) -> Annotated[str, "cleaned_doc"]:
    cleaned_doc = DocCleaner().clean_one(raw_doc)

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="cleaned_doc",
        metadata={
            "cleaned_doc": clean_doc,
        },
    )

    return cleaned_doc


@step(enable_cache=False)
def clean_docs(
    raw_docs: list[str],
) -> Annotated[list[str], "cleaned_docs"]:
    cleaned_docs = DocCleaner().clean_many(raw_docs)

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="cleaned_docs",
        metadata={"cleaned_docs": cleaned_docs},
    )

    return cleaned_docs


@step(enable_cache=False)
def load_doc(
    doc_config: dict[str, str],
    cleaned_doc: str,
) -> Annotated[str, "docpage"]:
    doc_datum = {
        **doc_config,
        "content": cleaned_doc,
    }

    loader = DocLoader(MongoRepository())
    asyncio.run(loader.load_one(doc_datum))

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="docpage",
        metadata={
            "docpage": doc_datum,
        },
    )

    return doc_datum


@step(enable_cache=False)
def load_docs(
    doc_configs: list[dict[str, str]],
    cleaned_docs: list[str],
) -> Annotated[list[dict[str, str]], "docpages"]:
    doc_data = [
        {**doc, "content": content}
        for doc, content in zip(doc_configs, cleaned_docs, strict=True)
    ]

    loader = DocLoader(MongoRepository())
    asyncio.run(loader.load_many(doc_data))

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="docpages",
        metadata={"docpages": doc_data},
    )

    return doc_data


@step(enable_cache=False)
def retrieve_doc(command: str) -> Annotated[dict[str, str], "docpage"]:
    loader = DocLoader(MongoRepository())
    docpage = asyncio.run(loader.retrieve_one(command))
    doc_datum = docpage.dict()

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="docpage",
        metadata={
            "docpage": doc_datum,
        },
    )

    return doc_datum


@step(enable_cache=False)
def retrieve_docs(commands: list[str]) -> Annotated[list[dict[str, str]], "doc_pages"]:
    loader = DocLoader(MongoRepository())
    docpages = asyncio.run(loader.retrieve_many(commands))
    allowed_keys = {"command", "source", "content"}
    doc_data = [
        {k: v for k, v in docpage.dict().items() if k in allowed_keys}
        for docpage in docpages
    ]

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="doc_pages",
        metadata={"doc_pages": doc_data},
    )

    return doc_data
