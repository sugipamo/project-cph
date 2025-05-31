"""
Demo: Unified Factory Pattern

This example demonstrates how the new unified factory pattern
replaces 14+ individual factory classes with a single, 
configurable factory.
"""

from unittest.mock import Mock
from src.env_factories.unified_factory import UnifiedCommandRequestFactory
from src.env_factories.unified_selector import UnifiedFactorySelector
from src.env_factories.command_types import CommandType


def create_mock_controller():
    """Create a mock controller for demonstration"""
    controller = Mock()
    controller.env_context = Mock()
    controller.env_context.contest_name = "abc123"
    controller.env_context.problem_name = "a"
    controller.format_string = lambda x: x  # Pass-through
    controller.format_value = lambda value, node: value  # Pass-through
    return controller


def demo_unified_factory_basic():
    """Demonstrate basic unified factory usage"""
    print("=== Demo: Basic Unified Factory Usage ===")
    
    # Create controller and factory
    controller = create_mock_controller()
    factory = UnifiedCommandRequestFactory(controller)
    
    # Create different types of requests using the same factory
    print("Supported command types:", [t.value for t in factory.get_supported_types()])
    
    # Shell request
    shell_request = factory.create_request_by_type(
        CommandType.SHELL,
        cmd=["echo", "Hello World"],
        cwd="/tmp",
        show_output=True
    )
    print(f"Shell request: {shell_request.cmd}")
    
    # File copy request  
    copy_request = factory.create_request_by_type(
        CommandType.COPY,
        src="/tmp/source.txt",
        dst="/tmp/destination.txt"
    )
    print(f"Copy request: {copy_request.path} -> {copy_request.dst_path}")
    
    # Directory creation request
    mkdir_request = factory.create_request_by_type(
        CommandType.MKDIR,
        path="/tmp/new_directory"
    )
    print(f"Mkdir request: {mkdir_request.path}")
    
    # Python execution request
    python_request = factory.create_request_by_type(
        CommandType.PYTHON,
        code_or_file=["print('Hello from Python!')"],
        cwd="/tmp"
    )
    print(f"Python request: {python_request.code_or_file}")


def demo_unified_factory_from_node():
    """Demonstrate creating requests from ConfigNode-like structures"""
    print("\n=== Demo: Unified Factory from Node ===")
    
    controller = create_mock_controller()
    factory = UnifiedCommandRequestFactory(controller)
    
    # Create mock node (simulating ConfigNode)
    mock_shell_node = Mock()
    mock_shell_node.value = {
        "type": "shell",
        "cmd": ["ls", "-la"],
        "cwd": "/home",
        "show_output": True,
        "allow_failure": False
    }
    mock_shell_node.next_nodes = []
    
    # Create request from node
    request = factory.create_request_from_node(mock_shell_node)
    print(f"Request from node: {type(request).__name__}")
    print(f"Command: {request.cmd}")
    print(f"Allow failure: {request.allow_failure}")


def demo_unified_selector():
    """Demonstrate the unified factory selector"""
    print("\n=== Demo: Unified Factory Selector ===")
    
    controller = create_mock_controller()
    selector = UnifiedFactorySelector()
    
    # Get factory instance (cached)
    factory1 = selector.get_factory(controller)
    factory2 = selector.get_factory(controller)
    print(f"Factory caching works: {factory1 is factory2}")
    
    # Get factory for specific step type
    shell_factory = selector.get_factory_for_step_type("shell", controller)
    print(f"Shell factory supports shell: {shell_factory.supports_command_type(CommandType.SHELL)}")
    
    # Create request directly through selector
    request = selector.create_request_for_type(
        "copy",
        controller,
        src="/tmp/a.txt",
        dst="/tmp/b.txt"
    )
    print(f"Direct request creation: {type(request).__name__}")
    
    # Get supported types
    supported = selector.get_supported_types(controller)
    print(f"Supported types: {len(supported)} types")


def demo_factory_vs_old_pattern():
    """Demonstrate the improvement over the old factory pattern"""
    print("\n=== Demo: New vs Old Pattern Comparison ===")
    
    controller = create_mock_controller()
    
    print("OLD PATTERN (14+ separate factory classes):")
    print("- ShellCommandRequestFactory(controller)")
    print("- CopyCommandRequestFactory(controller)")
    print("- MkdirCommandRequestFactory(controller)")
    print("- TouchCommandRequestFactory(controller)")
    print("- ... (11 more classes)")
    print("Total: 14+ individual factory classes with duplicated code")
    
    print("\nNEW PATTERN (1 unified factory):")
    factory = UnifiedCommandRequestFactory(controller)
    print(f"- UnifiedCommandRequestFactory(controller)")
    print(f"- Supports {len(factory.get_supported_types())} command types")
    print(f"- Single codebase with shared logic")
    print(f"- Configurable and extensible")


def demo_backward_compatibility():
    """Demonstrate backward compatibility"""
    print("\n=== Demo: Backward Compatibility ===")
    
    controller = create_mock_controller()
    
    # Old style usage still works through the selector
    from src.env_factories import get_factory_for_step_type
    
    try:
        factory = get_factory_for_step_type("shell", controller)
        print("✓ Backward compatibility maintained")
        print(f"  Factory type: {type(factory).__name__}")
        
        # Can create requests using the same interface
        request = factory.create_request_by_type(CommandType.SHELL, cmd=["echo", "test"])
        print(f"  Created request: {type(request).__name__}")
        
    except Exception as e:
        print(f"✗ Backward compatibility issue: {e}")


if __name__ == "__main__":
    print("Unified Factory Pattern Demonstration")
    print("=====================================")
    
    demo_unified_factory_basic()
    demo_unified_factory_from_node()
    demo_unified_selector()
    demo_factory_vs_old_pattern()
    demo_backward_compatibility()
    
    print("\n=== Summary ===")
    print("✓ Reduced 14+ factory classes to 1 unified factory")
    print("✓ Eliminated code duplication")
    print("✓ Improved maintainability")
    print("✓ Maintained backward compatibility")
    print("✓ Added configuration-driven approach")
    print("✓ Simplified testing and extensibility")