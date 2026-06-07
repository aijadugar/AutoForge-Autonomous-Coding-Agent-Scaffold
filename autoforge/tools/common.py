from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class EmptyInput(BaseModel):
    pass


class PathInput(BaseModel):
    path: str


class TextInput(BaseModel):
    text: str = ""


class CommandInput(BaseModel):
    command: str
    cwd: str | None = None
    timeout_seconds: int = 30


class GenericOutput(BaseModel):
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class ListOutput(BaseModel):
    items: list[str] = Field(default_factory=list)
    count: int = 0


class TextOutput(BaseModel):
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class BoolOutput(BaseModel):
    ok: bool
    message: str = ""


def safe_path(path: str, root: Path | None = None) -> Path:
    base = (root or Path.cwd()).resolve()
    target = (base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    # The tool namespace is intentionally constrained to the configured workspace.
    if base not in target.parents and target != base:
        raise ValueError(f"Path escapes workspace: {path}")
    return target

