from beanie import init_beanie
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from pymongo import AsyncMongoClient

from config import settings
from etl.domain.value_objects import Docpage


async def init_db():
    mongo_host = settings.MONGO_DATABASE_HOST
    mongo_db = settings.MONGO_DATABASE_NAME

    # Connect to MongoDB
    client = AsyncMongoClient(mongo_host)

    # Initialize Beanie
    await init_beanie(database=client[mongo_db], document_models=[Docpage])


async def html_to_markdown(url):
    config = CrawlerRunConfig(
        verbose=False,
        markdown_generator=DefaultMarkdownGenerator(
            content_source="fit_html", options={"ignore_links": True}
        ),
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)

        if result.success:
            return result.markdown
        else:
            raise RuntimeError(f"Crawl failed: {result.error_message}")
