"""Docker driver with SQLite tracking for container operations."""
import contextlib
import hashlib
import time
from typing import Any, Optional

from src.infrastructure.di_container import DIKey
from src.infrastructure.drivers.docker.docker_driver import LocalDockerDriver
from src.utils.deprecated import deprecated


class LocalDockerDriverWithTracking(LocalDockerDriver):
    """Docker driver that tracks operations in SQLite."""

    def __init__(self, container):
        """Initialize with DI container for repository access."""
        super().__init__()
        self.di_container = container
        self._container_repo = None
        self._image_repo = None

    @property
    def container_repo(self):
        """Lazy load container repository."""
        if self._container_repo is None:
            self._container_repo = self.di_container.resolve(DIKey.DOCKER_CONTAINER_REPOSITORY)
        return self._container_repo

    @property
    def image_repo(self):
        """Lazy load image repository."""
        if self._image_repo is None:
            self._image_repo = self.di_container.resolve(DIKey.DOCKER_IMAGE_REPOSITORY)
        return self._image_repo

    def run_container(self, image: str, name: Optional[str] = None, options: Optional[dict[str, Any]] = None, show_output: bool = True):
        """Run container and track in database."""
        result = super().run_container(image, name, options, show_output)

        if result.success and name:
            # Record container creation
            try:
                self.container_repo.update_container_status(name, "running", "started_at")
                self.container_repo.add_lifecycle_event(
                    name,
                    "started",
                    {"image": image, "options": options}
                )

                # Update container ID if we can get it
                if result.stdout:
                    container_id = result.stdout.strip()
                    if len(container_id) == 64:  # Docker container ID length
                        self.container_repo.update_container_id(name, container_id)
            except Exception:
                pass  # Don't fail operation if tracking fails

        return result

    def stop_container(self, name: str, show_output: bool = True):
        """Stop container and update tracking."""
        result = super().stop_container(name, show_output)

        if result.success:
            try:
                self.container_repo.update_container_status(name, "stopped", "stopped_at")
                self.container_repo.add_lifecycle_event(name, "stopped")
            except Exception:
                pass

        return result

    def remove_container(self, name: str, force: bool = False, show_output: bool = True):
        """Remove container and mark as removed in database."""
        result = super().remove_container(name, force, show_output)

        if result.success:
            try:
                self.container_repo.mark_container_removed(name)
                self.container_repo.add_lifecycle_event(
                    name,
                    "removed",
                    {"force": force}
                )
            except Exception:
                pass

        return result

    def build_docker_image(self, dockerfile_text: str, tag: Optional[str] = None, options: Optional[dict[str, Any]] = None, show_output: bool = True):
        """Build image and track in database."""
        # Calculate Dockerfile hash
        dockerfile_hash = hashlib.sha256(dockerfile_text.encode('utf-8')).hexdigest()[:12]

        # Record build start
        if tag:
            with contextlib.suppress(Exception):
                self.image_repo.create_or_update_image(
                    name=tag,
                    dockerfile_hash=dockerfile_hash,
                    build_command=f"docker build -t {tag}",
                    build_status="building"
                )

        # Execute build
        start_time = time.time()
        result = super().build_docker_image(dockerfile_text, tag, options, show_output)
        build_time_ms = int((time.time() - start_time) * 1000)

        # Update build result
        if tag:
            try:
                if result.success:
                    # Try to get image ID from output
                    image_id = None
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if 'Successfully built' in line:
                                parts = line.split()
                                if len(parts) > 2:
                                    image_id = parts[-1]
                                    break

                    self.image_repo.update_image_build_result(
                        name=tag,
                        tag="latest",
                        image_id=image_id,
                        build_status="success",
                        build_time_ms=build_time_ms
                    )
                else:
                    self.image_repo.update_image_build_result(
                        name=tag,
                        tag="latest",
                        build_status="failed",
                        build_time_ms=build_time_ms
                    )
            except Exception:
                pass

        return result

    @deprecated("Use build_docker_image instead")
    def build(self, dockerfile_text: str, tag: Optional[str] = None, options: Optional[dict[str, Any]] = None, show_output: bool = True):
        """Backward compatibility wrapper for build_docker_image"""
        return self.build_docker_image(dockerfile_text, tag, options, show_output)

    def image_rm(self, image: str, show_output: bool = True):
        """Remove image and update database."""
        result = super().image_rm(image, show_output)

        if result.success:
            try:
                # Parse image name and tag
                if ':' in image:
                    name, tag = image.split(':', 1)
                else:
                    name, tag = image, "latest"

                self.image_repo.delete_image(name, tag)
            except Exception:
                pass

        return result
