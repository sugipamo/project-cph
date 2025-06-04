"""
Fitting functionality for environment preparation - New pluggable architecture
"""

# New pluggable architecture
from .core import (
    ResourceInspector,
    TaskGenerator,
    StateManager,
    ProviderSet,
    ResourceStatus,
    ResourceRequirement,
    ResourceType,
    PreparationTask,
    RebuildDecision,
    ContainerRequirement,
    NetworkRequirement,
    PreparationOrchestrator
)
from .registry import (
    ProviderRegistry,
    get_global_registry,
    register_provider_factory,
    get_provider_set
)
from .providers import DockerProviderFactory

# Legacy compatibility - maintains existing interface
from .legacy_compatibility import (
    LegacyPreparationExecutor as PreparationExecutor,
    create_legacy_environment_inspector as EnvironmentInspector,
    create_legacy_docker_state_manager as DockerStateManager,
    create_legacy_preparation_error_handler as PreparationErrorHandler
)

# Auto-register Docker provider
register_provider_factory("docker", DockerProviderFactory())

__all__ = [
    # New architecture components
    "ResourceInspector",
    "TaskGenerator", 
    "StateManager",
    "ProviderSet",
    "PreparationOrchestrator",
    "ProviderRegistry",
    "get_global_registry",
    "register_provider_factory",
    "get_provider_set",
    "DockerProviderFactory",
    
    # Models
    "ResourceStatus",
    "ResourceRequirement", 
    "ResourceType",
    "PreparationTask",
    "RebuildDecision",
    "ContainerRequirement",
    "NetworkRequirement",
    
    # Legacy compatibility (existing interfaces)
    "EnvironmentInspector",
    "PreparationExecutor",
    "DockerStateManager",
    "PreparationErrorHandler"
]