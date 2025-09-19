from etl.domain.repositories import DocRepository
from etl.domain.value_objects import Docpage
from etl.infrastructure.utils import init_db


class DocLoader:
    def __init__(
        self,
        repository: DocRepository,
    ):
        self.repository = repository

    async def load_one(
        self,
        doc_datum: dict[str, str],
    ) -> Docpage:
        """
        Load the given document into the given repository.
        """
        await init_db()
        return await self.repository.save_one(Docpage.model_validate(doc_datum))

    async def load_many(
        self,
        doc_data: list[dict[str, str]],
    ) -> list[Docpage]:
        """
        Load all the given documents into the given repository.
        """
        await init_db()
        docpages = []

        for doc_datum in doc_data:
            docpages.append(Docpage.model_validate(doc_datum))

        return await self.repository.save_many(docpages)

    async def retrieve_one(
        self,
        command: str,
    ) -> Docpage:
        """
        Retrieve the given command's details from the given repository.
        """
        await init_db()
        return await self.repository.get(command)

    async def retrieve_many(self, commands: list[str]) -> list[Docpage]:
        """
        Retrieve all the given command's details from the given repository.
        """
        await init_db()
        return await self.repository.get(commands)
