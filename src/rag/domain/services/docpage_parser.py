import re
import shlex
import uuid

from rag.domain.entities import Command


class DocpageParser:
    PLACEHOLDER_RE = re.compile(r"\{[^}]+\}")

    def __init__(self):
        self._flags_table = {}

    def _extract_placeholders(self, text: str):
        """Return a list of placeholders like {int}, {path}, ... in order."""
        return self.PLACEHOLDER_RE.findall(text or "")

    def _ensure_long_has_placeholders(self, long_flag: str, spec_prefix: str) -> str:
        """Ensure the long flag includes any placeholders found in the spec."""
        if self.PLACEHOLDER_RE.search(long_flag):
            return long_flag.strip()
        placeholders = self._extract_placeholders(spec_prefix)
        if placeholders:
            return f"{long_flag.strip()} {' '.join(placeholders)}"
        return long_flag.strip()

    def _extract_command_name(self, lines: list[str]) -> str:
        """Extract the command name from the first heading."""
        for line in lines:
            heading_match = re.match(r"^#{1,6}\s*`([^`]+)`", line.strip())
            if heading_match:
                return heading_match.group(1).strip()
        raise ValueError("Command name not found in markdown.")

    def _extract_description(self, lines: list[str], start_index: int) -> str:
        """Return the first non-empty line after start_index as the description."""
        for i in range(start_index + 1, len(lines)):
            if lines[i].strip():
                return lines[i].strip()
        return ""

    def _parse_flags(self, lines: list[str], start_index: int) -> list[dict]:
        """
        Parse the flags section into a structured list.
        Assumes the cleaner has already removed short flags.
        """
        flags = []
        FLAG_LINE_RE = re.compile(r"^[\*\-\u2022]?\s*`([^`]+)`\s*:\s*(.+)$")

        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if re.match(r"^#{1,6}", line):
                break

            m = FLAG_LINE_RE.match(line)
            if m:
                long_flag_with_args = m.group(1).strip()
                desc = m.group(2).strip()
                long_plain = self.PLACEHOLDER_RE.sub("", long_flag_with_args).strip()
                flags.append({"name": long_flag_with_args, "desc": desc})
                self._flags_table[long_plain] = desc
            i += 1

        return flags

    def _merge_parentheses_tokens(self, tokens: list[str]) -> list[str]:
        """Merge tokens that are inside parentheses into a single token."""
        merged = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if "(" in token:
                # Start collecting tokens inside parentheses
                parts = [token]
                paren_count = token.count("(") - token.count(")")
                i += 1
                while i < len(tokens) and paren_count > 0:
                    parts.append(tokens[i])
                    paren_count += tokens[i].count("(") - tokens[i].count(")")
                    i += 1
                merged.append(" ".join(parts))
            else:
                merged.append(token)
                i += 1
        return merged

    def _parse_example_command(self, example_code: str) -> dict | None:
        """Parse a single example command line into structured format."""
        tokens = shlex.split(example_code.strip())
        tokens = self._merge_parentheses_tokens(tokens)
        if not tokens:
            return None

        command_name = tokens[0]
        args = []
        flags = []

        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token.startswith("--"):
                plain_flag = self.PLACEHOLDER_RE.sub("", token).strip()
                desc = self._flags_table.get(plain_flag, "")
                flag_entry = {"name": plain_flag, "desc": desc, "args": []}
                j = i + 1
                while j < len(tokens) and not tokens[j].startswith("-"):
                    flag_entry["args"].append(tokens[j])
                    j += 1
                flags.append(flag_entry)
                i = j
            else:
                args.append(token)
                i += 1

        return {"name": command_name, "args": args, "flags": flags}

    def _parse_examples(self, lines: list[str], start_index: int) -> list[dict]:
        """Parse the examples section into a structured list, skipping examples with pipes."""
        examples = []
        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith("```"):
                # Get caption from previous non-empty line
                j = i - 1
                while j >= 0 and not lines[j].strip():
                    j -= 1
                caption = lines[j].strip() if j >= 0 else "example"

                i += 1
                if i < len(lines):
                    code_line = lines[i].strip()
                    if code_line.startswith(">"):
                        code_text = code_line.lstrip("> ").strip()
                        # Skip examples containing pipes
                        if "|" not in code_text:
                            parsed_cmd = self._parse_example_command(code_text)
                            if parsed_cmd:
                                examples.append(
                                    {"instruction": caption, "command": parsed_cmd}
                                )

                # Skip until closing ```
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    i += 1
                i += 1
            else:
                i += 1
        return examples

    @staticmethod
    def _construct_id(command: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, command))

    def parse(self, md_text: str) -> Command:
        """Public entry point to parse a cleaned markdown docpage into structured JSON."""
        self._flags_table = {}
        lines = md_text.splitlines()
        command = {"name": None, "desc": None, "flags": [], "trainset": []}

        # Command name
        command["name"] = self._extract_command_name(lines)

        # Description
        cmd_index = next(
            i for i, line in enumerate(lines) if line.strip().startswith("#")
        )
        command["desc"] = self._extract_description(lines, cmd_index)

        # Identify section indices
        flags_start = examples_start = None
        for i, line in enumerate(lines):
            line_strip = line.strip()
            if line_strip.startswith("#"):
                heading_text = re.sub(r"^#{1,6}\s*", "", line_strip).lower()
                if "flags" in heading_text:
                    flags_start = i + 1
                elif "examples" in heading_text:
                    examples_start = i + 1

        # Parse flags/examples
        if flags_start is not None:
            command["flags"] = self._parse_flags(lines, flags_start)
        if examples_start is not None:
            command["trainset"] = self._parse_examples(lines, examples_start)

        # Construct an ID from the command name
        command["id"] = DocpageParser._construct_id(command["name"])

        return Command.model_validate(command)
