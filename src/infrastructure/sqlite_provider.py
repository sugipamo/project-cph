"""SQLiteプロバイダー - 副作用を集約"""
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union


class SQLiteProvider(ABC):
    """SQLite操作の抽象インターフェース"""

    @abstractmethod
    def connect(self, database: str, **kwargs) -> Any:
        """データベースに接続"""
        pass

    @abstractmethod
    def execute_sql_statement(self, connection: Any, sql: str, parameters: Tuple) -> Any:
        """SQL文の実行"""
        pass

    @abstractmethod
    def executemany(self, connection: Any, sql: str, seq_of_parameters: Optional[List[Tuple]]) -> Any:
        """複数SQL実行"""
        pass

    @abstractmethod
    def fetchone(self, cursor: Any) -> Optional[Tuple]:
        """1行取得"""
        pass

    @abstractmethod
    def fetchall(self, cursor: Any) -> List[Tuple]:
        """全行取得"""
        pass

    @abstractmethod
    def commit(self, connection: Any) -> None:
        """トランザクションコミット"""
        pass

    @abstractmethod
    def rollback(self, connection: Any) -> None:
        """トランザクションロールバック"""
        pass

    @abstractmethod
    def close(self, connection: Any) -> None:
        """接続クローズ"""
        pass


class SystemSQLiteProvider(SQLiteProvider):
    """システムSQLite操作の実装 - 副作用はここに集約"""

    def connect(self, database: str, **kwargs) -> Any:
        """データベースに接続（副作用）"""
        return sqlite3.connect(database, **kwargs)

    def execute_sql_statement(self, connection: Any, sql: str, parameters: Tuple) -> Any:
        """SQL文の実行（副作用）"""
        return connection.execute(sql, parameters)

    def executemany(self, connection: Any, sql: str, seq_of_parameters: Optional[List[Tuple]]) -> Any:
        """複数SQL実行（副作用）"""
        if seq_of_parameters is None:
            seq_of_parameters = []
        return connection.executemany(sql, seq_of_parameters)

    def fetchone(self, cursor: Any) -> Optional[Tuple]:
        """1行取得（副作用なし）"""
        return cursor.fetchone()

    def fetchall(self, cursor: Any) -> List[Tuple]:
        """全行取得（副作用なし）"""
        return cursor.fetchall()

    def commit(self, connection: Any) -> None:
        """トランザクションコミット（副作用）"""
        connection.commit()

    def rollback(self, connection: Any) -> None:
        """トランザクションロールバック（副作用）"""
        connection.rollback()

    def close(self, connection: Any) -> None:
        """接続クローズ（副作用）"""
        connection.close()


class MockSQLiteProvider(SQLiteProvider):
    """テスト用モックSQLiteプロバイダー - 副作用なし"""

    def __init__(self):
        self._connections: Dict[str, Dict] = {}
        self._data: Dict[str, Dict[str, List[Dict]]] = {}  # database -> table -> rows

    def connect(self, database: str, **kwargs) -> Any:
        """モック接続（副作用なし）"""
        if database not in self._connections:
            self._connections[database] = {
                'database': database,
                'closed': False,
                'in_transaction': False
            }
            self._data[database] = {}
        return MockSQLiteConnection(database, self)

    def execute_sql_statement(self, connection: Any, sql: str, parameters: Tuple) -> Any:
        """モックSQL文の実行（副作用なし）"""
        return MockSQLiteCursor(connection.database, sql, parameters, self)

    def executemany(self, connection: Any, sql: str, seq_of_parameters: Optional[List[Tuple]]) -> Any:
        """モック複数SQL実行（副作用なし）"""
        if seq_of_parameters is None:
            seq_of_parameters = []
        return MockSQLiteCursor(connection.database, sql, seq_of_parameters, self)

    def fetchone(self, cursor: Any) -> Optional[Tuple]:
        """モック1行取得（副作用なし）"""
        return cursor.fetchone()

    def fetchall(self, cursor: Any) -> List[Tuple]:
        """モック全行取得（副作用なし）"""
        return cursor.fetchall()

    def commit(self, connection: Any) -> None:
        """モックコミット（副作用なし）"""
        if connection.database in self._connections:
            self._connections[connection.database]['in_transaction'] = False

    def rollback(self, connection: Any) -> None:
        """モックロールバック（副作用なし）"""
        if connection.database in self._connections:
            self._connections[connection.database]['in_transaction'] = False

    def close(self, connection: Any) -> None:
        """モッククローズ（副作用なし）"""
        if connection.database in self._connections:
            self._connections[connection.database]['closed'] = True

    def add_mock_table(self, database: str, table: str, rows: List[Dict]) -> None:
        """テスト用テーブル追加"""
        if database not in self._data:
            self._data[database] = {}
        self._data[database][table] = rows


class MockSQLiteConnection:
    """モックSQLite接続オブジェクト"""

    def __init__(self, database: str, provider: MockSQLiteProvider):
        self.database = database
        self._provider = provider

    def execute(self, sql: str, parameters: Tuple) -> Any:
        """SQLite互換のexecuteメソッド"""
        return self._provider.execute_sql_statement(self, sql, parameters)

    def execute_sql_statement(self, sql: str, parameters: Tuple) -> Any:
        return self._provider.execute_sql_statement(self, sql, parameters)

    def executescript(self, sql_script: str) -> Any:
        """SQLite互換のexecutescriptメソッド"""
        # スクリプトを個別のSQL文に分割して実行
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        cursor = None
        for stmt in statements:
            cursor = self._provider.execute_sql_statement(self, stmt, ())
        return cursor

    def executemany(self, sql: str, seq_of_parameters: Optional[List[Tuple]]) -> Any:
        return self._provider.executemany(self, sql, seq_of_parameters)

    def commit(self) -> None:
        self._provider.commit(self)

    def rollback(self) -> None:
        self._provider.rollback(self)

    def close(self) -> None:
        self._provider.close(self)


class MockSQLiteCursor:
    """モックSQLiteカーソルオブジェクト"""

    def __init__(self, database: str, sql: str, parameters: Union[Tuple, List[Tuple]], provider: MockSQLiteProvider):
        self.database = database
        self.sql = sql
        self.parameters = parameters
        self._provider = provider
        self._results: List[Tuple] = []

    def fetchone(self) -> Optional[Tuple]:
        """モック1行取得"""
        if self._results:
            return self._results.pop(0)
        return None

    def fetchall(self) -> List[Tuple]:
        """モック全行取得"""
        results = self._results.copy()
        self._results.clear()
        return results
