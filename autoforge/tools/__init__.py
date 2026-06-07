from .registry import ToolRegistry, get_registry, register_tool

# Import namespaces for decorator-based self-registration.
from . import execution, filesystem, git, planning, quality, research  # noqa: F401

__all__ = ["ToolRegistry", "get_registry", "register_tool"]

