import pytest

from src.domain.requests.base.base_request import BaseRequest
from src.domain.requests.composite.base_composite_request import BaseCompositeRequest


class DummyRequest(BaseRequest):
    def __init__(self, name=None):
        super().__init__(name=name)
    @property
    def operation_type(self):
        return "DUMMY"
    def _execute_core(self, driver):
        return "ok"

class DummyCompositeRequest(BaseCompositeRequest):
    def _execute_core(self, driver):
        return [r._execute_core(driver) for r in self.requests]

def test_base_composite_request_set_name():
    reqs = [DummyRequest("a"), DummyRequest("b")]
    composite = DummyCompositeRequest(reqs)
    composite.set_name("new_name")
    assert composite.name == "new_name"

def test_base_composite_request_repr():
    reqs = [DummyRequest("a"), DummyRequest("b")]
    composite = DummyCompositeRequest(reqs, name="test")
    s = repr(composite)
    assert "DummyCompositeRequest" in s
    assert "test" in s
    assert "a" in s and "b" in s

def test_make_composite_request_single():
    req = DummyRequest("a")
    result = DummyCompositeRequest.make_composite_request([req], name="single")
    assert isinstance(result, DummyRequest)
    assert result.name == "single"

def test_make_composite_request_multiple():
    reqs = [DummyRequest("a"), DummyRequest("b")]
    result = DummyCompositeRequest.make_composite_request(reqs, name="multi")
    assert isinstance(result, DummyCompositeRequest)
    assert result.name == "multi"

def test_count_leaf_requests_nested():
    leaf1 = DummyRequest("a")
    leaf2 = DummyRequest("b")
    inner = DummyCompositeRequest([leaf1, leaf2])
    outer = DummyCompositeRequest([inner, DummyRequest("c")])
    assert outer.count_leaf_requests() == 3

def test_operation_type():
    reqs = [DummyRequest("a")]
    composite = DummyCompositeRequest(reqs)
    assert composite.operation_type.name == "COMPOSITE"
