import dspy
from pydantic import BaseModel, Field


class FlagInstance(BaseModel):
    name: str
    desc: str = ""
    args: list[str] = Field(default_factory=list)


class CommandInstance(BaseModel):
    name: str
    args: list[str] = Field(default_factory=list)
    flags: list[FlagInstance] = Field(default_factory=list)


class Example(BaseModel):
    instruction: str
    command: CommandInstance

    def to_dspy(self):
        return dspy.Example(
            instruction=self.instruction,
            command=self.command,
        ).with_inputs("instruction")


class Flag(BaseModel):
    name: str
    desc: str
