from functools import singledispatchmethod

from beanie import BulkWriter
from beanie.operators import In

from etl.domain.repositories import DocRepository
from etl.domain.value_objects import Docpage
from etl.infrastructure.exceptions import DocpageNotFoundError


class MongoRepository(DocRepository[Docpage]):
    async def save_one(self, page: Docpage) -> Docpage:
        return await page.save()

    async def save_many(self, pages: list[Docpage]) -> list[Docpage]:
        incoming_commands = {p.command for p in pages}
        existing_docs = await Docpage.find_all().to_list()
        existing_commands = {doc.command for doc in existing_docs}

        pages_to_update = [p for p in pages if p.command in existing_commands]
        pages_to_insert = [p for p in pages if p.command not in existing_commands]
        commands_to_delete = existing_commands - incoming_commands

        # Bulk update existing pages
        async with BulkWriter(ordered=False) as bulk_writer:
            for page in pages_to_update:
                await Docpage.find(Docpage.command == page.command).update(
                    {"$set": page.model_dump(exclude_unset=True)},
                    bulk_writer=bulk_writer,
                )

        # Insert new pages
        if pages_to_insert:
            await Docpage.insert_many(pages_to_insert)

        # Delete pages no longer present
        if commands_to_delete:
            await Docpage.find(In(Docpage.command, commands_to_delete)).delete()

        return await Docpage.find_all().to_list()

    @singledispatchmethod
    async def get(self, query):
        raise TypeError(f"Unsupported type for query: {type(query)}")

    @get.register
    async def _(self, query: str) -> Docpage:
        page = await Docpage.find_one(Docpage.command == query)
        if not page:
            raise DocpageNotFoundError(f"No Docpage found for command: {query}")
        return page

    @get.register
    async def _(self, query: list) -> list[Docpage]:
        if not all(isinstance(x, str) for x in query):
            raise TypeError("Expected the list of query to be list of 'str'.")

        return await Docpage.find(In(Docpage.command, query)).to_list()
