import pytest
import sqlite3
from unittest.mock import Mock, MagicMock, patch
from src.infrastructure.sqlite_provider import (
    SQLiteProvider,
    SystemSQLiteProvider,
    MockSQLiteProvider,
    MockSQLiteConnection,
    MockSQLiteCursor
)


class TestSystemSQLiteProvider:
    """Tests for SystemSQLiteProvider"""
    
    @pytest.fixture
    def provider(self):
        return SystemSQLiteProvider()
    
    def test_connect(self, provider):
        """Test database connection"""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn
            
            result = provider.connect(':memory:', timeout=10)
            
            mock_connect.assert_called_once_with(':memory:', timeout=10)
            assert result == mock_conn
    
    def test_execute_sql_statement(self, provider):
        """Test SQL statement execution"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.execute.return_value = mock_cursor
        
        result = provider.execute_sql_statement(mock_conn, "SELECT * FROM test", ('param',))
        
        mock_conn.execute.assert_called_once_with("SELECT * FROM test", ('param',))
        assert result == mock_cursor
    
    def test_executemany(self, provider):
        """Test executemany"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.executemany.return_value = mock_cursor
        
        params = [('value1',), ('value2',)]
        result = provider.executemany(mock_conn, "INSERT INTO test VALUES (?)", params)
        
        mock_conn.executemany.assert_called_once_with("INSERT INTO test VALUES (?)", params)
        assert result == mock_cursor
    
    def test_executemany_none_parameters(self, provider):
        """Test executemany with None parameters"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.executemany.return_value = mock_cursor
        
        result = provider.executemany(mock_conn, "DELETE FROM test", None)
        
        mock_conn.executemany.assert_called_once_with("DELETE FROM test", [])
        assert result == mock_cursor
    
    def test_fetchone(self, provider):
        """Test fetchone"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ('value1', 'value2')
        
        result = provider.fetchone(mock_cursor)
        
        mock_cursor.fetchone.assert_called_once()
        assert result == ('value1', 'value2')
    
    def test_fetchall(self, provider):
        """Test fetchall"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [('row1',), ('row2',)]
        
        result = provider.fetchall(mock_cursor)
        
        mock_cursor.fetchall.assert_called_once()
        assert result == [('row1',), ('row2',)]
    
    def test_commit(self, provider):
        """Test commit"""
        mock_conn = Mock()
        
        provider.commit(mock_conn)
        
        mock_conn.commit.assert_called_once()
    
    def test_rollback(self, provider):
        """Test rollback"""
        mock_conn = Mock()
        
        provider.rollback(mock_conn)
        
        mock_conn.rollback.assert_called_once()
    
    def test_close(self, provider):
        """Test close"""
        mock_conn = Mock()
        
        provider.close(mock_conn)
        
        mock_conn.close.assert_called_once()


class TestMockSQLiteProvider:
    """Tests for MockSQLiteProvider"""
    
    @pytest.fixture
    def provider(self):
        return MockSQLiteProvider()
    
    def test_init(self, provider):
        """Test initialization"""
        assert provider._connections == {}
        assert provider._data == {}
    
    def test_connect_new_database(self, provider):
        """Test connecting to a new database"""
        conn = provider.connect("test.db")
        
        assert isinstance(conn, MockSQLiteConnection)
        assert conn.database == "test.db"
        assert "test.db" in provider._connections
        assert provider._connections["test.db"] == {
            'database': 'test.db',
            'closed': False,
            'in_transaction': False
        }
        assert "test.db" in provider._data
    
    def test_connect_existing_database(self, provider):
        """Test connecting to an existing database"""
        conn1 = provider.connect("test.db")
        conn2 = provider.connect("test.db")
        
        assert conn1.database == conn2.database
        assert len(provider._connections) == 1
    
    def test_execute_sql_statement(self, provider):
        """Test SQL statement execution"""
        conn = provider.connect("test.db")
        cursor = provider.execute_sql_statement(conn, "SELECT * FROM test", ('param',))
        
        assert isinstance(cursor, MockSQLiteCursor)
        assert cursor.database == "test.db"
        assert cursor.sql == "SELECT * FROM test"
        assert cursor.parameters == ('param',)
    
    def test_executemany(self, provider):
        """Test executemany"""
        conn = provider.connect("test.db")
        params = [('value1',), ('value2',)]
        cursor = provider.executemany(conn, "INSERT INTO test VALUES (?)", params)
        
        assert isinstance(cursor, MockSQLiteCursor)
        assert cursor.sql == "INSERT INTO test VALUES (?)"
        assert cursor.parameters == params
    
    def test_executemany_none_parameters(self, provider):
        """Test executemany with None parameters"""
        conn = provider.connect("test.db")
        cursor = provider.executemany(conn, "DELETE FROM test", None)
        
        assert cursor.parameters == []
    
    def test_commit(self, provider):
        """Test commit"""
        conn = provider.connect("test.db")
        provider._connections["test.db"]['in_transaction'] = True
        
        provider.commit(conn)
        
        assert provider._connections["test.db"]['in_transaction'] is False
    
    def test_rollback(self, provider):
        """Test rollback"""
        conn = provider.connect("test.db")
        provider._connections["test.db"]['in_transaction'] = True
        
        provider.rollback(conn)
        
        assert provider._connections["test.db"]['in_transaction'] is False
    
    def test_close(self, provider):
        """Test close"""
        conn = provider.connect("test.db")
        
        provider.close(conn)
        
        assert provider._connections["test.db"]['closed'] is True
    
    def test_add_mock_table(self, provider):
        """Test adding mock table data"""
        rows = [{'id': 1, 'name': 'test1'}, {'id': 2, 'name': 'test2'}]
        provider.add_mock_table("test.db", "users", rows)
        
        assert "test.db" in provider._data
        assert "users" in provider._data["test.db"]
        assert provider._data["test.db"]["users"] == rows
    
    def test_fetchone(self, provider):
        """Test fetchone through provider"""
        cursor = Mock()
        cursor.fetchone.return_value = ('value',)
        
        result = provider.fetchone(cursor)
        
        assert result == ('value',)
    
    def test_fetchall(self, provider):
        """Test fetchall through provider"""
        cursor = Mock()
        cursor.fetchall.return_value = [('row1',), ('row2',)]
        
        result = provider.fetchall(cursor)
        
        assert result == [('row1',), ('row2',)]


class TestMockSQLiteConnection:
    """Tests for MockSQLiteConnection"""
    
    @pytest.fixture
    def provider(self):
        return MockSQLiteProvider()
    
    @pytest.fixture
    def connection(self, provider):
        return MockSQLiteConnection("test.db", provider)
    
    def test_init(self, connection):
        """Test initialization"""
        assert connection.database == "test.db"
    
    def test_execute(self, connection, provider):
        """Test execute method"""
        with patch.object(provider, 'execute_sql_statement') as mock_execute:
            mock_cursor = Mock()
            mock_execute.return_value = mock_cursor
            
            result = connection.execute("SELECT * FROM test", ('param',))
            
            mock_execute.assert_called_once_with(connection, "SELECT * FROM test", ('param',))
            assert result == mock_cursor
    
    def test_execute_sql_statement(self, connection, provider):
        """Test execute_sql_statement method"""
        with patch.object(provider, 'execute_sql_statement') as mock_execute:
            mock_cursor = Mock()
            mock_execute.return_value = mock_cursor
            
            result = connection.execute_sql_statement("SELECT 1", ())
            
            mock_execute.assert_called_once_with(connection, "SELECT 1", ())
            assert result == mock_cursor
    
    def test_executescript(self, connection, provider):
        """Test executescript method"""
        script = """
        CREATE TABLE test (id INTEGER);
        INSERT INTO test VALUES (1);
        INSERT INTO test VALUES (2);
        """
        
        with patch.object(provider, 'execute_sql_statement') as mock_execute:
            mock_cursor = Mock()
            mock_execute.return_value = mock_cursor
            
            result = connection.executescript(script)
            
            # Should be called 3 times for 3 statements
            assert mock_execute.call_count == 3
            assert result == mock_cursor
    
    def test_executemany(self, connection, provider):
        """Test executemany method"""
        params = [('value1',), ('value2',)]
        
        with patch.object(provider, 'executemany') as mock_executemany:
            mock_cursor = Mock()
            mock_executemany.return_value = mock_cursor
            
            result = connection.executemany("INSERT INTO test VALUES (?)", params)
            
            mock_executemany.assert_called_once_with(connection, "INSERT INTO test VALUES (?)", params)
            assert result == mock_cursor
    
    def test_commit(self, connection, provider):
        """Test commit method"""
        with patch.object(provider, 'commit') as mock_commit:
            connection.commit()
            mock_commit.assert_called_once_with(connection)
    
    def test_rollback(self, connection, provider):
        """Test rollback method"""
        with patch.object(provider, 'rollback') as mock_rollback:
            connection.rollback()
            mock_rollback.assert_called_once_with(connection)
    
    def test_close(self, connection, provider):
        """Test close method"""
        with patch.object(provider, 'close') as mock_close:
            connection.close()
            mock_close.assert_called_once_with(connection)


class TestMockSQLiteCursor:
    """Tests for MockSQLiteCursor"""
    
    @pytest.fixture
    def provider(self):
        return MockSQLiteProvider()
    
    def test_init_with_tuple_parameters(self, provider):
        """Test initialization with tuple parameters"""
        cursor = MockSQLiteCursor("test.db", "SELECT * FROM test", ('param',), provider)
        
        assert cursor.database == "test.db"
        assert cursor.sql == "SELECT * FROM test"
        assert cursor.parameters == ('param',)
        assert cursor._results == []
    
    def test_init_with_list_parameters(self, provider):
        """Test initialization with list parameters"""
        params = [('value1',), ('value2',)]
        cursor = MockSQLiteCursor("test.db", "INSERT INTO test VALUES (?)", params, provider)
        
        assert cursor.parameters == params
    
    def test_fetchone_with_results(self, provider):
        """Test fetchone when results exist"""
        cursor = MockSQLiteCursor("test.db", "SELECT * FROM test", (), provider)
        cursor._results = [('row1',), ('row2',), ('row3',)]
        
        assert cursor.fetchone() == ('row1',)
        assert cursor.fetchone() == ('row2',)
        assert cursor.fetchone() == ('row3',)
        assert cursor.fetchone() is None
    
    def test_fetchone_empty_results(self, provider):
        """Test fetchone when no results"""
        cursor = MockSQLiteCursor("test.db", "SELECT * FROM test", (), provider)
        
        assert cursor.fetchone() is None
    
    def test_fetchall_with_results(self, provider):
        """Test fetchall when results exist"""
        cursor = MockSQLiteCursor("test.db", "SELECT * FROM test", (), provider)
        cursor._results = [('row1',), ('row2',), ('row3',)]
        
        results = cursor.fetchall()
        assert results == [('row1',), ('row2',), ('row3',)]
        assert cursor._results == []
        
        # Second call should return empty list
        assert cursor.fetchall() == []
    
    def test_fetchall_empty_results(self, provider):
        """Test fetchall when no results"""
        cursor = MockSQLiteCursor("test.db", "SELECT * FROM test", (), provider)
        
        assert cursor.fetchall() == []