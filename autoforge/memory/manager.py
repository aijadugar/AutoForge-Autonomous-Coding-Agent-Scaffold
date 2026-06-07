from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class MemoryItem:
    key: str
    value: Any
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class MemoryManager:
    """Namespaced memory store.

    Subagents receive different namespaces, giving them independent context while
    still allowing the parent agent to read structured handoff summaries.
    """

    def __init__(self) -> None:
        self._items: dict[str, list[MemoryItem]] = defaultdict(list)

    def remember(self, namespace: str, key: str, value: Any) -> None:
        self._items[namespace].append(MemoryItem(key=key, value=value))

    def recall(self, namespace: str, key: str | None = None) -> list[Any]:
        items = self._items.get(namespace, [])
        if key is not None:
            items = [item for item in items if item.key == key]
        return [item.value for item in items]

    def summarize(self, namespace: str, limit: int = 12) -> str:
        items = self._items.get(namespace, [])[-limit:]
        fragments = [f"{item.key}: {str(item.value)[:160]}" for item in items]
        return "\n".join(fragments)
