import pytest

from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.composite.base_composite_request import CompositeRequestFoundation


class DummyRequest(OperationRequestFoundation):
    def __init__(self, name=None):
        super().__init__(name=name, debug_tag=None, _executed=False, _result=None, _debug_info=None)
    @property
    def operation_type(self):
        return "DUMMY"
    def _execute_core(self, driver, logger):
        return "ok"

class DummyCompositeRequest(CompositeRequestFoundation):
    def __init__(self, requests, debug_tag=None, name=None, _executed=False, _results=None, _debug_info=None):
        super().__init__(requests=requests, debug_tag=debug_tag, name=name, _executed=_executed, _results=_results, _debug_info=_debug_info)

    def _execute_core(self, driver, logger):
        return [r._execute_core(driver, logger) for r in self.requests]

def test_base_composite_request_set_name():
    reqs = [DummyRequest("a"), DummyRequest("b")]
    composite = DummyCompositeRequest(reqs)
    composite.set_name("new_name")
    assert composite.name == "new_name"

def test_base_composite_request_repr():
    reqs = [DummyRequest("a"), DummyRequest("b")]
    composite = DummyCompositeRequest(reqs, name="test")
    s = repr(composite)
    assert "CompositeFoundation" in s  # Updated to match new request_type.short_name
    assert "test" in s
    assert "a" in s and "b" in s

def test_make_composite_request_single():
    req = DummyRequest("a")
    result = DummyCompositeRequest.make_composite_request([req], debug_tag=None, name="single")
    assert isinstance(result, DummyRequest)
    assert result.name == "single"

def test_make_composite_request_multiple():
    reqs = [DummyRequest("a"), DummyRequest("b")]
    result = DummyCompositeRequest.make_composite_request(reqs, debug_tag=None, name="multi")
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
