"""Repository for managing contest_current file structure tracking."""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.infrastructure.persistence.base.base_repository import BaseRepository


@dataclass
class ContestCurrentFile:
    """Data class for contest_current file tracking."""
    id: Optional[int]
    language_name: str
    contest_name: str
    problem_name: str
    relative_path: str
    source_type: str  # 'template' or 'stock'
    source_path: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContestCurrentFilesRepository(BaseRepository):
    """Repository for contest_current file structure management."""

    def track_file(self, language_name: str, contest_name: str, problem_name: str,
                   relative_path: str, source_type: str, source_path: str) -> bool:
        """Track a file in contest_current directory.
        
        Args:
            language_name: Programming language
            contest_name: Contest name
            problem_name: Problem name
            relative_path: Path relative to contest_current
            source_type: 'template' or 'stock'
            source_path: Original source file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.manager.execute_query(
                """
                INSERT OR REPLACE INTO contest_current_files 
                (language_name, contest_name, problem_name, relative_path, source_type, source_path, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (language_name, contest_name, problem_name, relative_path, source_type, source_path)
            )
            return True
        except Exception:
            return False

    def get_files_for_contest(self, language_name: str, contest_name: str, 
                             problem_name: str) -> List[ContestCurrentFile]:
        """Get all tracked files for a specific contest context.
        
        Args:
            language_name: Programming language
            contest_name: Contest name
            problem_name: Problem name
            
        Returns:
            List of ContestCurrentFile objects
        """
        try:
            rows = self.manager.fetch_all(
                """
                SELECT id, language_name, contest_name, problem_name, relative_path, 
                       source_type, source_path, created_at, updated_at
                FROM contest_current_files 
                WHERE language_name = ? AND contest_name = ? AND problem_name = ?
                ORDER BY relative_path
                """,
                (language_name, contest_name, problem_name)
            )
            
            return [
                ContestCurrentFile(
                    id=row[0],
                    language_name=row[1],
                    contest_name=row[2],
                    problem_name=row[3],
                    relative_path=row[4],
                    source_type=row[5],
                    source_path=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                )
                for row in rows
            ]
        except Exception:
            return []

    def clear_contest_tracking(self, language_name: str, contest_name: str, 
                              problem_name: str) -> bool:
        """Clear all file tracking for a specific contest context.
        
        Args:
            language_name: Programming language
            contest_name: Contest name
            problem_name: Problem name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.manager.execute_query(
                """
                DELETE FROM contest_current_files 
                WHERE language_name = ? AND contest_name = ? AND problem_name = ?
                """,
                (language_name, contest_name, problem_name)
            )
            return True
        except Exception:
            return False

    def get_file_paths_by_source_type(self, language_name: str, contest_name: str,
                                     problem_name: str, source_type: str) -> List[str]:
        """Get relative paths of files by source type.
        
        Args:
            language_name: Programming language
            contest_name: Contest name
            problem_name: Problem name
            source_type: 'template' or 'stock'
            
        Returns:
            List of relative paths
        """
        try:
            rows = self.manager.fetch_all(
                """
                SELECT relative_path 
                FROM contest_current_files 
                WHERE language_name = ? AND contest_name = ? AND problem_name = ? AND source_type = ?
                ORDER BY relative_path
                """,
                (language_name, contest_name, problem_name, source_type)
            )
            
            return [row[0] for row in rows]
        except Exception:
            return []

    def has_files_for_contest(self, language_name: str, contest_name: str, 
                             problem_name: str) -> bool:
        """Check if any files are tracked for a contest context.
        
        Args:
            language_name: Programming language
            contest_name: Contest name
            problem_name: Problem name
            
        Returns:
            True if files exist, False otherwise
        """
        try:
            result = self.manager.fetch_one(
                """
                SELECT COUNT(*) 
                FROM contest_current_files 
                WHERE language_name = ? AND contest_name = ? AND problem_name = ?
                """,
                (language_name, contest_name, problem_name)
            )
            return result[0] > 0 if result else False
        except Exception:
            return False

    def track_multiple_files(self, files: List[Tuple[str, str, str, str, str, str]]) -> bool:
        """Track multiple files in a single transaction.
        
        Args:
            files: List of tuples (language_name, contest_name, problem_name, 
                                  relative_path, source_type, source_path)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.manager.execute_many(
                """
                INSERT OR REPLACE INTO contest_current_files 
                (language_name, contest_name, problem_name, relative_path, source_type, source_path, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                files
            )
            return True
        except Exception:
            return False

    # Required abstract method implementations from BaseRepository
    def create(self, entity):
        """Create method for BaseRepository compatibility."""
        pass

    def find_by_id(self, entity_id):
        """Find by ID method for BaseRepository compatibility."""
        pass

    def find_all(self):
        """Find all method for BaseRepository compatibility."""
        pass

    def update(self, entity):
        """Update method for BaseRepository compatibility."""
        pass

    def delete(self, entity_id):
        """Delete method for BaseRepository compatibility."""
        pass