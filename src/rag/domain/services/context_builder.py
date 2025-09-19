from functools import singledispatchmethod

from rag.domain.entities import Command


class ContextBuilder:
    @singledispatchmethod
    def build(self, payload):
        raise TypeError(f"Unsupported type for payload: {type(payload)}")

    @staticmethod
    @build.register
    def _(payload: Command) -> str:
        text = f"{payload.name}: {payload.desc}"
        for flag in payload.flags:
            text += f"\n{flag.name}: {flag.desc}"
        return text

    @staticmethod
    @build.register
    def _(payload: list) -> list[str]:
        texts = []
        for command in payload:
            text = ""
            text = f"{command.name}: {command.desc}"
            for flag in command.flags:
                text += f"\n{flag.name}: {flag.desc}"
            texts.append(text)
        return texts
