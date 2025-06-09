"""Integration test for the simplified workspace system."""
import pytest

from src.application.factories.unified_request_factory import UnifiedRequestFactory
from src.infrastructure.config.di_config import configure_test_dependencies
from src.infrastructure.di_container import DIContainer
from src.infrastructure.environment.environment_manager import EnvironmentManager
from src.workflow.step.step import Step, StepType


class MockContext:
    """Mock context for testing"""

    def __init__(self):
        self.env_type = "local"
        self.language = "python"
        self.contest_name = "abc300"
        self.problem_name = "a"

    def to_format_dict(self):
        """Convert context to dictionary for formatting"""
        return {
            "env_type": self.env_type,
            "language": self.language,
            "contest_name": self.contest_name,
            "problem_name": self.problem_name
        }


class TestWorkspaceSystemIntegration:
    """Test the integrated workspace system"""

    def test_workspace_service_creation_through_di(self):
        """Test that workspace service can be created through DI container"""
        container = DIContainer()
        configure_test_dependencies(container)

        # Should be able to resolve all workspace-related services
        workspace_service = container.resolve("problem_workspace_service")
        workspace_driver = container.resolve("workspace_driver")

        assert workspace_service is not None
        assert workspace_driver is not None

        # Verify that workspace driver has a workspace service instance
        assert hasattr(workspace_driver, 'workspace_service')
        assert workspace_driver.workspace_service is not None

        # Both should be of the correct types
        from src.infrastructure.drivers.workspace.workspace_driver import WorkspaceDriver
        from src.workflow.problem_workspace_service import ProblemWorkspaceService

        assert isinstance(workspace_service, ProblemWorkspaceService)
        assert isinstance(workspace_driver, WorkspaceDriver)
        assert isinstance(workspace_driver.workspace_service, ProblemWorkspaceService)

    def test_workspace_request_creation_through_factory(self):
        """Test that workspace requests can be created through factory"""
        factory = UnifiedRequestFactory()
        context = MockContext()
        env_manager = EnvironmentManager("local")

        # Test workspace switch step
        step = Step(
            type=StepType.FILE_PREPARATION,
            cmd=["abc300", "a", "python"]
        )

        request = factory.create_request_from_step(step, context, env_manager)

        assert request is not None
        assert request.workspace_operation == "workspace_switch"
        assert request.contest == "abc300"
        assert request.problem == "a"
        assert request.language == "python"

    def test_workspace_request_execution_with_mock(self):
        """Test that workspace requests can be executed with mocked services"""
        from unittest.mock import Mock

        from src.infrastructure.drivers.workspace.workspace_driver import WorkspaceDriver
        from src.workflow.problem_workspace_service import SwitchResult
        from src.workflow.workspace_request import WorkspaceRequest

        # Create mock workspace service
        mock_service = Mock()
        mock_service.switch_to_problem.return_value = SwitchResult(
            success=True,
            message="Successfully switched to abc300/a",
            files_moved=3
        )

        # Create workspace driver with mock service
        driver = WorkspaceDriver(mock_service)

        # Create workspace request
        request = WorkspaceRequest(
            operation_type="workspace_switch",
            contest="abc300",
            problem="a",
            language="python"
        )

        # Execute request
        result = request.execute(driver)

        # Verify the result
        assert result.success is True
        assert "Successfully switched to abc300/a" in result.content
        assert result.metadata["files_moved"] == 3

        # Verify mock was called correctly
        mock_service.switch_to_problem.assert_called_once_with(
            "abc300", "a", "python", False
        )

    def test_end_to_end_workflow_step_processing(self):
        """Test complete workflow from step to execution"""
        from unittest.mock import Mock

        from src.application.orchestration.unified_driver import UnifiedDriver
        from src.workflow.problem_workspace_service import SwitchResult

        # Create mock workspace service
        mock_workspace_service = Mock()
        mock_workspace_service.switch_to_problem.return_value = SwitchResult(
            success=True,
            message="Test switch successful",
            files_moved=2
        )

        # Create workspace driver with mock service
        from src.infrastructure.drivers.workspace.workspace_driver import WorkspaceDriver
        workspace_driver = WorkspaceDriver(mock_workspace_service)

        # Create a mock container that returns our drivers
        mock_container = Mock()
        def container_resolve(key):
            if key == "workspace_driver":
                return workspace_driver
            return Mock()
        mock_container.resolve.side_effect = container_resolve

        # Create unified driver with mock container
        unified_driver = UnifiedDriver(mock_container)

        # Create factory
        factory = UnifiedRequestFactory()

        # Create step
        step = Step(
            type=StepType.FILE_PREPARATION,
            cmd=["test_contest", "test_problem", "python"]
        )

        context = MockContext()
        context.contest_name = "test_contest"
        context.problem_name = "test_problem"

        # Convert step to request
        request = factory.create_request_from_step(step, context, EnvironmentManager("local"))

        # Execute through unified driver
        result = unified_driver.execute(request)

        # Verify execution
        assert result.success is True
        assert "Test switch successful" in result.content
        mock_workspace_service.switch_to_problem.assert_called_once()

    def test_workspace_driver_handles_different_operations(self):
        """Test that workspace driver handles different operation types"""
        from unittest.mock import Mock

        from src.infrastructure.drivers.workspace.workspace_driver import WorkspaceDriver
        from src.workflow.workspace_request import WorkspaceRequest

        # Create mock workspace service
        mock_service = Mock()

        # Setup different return values for different operations
        mock_service.switch_to_problem.return_value = Mock(success=True, message="Switched")
        mock_service.archive_current_work.return_value = Mock(success=True, message="Archived")
        mock_service.get_current_workspace_info.return_value = Mock(is_working=True)
        mock_service.cleanup_workspace.return_value = (True, "Cleaned up")

        driver = WorkspaceDriver(mock_service)

        # Test workspace switch
        request1 = WorkspaceRequest("workspace_switch", "abc300", "a", "python")
        result1 = driver.execute(request1)
        assert result1.success is True
        mock_service.switch_to_problem.assert_called_once()

        # Test archive operation
        request2 = WorkspaceRequest("archive_current", "abc300", "a", "python")
        result2 = driver.execute(request2)
        assert result2.success is True
        mock_service.archive_current_work.assert_called_once()

        # Test get workspace info
        request3 = WorkspaceRequest("get_workspace_info", "abc300", "a", "python")
        result3 = driver.execute(request3)
        assert result3.success is True
        mock_service.get_current_workspace_info.assert_called_once()

        # Test cleanup
        request4 = WorkspaceRequest("cleanup_workspace", "abc300", "a", "python")
        result4 = driver.execute(request4)
        assert result4.success is True
        mock_service.cleanup_workspace.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
