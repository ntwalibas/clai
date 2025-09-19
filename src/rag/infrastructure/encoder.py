import logging

from sentence_transformers import SentenceTransformer

logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


class Encoder:
    def __init__(self, model_name: str):
        self._model = SentenceTransformer(model_name)

    @property
    def size(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    def encode_one(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()

    def encode_many(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts).tolist()
