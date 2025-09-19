from etl.domain.repositories import DocRepository


class DocCrawler:
    def __init__(
        self,
        repository: DocRepository,
    ):
        self.repository = repository

    async def crawl_one(self, source: str) -> str:
        """
        Given the source of the documentation,
        fetch its markdown content using the repository.
        """
        return await self.repository.get(source)

    async def crawl_many(
        self,
        sources: list[str],
    ) -> list[str]:
        """
        Fetch the markdown content from multiple documentation sources.
        """
        docs = []

        for source in sources:
            try:
                doc = await self.repository.get(source)
                docs.append(doc)
            except Exception:
                raise

        return docs
