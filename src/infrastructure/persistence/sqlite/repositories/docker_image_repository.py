"""Repository for managing Docker image records in SQLite."""
from typing import List, Optional, Dict, Any
from src.infrastructure.persistence.base.base_repository import BaseRepository


class DockerImageRepository(BaseRepository):
    """Repository for Docker image operations."""

    def create_or_update_image(
        self,
        name: str,
        tag: str = "latest",
        dockerfile_hash: Optional[str] = None,
        build_command: Optional[str] = None,
        build_status: str = "pending",
    ) -> int:
        """Create or update an image record."""
        # First try to update existing
        existing = self.find_image(name, tag)
        
        if existing:
            query = """
                UPDATE docker_images
                SET dockerfile_hash = ?,
                    build_command = ?,
                    build_status = ?,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE name = ? AND tag = ?
            """
            params = (dockerfile_hash, build_command, build_status, name, tag)
            self.connection.execute(query, params)
            return existing['id']
        else:
            query = """
                INSERT INTO docker_images (
                    name, tag, dockerfile_hash, build_command, build_status
                ) VALUES (?, ?, ?, ?, ?)
            """
            params = (name, tag, dockerfile_hash, build_command, build_status)
            return self.connection.execute(query, params).lastrowid

    def update_image_build_result(
        self,
        name: str,
        tag: str,
        image_id: Optional[str] = None,
        build_status: str = "success",
        build_time_ms: Optional[int] = None,
        size_bytes: Optional[int] = None,
    ) -> None:
        """Update image build results."""
        query = """
            UPDATE docker_images
            SET image_id = ?,
                build_status = ?,
                build_time_ms = ?,
                size_bytes = ?,
                last_used_at = CURRENT_TIMESTAMP
            WHERE name = ? AND tag = ?
        """
        params = (image_id, build_status, build_time_ms, size_bytes, name, tag)
        self.connection.execute(query, params)

    def find_image(self, name: str, tag: str = "latest") -> Optional[Dict[str, Any]]:
        """Find an image by name and tag."""
        query = """
            SELECT * FROM docker_images
            WHERE name = ? AND tag = ?
        """
        cursor = self.connection.execute(query, (name, tag))
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_images_by_status(self, build_status: str) -> List[Dict[str, Any]]:
        """Find all images with a specific build status."""
        query = """
            SELECT * FROM docker_images
            WHERE build_status = ?
            ORDER BY created_at DESC
        """
        cursor = self.connection.execute(query, (build_status,))
        return [dict(row) for row in cursor.fetchall()]

    def find_images_by_name_prefix(self, prefix: str) -> List[Dict[str, Any]]:
        """Find all images with names starting with a prefix."""
        query = """
            SELECT * FROM docker_images
            WHERE name LIKE ?
            ORDER BY name, tag
        """
        cursor = self.connection.execute(query, (f"{prefix}%",))
        return [dict(row) for row in cursor.fetchall()]

    def get_all_images(self) -> List[Dict[str, Any]]:
        """Get all registered images."""
        query = """
            SELECT * FROM docker_images
            ORDER BY last_used_at DESC
        """
        cursor = self.connection.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def find_unused_images(self, days: int = 30) -> List[Dict[str, Any]]:
        """Find images not used for specified number of days."""
        query = """
            SELECT * FROM docker_images
            WHERE last_used_at < datetime('now', '-' || ? || ' days')
            ORDER BY last_used_at ASC
        """
        cursor = self.connection.execute(query, (days,))
        return [dict(row) for row in cursor.fetchall()]

    def update_last_used(self, name: str, tag: str = "latest") -> None:
        """Update the last used timestamp for an image."""
        query = """
            UPDATE docker_images
            SET last_used_at = CURRENT_TIMESTAMP
            WHERE name = ? AND tag = ?
        """
        self.connection.execute(query, (name, tag))

    def delete_image(self, name: str, tag: str = "latest") -> bool:
        """Delete an image record."""
        query = """
            DELETE FROM docker_images
            WHERE name = ? AND tag = ?
        """
        cursor = self.connection.execute(query, (name, tag))
        return cursor.rowcount > 0

    def get_image_stats(self) -> Dict[str, Any]:
        """Get statistics about images."""
        stats = {}
        
        # Total images
        cursor = self.connection.execute("SELECT COUNT(*) FROM docker_images")
        stats['total'] = cursor.fetchone()[0]
        
        # Images by status
        cursor = self.connection.execute("""
            SELECT build_status, COUNT(*) 
            FROM docker_images 
            GROUP BY build_status
        """)
        stats['by_status'] = dict(cursor.fetchall())
        
        # Total size
        cursor = self.connection.execute("""
            SELECT SUM(size_bytes) 
            FROM docker_images 
            WHERE size_bytes IS NOT NULL
        """)
        stats['total_size_bytes'] = cursor.fetchone()[0] or 0
        
        return stats