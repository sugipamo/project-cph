"""
Abstract interfaces for environment fitting providers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .models import (
    ResourceStatus, ResourceRequirement, PreparationTask, 
    RebuildDecision, ContainerRequirement, NetworkRequirement
)


class ResourceInspector(ABC):
    """Abstract interface for environment resource inspection"""
    
    @abstractmethod
    def inspect_containers(self, requirements: List[ContainerRequirement]) -> Dict[str, ResourceStatus]:
        """Inspect container states against requirements
        
        Args:
            requirements: List of container requirements
            
        Returns:
            Dict mapping container identifier to ResourceStatus
        """
        pass
    
    @abstractmethod
    def inspect_directories(self, required_directories: List[str]) -> Dict[str, ResourceStatus]:
        """Inspect directory existence
        
        Args:
            required_directories: List of directory paths that should exist
            
        Returns:
            Dict mapping directory path to ResourceStatus
        """
        pass
    
    @abstractmethod
    def inspect_images(self, required_images: List[str]) -> Dict[str, ResourceStatus]:
        """Inspect image availability
        
        Args:
            required_images: List of image names that should be available
            
        Returns:
            Dict mapping image name to ResourceStatus
        """
        pass
    
    @abstractmethod
    def inspect_networks(self, requirements: List[NetworkRequirement]) -> Dict[str, ResourceStatus]:
        """Inspect network states against requirements
        
        Args:
            requirements: List of network requirements
            
        Returns:
            Dict mapping network identifier to ResourceStatus
        """
        pass
    
    @abstractmethod
    def extract_requirements_from_workflow_tasks(self, workflow_tasks: List) -> List[ResourceRequirement]:
        """Extract resource requirements from workflow tasks
        
        Args:
            workflow_tasks: List of workflow task objects or dicts
            
        Returns:
            List of ResourceRequirement objects
        """
        pass


class TaskGenerator(ABC):
    """Abstract interface for preparation task generation"""
    
    @abstractmethod
    def generate_preparation_tasks(self, statuses: Dict[str, ResourceStatus]) -> List[PreparationTask]:
        """Generate preparation tasks based on resource statuses
        
        Args:
            statuses: Dict mapping resource identifier to ResourceStatus
            
        Returns:
            List of PreparationTask objects
        """
        pass
    
    @abstractmethod
    def convert_to_workflow_requests(self, preparation_tasks: List[PreparationTask]) -> List:
        """Convert preparation tasks to workflow-compatible request objects
        
        Args:
            preparation_tasks: List of PreparationTask objects
            
        Returns:
            List of request objects ready for workflow execution
        """
        pass


class StateManager(ABC):
    """Abstract interface for environment state management"""
    
    @abstractmethod
    def check_rebuild_needed(self, context) -> RebuildDecision:
        """Check if rebuild or recreate operations are needed
        
        Args:
            context: Execution context with configuration
            
        Returns:
            RebuildDecision object with rebuild/recreate flags
        """
        pass
    
    @abstractmethod
    def update_state(self, context) -> None:
        """Update stored state with current context information
        
        Args:
            context: Execution context to store
        """
        pass
    
    @abstractmethod
    def clear_state(self, identifier: str = None) -> None:
        """Clear stored state for cleanup
        
        Args:
            identifier: Optional specific identifier to clear (clears all if None)
        """
        pass


class ErrorHandler(ABC):
    """Abstract interface for preparation error handling"""
    
    @abstractmethod
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Handle a preparation error with context
        
        Args:
            error: The exception that occurred
            context: Context information about the operation
            
        Returns:
            Error object with classification and suggestions
        """
        pass
    
    @abstractmethod
    def should_retry(self, error: Any, attempt_count: int) -> bool:
        """Determine if an operation should be retried
        
        Args:
            error: The preparation error
            attempt_count: Current attempt number (1-based)
            
        Returns:
            True if retry should be attempted
        """
        pass


@dataclass
class ProviderSet:
    """Set of providers for a specific environment type"""
    inspector: ResourceInspector
    generator: TaskGenerator
    state_manager: StateManager
    error_handler: ErrorHandler
    env_type: str
    
    def validate(self) -> bool:
        """Validate that all providers are compatible"""
        return all([
            self.inspector is not None,
            self.generator is not None,
            self.state_manager is not None,
            self.error_handler is not None,
            self.env_type is not None
        ])


class ProviderFactory(ABC):
    """Abstract factory for creating provider sets"""
    
    @abstractmethod
    def create_provider_set(self, operations, context) -> ProviderSet:
        """Create a complete provider set for the environment
        
        Args:
            operations: Operations container
            context: Execution context
            
        Returns:
            Complete ProviderSet for the environment
        """
        pass
    
    @abstractmethod
    def supports_env_type(self, env_type: str) -> bool:
        """Check if this factory supports the given environment type
        
        Args:
            env_type: Environment type to check
            
        Returns:
            True if supported
        """
        pass