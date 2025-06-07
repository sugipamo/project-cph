"""
Composite structure management class
"""
from typing import List, Iterator
from src.domain.requests.base.base_request import BaseRequest


class CompositeStructure:
    """Responsible for managing composite request structure"""
    
    def __init__(self, requests: List[BaseRequest]):
        if not all(isinstance(r, BaseRequest) for r in requests):
            raise TypeError("All elements of 'requests' must be BaseRequest (or its subclass)")
        self.requests = requests
    
    def count_leaf_requests(self) -> int:
        """
        Recursively count all leaves (BaseCompositeRequest that are not CompositeRequest).
        """
        count = 0
        for req in self.requests:
            # Check if request has count_leaf_requests method (duck typing)
            if hasattr(req, 'count_leaf_requests') and callable(getattr(req, 'count_leaf_requests')):
                count += req.count_leaf_requests()
            else:
                count += 1
        return count
    
    def __len__(self) -> int:
        return len(self.requests)
    
    def __iter__(self) -> Iterator[BaseRequest]:
        return iter(self.requests)
    
    def __repr__(self) -> str:
        reqs_str = ",\n  ".join(repr(r) for r in self.requests)
        return f"CompositeStructure [\n  {reqs_str}\n]"
    
    @classmethod
    def make_optimal_structure(cls, requests: List[BaseRequest], name: str = None) -> BaseRequest:
        """
        If requests has only one item, return it as-is; if two or more, structure it.
        However, if name is specified, call set_name.
        """
        if len(requests) == 1:
            req = requests[0]
            if name is not None:
                req = req.set_name(name)
            return req
        return cls(requests)