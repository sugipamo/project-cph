"""Command for cleaning up old Docker containers and images."""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.context.commands.base_command import BaseCommand
from src.infrastructure.di_container import DIKey


@dataclass
class CleanupResult:
    """Result of cleanup operation."""
    containers_removed: List[str]
    images_removed: List[str]
    errors: List[str]
    space_freed_bytes: int = 0


class DockerCleanupCommand(BaseCommand):
    """Command to clean up old Docker containers and images."""
    
    def __init__(self, container):
        """Initialize with DI container."""
        self.container = container
        self._container_repo = None
        self._image_repo = None
        self._docker_driver = None
        
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
    
    @property
    def docker_driver(self):
        """Lazy load Docker driver."""
        if self._docker_driver is None:
            self._docker_driver = self.container.resolve(DIKey.DOCKER_DRIVER)
        return self._docker_driver
    
    def find_unused_containers(self, days: int = 7) -> List[Dict[str, Any]]:
        """Find containers not used for specified days."""
        return self.container_repo.find_unused_containers(days)
    
    def find_unused_images(self, days: int = 30) -> List[Dict[str, Any]]:
        """Find images not used for specified days."""
        return self.image_repo.find_unused_images(days)
    
    def cleanup_containers(
        self, 
        days_unused: int = 7,
        dry_run: bool = False,
        exclude_patterns: Optional[List[str]] = None
    ) -> CleanupResult:
        """Clean up unused containers.
        
        Args:
            days_unused: Remove containers not used for this many days
            dry_run: If True, only show what would be removed
            exclude_patterns: List of container name patterns to exclude
            
        Returns:
            CleanupResult with details of the operation
        """
        result = CleanupResult(
            containers_removed=[],
            images_removed=[],
            errors=[]
        )
        
        # Find unused containers
        unused_containers = self.find_unused_containers(days_unused)
        
        # Filter out excluded patterns
        if exclude_patterns:
            unused_containers = [
                c for c in unused_containers
                if not any(pattern in c['container_name'] for pattern in exclude_patterns)
            ]
        
        # Remove containers
        for container in unused_containers:
            container_name = container['container_name']
            
            if dry_run:
                print(f"Would remove container: {container_name} (last used: {container['last_used_at']})")
                result.containers_removed.append(container_name)
                continue
            
            try:
                # Check if container exists in Docker
                ps_result = self.docker_driver.ps(all=True, show_output=False, names_only=True)
                if container_name in ps_result:
                    # Remove from Docker
                    remove_result = self.docker_driver.remove_container(
                        container_name, 
                        force=True, 
                        show_output=False
                    )
                    
                    if remove_result.success:
                        result.containers_removed.append(container_name)
                        print(f"Removed container: {container_name}")
                    else:
                        result.errors.append(
                            f"Failed to remove container {container_name}: {remove_result.stderr}"
                        )
                else:
                    # Container doesn't exist in Docker but exists in DB
                    self.container_repo.mark_container_removed(container_name)
                    result.containers_removed.append(container_name)
                    print(f"Marked container as removed (not in Docker): {container_name}")
                    
            except Exception as e:
                result.errors.append(f"Error removing container {container_name}: {str(e)}")
        
        return result
    
    def cleanup_images(
        self,
        days_unused: int = 30,
        dry_run: bool = False,
        exclude_patterns: Optional[List[str]] = None
    ) -> CleanupResult:
        """Clean up unused images.
        
        Args:
            days_unused: Remove images not used for this many days
            dry_run: If True, only show what would be removed
            exclude_patterns: List of image name patterns to exclude
            
        Returns:
            CleanupResult with details of the operation
        """
        result = CleanupResult(
            containers_removed=[],
            images_removed=[],
            errors=[]
        )
        
        # Find unused images
        unused_images = self.find_unused_images(days_unused)
        
        # Filter out excluded patterns
        if exclude_patterns:
            unused_images = [
                img for img in unused_images
                if not any(pattern in img['name'] for pattern in exclude_patterns)
            ]
        
        # Check if any containers are using these images
        for image in unused_images:
            image_name = f"{image['name']}:{image['tag']}"
            
            # Check if any containers use this image
            containers_using = self.container_repo.find_containers_by_status("running")
            containers_using.extend(self.container_repo.find_containers_by_status("stopped"))
            
            image_in_use = any(
                c['image_name'] == image['name'] 
                for c in containers_using 
                if c['status'] != 'removed'
            )
            
            if image_in_use:
                continue
            
            if dry_run:
                print(f"Would remove image: {image_name} (last used: {image['last_used_at']})")
                result.images_removed.append(image_name)
                continue
            
            try:
                # Remove from Docker
                remove_result = self.docker_driver.image_rm(image_name, show_output=False)
                
                if remove_result.success:
                    result.images_removed.append(image_name)
                    if image.get('size_bytes'):
                        result.space_freed_bytes += image['size_bytes']
                    print(f"Removed image: {image_name}")
                else:
                    result.errors.append(
                        f"Failed to remove image {image_name}: {remove_result.stderr}"
                    )
                    
            except Exception as e:
                result.errors.append(f"Error removing image {image_name}: {str(e)}")
        
        return result
    
    def cleanup_all(
        self,
        container_days: int = 7,
        image_days: int = 30,
        dry_run: bool = False,
        exclude_patterns: Optional[List[str]] = None
    ) -> CleanupResult:
        """Clean up both containers and images.
        
        Args:
            container_days: Remove containers not used for this many days
            image_days: Remove images not used for this many days
            dry_run: If True, only show what would be removed
            exclude_patterns: List of patterns to exclude
            
        Returns:
            Combined CleanupResult
        """
        # Clean up containers first
        container_result = self.cleanup_containers(container_days, dry_run, exclude_patterns)
        
        # Then clean up images
        image_result = self.cleanup_images(image_days, dry_run, exclude_patterns)
        
        # Combine results
        return CleanupResult(
            containers_removed=container_result.containers_removed,
            images_removed=image_result.images_removed,
            errors=container_result.errors + image_result.errors,
            space_freed_bytes=image_result.space_freed_bytes
        )
    
    def get_cleanup_summary(self) -> Dict[str, Any]:
        """Get summary of what would be cleaned up."""
        summary = {
            "containers": {
                "7_days": len(self.find_unused_containers(7)),
                "14_days": len(self.find_unused_containers(14)),
                "30_days": len(self.find_unused_containers(30)),
            },
            "images": {
                "30_days": len(self.find_unused_images(30)),
                "60_days": len(self.find_unused_images(60)),
                "90_days": len(self.find_unused_images(90)),
            }
        }
        
        # Get total space used by unused images
        unused_images_30 = self.find_unused_images(30)
        total_space = sum(img.get('size_bytes', 0) for img in unused_images_30)
        summary["potential_space_freed_mb"] = total_space / (1024 * 1024)
        
        return summary