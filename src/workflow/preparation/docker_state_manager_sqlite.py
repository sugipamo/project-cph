"""Docker state manager with SQLite backend for tracking image builds and container compatibility."""
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from src.infrastructure.di_container import DIKey


@dataclass
class DockerStateInfo:
    """Docker state information for a specific environment."""
    language: str
    dockerfile_hash: Optional[str]
    oj_dockerfile_hash: Optional[str]
    image_name: str
    oj_image_name: str
    container_name: str
    oj_container_name: str
    last_updated: str

    @classmethod
    def from_context(cls, context) -> 'DockerStateInfo':
        """Create DockerStateInfo from ExecutionContext."""
        docker_names = context.get_docker_names()

        # Calculate hashes if Dockerfile content is available
        dockerfile_hash = None
        oj_dockerfile_hash = None

        if context.dockerfile_resolver:
            dockerfile_content = context.dockerfile_resolver.dockerfile
            oj_dockerfile_content = context.dockerfile_resolver.oj_dockerfile

            if dockerfile_content:
                dockerfile_hash = hashlib.sha256(dockerfile_content.encode('utf-8')).hexdigest()[:12]
            if oj_dockerfile_content:
                oj_dockerfile_hash = hashlib.sha256(oj_dockerfile_content.encode('utf-8')).hexdigest()[:12]

        return cls(
            language=context.language,
            dockerfile_hash=dockerfile_hash,
            oj_dockerfile_hash=oj_dockerfile_hash,
            image_name=docker_names["image_name"],
            oj_image_name=docker_names["oj_image_name"],
            container_name=docker_names["container_name"],
            oj_container_name=docker_names["oj_container_name"],
            last_updated=datetime.now().isoformat()
        )


class DockerStateManagerSQLite:
    """Manages Docker state tracking using SQLite for rebuild/recreate decisions."""

    def __init__(self, container):
        """Initialize DockerStateManager with SQLite backend.
        
        Args:
            container: DI container to resolve repositories
        """
        self.container = container
        self._container_repo = None
        self._image_repo = None
        self._migrated_states = set()  # Track which states have been migrated

    @property
    def container_repo(self):
        """Lazy load container repository."""
        if self._container_repo is None:
            self._container_repo = self.container.resolve(DIKey.DOCKER_CONTAINER_REPOSITORY)
        return self._container_repo

    @property
    def image_repo(self):
        """Lazy load image repository."""
        if self._image_repo is None:
            self._image_repo = self.container.resolve(DIKey.DOCKER_IMAGE_REPOSITORY)
        return self._image_repo

    def get_state_key(self, language: str, env_type: str) -> str:
        """Generate unique key for state tracking."""
        return f"{language}_{env_type}"

    def _ensure_initial_state(self, context, state_key: str) -> None:
        """Ensure initial state exists for new installations."""
        if state_key in self._migrated_states:
            return

        # Mark as initialized to avoid repeated checks
        self._migrated_states.add(state_key)

    def check_rebuild_needed(self, context) -> tuple[bool, bool, bool, bool]:
        """Check if image rebuild or container recreate is needed.
        
        Returns:
            Tuple[bool, bool, bool, bool]: (
                image_rebuild_needed,
                oj_image_rebuild_needed,
                container_recreate_needed,
                oj_container_recreate_needed
            )
        """
        state_key = self.get_state_key(context.language, context.env_type)
        self._ensure_initial_state(context, state_key)
        
        current_state = DockerStateInfo.from_context(context)
        
        # Check main image
        image_record = self.image_repo.find_image(current_state.image_name)
        image_rebuild_needed = True
        
        if image_record:
            # Image exists, check if Dockerfile changed
            image_rebuild_needed = (
                image_record.get("dockerfile_hash") != current_state.dockerfile_hash
            )
        
        # Check OJ image
        oj_image_record = self.image_repo.find_image(current_state.oj_image_name)
        oj_image_rebuild_needed = True
        
        if oj_image_record:
            oj_image_rebuild_needed = (
                oj_image_record.get("dockerfile_hash") != current_state.oj_dockerfile_hash
            )
        
        # Check containers
        container_record = self.container_repo.find_container_by_name(current_state.container_name)
        container_recreate_needed = True
        
        if container_record and not image_rebuild_needed:
            # Container exists and image hasn't changed
            container_recreate_needed = (
                container_record.get("image_name") != current_state.image_name or
                container_record.get("status") == "removed"
            )
        
        oj_container_record = self.container_repo.find_container_by_name(current_state.oj_container_name)
        oj_container_recreate_needed = True
        
        if oj_container_record and not oj_image_rebuild_needed:
            oj_container_recreate_needed = (
                oj_container_record.get("image_name") != current_state.oj_image_name or
                oj_container_record.get("status") == "removed"
            )
        
        return (
            image_rebuild_needed,
            oj_image_rebuild_needed,
            container_recreate_needed,
            oj_container_recreate_needed
        )

    def update_state(self, context) -> None:
        """Update stored state with current context information."""
        current_state = DockerStateInfo.from_context(context)
        
        # Update image records
        if current_state.dockerfile_hash:
            self.image_repo.create_or_update_image(
                name=current_state.image_name,
                dockerfile_hash=current_state.dockerfile_hash,
                build_status="success"
            )
        
        if current_state.oj_dockerfile_hash:
            self.image_repo.create_or_update_image(
                name=current_state.oj_image_name,
                dockerfile_hash=current_state.oj_dockerfile_hash,
                build_status="success"
            )
        
        # Update/create container records
        container_record = self.container_repo.find_container_by_name(current_state.container_name)
        if not container_record:
            self.container_repo.create_container(
                container_name=current_state.container_name,
                image_name=current_state.image_name,
                language=context.language,
                contest_name=context.contest_name,
                problem_name=context.problem_name,
                env_type=context.env_type
            )
        
        oj_container_record = self.container_repo.find_container_by_name(current_state.oj_container_name)
        if not oj_container_record:
            self.container_repo.create_container(
                container_name=current_state.oj_container_name,
                image_name=current_state.oj_image_name,
                language=context.language,
                contest_name=context.contest_name,
                problem_name=context.problem_name,
                env_type=context.env_type
            )

    def get_expected_image_name(self, context, is_oj: bool = False) -> str:
        """Get expected image name for current context."""
        current_state = DockerStateInfo.from_context(context)
        return current_state.oj_image_name if is_oj else current_state.image_name

    def clear_state(self, language: Optional[str] = None, env_type: Optional[str] = None) -> None:
        """Clear stored state (for testing or cleanup)."""
        if language:
            # Find and mark containers as removed
            containers = self.container_repo.find_containers_by_language(language)
            for container in containers:
                if not env_type or container.get("env_type") == env_type:
                    self.container_repo.mark_container_removed(container["container_name"])

    def inspect_container_compatibility(self, operations, container_name: str, expected_image: str) -> bool:
        """Check if existing container was created from expected image.
        
        Args:
            operations: Operations container for Docker driver
            container_name: Name of container to inspect
            expected_image: Expected image name that container should be based on
            
        Returns:
            bool: True if container is compatible, False if recreation needed
        """
        # First check database record
        container_record = self.container_repo.find_container_by_name(container_name)
        if not container_record or container_record.get("status") == "removed":
            return False
        
        # Check if the container was created from the expected image
        if container_record.get("image_name") != expected_image:
            return False
        
        # Then verify with actual Docker state
        try:
            docker_driver = operations.resolve("docker_driver")
            
            # Check if container exists
            ps_result = docker_driver.ps(all=True, show_output=False, names_only=True)
            if container_name not in ps_result:
                # Container doesn't exist in Docker but exists in DB - mark as removed
                self.container_repo.mark_container_removed(container_name)
                return False
            
            # Inspect container to get image information
            inspect_result = docker_driver.inspect(container_name, show_output=False)
            if not inspect_result.success:
                return False
            
            import json
            inspect_data = json.loads(inspect_result.stdout)
            if not isinstance(inspect_data, list) or len(inspect_data) == 0:
                return False
            
            container_info = inspect_data[0]
            container_image = container_info.get("Config", {}).get("Image", "")
            
            # Check if container was created from expected image
            # Note: Docker may store image with tag or hash, so we check if expected name is contained
            is_compatible = expected_image in container_image or container_image.startswith(expected_image)
            
            # Update container status based on Docker state
            container_state = container_info.get("State", {})
            if container_state.get("Running"):
                self.container_repo.update_container_status(container_name, "running", "started_at")
            elif container_state.get("Status") == "exited":
                self.container_repo.update_container_status(container_name, "stopped", "stopped_at")
            
            return is_compatible
            
        except Exception:
            # If inspection fails, assume recreation is needed
            return False

    def record_container_event(self, container_name: str, event_type: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Record a lifecycle event for a container."""
        self.container_repo.add_lifecycle_event(container_name, event_type, event_data)