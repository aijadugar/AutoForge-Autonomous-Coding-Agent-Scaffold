import hashlib
import shutil
from pathlib import Path

from pydantic import BaseModel

from .common import BoolOutput, GenericOutput, ListOutput, PathInput, TextOutput, safe_path
from .registry import register_tool


class WriteFileInput(BaseModel):
    path: str
    content: str
    create_parents: bool = True


class SearchFilesInput(BaseModel):
    pattern: str
    root: str = "."


class MoveFileInput(BaseModel):
    source: str
    destination: str


class CopyFileInput(MoveFileInput):
    pass


class AppendFileInput(BaseModel):
    path: str
    content: str


class JsonOutput(GenericOutput):
    pass


@register_tool("filesystem", description="Read a UTF-8 text file")
def read_file(inp: PathInput) -> TextOutput:
    path = safe_path(inp.path)
    return TextOutput(text=path.read_text(encoding="utf-8"), metadata={"path": str(path)})


@register_tool("filesystem", risk="medium", description="Write a UTF-8 text file")
def write_file(inp: WriteFileInput) -> BoolOutput:
    path = safe_path(inp.path)
    if inp.create_parents:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(inp.content, encoding="utf-8")
    return BoolOutput(ok=True, message=f"Wrote {path}")


@register_tool("filesystem", description="Search files by glob pattern")
def search_files(inp: SearchFilesInput) -> ListOutput:
    root = safe_path(inp.root)
    items = [str(path.relative_to(root)) for path in root.rglob(inp.pattern) if path.is_file()]
    return ListOutput(items=items, count=len(items))


@register_tool("filesystem", description="Move a file within the workspace", risk="medium")
def move_file(inp: MoveFileInput) -> BoolOutput:
    src, dst = safe_path(inp.source), safe_path(inp.destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return BoolOutput(ok=True, message=f"Moved {src} to {dst}")


@register_tool("filesystem", description="Delete a file within the workspace", risk="high")
def delete_file(inp: PathInput) -> BoolOutput:
    path = safe_path(inp.path)
    path.unlink()
    return BoolOutput(ok=True, message=f"Deleted {path}")


@register_tool("filesystem", description="List directory entries")
def list_directory(inp: PathInput) -> ListOutput:
    path = safe_path(inp.path)
    items = sorted(child.name for child in path.iterdir())
    return ListOutput(items=items, count=len(items))


@register_tool("filesystem", description="Create a directory", risk="medium")
def make_directory(inp: PathInput) -> BoolOutput:
    path = safe_path(inp.path)
    path.mkdir(parents=True, exist_ok=True)
    return BoolOutput(ok=True, message=f"Created {path}")


@register_tool("filesystem", description="Copy a file", risk="medium")
def copy_file(inp: CopyFileInput) -> BoolOutput:
    src, dst = safe_path(inp.source), safe_path(inp.destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return BoolOutput(ok=True, message=f"Copied {src} to {dst}")


@register_tool("filesystem", description="Append text to a file", risk="medium")
def append_file(inp: AppendFileInput) -> BoolOutput:
    path = safe_path(inp.path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(inp.content)
    return BoolOutput(ok=True, message=f"Appended to {path}")


@register_tool("filesystem", description="Return file metadata")
def stat_file(inp: PathInput) -> GenericOutput:
    path = safe_path(inp.path)
    stat = path.stat()
    return GenericOutput(message="ok", data={"size": stat.st_size, "modified": stat.st_mtime, "is_file": path.is_file()})


@register_tool("filesystem", description="Hash file contents with SHA256")
def hash_file(inp: PathInput) -> TextOutput:
    path = safe_path(inp.path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return TextOutput(text=digest, metadata={"path": str(path)})


@register_tool("filesystem", description="Count lines in a text file")
def count_lines(inp: PathInput) -> GenericOutput:
    path = safe_path(inp.path)
    return GenericOutput(message="ok", data={"lines": len(path.read_text(encoding="utf-8").splitlines())})


@register_tool("filesystem", description="Return workspace root")
def workspace_root(inp: PathInput) -> TextOutput:
    return TextOutput(text=str(Path.cwd().resolve()), metadata={"ignored_path": inp.path})

