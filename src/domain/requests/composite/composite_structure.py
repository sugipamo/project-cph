"""Composite structure management class
"""
from collections.abc import Iterator
from typing import Optional

from src.domain.requests.base.base_request import OperationRequestFoundation


class CompositeStructure:
    """Responsible for managing composite request structure"""

    def __init__(self, requests: list[OperationRequestFoundation]):
        if not all(isinstance(r, OperationRequestFoundation) for r in requests):
            raise TypeError("All elements of 'requests' must be OperationRequestFoundation (or its subclass)")
        self.requests = requests

    def count_leaf_requests(self) -> int:
        """Recursively count all leaves (CompositeRequestFoundation that are not CompositeRequest).
        """
        count = 0
        for req in self.requests:
            # Check if request has count_leaf_requests method (duck typing)
            if hasattr(req, 'count_leaf_requests') and callable(req.count_leaf_requests):
                count += req.count_leaf_requests()
            else:
                count += 1
        return count

    def __len__(self) -> int:
        return len(self.requests)

    def __iter__(self) -> Iterator[OperationRequestFoundation]:
        return iter(self.requests)

    def __repr__(self) -> str:
        reqs_str = ",\n  ".join(repr(r) for r in self.requests)
        return f"CompositeStructure [\n  {reqs_str}\n]"

    @classmethod
    def make_optimal_structure(cls, requests: list[OperationRequestFoundation], name: Optional[str] = None) -> OperationRequestFoundation:
        """If requests has only one item, return it as-is; if two or more, structure it.
        However, if name is specified, call set_name.
        """
        if len(requests) == 1:
            req = requests[0]
            if name is not None:
                req = req.set_name(name)
            return req
        return cls(requests)
