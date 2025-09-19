from etl.domain.services import MarkdownCleanerService


class DocCleaner:
    def clean_one(self, raw_doc: str) -> str:
        """
        Clean a single document.
        """
        return MarkdownCleanerService(raw_doc).clean()

    def clean_many(
        self,
        raw_docs: list[str],
    ) -> list[str]:
        """
        Clean multiple documents.
        """
        cleaned_docs = []

        for raw_doc in raw_docs:
            cleaned_docs.append(MarkdownCleanerService(raw_doc).clean())

        return cleaned_docs
