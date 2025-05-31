"""
コンポジット構造の管理を担当するクラス
"""
from typing import List
from src.operations.base_request import BaseRequest


class CompositeStructure:
    """コンポジットリクエストの構造管理を担当"""
    
    def __init__(self, requests: List[BaseRequest]):
        if not all(isinstance(r, BaseRequest) for r in requests):
            raise TypeError("All elements of 'requests' must be BaseRequest (or its subclass)")
        self.requests = requests
    
    def count_leaf_requests(self):
        """
        再帰的に全ての葉(BaseCompositeRequestでCompositeRequestでないもの)の数を数える。
        """
        from src.operations.composite.composite_request import CompositeRequest
        
        count = 0
        for req in self.requests:
            if isinstance(req, CompositeRequest):
                count += req.count_leaf_requests()
            else:
                count += 1
        return count
    
    def __len__(self):
        return len(self.requests)
    
    def __iter__(self):
        return iter(self.requests)
    
    def __repr__(self):
        reqs_str = ",\n  ".join(repr(r) for r in self.requests)
        return f"CompositeStructure [\n  {reqs_str}\n]"
    
    @classmethod
    def make_optimal_structure(cls, requests, name=None):
        """
        requestsが1つだけならそのまま返し、2つ以上なら構造化する。
        ただし、nameが指定されている場合はset_nameを呼ぶ。
        """
        if len(requests) == 1:
            req = requests[0]
            if name is not None:
                req = req.set_name(name)
            return req
        return cls(requests)