"""Tests for DockerImageRepository."""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.data.docker_image.docker_image_repository import DockerImageRepository


class MockSQLiteRow:
    """Mock SQLite row that behaves like a real row object."""
    def __init__(self, data):
        self._data = data
    
    def keys(self):
        return self._data.keys()
    
    def __getitem__(self, key):
        if isinstance(key, int):
            values = list(self._data.values())
            return values[key] if key < len(values) else None
        return self._data.get(key)
    
    def __iter__(self):
        return iter(self._data.values())


class TestDockerImageRepository:
    """Test cases for DockerImageRepository."""
    
    @pytest.fixture
    def mock_sqlite_manager(self):
        """Create a mock SQLite manager."""
        return Mock()
    
    @pytest.fixture
    def mock_connection(self):
        """Create a mock database connection with context manager support."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        return mock_conn
    
    @pytest.fixture
    def repository(self, mock_sqlite_manager, mock_connection):
        """Create a repository instance with mocked dependencies."""
        mock_sqlite_manager.get_connection.return_value = mock_connection
        return DockerImageRepository(mock_sqlite_manager)
    
    # Test initialization
    def test_init(self, mock_sqlite_manager):
        """Test repository initialization."""
        repo = DockerImageRepository(mock_sqlite_manager)
        assert repo.persistence_manager == mock_sqlite_manager
    
    # Test create_entity_record
    def test_create_entity_record(self, repository, mock_connection):
        """Test creating entity through create_entity_record."""
        entity = {
            'name': 'test-image',
            'tag': 'v1.0',
            'dockerfile_hash': 'abc123',
            'build_command': 'docker build .',
            'build_status': 'pending'
        }
        
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None  # No existing image
        mock_cursor.lastrowid = 42
        
        result = repository.create_entity_record(entity)
        
        assert result == 42
        # Should execute INSERT query
        assert mock_connection.execute.called
    
    def test_create_image_record(self, repository, mock_connection):
        """Test creating entity through create_image_record."""
        entity = {
            'name': 'test-image',
            'tag': 'latest',
            'dockerfile_hash': 'def456',
            'build_command': 'docker build -t test .',
            'build_status': 'success'
        }
        
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        mock_cursor.lastrowid = 24
        
        result = repository.create_image_record(entity)
        
        assert result == 24
    
    # Test find_by_id
    def test_find_by_id_with_tag(self, repository, mock_connection):
        """Test finding image by ID with tag specified."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'id': 1,
            'name': 'test-image',
            'tag': 'v1.0',
            'build_status': 'success'
        })
        
        result = repository.find_by_id('test-image:v1.0')
        
        assert result is not None
        assert result['name'] == 'test-image'
        assert result['tag'] == 'v1.0'
    
    def test_find_by_id_without_tag(self, repository, mock_connection):
        """Test finding image by ID without tag (defaults to 'latest')."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'id': 1,
            'name': 'test-image',
            'tag': 'latest',
            'build_status': 'success'
        })
        
        result = repository.find_by_id('test-image')
        
        assert result is not None
        assert result['tag'] == 'latest'
    
    def test_find_by_id_not_found(self, repository, mock_connection):
        """Test finding non-existent image."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        result = repository.find_by_id('non-existent:tag')
        
        assert result is None
    
    # Test find_all
    def test_find_all_with_pagination(self, repository, mock_connection):
        """Test finding all images with limit and offset."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            MockSQLiteRow({'id': 1, 'name': 'image1', 'tag': 'latest'}),
            MockSQLiteRow({'id': 2, 'name': 'image2', 'tag': 'v1.0'}),
            MockSQLiteRow({'id': 3, 'name': 'image3', 'tag': 'v2.0'}),
            MockSQLiteRow({'id': 4, 'name': 'image4', 'tag': 'latest'}),
        ]
        
        result = repository.find_all(limit=2, offset=1)
        
        assert len(result) == 2
        assert result[0]['name'] == 'image2'
        assert result[1]['name'] == 'image3'
    
    def test_find_all_no_pagination(self, repository, mock_connection):
        """Test finding all images without pagination."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            MockSQLiteRow({'id': 1, 'name': 'image1', 'tag': 'latest'}),
            MockSQLiteRow({'id': 2, 'name': 'image2', 'tag': 'v1.0'}),
        ]
        
        result = repository.find_all(limit=None, offset=None)
        
        assert len(result) == 2
    
    # Test update
    def test_update_existing_image(self, repository, mock_connection):
        """Test updating existing image."""
        # Mock finding existing image
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'id': 1,
            'name': 'test-image',
            'tag': 'v1.0'
        })
        
        updates = {
            'build_status': 'success',
            'image_id': 'sha256:abcdef',
            'build_time_ms': 5000,
            'size_bytes': 1024000
        }
        
        result = repository.update('test-image:v1.0', updates)
        
        assert result is True
        # Should execute SELECT and UPDATE queries
        assert mock_connection.execute.call_count >= 2
    
    def test_update_non_existing_image(self, repository, mock_connection):
        """Test updating non-existing image."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None
        
        result = repository.update('non-existent:tag', {'build_status': 'success'})
        
        assert result is False
    
    # Test delete
    def test_delete_with_tag(self, repository, mock_connection):
        """Test deleting image with tag."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.rowcount = 1
        
        result = repository.delete('test-image:v1.0')
        
        assert result is True
    
    def test_delete_without_tag(self, repository, mock_connection):
        """Test deleting image without tag (defaults to 'latest')."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.rowcount = 1
        
        result = repository.delete('test-image')
        
        assert result is True
        # Check that 'latest' tag was used
        call_args = mock_connection.execute.call_args
        assert call_args[0][1] == ('test-image', 'latest')
    
    def test_delete_non_existing(self, repository, mock_connection):
        """Test deleting non-existing image."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.rowcount = 0
        
        result = repository.delete('non-existent:tag')
        
        assert result is False
    
    # Test create_or_update_image
    def test_create_or_update_image_new(self, repository, mock_connection):
        """Test creating new image."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = None  # No existing image
        mock_cursor.lastrowid = 10
        
        result = repository.create_or_update_image(
            name='new-image',
            tag='v1.0',
            dockerfile_hash='hash123',
            build_command='docker build .',
            build_status='pending'
        )
        
        assert result == 10
        # Should execute SELECT then INSERT
        assert mock_connection.execute.call_count == 2
    
    def test_create_or_update_image_existing(self, repository, mock_connection):
        """Test updating existing image."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'id': 5,
            'name': 'existing-image',
            'tag': 'v1.0'
        })
        
        result = repository.create_or_update_image(
            name='existing-image',
            tag='v1.0',
            dockerfile_hash='newhash',
            build_command='docker build .',
            build_status='rebuilt'
        )
        
        assert result == 5
        # Should execute SELECT then UPDATE
        assert mock_connection.execute.call_count == 2
    
    # Test update_image_build_result
    def test_update_image_build_result(self, repository, mock_connection):
        """Test updating image build results."""
        repository.update_image_build_result(
            name='test-image',
            tag='v1.0',
            image_id='sha256:123456',
            build_status='success',
            build_time_ms=3000,
            size_bytes=500000
        )
        
        # Should execute UPDATE query
        assert mock_connection.execute.called
        call_args = mock_connection.execute.call_args
        assert 'UPDATE docker_images' in call_args[0][0]
    
    # Test find_image
    def test_find_image(self, repository, mock_connection):
        """Test finding specific image."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'id': 1,
            'name': 'test-image',
            'tag': 'v1.0',
            'build_status': 'success'
        })
        
        result = repository.find_image('test-image', 'v1.0')
        
        assert result is not None
        assert result['name'] == 'test-image'
        assert result['tag'] == 'v1.0'
    
    # Test find_images_by_status
    def test_find_images_by_status(self, repository, mock_connection):
        """Test finding images by build status."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            MockSQLiteRow({'id': 1, 'name': 'image1', 'build_status': 'success'}),
            MockSQLiteRow({'id': 2, 'name': 'image2', 'build_status': 'success'}),
        ]
        
        result = repository.find_images_by_status('success')
        
        assert len(result) == 2
        assert all(img['build_status'] == 'success' for img in result)
    
    # Test find_images_by_name_prefix
    def test_find_images_by_name_prefix(self, repository, mock_connection):
        """Test finding images by name prefix."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            MockSQLiteRow({'id': 1, 'name': 'test-app-1', 'tag': 'latest'}),
            MockSQLiteRow({'id': 2, 'name': 'test-app-2', 'tag': 'v1.0'}),
        ]
        
        result = repository.find_images_by_name_prefix('test-app')
        
        assert len(result) == 2
        assert all(img['name'].startswith('test-app') for img in result)
        
        # Check LIKE pattern
        call_args = mock_connection.execute.call_args
        assert call_args[0][1] == ('test-app%',)
    
    # Test get_all_images
    def test_get_all_images(self, repository, mock_connection):
        """Test getting all images."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            MockSQLiteRow({'id': 1, 'name': 'image1', 'last_used_at': '2024-01-01'}),
            MockSQLiteRow({'id': 2, 'name': 'image2', 'last_used_at': '2024-01-02'}),
        ]
        
        result = repository.get_all_images()
        
        assert len(result) == 2
        # Check ORDER BY last_used_at DESC
        call_args = mock_connection.execute.call_args
        assert 'ORDER BY last_used_at DESC' in call_args[0][0]
    
    # Test find_unused_images
    def test_find_unused_images_default_days(self, repository, mock_connection):
        """Test finding unused images with default 30 days."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = [
            MockSQLiteRow({'id': 1, 'name': 'old-image', 'last_used_at': '2023-01-01'}),
        ]
        
        result = repository.find_unused_images()
        
        assert len(result) == 1
        # Check default 30 days parameter
        call_args = mock_connection.execute.call_args
        assert call_args[0][1] == (30,)
    
    def test_find_unused_images_custom_days(self, repository, mock_connection):
        """Test finding unused images with custom days."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchall.return_value = []
        
        result = repository.find_unused_images(days=7)
        
        assert len(result) == 0
        # Check custom days parameter
        call_args = mock_connection.execute.call_args
        assert call_args[0][1] == (7,)
    
    # Test update_last_used
    def test_update_last_used(self, repository, mock_connection):
        """Test updating last used timestamp."""
        repository.update_last_used('test-image', 'v1.0')
        
        # Should execute UPDATE query
        assert mock_connection.execute.called
        call_args = mock_connection.execute.call_args
        assert 'UPDATE docker_images' in call_args[0][0]
        assert 'last_used_at = CURRENT_TIMESTAMP' in call_args[0][0]
        assert call_args[0][1] == ('test-image', 'v1.0')
    
    # Test delete_image
    def test_delete_image_success(self, repository, mock_connection):
        """Test successful image deletion."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.rowcount = 1
        
        result = repository.delete_image('test-image', 'v1.0')
        
        assert result is True
    
    def test_delete_image_not_found(self, repository, mock_connection):
        """Test deleting non-existent image."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.rowcount = 0
        
        result = repository.delete_image('non-existent', 'tag')
        
        assert result is False
    
    # Test get_image_stats
    def test_get_image_stats(self, repository, mock_connection):
        """Test getting image statistics."""
        mock_cursor = mock_connection.execute.return_value
        
        # Mock responses for each query
        mock_cursor.fetchone.side_effect = [
            (10,),  # Total count
            (1500000,)  # Total size
        ]
        
        mock_cursor.fetchall.return_value = [
            ('success', 7),
            ('failed', 2),
            ('pending', 1)
        ]
        
        result = repository.get_image_stats()
        
        assert result['total'] == 10
        assert result['by_status'] == {
            'success': 7,
            'failed': 2,
            'pending': 1
        }
        assert result['total_size_bytes'] == 1500000
        
        # Should execute 3 queries
        assert mock_connection.execute.call_count == 3
    
    def test_get_image_stats_no_size_info(self, repository, mock_connection):
        """Test getting stats when no images have size info."""
        mock_cursor = mock_connection.execute.return_value
        
        # Mock responses
        mock_cursor.fetchone.side_effect = [
            (5,),  # Total count
            (None,)  # No size info
        ]
        
        mock_cursor.fetchall.return_value = [('success', 5)]
        
        with pytest.raises(ValueError, match="No docker images with size information found"):
            repository.get_image_stats()
    
    # Test edge cases
    def test_entity_id_with_multiple_colons(self, repository, mock_connection):
        """Test handling entity ID with multiple colons."""
        mock_cursor = mock_connection.execute.return_value
        mock_cursor.fetchone.return_value = MockSQLiteRow({
            'id': 1,
            'name': 'registry.example.com:5000/test-image',
            'tag': 'v1.0.0',
        })
        
        # Should split on first colon only
        result = repository.find_by_id('registry.example.com:5000/test-image:v1.0.0')
        
        assert result is not None
        call_args = mock_connection.execute.call_args
        assert call_args[0][1] == ('registry.example.com', '5000/test-image:v1.0.0')