import json
import os
import tarfile
import tempfile
from typing import Any

import dspy
from zenml.enums import ArtifactType
from zenml.io import fileio
from zenml.materializers.base_materializer import BaseMaterializer
from zenml.metadata.metadata_types import MetadataType

from rag.domain.entities import Command


class CommandMaterializer(BaseMaterializer):
    """Materializer for serializing / deserializing Command objects as JSON."""

    ASSOCIATED_TYPES = (Command,)
    ASSOCIATED_ARTIFACT_TYPE = ArtifactType.DATA

    def save(self, data: Command) -> None:
        """Serialize Command to JSON and save to artifact store."""
        filepath = os.path.join(self.uri, "command.json")
        with self.artifact_store.open(filepath, "w") as f:
            json.dump(data.dict(), f, default=str)

    def load(self, data_type: type[Any]) -> Command:
        """Load Command from JSON and reconstruct Pydantic model."""
        filepath = os.path.join(self.uri, "command.json")
        with self.artifact_store.open(filepath, "r") as f:
            data = json.load(f)
        return Command.parse_obj(data)

    def extract_metadata(self, data: Command) -> dict[str, MetadataType]:
        """Optional: extract metadata for the ZenML dashboard."""
        return {
            "command_name": data.name,
            "flag_count": len(data.flags),
            "trainset_size": len(data.trainset),
        }


class ListCommandMaterializer(BaseMaterializer):
    """Materializer for lists of Command objects."""

    ASSOCIATED_TYPES = (list,)
    ASSOCIATED_ARTIFACT_TYPE = ArtifactType.DATA

    def save(self, data: list[Command]) -> None:
        filepath = os.path.join(self.uri, "commands.json")
        with self.artifact_store.open(filepath, "w") as f:
            json.dump([c.model_dump() for c in data], f, default=str)

    def load(self, data_type: type) -> list[Command]:
        filepath = os.path.join(self.uri, "commands.json")
        with self.artifact_store.open(filepath, "r") as f:
            data = json.load(f)
        return [Command.model_validate(d) for d in data]

    def extract_metadata(self, data: list[Command]):
        return {
            "num_commands": len(data),
            "command_names": [c.name for c in data],
        }


class ListProgramMaterializer(BaseMaterializer):
    """Materializer for serializing / deserializing lists of DSPy program objects."""

    ASSOCIATED_TYPES = (list,)
    ASSOCIATED_ARTIFACT_TYPE = ArtifactType.DATA

    def save(self, data: list[dspy.Module]) -> None:
        """Serialize DSPy programs as gzipped archives and save to the artifact store."""
        for program in data:
            with tempfile.TemporaryDirectory() as tmpdir:
                clai_temp_dir = os.path.join(tmpdir, "clai_program")
                os.makedirs(clai_temp_dir, exist_ok=True)

                # Save the program into a temp folder
                program_dir = os.path.join(clai_temp_dir, f"{program.command.name}")
                os.makedirs(program_dir, exist_ok=True)
                program.save(program_dir, save_program=True)

                # Destination archive path inside the artifact store
                archived_program_path = os.path.join(
                    self.uri, "programs", f"archived_{program.command.name}.tar.gz"
                )

                # Ensure the artifact store directory exists
                fileio.makedirs(os.path.dirname(archived_program_path))

                # Stream tar.gz directly to artifact store
                with self.artifact_store.open(archived_program_path, "wb") as f:
                    with tarfile.open(fileobj=f, mode="w:gz") as tar:
                        tar.add(program_dir, arcname=os.path.basename(program_dir))

    def load(self, data_type: type[dspy.Module]) -> list[dspy.Module]:
        """Load a list of DSPy programs from the artifact store."""
        programs = []
        archive_dir = os.path.join(self.uri, "programs")

        if not fileio.exists(archive_dir):
            return programs  # No programs stored yet

        # Create a single temporary directory for all extractions
        with tempfile.TemporaryDirectory() as tmpdir:
            clai_temp_dir = os.path.join(tmpdir, "clai_program")
            os.makedirs(clai_temp_dir, exist_ok=True)

            # Iterate over all archived programs
            for entry in fileio.listdir(archive_dir):
                if not entry.endswith(".tar.gz"):
                    continue

                archive_path = os.path.join(archive_dir, entry)

                # Extract archive into clai_temp_dir
                with self.artifact_store.open(archive_path, "rb") as f:
                    with tarfile.open(fileobj=f, mode="r:gz") as tar:
                        tar.extractall(path=clai_temp_dir)

                # Folder name = archive filename without "archived_" prefix and ".tar.gz" suffix
                folder_name = entry[len("archived_") : -len(".tar.gz")]
                program_dir = os.path.join(clai_temp_dir, folder_name)

                # Load the program
                program_obj = dspy.load(program_dir)
                programs.append(program_obj)

        return programs

    def extract_metadata(self, data: list[dspy.Module]):
        return {
            "num_programs": len(data),
            "program_names": [p.command.name for p in data],
        }
