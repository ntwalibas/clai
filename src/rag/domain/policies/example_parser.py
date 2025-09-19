from rag.domain.value_objects import Example


class ExampleParser:
    @staticmethod
    def parse(example: dict) -> Example:
        return Example.model_validate(example)
