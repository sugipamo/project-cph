"""
Docker-specific state manager implementation
"""
import json
import os
import hashlib
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from ...core.interfaces import StateManager
from ...core.models import RebuildDecision


@dataclass
class DockerStateInfo:
    """Docker state information for a specific environment"""
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
        """Create DockerStateInfo from ExecutionContext"""
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


class DockerStateManager(StateManager):
    """Docker-specific implementation of StateManager"""
    
    def __init__(self, context=None, initial_state: Optional[Dict] = None, state_file_path: Optional[str] = None):
        """
        Initialize DockerStateManager with JSON state
        
        Args:
            context: Execution context with env.json settings
            initial_state: State dict (for dependency injection and testing)
            state_file_path: Optional file path for persistence (if None, state is not persisted)
        """
        self.context = context
        self._state_cache: Dict = initial_state if initial_state is not None else {}
        self.state_file_path = state_file_path
    
    @classmethod
    def from_filepath(cls, state_file_path: str) -> 'DockerStateManager':
        """
        Entry point: Create DockerStateManager by loading state from file
        
        Args:
            state_file_path: Path to JSON file to load
            
        Returns:
            DockerStateManager instance with loaded state
        """
        # Load state from file
        loaded_state = cls._load_state_from_file(state_file_path)
        return cls(initial_state=loaded_state, state_file_path=state_file_path)
    
    @staticmethod
    def _load_state_from_file(file_path: str) -> Dict:
        """
        Load state from JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dict: Loaded state or empty dict if file doesn't exist or is invalid
        """
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _get_state(self) -> Dict:
        """Get current state"""
        return self._state_cache
    
    def _save_state(self, state: Dict) -> None:
        """Save docker state to file and update cache"""
        # Update cache
        self._state_cache = state
        
        # Save to file if file path is provided
        if self.state_file_path:
            try:
                with open(self.state_file_path, 'w') as f:
                    json.dump(state, f, indent=2)
            except Exception:
                # If save fails, continue without persistence
                pass
    
    def get_state_key(self, language: str, env_type: str) -> str:
        """Generate unique key for state tracking"""
        return f"{language}_{env_type}"
    
    def check_rebuild_needed(self, context) -> RebuildDecision:
        """
        Check if image rebuild or container recreate is needed
        
        Args:
            context: Execution context with configuration
            
        Returns:
            RebuildDecision with rebuild/recreate flags
        """
        current_state = DockerStateInfo.from_context(context)
        state_key = self.get_state_key(context.language, context.env_type)
        
        stored_state = self._get_state().get(state_key)
        
        if not stored_state:
            # No previous state - need to build everything
            return RebuildDecision(
                image_rebuild_needed=True,
                oj_image_rebuild_needed=True,
                container_recreate_needed=True,
                oj_container_recreate_needed=True,
                reason="No previous state found"
            )
        
        # Check image rebuild needs (based on Dockerfile content changes)
        image_rebuild_needed = (
            stored_state.get("dockerfile_hash") != current_state.dockerfile_hash
        )
        
        oj_image_rebuild_needed = (
            stored_state.get("oj_dockerfile_hash") != current_state.oj_dockerfile_hash
        )
        
        # Check container recreate needs (if images changed or names changed)
        container_recreate_needed = (
            image_rebuild_needed or
            stored_state.get("image_name") != current_state.image_name or
            stored_state.get("container_name") != current_state.container_name
        )
        
        oj_container_recreate_needed = (
            oj_image_rebuild_needed or
            stored_state.get("oj_image_name") != current_state.oj_image_name or
            stored_state.get("oj_container_name") != current_state.oj_container_name
        )
        
        return RebuildDecision(
            image_rebuild_needed=image_rebuild_needed,
            oj_image_rebuild_needed=oj_image_rebuild_needed,
            container_recreate_needed=container_recreate_needed,
            oj_container_recreate_needed=oj_container_recreate_needed,
            reason=f"State comparison: image={image_rebuild_needed}, oj_image={oj_image_rebuild_needed}"
        )
    
    def update_state(self, context) -> None:
        """Update stored state with current context information"""
        current_state = DockerStateInfo.from_context(context)
        state_key = self.get_state_key(context.language, context.env_type)
        
        state = self._get_state().copy()  # Copy to avoid modifying original
        state[state_key] = asdict(current_state)
        self._save_state(state)
    
    def clear_state(self, identifier: str = None) -> None:
        """Clear stored state (for testing or cleanup)"""
        if identifier:
            # Try to parse identifier as language_env_type
            if '_' in identifier:
                language, env_type = identifier.split('_', 1)
                state_key = self.get_state_key(language, env_type)
            else:
                state_key = identifier
            
            state = self._get_state().copy()
            if state_key in state:
                del state[state_key]
                self._save_state(state)
        else:
            # Clear all state
            self._save_state({})
    
    def get_expected_image_name(self, context, is_oj: bool = False) -> str:
        """Get expected image name for current context"""
        current_state = DockerStateInfo.from_context(context)
        return current_state.oj_image_name if is_oj else current_state.image_name
    
    def inspect_container_compatibility(self, operations, container_name: str, expected_image: str) -> bool:
        """
        Check if existing container was created from expected image
        
        Args:
            operations: Operations container for Docker driver
            container_name: Name of container to inspect
            expected_image: Expected image name that container should be based on
            
        Returns:
            bool: True if container is compatible, False if recreation needed
        """
        try:
            docker_driver = operations.resolve("docker_driver")
            
            # Check if container exists
            ps_result = docker_driver.ps(all=True, show_output=False, names_only=True)
            if container_name not in ps_result:
                return False  # Container doesn't exist
            
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
            return expected_image in container_image or container_image.startswith(expected_image)
            
        except Exception:
            # If inspection fails, assume recreation is needed
            return False