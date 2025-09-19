from uuid import UUID

from pydantic import BaseModel, Field

from rag.domain.value_objects import Example, Flag


class Command(BaseModel):
    id: UUID = Field(default=UUID(int=0))
    name: str = ""
    desc: str = ""
    flags: list[Flag] = Field(default_factory=list)
    trainset: list[Example] = Field(default_factory=list)

    def __bool__(self) -> bool:
        return self.id != UUID(int=0) or bool(self.name)
