"""Repository for managing system configuration in SQLite."""
import json
from typing import Any, Dict, List, Optional
from src.infrastructure.persistence.base.base_repository import BaseRepository


class SystemConfigRepository(BaseRepository):
    """Repository for system configuration operations."""
    
    def __init__(self, sqlite_manager):
        """Initialize with SQLite manager."""
        self.sqlite_manager = sqlite_manager
        
    @property 
    def connection(self):
        """Get database connection."""
        return self.sqlite_manager.get_connection()
    
    # Abstract method implementations
    def create(self, entity: Any) -> Any:
        """Create a new entity."""
        return None
        
    def find_by_id(self, entity_id: Any) -> Optional[Any]:
        """Find entity by ID."""
        return None
        
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Any]:
        """Find all entities."""
        return []
        
    def update(self, entity: Any) -> Any:
        """Update an entity."""
        return None
        
    def delete(self, entity_id: Any) -> bool:
        """Delete entity by ID."""
        return False

    def set_config(
        self,
        key: str,
        value: Any,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Set or update a configuration value."""
        # Convert value to JSON string
        json_value = json.dumps(value, ensure_ascii=False, indent=2)
        
        # Check if key exists
        existing = self.get_config(key)
        
        if existing is not None:
            query = """
                UPDATE system_config
                SET config_value = ?,
                    category = COALESCE(?, category),
                    description = COALESCE(?, description),
                    updated_at = CURRENT_TIMESTAMP
                WHERE config_key = ?
            """
            params = (json_value, category, description, key)
        else:
            query = """
                INSERT INTO system_config (
                    config_key, config_value, category, description
                ) VALUES (?, ?, ?, ?)
            """
            params = (key, json_value, category, description)
        
        with self.connection as conn:
            conn.execute(query, params)

    def get_config(self, key: str) -> Optional[Any]:
        """Get a configuration value by key."""
        query = """
            SELECT config_value FROM system_config
            WHERE config_key = ?
        """
        with self.connection as conn:
            cursor = conn.execute(query, (key,))
            row = cursor.fetchone()
        
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return row[0]
        return None

    def get_config_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get configuration with all metadata."""
        query = """
            SELECT * FROM system_config
            WHERE config_key = ?
        """
        with self.connection as conn:
            cursor = conn.execute(query, (key,))
            row = cursor.fetchone()
        
        if row:
            result = dict(row)
            try:
                result['config_value'] = json.loads(result['config_value'])
            except json.JSONDecodeError:
                pass
            return result
        return None

    def get_configs_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all configurations in a category."""
        query = """
            SELECT * FROM system_config
            WHERE category = ?
            ORDER BY config_key
        """
        with self.connection as conn:
            cursor = conn.execute(query, (category,))
            
            results = []
            for row in cursor.fetchall():
                config = dict(row)
                try:
                    config['config_value'] = json.loads(config['config_value'])
                except json.JSONDecodeError:
                    pass
                results.append(config)
        
        return results

    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations as a dictionary."""
        query = """
            SELECT config_key, config_value FROM system_config
            ORDER BY category, config_key
        """
        with self.connection as conn:
            cursor = conn.execute(query)
            
            configs = {}
            for key, value in cursor.fetchall():
                try:
                    configs[key] = json.loads(value)
                except json.JSONDecodeError:
                    configs[key] = value
        
        return configs

    def get_all_configs_with_metadata(self) -> List[Dict[str, Any]]:
        """Get all configurations with metadata."""
        query = """
            SELECT * FROM system_config
            ORDER BY category, config_key
        """
        with self.connection as conn:
            cursor = conn.execute(query)
            
            results = []
            for row in cursor.fetchall():
                config = dict(row)
                try:
                    config['config_value'] = json.loads(config['config_value'])
                except json.JSONDecodeError:
                    pass
                results.append(config)
        
        return results

    def delete_config(self, key: str) -> bool:
        """Delete a configuration."""
        query = """
            DELETE FROM system_config
            WHERE config_key = ?
        """
        with self.connection as conn:
            cursor = conn.execute(query, (key,))
        return cursor.rowcount > 0

    def bulk_set_configs(self, configs: Dict[str, Any], category: Optional[str] = None) -> None:
        """Set multiple configurations at once."""
        for key, value in configs.items():
            self.set_config(key, value, category)

    def search_configs(self, search_term: str) -> List[Dict[str, Any]]:
        """Search configurations by key or description."""
        query = """
            SELECT * FROM system_config
            WHERE config_key LIKE ? OR description LIKE ?
            ORDER BY config_key
        """
        search_pattern = f"%{search_term}%"
        with self.connection as conn:
            cursor = conn.execute(query, (search_pattern, search_pattern))
            
            results = []
            for row in cursor.fetchall():
                config = dict(row)
                try:
                    config['config_value'] = json.loads(config['config_value'])
                except json.JSONDecodeError:
                    pass
                results.append(config)
        
        return results

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        query = """
            SELECT DISTINCT category FROM system_config
            WHERE category IS NOT NULL
            ORDER BY category
        """
        with self.connection as conn:
            cursor = conn.execute(query)
            return [row[0] for row in cursor.fetchall()]