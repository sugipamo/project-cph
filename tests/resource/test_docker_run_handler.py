from src.env.resource.run.docker_run_handler import DockerRunHandler
from src.context.execution_context import ExecutionContext
from src.operations.docker.docker_request import DockerRequest, DockerOpType


def test_docker_run_handler_create_process_options():
    """Test DockerRunHandler.create_process_options method"""
    # Create a mock ExecutionContext with dockerfile attribute
    context = ExecutionContext(
        command_type="test",
        language="python",
        contest_name="abc123",
        problem_name="a",
        env_type="docker",
        env_json={"python": {"some": "config"}}
    )
    context.dockerfile = "FROM python:3.9"
    
    handler = DockerRunHandler(context)
    result = handler.create_process_options(["python", "main.py"])
    
    assert isinstance(result, DockerRequest)
    assert result.op_type == DockerOpType.EXEC
    assert "python" in result.container  # Container name should contain language
    assert result.command == "python main.py"


def test_docker_run_handler_without_dockerfile():
    """Test DockerRunHandler when context has no dockerfile attribute"""
    context = ExecutionContext(
        command_type="test",
        language="cpp",
        contest_name="abc123",
        problem_name="a",
        env_type="docker",
        env_json={"cpp": {"some": "config"}}
    )
    # No dockerfile attribute
    
    handler = DockerRunHandler(context)
    result = handler.create_process_options(["g++", "main.cpp"])
    
    assert isinstance(result, DockerRequest)
    assert result.op_type == DockerOpType.EXEC
    assert "cpp" in result.container  # Container name should contain language
    assert result.command == "g++ main.cpp"