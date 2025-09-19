from rag.domain.entities import Command
from rag.domain.services.docpage_parser import DocpageParser


class DocpageService:
    def parse_one(self, doc_content: str) -> Command:
        """
        Parse a single document's content.
        """
        return DocpageParser().parse(doc_content)

    def parse_many(
        self,
        doc_contents: list[str],
    ) -> list[Command]:
        """
        Parse multiple documents' contents.
        """
        parsed_contents = []

        for doc_content in doc_contents:
            parsed_contents.append(DocpageParser().parse(doc_content))

        return parsed_contents
