from beanie import Document
import pymongo


class Docpage(Document):
    # The command whose documentation page we are working with: e.g. "glob"
    command: str

    # Where the content was sourced from: e.g. "https://www.nushell.sh/commands/docs/glob.html"
    source: str

    # The entire content of the docpage properly cleaned
    content: str

    class Settings:
        name = "docpages"
        indexes = [
            pymongo.IndexModel(
                [("command", pymongo.ASCENDING)],
                unique=True,
                name="command_unique_index",
            ),
            pymongo.IndexModel(
                [("source", pymongo.ASCENDING)], unique=True, name="source_unique_index"
            ),
        ]

        # We don't have concurrent updates on this document
        # so we can disable state management
        use_state_management = False
