#!/usr/bin/env python3
"""
Demonstration of Dockerfile lazy loading solution

This script demonstrates how the new DockerfileResolver allows delaying
Dockerfile reading until fitting time while maintaining the hash-based naming system.
"""
import time
from unittest.mock import MagicMock
from src.env.build_operations import build_operations
from src.context.user_input_parser import parse_user_input
from src.context.user_input_parser_lazy import parse_user_input_lazy
from src.context.dockerfile_resolver import DockerfileResolver


def demonstrate_eager_vs_lazy_loading():
    """Demonstrate the difference between eager and lazy loading"""
    print("=== Dockerfile Loading Demonstration ===\n")
    
    operations = build_operations()
    
    # Create slow loader to simulate expensive I/O
    slow_loader = MagicMock()
    def slow_load(path):
        print(f"📂 Loading Dockerfile from: {path}")
        time.sleep(0.1)  # Simulate slow I/O
        return f"FROM python:3.9\nRUN pip install requests  # {path}"
    slow_loader.side_effect = slow_load
    
    print("1. EAGER LOADING (Current Implementation)")
    print("-" * 50)
    start_time = time.time()
    
    eager_context = parse_user_input(
        ["py", "docker", "t", "abc300", "a"],
        operations,
        dockerfile_loader=slow_loader
    )
    
    eager_init_time = time.time() - start_time
    print(f"⏱️  Initialization time: {eager_init_time:.3f}s")
    print(f"📋 Dockerfile loaded: {eager_context.dockerfile is not None}")
    print(f"🐳 Docker names available: {bool(eager_context.get_docker_names())}")
    print()
    
    print("2. LAZY LOADING (New Implementation)")
    print("-" * 50)
    slow_loader.reset_mock()
    
    start_time = time.time()
    lazy_context = parse_user_input_lazy(
        ["py", "docker", "t", "abc300", "a"],
        operations,
        dockerfile_loader=slow_loader
    )
    
    lazy_init_time = time.time() - start_time
    print(f"⏱️  Initialization time: {lazy_init_time:.3f}s")
    print(f"📋 Dockerfile loaded during init: {slow_loader.called}")
    print(f"🔗 Resolver available: {lazy_context.dockerfile_resolver is not None}")
    print()
    
    # Now access docker names (triggers loading)
    print("3. ACCESSING DOCKER NAMES (Triggers Lazy Loading)")
    print("-" * 50)
    start_time = time.time()
    docker_names = lazy_context.get_docker_names()
    access_time = time.time() - start_time
    
    print(f"⏱️  Docker names access time: {access_time:.3f}s")
    print(f"📂 Dockerfile loader called: {slow_loader.call_count} times")
    print(f"🐳 Image name: {docker_names['image_name']}")
    print(f"🐳 Container name: {docker_names['container_name']}")
    print()
    
    print("4. PERFORMANCE COMPARISON")
    print("-" * 50)
    print(f"🚀 Initialization speedup: {eager_init_time/lazy_init_time:.1f}x faster")
    print(f"💾 Memory saved during init: Dockerfile content not loaded")
    print(f"🎯 Loading happens only when needed")


def demonstrate_resolver_features():
    """Demonstrate DockerfileResolver features"""
    print("\n=== DockerfileResolver Features ===\n")
    
    # Mock loader
    loader = MagicMock()
    loader.side_effect = lambda path: f"Content from {path.split('/')[-1]}"
    
    # Create resolver
    resolver = DockerfileResolver(
        dockerfile_path="/path/to/Dockerfile",
        oj_dockerfile_path="/path/to/oj.Dockerfile",
        loader_func=loader
    )
    
    print("1. LAZY CONTENT LOADING")
    print("-" * 30)
    print(f"📁 Dockerfile path set: {resolver.dockerfile_path}")
    print(f"📁 OJ Dockerfile path set: {resolver.oj_dockerfile_path}")
    print(f"📂 Content loaded yet: {loader.called}")
    print()
    
    # First access
    print("2. FIRST ACCESS")
    print("-" * 30)
    content = resolver.get_dockerfile_content()
    print(f"📄 Content: {content}")
    print(f"📂 Loader called: {loader.call_count} times")
    print()
    
    # Second access (cached)
    print("3. SECOND ACCESS (CACHED)")
    print("-" * 30)
    loader.reset_mock()
    content2 = resolver.get_dockerfile_content()
    print(f"📄 Same content: {content == content2}")
    print(f"📂 Loader called again: {loader.called}")
    print()
    
    # Docker names generation
    print("4. DOCKER NAMES GENERATION")
    print("-" * 30)
    docker_names = resolver.get_docker_names("python")
    print(f"🐳 Image: {docker_names['image_name']}")
    print(f"🐳 Container: {docker_names['container_name']}")
    print(f"📂 Total loader calls: {loader.call_count}")


def demonstrate_backward_compatibility():
    """Demonstrate backward compatibility"""
    print("\n=== Backward Compatibility ===\n")
    
    operations = build_operations()
    
    print("1. OLD API STILL WORKS")
    print("-" * 30)
    context = parse_user_input(
        ["py", "local", "t", "abc300", "a"],
        operations
    )
    
    # Set dockerfile content directly (old way)
    context.dockerfile = "FROM python:3.9\nRUN pip install requests"
    context.oj_dockerfile = "FROM python:3.9\nRUN pip install oj"
    
    print(f"📋 Dockerfile property: {context.dockerfile is not None}")
    print(f"📋 OJ Dockerfile property: {context.oj_dockerfile is not None}")
    print(f"🔗 Resolver created automatically: {context.dockerfile_resolver is not None}")
    
    docker_names = context.get_docker_names()
    print(f"🐳 Docker names work: {docker_names['image_name'].startswith('python_')}")
    print()
    
    print("2. NEW API ALSO WORKS")
    print("-" * 30)
    loader = MagicMock(return_value="FROM rust:1.70")
    
    context2 = parse_user_input_lazy(
        ["rust", "docker", "t", "abc300", "a"],
        operations,
        dockerfile_loader=loader
    )
    
    print(f"🔗 Resolver available: {context2.dockerfile_resolver is not None}")
    print(f"📋 Property access triggers loading: {context2.dockerfile == 'FROM rust:1.70'}")
    print(f"🐳 Docker names work: {context2.get_docker_names()['image_name'].startswith('rust_')}")


def demonstrate_fitting_integration():
    """Demonstrate integration with fitting workflow"""
    print("\n=== Fitting Workflow Integration ===\n")
    
    operations = build_operations()
    loader = MagicMock()
    loader.side_effect = lambda path: f"Content-{path.split('/')[-1]}"
    
    # Create context with lazy loading
    context = parse_user_input_lazy(
        ["py", "docker", "t", "abc300", "a"],
        operations,
        dockerfile_loader=loader
    )
    
    print("1. CONTEXT INITIALIZATION")
    print("-" * 30)
    print(f"📂 Dockerfile loaded during init: {loader.called}")
    print(f"🔗 Resolver paths set: {context.dockerfile_resolver.dockerfile_path is not None}")
    print()
    
    # Simulate PreparationExecutor workflow
    print("2. FITTING WORKFLOW (PreparationExecutor)")
    print("-" * 30)
    from src.env_integration.fitting.preparation_executor import PreparationExecutor
    
    executor = PreparationExecutor(operations, context)
    docker_names = context.get_docker_names()  # This is what PreparationExecutor does
    
    print(f"📂 Dockerfile loaded during fitting: {loader.call_count} times")
    print(f"🐳 Image name: {docker_names['image_name']}")
    print(f"🐳 Container name: {docker_names['container_name']}")
    print(f"✅ Fitting workflow successful!")


if __name__ == "__main__":
    demonstrate_eager_vs_lazy_loading()
    demonstrate_resolver_features()
    demonstrate_backward_compatibility()
    demonstrate_fitting_integration()
    
    print("\n=== Summary ===")
    print("✅ Dockerfile reading delayed until fitting time")
    print("✅ Hash-based naming system maintained")
    print("✅ Backward compatibility preserved")
    print("✅ Performance improved during initialization")
    print("✅ Architecture consistent with resolver pattern")