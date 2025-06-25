from typing import Protocol, Any, Optional, runtime_checkable


@runtime_checkable
class ConfigNodeProtocol(Protocol):
    key: str
    value: Any
    parent: Optional['ConfigNodeProtocol']
    next_nodes: list['ConfigNodeProtocol']
    matches: set[str]