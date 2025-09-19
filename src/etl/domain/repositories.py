from abc import ABC, abstractmethod
from typing import TypeVar, overload

T = TypeVar("T")


class DocRepository[T](ABC):
    @abstractmethod
    async def save_one(self, page: T) -> T: ...

    @abstractmethod
    async def save_many(self, pages: list[T]) -> list[T]: ...

    @overload
    async def get(self, query: str) -> T: ...

    @overload
    async def get(self, query: list[str]) -> list[T]: ...

    @abstractmethod
    async def get(self, query): ...
