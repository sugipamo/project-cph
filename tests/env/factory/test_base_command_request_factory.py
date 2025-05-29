import pytest
from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.context.resolver.config_resolver import ConfigNode


class MockController:
    def __init__(self):
        self.env_context = type("EnvContext", (), {
            "contest_name": "test_contest",
            "problem_name": "a",
            "language": "python",
            "command_type": "test",
            "env_type": "local"
        })()


class ConcreteFactory(BaseCommandRequestFactory):
    """Concrete implementation for testing"""
    def create_request(self, run_step):
        return "test_request"
    
    def create_request_from_node(self, node):
        return "test_request_from_node"


def test_base_factory_format_value_string():
    """Test format_value with string value"""
    factory = ConcreteFactory(MockController())
    node = ConfigNode("test", "value")
    
    # Mock resolve_format_string
    import src.env.factory.base_command_request_factory as module
    original_resolve = module.resolve_format_string
    
    def mock_resolve(node, initial_values):
        return "formatted_value"
    
    module.resolve_format_string = mock_resolve
    
    try:
        result = factory.format_value("test_string", node)
        assert result == "formatted_value"
    finally:
        module.resolve_format_string = original_resolve


def test_base_factory_format_value_non_string():
    """Test format_value with non-string value"""
    factory = ConcreteFactory(MockController())
    node = ConfigNode("test", "value")
    
    # Test with integer
    result = factory.format_value(123, node)
    assert result == 123
    
    # Test with list
    result = factory.format_value([1, 2, 3], node)
    assert result == [1, 2, 3]


def test_base_factory_constructor():
    """Test BaseCommandRequestFactory constructor"""
    controller = MockController()
    factory = BaseCommandRequestFactory(controller)
    assert factory.controller == controller