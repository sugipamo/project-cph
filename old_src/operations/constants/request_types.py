"""Request type constants for type-safe class identification."""
from enum import Enum, auto


class RequestType(Enum):
    """Enumeration of request types for type-safe identification."""

    # Core request types
    OPERATION_REQUEST_FOUNDATION = auto()
    COMPOSITE_REQUEST_FOUNDATION = auto()

    # Specific request types
    DOCKER_REQUEST = auto()
    FILE_REQUEST = auto()
    SHELL_REQUEST = auto()
    PYTHON_REQUEST = auto()
    COMPOSITE_REQUEST = auto()

    # Step types
    BUILD_STEP = auto()
    RUN_STEP = auto()
    TEST_STEP = auto()

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        return self.name.replace('_', ' ').title()

    @property
    def short_name(self) -> str:
        """Get short name for logging/display."""
        name_map = {
            self.DOCKER_REQUEST: "Docker",
            self.FILE_REQUEST: "File",
            self.SHELL_REQUEST: "Shell",
            self.PYTHON_REQUEST: "Python",
            self.COMPOSITE_REQUEST: "Composite",
            self.COMPOSITE_REQUEST_FOUNDATION: "CompositeFoundation",
            self.OPERATION_REQUEST_FOUNDATION: "OperationFoundation",
            self.BUILD_STEP: "Build",
            self.RUN_STEP: "Run",
            self.TEST_STEP: "Test",
        }
        return name_map[self]
