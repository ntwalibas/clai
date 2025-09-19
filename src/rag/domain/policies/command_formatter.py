from rag.domain.value_objects import CommandInstance


class CommandFormatter:
    def format(self, command: CommandInstance) -> str:
        formatted_command = command.name
        for arg in command.args:
            formatted_command += f" {arg}"

        for flag in command.flags:
            formatted_command += f" {flag.name}"
            for arg in flag.args:
                formatted_command += f" {arg}"

        return formatted_command
