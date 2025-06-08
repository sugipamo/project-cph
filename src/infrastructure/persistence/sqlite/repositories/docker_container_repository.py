"""Repository for managing Docker container records in SQLite."""
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
from src.infrastructure.persistence.base.base_repository import BaseRepository


class DockerContainerRepository(BaseRepository):
    """Repository for Docker container operations."""
    
    def __init__(self, sqlite_manager):
        """Initialize with SQLite manager."""
        super().__init__(sqlite_manager)

    # RepositoryInterface implementations
    def create(self, entity: Dict[str, Any]) -> Any:
        """Create a new container entity."""
        return self.create_container(**entity)
        
    def find_by_id(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """Find container by ID."""
        return self.find_container_by_name(str(entity_id))
        
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find all containers."""
        containers = self.get_active_containers()
        if offset:
            containers = containers[offset:]
        if limit:
            containers = containers[:limit]
        return containers
        
    def update(self, entity_id: Any, updates: Dict[str, Any]) -> bool:
        """Update a container."""
        container = self.find_container_by_name(str(entity_id))
        if not container:
            return False
        
        if 'status' in updates:
            self.update_container_status(str(entity_id), updates['status'])
        return True
        
    def delete(self, entity_id: Any) -> bool:
        """Delete container by ID."""
        container = self.find_container_by_name(str(entity_id))
        if not container:
            return False
        
        self.mark_container_removed(str(entity_id))
        return True

    def create_container(
        self,
        container_name: str,
        image_name: str,
        image_tag: str = "latest",
        language: Optional[str] = None,
        contest_name: Optional[str] = None,
        problem_name: Optional[str] = None,
        env_type: Optional[str] = None,
        volumes: Optional[List[Dict[str, str]]] = None,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """Create a new container record."""
        query = """
            INSERT INTO docker_containers (
                container_name, image_name, image_tag, status,
                language, contest_name, problem_name, env_type,
                volumes, environment, ports
            ) VALUES (?, ?, ?, 'created', ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            container_name,
            image_name,
            image_tag,
            language,
            contest_name,
            problem_name,
            env_type,
            json.dumps(volumes) if volumes else None,
            json.dumps(environment) if environment else None,
            json.dumps(ports) if ports else None,
        )
        
        with self.connection as conn:
            return conn.execute(query, params).lastrowid

    def update_container_id(self, container_name: str, container_id: str) -> None:
        """Update the Docker container ID after creation."""
        query = """
            UPDATE docker_containers
            SET container_id = ?
            WHERE container_name = ?
        """
        with self.connection as conn:
            conn.execute(query, (container_id, container_name))

    def update_container_status(
        self, 
        container_name: str, 
        status: str,
        timestamp_field: Optional[str] = None
    ) -> None:
        """Update container status and related timestamp."""
        query = "UPDATE docker_containers SET status = ?, last_used_at = CURRENT_TIMESTAMP"
        params = [status]
        
        if timestamp_field:
            query += f", {timestamp_field} = CURRENT_TIMESTAMP"
        
        query += " WHERE container_name = ?"
        params.append(container_name)
        
        with self.connection as conn:
            conn.execute(query, params)

    def find_container_by_name(self, container_name: str) -> Optional[Dict[str, Any]]:
        """Find a container by its name."""
        query = """
            SELECT * FROM docker_containers
            WHERE container_name = ?
        """
        with self.connection as conn:
            cursor = conn.execute(query, (container_name,))
            return self._parse_result(cursor.fetchone())

    def find_containers_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Find all containers with a specific status."""
        query = """
            SELECT * FROM docker_containers
            WHERE status = ?
            ORDER BY last_used_at DESC
        """
        with self.connection as conn:
            cursor = conn.execute(query, (status,))
            return [self._parse_result(row) for row in cursor.fetchall()]

    def find_containers_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Find all containers for a specific language."""
        query = """
            SELECT * FROM docker_containers
            WHERE language = ?
            ORDER BY last_used_at DESC
        """
        with self.connection as conn:
            cursor = conn.execute(query, (language,))
            return [self._parse_result(row) for row in cursor.fetchall()]

    def find_unused_containers(self, days: int = 7) -> List[Dict[str, Any]]:
        """Find containers not used for specified number of days."""
        query = """
            SELECT * FROM docker_containers
            WHERE last_used_at < datetime('now', '-' || ? || ' days')
            AND status != 'removed'
            ORDER BY last_used_at ASC
        """
        with self.connection as conn:
            cursor = conn.execute(query, (days,))
            return [self._parse_result(row) for row in cursor.fetchall()]

    def get_active_containers(self) -> List[Dict[str, Any]]:
        """Get all active (running or created) containers."""
        query = """
            SELECT * FROM docker_containers
            WHERE status IN ('running', 'created', 'started')
            ORDER BY last_used_at DESC
        """
        with self.connection as conn:
            cursor = conn.execute(query)
            return [self._parse_result(row) for row in cursor.fetchall()]

    def mark_container_removed(self, container_name: str) -> None:
        """Mark a container as removed."""
        self.update_container_status(container_name, 'removed', 'removed_at')

    def _parse_result(self, row) -> Optional[Dict[str, Any]]:
        """Parse a database row into a dictionary."""
        if not row:
            return None
        
        result = dict(row)
        
        # Parse JSON fields
        for field in ['volumes', 'environment', 'ports']:
            if result.get(field):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    result[field] = None
        
        return result

    def add_lifecycle_event(
        self, 
        container_name: str, 
        event_type: str, 
        event_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a lifecycle event for a container."""
        query = """
            INSERT INTO container_lifecycle_events (
                container_name, event_type, event_data
            ) VALUES (?, ?, ?)
        """
        params = (
            container_name,
            event_type,
            json.dumps(event_data) if event_data else None
        )
        with self.connection as conn:
            conn.execute(query, params)

    def get_container_events(
        self, 
        container_name: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get lifecycle events for a container."""
        query = """
            SELECT * FROM container_lifecycle_events
            WHERE container_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        with self.connection as conn:
            cursor = conn.execute(query, (container_name, limit))
        
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            if event.get('event_data'):
                try:
                    event['event_data'] = json.loads(event['event_data'])
                except json.JSONDecodeError:
                    event['event_data'] = None
            events.append(event)
        
        return events