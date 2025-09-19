from pydantic import BaseModel, Field


class FlagInstance(BaseModel):
    name: str
    desc: str
    args: list[str]


class CommandInstance(BaseModel):
    name: str
    args: list[str] = Field(default_factory=list)
    flags: list[FlagInstance] = Field(default_factory=list)


class Example(BaseModel):
    instruction: str
    command: CommandInstance


class Flag(BaseModel):
    name: str
    desc: str
