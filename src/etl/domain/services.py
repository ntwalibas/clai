import re
import shlex


class MarkdownCleanerService:
    """
    Cleans Nushell command markdown files by:
    - Removing everything before the first heading.
    - Keeping only specific subheadings: 'signature', 'flags', and 'examples'.
    - Removing short forms (', -x') in the 'flags' section if present.
    - Expanding combined short flags (e.g., '-am' → '-a -m') in examples.
    - Normalizing examples to use only long flags.
    """

    ALLOWED_SUBHEADINGS = {"signature", "flags", "examples"}

    def __init__(self, content: str):
        self.content = content
        self.FLAG_SYNONYMS: dict[str, str] = {}

    def _remove_before_first_heading(self) -> None:
        """Removes everything before the first Markdown heading (# ...)."""
        match = re.search(r"(# .*)", self.content, re.DOTALL)
        self.content = self.content[match.start() :] if match else ""

    def _filter_subheadings(self) -> None:
        """Removes all subheadings except 'signature', 'flags', and 'examples'."""
        lines = self.content.splitlines()
        cleaned_lines = []
        keep_section = True

        for line in lines:
            heading_match = re.match(r"^(##+)\s+(.*)", line.strip(), re.IGNORECASE)
            if heading_match:
                _, heading_text = heading_match.groups()
                heading_key = heading_text.strip().lower()
                keep_section = heading_key in self.ALLOWED_SUBHEADINGS
                if keep_section:
                    cleaned_lines.append(line)
                continue

            if keep_section:
                cleaned_lines.append(line)

        self.content = "\n".join(cleaned_lines)

    def _clean_flags_short_form(self) -> None:
        """
        Removes the short form (', -x') in the 'Flags' section if present.
        Populates FLAG_SYNONYMS dict for later example normalization.
        """
        lines = self.content.splitlines()
        cleaned_lines = []
        inside_flags_section = False

        def strip_short_form(line: str) -> str:
            # Regex: group 1 = long flag, group 2 = optional short flag
            pattern = r"(`--[^,`]+)(?:,\s*-(\w))?"

            def repl(m):
                long_flag = m.group(1)
                short_flag = m.group(2)
                # Record mapping for example normalization (strip backticks)
                if short_flag:
                    self.FLAG_SYNONYMS[f"-{short_flag}"] = long_flag.strip("`")
                # Return only long flag (keep backticks for markdown)
                return long_flag

            return re.sub(pattern, repl, line)

        for line in lines:
            if re.match(r"^##+\s+flags\b", line.strip(), re.IGNORECASE):
                inside_flags_section = True
                cleaned_lines.append(line)
                continue

            if inside_flags_section and re.match(
                r"^##+\s+\w+", line.strip(), re.IGNORECASE
            ):
                inside_flags_section = False
                cleaned_lines.append(line)
                continue

            if inside_flags_section:
                cleaned_lines.append(strip_short_form(line))
            else:
                cleaned_lines.append(line)

        self.content = "\n".join(cleaned_lines)

    def _expand_combined_short_flags(self) -> None:
        """
        Expands combined short flags in example lines.
        For example, '-am' becomes '-a -m'.
        Only affects tokens starting with '-' and having multiple letters.
        """
        lines = self.content.splitlines()
        cleaned_lines = []
        inside_examples = False

        for line in lines:
            stripped = line.strip()

            if re.match(r"^##+\s+examples\b", stripped, re.IGNORECASE):
                inside_examples = True
                cleaned_lines.append(line)
                continue

            if inside_examples and re.match(r"^##+\s+\w+", stripped, re.IGNORECASE):
                inside_examples = False
                cleaned_lines.append(line)
                continue

            if inside_examples and stripped.startswith(">"):
                prefix_match = re.match(r"^(\s*> ?)(.*)", line)
                if prefix_match:
                    prefix, cmd_text = prefix_match.groups()
                else:
                    prefix, cmd_text = "", line

                tokens = shlex.split(cmd_text)
                expanded_tokens = []

                for tok in tokens:
                    if (
                        tok.startswith("-")
                        and not tok.startswith("--")
                        and len(tok) > 2
                    ):
                        # Split combined short flags: -am -> -a -m
                        expanded_tokens.extend([f"-{c}" for c in tok[1:]])
                    else:
                        expanded_tokens.append(tok)

                new_line = prefix + " ".join(expanded_tokens)
                cleaned_lines.append(new_line)
            else:
                cleaned_lines.append(line)

        self.content = "\n".join(cleaned_lines)

    def _normalize_example_short_flags(self) -> None:
        """
        Replaces short flags in examples with their corresponding long flags
        using the FLAG_SYNONYMS dict. Uses shlex to safely handle arguments.
        """
        if not self.FLAG_SYNONYMS:
            return self.content

        lines = self.content.splitlines()
        cleaned_lines = []
        inside_examples = False

        for line in lines:
            stripped = line.strip()

            if re.match(r"^##+\s+examples\b", stripped, re.IGNORECASE):
                inside_examples = True
                cleaned_lines.append(line)
                continue

            if inside_examples and re.match(r"^##+\s+\w+", stripped, re.IGNORECASE):
                inside_examples = False
                cleaned_lines.append(line)
                continue

            if inside_examples and stripped.startswith(">"):
                prefix_match = re.match(r"^(\s*> ?)(.*)", line)
                if prefix_match:
                    prefix, cmd_text = prefix_match.groups()
                else:
                    prefix, cmd_text = "", line

                tokens = shlex.split(cmd_text)
                # Replace short flags with long flags from FLAG_SYNONYMS
                tokens = [self.FLAG_SYNONYMS.get(tok, tok) for tok in tokens]
                new_line = prefix + " ".join(tokens)
                cleaned_lines.append(new_line)
            else:
                cleaned_lines.append(line)

        self.content = "\n".join(cleaned_lines)

    def clean(self) -> str:
        """Runs the full cleaning process."""
        self._remove_before_first_heading()
        self._filter_subheadings()
        self._clean_flags_short_form()
        self._expand_combined_short_flags()
        self._normalize_example_short_flags()
        return self.content
