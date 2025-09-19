#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import sys

import anyio
from prompt_toolkit import PromptSession
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import clear, print_formatted_text
from yaspin import yaspin
from yaspin.spinners import Spinners

from config import settings
from rag.application.use_cases.command_generator import CommandGenerator
from rag.domain.policies.command_formatter import CommandFormatter
from rag.infrastructure.encoder import Encoder
from rag.infrastructure.qdrant_repository import QdrantRepository
from rag.infrastructure.utils import configure_llm, qdrant_client

if "NU_VERSION" not in os.environ:
    print_formatted_text(
        "Error: CLAI must be run inside Nushell. Exiting.", fg="red", bold=True
    )
    sys.exit(1)


def shorten_path(path: str, head_len: int = 2) -> str:
    p = Path(path).expanduser().resolve()
    home = str(Path.home())
    parts = list(p.parts)

    # Replace home dir with '~'
    if str(p).startswith(home):
        parts = ["~"] + parts[len(Path(home).parts) :]

    if len(parts) <= 2:
        return os.sep.join(parts)

    new_parts = [parts[0]]  # root or '~'
    for part in parts[1:-1]:
        new_parts.append(part[:head_len])
    new_parts.append(parts[-1])  # Keep last directory/file in full
    return os.sep.join(new_parts)


class CLIState:
    def __init__(self):
        self.is_command_mode = False  # start in plain text mode
        self.text_history = InMemoryHistory()
        self.command_history = InMemoryHistory()

    @property
    def history(self):
        return self.command_history if self.is_command_mode else self.text_history

    @property
    def prompt_text(self):
        emoji = "🔥" if self.is_command_mode else "✨"
        cwd = os.getcwd()
        short_cwd = shorten_path(cwd, head_len=2)

        return HTML(
            f"\n<b><ansiyellow>{short_cwd}</ansiyellow></b> {emoji} <ansiyellow>❯</ansiyellow> "
        )


# Shared state
state = CLIState()

# Key bindings
kb = KeyBindings()


def print_welcome():
    print_formatted_text(
        HTML(
            "<ansimagenta><b>🔥 Welcome to CLAI — your AI-powered CLI! 🔥</b></ansimagenta>"
        )
    )
    print_formatted_text(
        HTML(
            "<ansicyan>✨ Ctrl+T → switch between free text and command modes</ansicyan>"
        )
    )
    print_formatted_text(HTML("<ansiyellow>🚪 Ctrl+C → exit</ansiyellow>"))


@kb.add("c-t")
def _(event):
    state.is_command_mode = not state.is_command_mode
    event.app.exit(result=None)


async def cli():
    clear()
    print_welcome()

    configure_llm(settings.LLM_NAME, settings.LLM_ENDPOINT)
    formatter = CommandFormatter()
    encoder = Encoder(settings.QDRANT_EMBEDDING_MODEL)

    # Confirmation session with NO history: used for any follow-up prompts
    confirmation_session = PromptSession()

    async with qdrant_client(encoder.size) as client:
        qdrant_repo = QdrantRepository(client, settings.QDRANT_COLLECTION_NAME)
        generator = CommandGenerator(qdrant_repo, encoder, formatter)

        while True:
            try:
                instruction_session = PromptSession(
                    history=state.command_history
                    if state.is_command_mode
                    else state.text_history,
                    key_bindings=kb,
                    cursor=CursorShape.BLINKING_BLOCK,
                )

                text = await instruction_session.prompt_async(lambda: state.prompt_text)

                if text is None:
                    clear()
                    continue

                if not text.strip():
                    continue

                # Users have a tendency to type exit or quit when they want to
                # We capture that here and honor it
                if text == "exit" or text == "quit":
                    print_formatted_text("\nExiting CLAI. Goodbye!")
                    sys.exit(0)

                if not state.is_command_mode:
                    run_opt = "<ansiblue>[<b>r</b>]un the command</ansiblue>"
                    edit_opt = "<ansiblue>[<b>e</b>]dit the command</ansiblue>"
                    nothing_opt = "<ansiblue>or do [<b>n</b>]othing</ansiblue>"
                    choices_text = HTML(
                        f"<b>How would you like to proceed?</b> {run_opt}, {edit_opt}, {nothing_opt}<b>:</b> "
                    )

                    with yaspin(
                        Spinners.dots, text="Generating command...", color="yellow"
                    ) as spinner:
                        formatted_command = await generator.generate(text)
                        spinner.stop()
                        if not formatted_command:
                            print_formatted_text(
                                HTML(
                                    "<ansired>💥 Could not generate a command from the given instruction.</ansired>"
                                )
                            )
                            continue
                        else:
                            print_formatted_text(
                                HTML(
                                    f"✅ Generated command: <ansigreen><b>{formatted_command}</b></ansigreen>"
                                )
                            )

                    choice = ""
                    while choice not in ["r", "e", "n"]:
                        choice = await confirmation_session.prompt_async(choices_text)
                        choice = choice.strip().lower()

                    if choice == "r":
                        try:
                            subprocess.run(["nu", "-c", formatted_command], check=True)
                        except subprocess.CalledProcessError as e:
                            print_formatted_text(
                                HTML(f"<ansired>Command failed: {e}</ansired>")
                            )

                    elif choice == "e":
                        state.is_command_mode = True
                        edit_session = PromptSession(
                            history=state.command_history, key_bindings=kb
                        )
                        edited = await edit_session.prompt_async(
                            lambda: state.prompt_text, default=formatted_command
                        )
                        if edited is None:
                            clear()
                            continue

                        if edited.strip():
                            try:
                                subprocess.run(["nu", "-c", edited], check=True)
                            except subprocess.CalledProcessError as e:
                                print_formatted_text(
                                    HTML(f"<ansired>Command failed: {e}</ansired>")
                                )

                else:
                    try:
                        subprocess.run(["nu", "-c", text], check=True)
                    except subprocess.CalledProcessError as e:
                        print_formatted_text(
                            HTML(f"<ansired>Command failed: {e}</ansired>")
                        )

            except (EOFError, KeyboardInterrupt):
                print_formatted_text("\nExiting CLAI. Goodbye!")
                sys.exit(0)


if __name__ == "__main__":
    anyio.run(lambda: cli())
