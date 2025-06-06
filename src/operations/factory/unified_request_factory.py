"""
Unified Request Factory - Consolidates all request creation logic
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from src.env_core.step.step import Step, StepType
from src.operations.base_request import BaseRequest
from src.operations.environment.environment_manager import EnvironmentManager
from src.context.commands.base_command import Command


class RequestCreationStrategy(ABC):
    """
    Abstract strategy for creating specific types of requests.
    """
    
    @abstractmethod
    def can_handle(self, step_type: StepType) -> bool:
        """
        Check if this strategy can handle the given step type.
        
        Args:
            step_type: The type of step to check
            
        Returns:
            True if this strategy can handle the step type
        """
        pass
    
    @abstractmethod
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        """
        Create a request from the given step.
        
        Args:
            step: The step to convert
            context: Execution context
            env_manager: Environment manager for strategy-based execution
            
        Returns:
            Created request or None if cannot create
        """
        pass


class FileRequestStrategy(RequestCreationStrategy):
    """Strategy for creating file operation requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type in [
            StepType.MKDIR, StepType.TOUCH, StepType.COPY, 
            StepType.MOVE, StepType.MOVETREE, StepType.REMOVE
        ]
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.operations.file.file_request import FileRequest
        from src.operations.file.file_op_type import FileOpType
        
        # Map step type to file operation type
        op_mapping = {
            StepType.MKDIR: FileOpType.MKDIR,
            StepType.TOUCH: FileOpType.TOUCH,
            StepType.COPY: FileOpType.COPY,
            StepType.MOVE: FileOpType.MOVE,
            StepType.MOVETREE: FileOpType.COPYTREE,
            StepType.REMOVE: FileOpType.REMOVE,
        }
        
        op_type = op_mapping.get(step.type)
        if not op_type:
            return None
        
        # Format command with context
        formatted_cmd = self._format_step_values(step.cmd, context)
        
        if len(formatted_cmd) == 1:
            # Single path operations
            return FileRequest(
                op=op_type,
                path=formatted_cmd[0],
                allow_failure=step.allow_failure
            )
        elif len(formatted_cmd) >= 2:
            # Two path operations
            return FileRequest(
                op=op_type,
                path=formatted_cmd[0],
                dst_path=formatted_cmd[1],
                allow_failure=step.allow_failure
            )
        
        return None
    
    def _format_step_values(self, values: List[str], context: Any) -> List[str]:
        """Format step values with context"""
        if hasattr(context, 'format_string'):
            return [context.format_string(v) for v in values]
        return values


class ShellRequestStrategy(RequestCreationStrategy):
    """Strategy for creating shell execution requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type == StepType.SHELL
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.operations.shell.shell_request import ShellRequest
        
        # Format command with context
        formatted_cmd = self._format_step_values(step.cmd, context)
        
        # Get environment-specific settings
        timeout = env_manager.get_timeout()
        cwd = self._format_value(step.cwd, context) if step.cwd else env_manager.get_working_directory()
        shell = env_manager.get_shell()
        
        return ShellRequest(
            cmd=formatted_cmd,
            timeout=timeout,
            cwd=cwd,
            env=getattr(step, 'env', None),
            allow_failure=step.allow_failure
        )
    
    def _format_value(self, value: str, context: Any) -> str:
        """Format a single value with context"""
        if hasattr(context, 'format_string'):
            return context.format_string(value)
        return value
    
    def _format_step_values(self, values: List[str], context: Any) -> List[str]:
        """Format step values with context"""
        return [self._format_value(v, context) for v in values]


class PythonRequestStrategy(RequestCreationStrategy):
    """Strategy for creating Python execution requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type == StepType.PYTHON
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.operations.python.python_request import PythonRequest
        
        # Format and join command lines
        formatted_cmd = self._format_step_values(step.cmd, context)
        code = '\n'.join(formatted_cmd)
        
        return PythonRequest(
            code_or_file=code
        )
    
    def _format_step_values(self, values: List[str], context: Any) -> List[str]:
        """Format step values with context"""
        if hasattr(context, 'format_string'):
            return [context.format_string(v) for v in values]
        return values


class DockerRequestStrategy(RequestCreationStrategy):
    """Strategy for creating Docker operation requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type in [StepType.DOCKER_RUN, StepType.DOCKER_EXEC, StepType.DOCKER_CP]
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.operations.docker.docker_request import DockerRequest, DockerOpType
        
        # Parse docker command
        if not step.cmd:
            return None
        
        docker_cmd = step.cmd[0].lower()
        
        # Map docker commands to operations
        op_mapping = {
            'run': DockerOpType.RUN,
            'exec': DockerOpType.EXEC,
            'cp': DockerOpType.CP,
            'build': DockerOpType.BUILD,
        }
        
        op_type = op_mapping.get(docker_cmd)
        if not op_type:
            return None
        
        # Extract container name and options
        container_name = step.cmd[1] if len(step.cmd) > 1 else "default"
        options = {}
        
        if len(step.cmd) > 2:
            options['args'] = step.cmd[2:]
        
        return DockerRequest(
            op=op_type,
            container=container_name,
            options=options
        )


class ComplexRequestStrategy(RequestCreationStrategy):
    """Strategy for creating complex requests (TEST, BUILD, OJ)"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type in [StepType.TEST, StepType.BUILD, StepType.OJ]
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        if step.type == StepType.TEST:
            from src.operations.shell.shell_request import ShellRequest
            
            # Format command with context  
            formatted_cmd = self._format_step_values(step.cmd, context)
            cwd = self._format_value(step.cwd, context) if step.cwd else env_manager.get_working_directory()
            
            # Create test script that runs the program against all test cases
            contest_current_path = self._format_value('{contest_current_path}', context) if context else './contest_current'
            
            # Check for custom format options
            format_options = getattr(step, 'format_options', {}) or {}
            output_format = getattr(step, 'output_format', 'default')
            
            if output_format == 'template':
                # Use template-based formatting
                test_script = self._create_template_test_script(
                    contest_current_path, formatted_cmd, format_options
                )
            else:
                # Use default formatting
                test_script = self._create_default_test_script(contest_current_path, formatted_cmd)
            
            request = ShellRequest(
                cmd=['bash', '-c', test_script],
                timeout=env_manager.get_timeout(),
                cwd=cwd,
                env=getattr(step, 'env', None),
                show_output=getattr(step, 'show_output', True)
            )
            request.allow_failure = getattr(step, 'allow_failure', False)
            return request
        
        # For BUILD and OJ, return None for now (can be implemented later)
        return None
    
    def _format_value(self, value: str, context: Any) -> str:
        """Format a single value with context"""
        if hasattr(context, 'format_string'):
            return context.format_string(value)
        return value
    
    def _format_step_values(self, values: List[str], context: Any) -> List[str]:
        """Format step values with context"""
        return [self._format_value(v, context) for v in values]
    
    def _create_default_test_script(self, contest_current_path: str, formatted_cmd: List[str]) -> str:
        """Create default test script"""
        return f'''
        for i in {contest_current_path}/test/sample-*.in; do
            if [ -f "$i" ]; then
                echo "Testing $(basename "$i")"
                expected="${{i%.in}}.out"
                if [ -f "$expected" ]; then
                    if {' '.join(formatted_cmd)} < "$i" > output.tmp 2>error.tmp; then
                        if diff -q output.tmp "$expected" > /dev/null 2>&1; then
                            echo "✓ PASS"
                        else
                            echo "✗ FAIL"
                            echo "Expected:"
                            cat "$expected"
                            echo "Got:"
                            cat output.tmp
                        fi
                    else
                        echo "✗ ERROR"
                        echo "Program failed with error:"
                        cat error.tmp
                    fi
                    rm -f output.tmp error.tmp
                else
                    echo "Expected output file not found: $expected"
                fi
            else
                echo "No test files found"
            fi
        done
        '''
    
    def _create_template_test_script(self, contest_current_path: str, formatted_cmd: List[str], format_options: Dict[str, Any]) -> str:
        """Create template-based test script with custom formatting"""
        # Get template configuration
        templates = format_options.get('templates', {})
        default_template = templates.get('default', '{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}')
        fail_template = templates.get('fail', default_template + '\\n  Expected: {expected_output}\\n  Got:      {actual_output}')
        error_template = templates.get('error', default_template + '\\n  Error: {error_message}')
        summary_template = templates.get('summary', 'Tests: {passed:03d}/{total:03d} passed ({pass_rate:.1f}%)')
        
        # Simple template-based test script using basic shell formatting
        return f'''
        total_tests=0
        passed_tests=0
        
        for i in {contest_current_path}/test/sample-*.in; do
            if [ -f "$i" ]; then
                total_tests=$((total_tests + 1))
                test_name=$(basename "$i" .in)
                expected="${{i%.in}}.out"
                
                if [ -f "$expected" ]; then
                    start_time=$(date +%s.%N)
                    if {' '.join(formatted_cmd)} < "$i" > output.tmp 2>error.tmp; then
                        end_time=$(date +%s.%N)
                        exec_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0.000")
                        
                        if diff -q output.tmp "$expected" > /dev/null 2>&1; then
                            passed_tests=$((passed_tests + 1))
                            printf "%-25s | ✅   PASS   | %10.3fs\\n" "$test_name" "$exec_time"
                        else
                            printf "%-25s | ❌   FAIL   | %10.3fs\\n" "$test_name" "$exec_time"
                            echo "  Expected: $(cat "$expected" | tr '\\n' ' ')"
                            echo "  Got:      $(cat output.tmp | tr '\\n' ' ')"
                        fi
                    else
                        end_time=$(date +%s.%N)
                        exec_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0.000")
                        printf "%-25s | 💥  ERROR   | %10.3fs\\n" "$test_name" "$exec_time"
                        echo "  Error: $(cat error.tmp | tr '\\n' ' ')"
                    fi
                    rm -f output.tmp error.tmp
                else
                    echo "Expected output file not found: $expected"
                fi
            else
                echo "No test files found"
            fi
        done
        
        # Print summary
        if [ $total_tests -gt 0 ]; then
            pass_rate=$(echo "scale=1; $passed_tests * 100 / $total_tests" | bc -l 2>/dev/null || echo "0.0")
            printf "Tests: %03d/%03d passed (%s%%)\\n" "$passed_tests" "$total_tests" "$pass_rate"
        fi
        '''


class UnifiedRequestFactory:
    """
    Unified factory that consolidates all request creation logic.
    Uses strategy pattern to handle different request types.
    """
    
    def __init__(self):
        self._strategies: List[RequestCreationStrategy] = []
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize all request creation strategies"""
        self._strategies = [
            FileRequestStrategy(),
            ShellRequestStrategy(),
            PythonRequestStrategy(),
            DockerRequestStrategy(),
            ComplexRequestStrategy(),  # Keep last as fallback
        ]
    
    def create_request(self, step: Step, context: Any = None, env_manager: EnvironmentManager = None) -> Optional[BaseRequest]:
        """
        Create a request from a step using appropriate strategy.
        
        Args:
            step: The step to convert to a request
            context: Execution context for formatting
            env_manager: Environment manager for environment-specific logic
            
        Returns:
            Created request or None if no strategy can handle the step
        """
        # Create environment manager if not provided
        if env_manager is None:
            env_manager = EnvironmentManager.from_context(context) if context else EnvironmentManager()
        
        # Check if step should be forced to local
        if env_manager.should_force_local(step.__dict__):
            # Temporarily switch to local strategy
            original_env = env_manager._env_type
            env_manager.switch_environment('local')
            request = self._create_request_with_strategies(step, context, env_manager)
            if original_env:
                env_manager.switch_environment(original_env)
            return request
        
        return self._create_request_with_strategies(step, context, env_manager)
    
    def _create_request_with_strategies(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        """Create request using registered strategies"""
        for strategy in self._strategies:
            if strategy.can_handle(step.type):
                request = strategy.create_request(step, context, env_manager)
                if request:
                    return request
        
        return None
    
    def register_strategy(self, strategy: RequestCreationStrategy):
        """
        Register a new request creation strategy.
        
        Args:
            strategy: The strategy to register
        """
        self._strategies.append(strategy)
    
    def create_requests_from_steps(self, steps: List[Step], context: Any = None) -> List[BaseRequest]:
        """
        Create multiple requests from a list of steps.
        
        Args:
            steps: List of steps to convert
            context: Execution context
            
        Returns:
            List of created requests (skips steps that cannot be converted)
        """
        requests = []
        env_manager = EnvironmentManager.from_context(context) if context else EnvironmentManager()
        
        for step in steps:
            request = self.create_request(step, context, env_manager)
            if request:
                requests.append(request)
        
        return requests
    
    def create_composite_request(self, steps: List[Step], context: Any = None, operations = None):
        """
        Create a composite request from a list of steps.
        
        Args:
            steps: List of steps to convert
            context: Execution context
            operations: DI container for driver binding
            
        Returns:
            CompositeRequest containing all converted steps
        """
        from src.operations.composite.composite_request import CompositeRequest
        from src.operations.composite.driver_bound_request import DriverBoundRequest
        from src.operations.file.file_request import FileRequest
        
        requests = self.create_requests_from_steps(steps, context)
        
        # Bind drivers if operations container is provided
        if operations:
            bound_requests = []
            for request in requests:
                if isinstance(request, FileRequest):
                    file_driver = operations.resolve('file_driver')
                    request = DriverBoundRequest(request, file_driver)
                bound_requests.append(request)
            requests = bound_requests
        
        return CompositeRequest.make_composite_request(requests)


# Global unified factory instance
_unified_factory = UnifiedRequestFactory()


def create_request(step: Step, context: Any = None, env_manager: EnvironmentManager = None) -> Optional[BaseRequest]:
    """Create a request using the global unified factory"""
    return _unified_factory.create_request(step, context, env_manager)


def create_requests_from_steps(steps: List[Step], context: Any = None) -> List[BaseRequest]:
    """Create multiple requests using the global unified factory"""
    return _unified_factory.create_requests_from_steps(steps, context)


def create_composite_request(steps: List[Step], context: Any = None, operations = None):
    """Create a composite request using the global unified factory"""
    return _unified_factory.create_composite_request(steps, context, operations)


def register_strategy(strategy: RequestCreationStrategy):
    """Register a strategy in the global unified factory"""
    _unified_factory.register_strategy(strategy)