"""Container image builder configuration."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Image:
    """Defines the container image for a function.

    Examples:
        >>> image = Image(python_version="3.11", python_packages=["torch", "transformers"])
        >>> image = Image(cuda_version="12.4", system_packages=["libgl1"])
    """
    python_version: str = "3.11"
    python_packages: list[str] = field(default_factory=list)
    system_packages: list[str] = field(default_factory=list)
    cuda_version: str | None = None
    base_image: str | None = None
    dockerfile: str | None = None
    commands: list[str] = field(default_factory=list)

    def add_python_packages(self, packages: list[str]) -> "Image":
        self.python_packages.extend(packages)
        return self

    def add_system_packages(self, packages: list[str]) -> "Image":
        self.system_packages.extend(packages)
        return self

    def add_commands(self, commands: list[str]) -> "Image":
        self.commands.extend(commands)
        return self

    def to_dict(self) -> dict:
        return {
            "python_version": self.python_version,
            "python_packages": self.python_packages,
            "system_packages": self.system_packages,
            "cuda_version": self.cuda_version,
            "base_image": self.base_image,
            "dockerfile": self.dockerfile,
            "commands": self.commands,
        }
