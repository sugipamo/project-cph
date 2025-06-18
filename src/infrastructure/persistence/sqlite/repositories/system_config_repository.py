"""Repository for managing system configuration in SQLite."""
import contextlib
import json
from typing import Any, Dict, List, Optional

from src.infrastructure.persistence.base.base_repository import DatabaseRepositoryFoundation


class SystemConfigRepository(DatabaseRepositoryFoundation):
    """Repository for system configuration operations."""

    def __init__(self, sqlite_manager):
        """Initialize with SQLite manager."""
        super().__init__(sqlite_manager)

    # RepositoryInterface implementations
    def create_entity_record(self, entity: Dict[str, Any]) -> Any:
        """Create a new config entity."""
        key = entity['config_key'] if 'config_key' in entity else (entity.get('key'))
        value = entity['config_value'] if 'config_value' in entity else (entity.get('value'))
        category = entity.get('category')
        description = entity.get('description')

        self.set_config(key, value, category, description)
        return key

    def create_config_record(self, entity: Dict[str, Any]) -> Any:
        """Create a new config entity."""
        key = entity['config_key'] if 'config_key' in entity else (entity.get('key'))
        value = entity['config_value'] if 'config_value' in entity else (entity.get('value'))
        category = entity.get('category')
        description = entity.get('description')

        self.set_config(key, value, category, description)
        return key


    def find_by_id(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """Find config by key."""
        return self.get_config_with_metadata(str(entity_id))

    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find all configs."""
        configs = self.get_all_configs_with_metadata()
        if offset:
            configs = configs[offset:]
        if limit:
            configs = configs[:limit]
        return configs

    def update(self, entity_id: Any, updates: Dict[str, Any]) -> bool:
        """Update a config."""
        existing = self.get_config_with_metadata(str(entity_id))
        if not existing:
            return False

        value = updates['config_value'] if 'config_value' in updates else (updates.get('value'))
        category = updates['category'] if 'category' in updates else (existing.get('category', None))
        description = updates['description'] if 'description' in updates else (existing.get('description', None))

        self.set_config(str(entity_id), value, category, description)
        return True

    def delete(self, entity_id: Any) -> bool:
        """Delete config by key."""
        return self.delete_config(str(entity_id))

    def set_config(
        self,
        key: str,
        value: Any,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Set or update a configuration value."""
        # Handle None values - store as NULL in database
        if value is None:
            json_value = None
        else:
            json_value = json.dumps(value, ensure_ascii=False, indent=2)

        # Check if key exists
        existing = self.get_config_with_metadata(key)

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

        if row and row[0] is not None:
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
            with contextlib.suppress(json.JSONDecodeError):
                result['config_value'] = json.loads(result['config_value'])
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
                with contextlib.suppress(json.JSONDecodeError):
                    config['config_value'] = json.loads(config['config_value'])
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
                with contextlib.suppress(json.JSONDecodeError):
                    config['config_value'] = json.loads(config['config_value'])
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

    def get_user_specified_configs(self) -> Dict[str, Any]:
        """Get only user-specified configuration values (non-NULL)."""
        query = """
            SELECT config_key, config_value FROM system_config
            WHERE config_key IN ('command', 'language', 'env_type', 'contest_name', 'problem_name')
            AND config_value IS NOT NULL
            ORDER BY config_key
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

    def get_execution_context_summary(self) -> Dict[str, Any]:
        """Get execution context with user specification status."""
        query = """
            SELECT config_key,
                   config_value,
                   CASE WHEN config_value IS NULL THEN 0 ELSE 1 END as user_specified
            FROM system_config
            WHERE config_key IN ('command', 'language', 'env_type', 'contest_name', 'problem_name')
            ORDER BY config_key
        """
        with self.connection as conn:
            cursor = conn.execute(query)

            result = {
                'values': {},
                'user_specified': {}
            }

            for row in cursor.fetchall():
                key = row[0]
                value = row[1]
                user_specified = bool(row[2])

                if value is not None:
                    try:
                        result['values'][key] = json.loads(value)
                    except json.JSONDecodeError:
                        result['values'][key] = value
                else:
                    result['values'][key] = None

                result['user_specified'][key] = user_specified

            return result

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
                if config['config_value'] is not None:
                    with contextlib.suppress(json.JSONDecodeError):
                        config['config_value'] = json.loads(config['config_value'])
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
