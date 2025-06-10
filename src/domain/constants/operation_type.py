"""Operation type constants."""
from enum import Enum, auto


class OperationType(Enum):
    """Enumeration of operation types."""
    SHELL = auto()
    SHELL_INTERACTIVE = auto()
    FILE = auto()
    DOCKER = auto()
    COMPOSITE = auto()
    PYTHON = auto()
    FILE_PREPARATION = auto()
    STATE_SHOW = auto()
    WORKSPACE = auto()


class WorkspaceOperationType(Enum):
    """Workspace operation types."""
    WORKSPACE_SWITCH = "workspace_switch"
    MOVE_TEST_FILES = "move_test_files"
    CLEANUP_WORKSPACE = "cleanup_workspace"
    ARCHIVE_CURRENT = "archive_current"


class FileOperationType(Enum):
    """File operation types."""
    MKDIR = "mkdir"
    TOUCH = "touch"
    COPY = "copy"
    MOVE = "move"
    REMOVE = "remove"
    READ = "read"
    WRITE = "write"
    EXISTS = "exists"


class DirectoryName(Enum):
    """Directory names."""
    TEST = "test"
    TEMPLATE = "template"
    STOCK = "stock"
    CURRENT = "current"
    WORKSPACE = "workspace"
    CONTEST_ENV = "contest_env"


class FilePattern(Enum):
    """File patterns."""
    TEST_INPUT_PATTERN = "sample-*.in"
    TEST_OUTPUT_PATTERN = "sample-*.out"
    TEST_INPUT_EXTENSION = ".in"
    TEST_OUTPUT_EXTENSION = ".out"
    CONFIG_FILE = "env.json"
    DOCKERFILE = "Dockerfile"


class PreparationAction(Enum):
    """Docker preparation actions."""
    REMOVE_STOPPED_CONTAINER = "remove_stopped_container"
    RUN_NEW_CONTAINER = "run_new_container"
    CREATE_DIRECTORY = "create_directory"
    BUILD_OR_PULL_IMAGE = "build_or_pull_image"
