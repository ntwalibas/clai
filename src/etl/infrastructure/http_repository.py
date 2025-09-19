from functools import singledispatchmethod

from etl.domain.repositories import DocRepository
from etl.infrastructure.utils import html_to_markdown


class HttpRepository(DocRepository[str]):
    async def save_one(self, page: str) -> str:
        """
        This method is not implemented because documentation pages are typically
        read from the remote endpoint and not saved back to it.
        """
        raise NotImplementedError(
            "HttpRepository does not support saving a documentation page."
        )

    async def save_many(self, pages: list[str]) -> list[str]:
        """
        This method is not implemented because documentation pages are typically
        read from the remote endpoint and not saved back to it.
        """
        raise NotImplementedError(
            "HttpRepository does not support saving documentation pages."
        )

    @singledispatchmethod
    async def get(self, query) -> str:
        raise TypeError(f"Unsupported type for query: {type(query)}")

    @get.register
    async def get(self, query: str) -> str:
        """
        Given the source URL, fetch the content and convert it to markdown.
        """
        try:
            return await html_to_markdown(query)
        except RuntimeError:
            raise
