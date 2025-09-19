import dspy

from rag.domain.value_objects import CommandInstance


class CommandGenerator(dspy.Signature):
    """
    You are a command generator.
    You receive:
    - A user instruction
    - A context containing ONLY the supported command and its description, the command flags and their descriptions if applicable

    Your job:
    - Return a JSON object describing the command name, its flags, and positional arguments.

    Rules (STRICT, IN ORDER OF PRIORITY):
    1. NEVER invent, infer, or guess. Use ONLY what is explicitly present in the user instruction and context.
    2. NEVER add flags, arguments, or options that the user did not explicitly request in their instruction, even if those flags are valid according to the context.
    3. If the user instruction asks for something not supported by the context:
       Return strictly:
       {"name": "", "args": [], "flags": []}
    4. Always return a well-formed JSON object that follows this format:
       {
         "name": "<command_name>",
         "args": ["<positional_argument>"],
         "flags": [{"name": "<flag>", "desc": "<description>", "args": ["<value>"]}]
       }
    5. Do NOT include explanations, reasoning, or any text outside the JSON object.
    """

    context: str = dspy.InputField(
        description="The command name with its description and the command's flags and their descriptions if applicable."
    )

    instruction: str = dspy.InputField(
        description="User instruction describing the task to perform in the command line."
    )

    command: CommandInstance = dspy.OutputField(
        description=(
            "A Command object with 'name', 'flags', and 'args' if the instruction can be answered, "
            "or an empty command '{'name': '', 'args': [], 'flags': []}' if the instruction cannot be answered "
            "using only the provided context."
        )
    )
