"""Domain interfaces for dependency injection."""
try:
    from .docker_interface import DockerInterface
    _has_docker_interface = True
except ImportError:
    _has_docker_interface = False

try:
    from .execution_interface import ExecutionInterface  
    _has_execution_interface = True
except ImportError:
    _has_execution_interface = False

from .persistence_interface import PersistenceInterface, RepositoryInterface

__all__ = ["PersistenceInterface", "RepositoryInterface"]

if _has_docker_interface:
    __all__.append("DockerInterface")
if _has_execution_interface:
    __all__.append("ExecutionInterface")
