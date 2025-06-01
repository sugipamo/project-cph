"""
Docker state manager for tracking image builds and container compatibility
"""
import json
import os
import hashlib
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


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


class DockerStateManager:
    """
    Manages Docker state tracking for rebuild/recreate decisions
    """
    
    def __init__(self, state_file_path: str = "docker_state.json"):
        self.state_file_path = state_file_path
        self._state_cache: Optional[Dict] = None
    
    def _load_state(self) -> Dict:
        """Load docker state from file"""
        if self._state_cache is not None:
            return self._state_cache
            
        if not os.path.exists(self.state_file_path):
            self._state_cache = {}
            return self._state_cache
        
        try:
            with open(self.state_file_path, 'r') as f:
                self._state_cache = json.load(f)
        except Exception:
            self._state_cache = {}
        
        return self._state_cache
    
    def _save_state(self, state: Dict) -> None:
        """Save docker state to file"""
        try:
            with open(self.state_file_path, 'w') as f:
                json.dump(state, f, indent=2)
            self._state_cache = state
        except Exception:
            # If save fails, continue without caching
            pass
    
    def get_state_key(self, language: str, env_type: str) -> str:
        """Generate unique key for state tracking"""
        return f"{language}_{env_type}"
    
    def check_rebuild_needed(self, context) -> Tuple[bool, bool, bool, bool]:
        """
        Check if image rebuild or container recreate is needed
        
        Returns:
            Tuple[bool, bool, bool, bool]: (
                image_rebuild_needed, 
                oj_image_rebuild_needed,
                container_recreate_needed,
                oj_container_recreate_needed
            )
        """
        current_state = DockerStateInfo.from_context(context)
        state_key = self.get_state_key(context.language, context.env_type)
        
        stored_state = self._load_state().get(state_key)
        
        if not stored_state:
            # No previous state - need to build everything
            return True, True, True, True
        
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
        
        return (
            image_rebuild_needed,
            oj_image_rebuild_needed, 
            container_recreate_needed,
            oj_container_recreate_needed
        )
    
    def update_state(self, context) -> None:
        """Update stored state with current context information"""
        current_state = DockerStateInfo.from_context(context)
        state_key = self.get_state_key(context.language, context.env_type)
        
        state = self._load_state()
        state[state_key] = asdict(current_state)
        self._save_state(state)
    
    def get_expected_image_name(self, context, is_oj: bool = False) -> str:
        """Get expected image name for current context"""
        current_state = DockerStateInfo.from_context(context)
        return current_state.oj_image_name if is_oj else current_state.image_name
    
    def clear_state(self, language: str = None, env_type: str = None) -> None:
        """Clear stored state (for testing or cleanup)"""
        if language and env_type:
            state_key = self.get_state_key(language, env_type)
            state = self._load_state()
            if state_key in state:
                del state[state_key]
                self._save_state(state)
        else:
            # Clear all state
            self._save_state({})
        
        self._state_cache = None
    
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