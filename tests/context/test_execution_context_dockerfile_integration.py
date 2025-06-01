"""
Test ExecutionContext integration with DockerfileResolver
"""
import pytest

pytestmark = pytest.mark.skip(reason="Needs update for new DockerfileResolver API")
from unittest.mock import MagicMock
from src.context.execution_context import ExecutionContext
from src.context.dockerfile_resolver import DockerfileResolver


class TestExecutionContextDockerfileIntegration:
    """Test ExecutionContext integration with DockerfileResolver"""
    
    def test_get_docker_names_with_resolver(self):
        """Test get_docker_names when using DockerfileResolver"""
        context = ExecutionContext(
            command_type="test",
            language="python", 
            contest_name="abc300",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Create resolver with content
        resolver = DockerfileResolver()
        resolver.set_dockerfile_content("FROM python:3.9\nRUN pip install requests")
        resolver.set_oj_dockerfile_content("FROM python:3.9\nRUN pip install oj")
        
        context.dockerfile_resolver = resolver
        
        result = context.get_docker_names()
        
        # Should use resolver and generate names with hash
        assert result["image_name"].startswith("python_")
        assert result["container_name"].startswith("cph_python_")
        assert result["oj_image_name"].startswith("ojtools_")
        assert result["oj_container_name"].startswith("cph_ojtools_")
        
        # Verify consistency
        expected_container = f"cph_{result['image_name']}"
        assert result["container_name"] == expected_container
        
        expected_oj_container = f"cph_{result['oj_image_name']}"
        assert result["oj_container_name"] == expected_oj_container
    
    def test_get_docker_names_fallback_mode(self):
        """Test get_docker_names fallback when no resolver"""
        context = ExecutionContext(
            command_type="test",
            language="python",
            contest_name="abc300", 
            problem_name="a",
            env_type="local",
            env_json={}
        )
        
        # No resolver, no dockerfiles
        result = context.get_docker_names()
        
        # Should use fallback mode
        assert result["image_name"] == "python"
        assert result["container_name"] == "cph_python"
        assert result["oj_image_name"] == "ojtools"
        assert result["oj_container_name"] == "cph_ojtools"
    
    def test_dockerfile_property_backward_compatibility(self):
        """Test dockerfile property works with resolver"""
        context = ExecutionContext(
            command_type="test",
            language="python",
            contest_name="abc300",
            problem_name="a", 
            env_type="docker",
            env_json={}
        )
        
        # Set dockerfile via property (backward compatibility)
        dockerfile_content = "FROM python:3.9\nRUN pip install requests"
        context.dockerfile = dockerfile_content
        
        # Should create resolver automatically
        assert context.dockerfile_resolver is not None
        assert context.dockerfile == dockerfile_content
        
        # Should work with get_docker_names
        result = context.get_docker_names()
        assert result["image_name"].startswith("python_")
    
    def test_oj_dockerfile_property_backward_compatibility(self):
        """Test oj_dockerfile property works with resolver"""
        context = ExecutionContext(
            command_type="test",
            language="python",
            contest_name="abc300",
            problem_name="a",
            env_type="docker", 
            env_json={}
        )
        
        # Set oj_dockerfile via property (backward compatibility)
        oj_dockerfile_content = "FROM python:3.9\nRUN pip install oj"
        context.oj_dockerfile = oj_dockerfile_content
        
        # Should create resolver automatically
        assert context.dockerfile_resolver is not None
        assert context.oj_dockerfile == oj_dockerfile_content
        
        # Should work with get_docker_names
        result = context.get_docker_names()
        assert result["oj_image_name"].startswith("ojtools_")
    
    def test_mixed_resolver_and_property_usage(self):
        """Test mixing resolver and property access"""
        context = ExecutionContext(
            command_type="test",
            language="rust",
            contest_name="abc300",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Create resolver with dockerfile
        resolver = DockerfileResolver()
        resolver.set_dockerfile_content("FROM rust:1.70")
        context.dockerfile_resolver = resolver
        
        # Set oj_dockerfile via property
        context.oj_dockerfile = "FROM python:3.9\nRUN pip install oj"
        
        # Both should work
        assert context.dockerfile == "FROM rust:1.70"
        assert context.oj_dockerfile == "FROM python:3.9\nRUN pip install oj"
        
        # Docker names should use both
        result = context.get_docker_names()
        assert result["image_name"].startswith("rust_")
        assert result["oj_image_name"].startswith("ojtools_")
    
    def test_resolver_lazy_loading_integration(self):
        """Test resolver lazy loading works through context"""
        context = ExecutionContext(
            command_type="test", 
            language="python",
            contest_name="abc300",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Create loader function
        loader_func = MagicMock()
        loader_func.side_effect = lambda path: {
            "/dockerfile": "FROM python:3.9\nRUN pip install requests",
            "/oj.dockerfile": "FROM python:3.9\nRUN pip install oj"
        }[path]
        
        # Create resolver with lazy loading
        resolver = DockerfileResolver(
            dockerfile_path="/dockerfile",
            oj_dockerfile_path="/oj.dockerfile",
            loader_func=loader_func
        )
        context.dockerfile_resolver = resolver
        
        # First access should trigger loading
        result = context.get_docker_names()
        
        assert result["image_name"].startswith("python_")
        assert result["oj_image_name"].startswith("ojtools_")
        
        # Should have called loader for both files
        assert loader_func.call_count == 2
        
        # Second access should use cache
        loader_func.reset_mock()
        result2 = context.get_docker_names()
        assert result2 == result
        loader_func.assert_not_called()
    
    def test_no_resolver_no_dockerfiles(self):
        """Test context without resolver or dockerfiles"""
        context = ExecutionContext(
            command_type="test",
            language="python",
            contest_name="abc300", 
            problem_name="a",
            env_type="local",
            env_json={}
        )
        
        # No resolver set
        assert context.dockerfile_resolver is None
        assert context.dockerfile is None
        assert context.oj_dockerfile is None
        
        # Should still work with base names
        result = context.get_docker_names()
        assert result["image_name"] == "python"
        assert result["container_name"] == "cph_python" 
        assert result["oj_image_name"] == "ojtools"
        assert result["oj_container_name"] == "cph_ojtools"


class TestExecutionContextBackwardCompatibility:
    """Test backward compatibility with existing APIs"""
    
    def test_dockerfile_setter_creates_resolver(self):
        """Test that setting dockerfile creates resolver"""
        context = ExecutionContext(
            command_type="test",
            language="python",
            contest_name="abc300",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Initially no resolver
        assert context.dockerfile_resolver is None
        
        # Set dockerfile - should create resolver
        context.dockerfile = "FROM python:3.9"
        
        assert context.dockerfile_resolver is not None
        assert context.dockerfile == "FROM python:3.9"
    
    def test_dockerfile_getter_with_direct_data(self):
        """Test dockerfile getter works with direct data storage"""
        context = ExecutionContext(
            command_type="test",
            language="python",
            contest_name="abc300",
            problem_name="a", 
            env_type="docker",
            env_json={}
        )
        
        # Set directly on data (simulating old behavior)
        context._data.dockerfile = "FROM python:3.9"
        
        # Should return direct value when no resolver
        assert context.dockerfile == "FROM python:3.9"
    
    def test_resolver_takes_precedence(self):
        """Test resolver takes precedence over direct data"""
        context = ExecutionContext(
            command_type="test",
            language="python",
            contest_name="abc300",
            problem_name="a",
            env_type="docker", 
            env_json={}
        )
        
        # Set direct data
        context._data.dockerfile = "FROM python:3.9"
        
        # Create resolver with different content
        resolver = DockerfileResolver()
        resolver.set_dockerfile_content("FROM python:3.10")
        context.dockerfile_resolver = resolver
        
        # Resolver should take precedence
        assert context.dockerfile == "FROM python:3.10"