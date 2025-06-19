"""設定データアクセス層"""
from pathlib import Path
from typing import Dict, Optional


class ConfigurationRepository:
    """設定データの永続化とアクセスを担当

    責任:
    - SQLiteデータベースからの設定読み込み
    - 設定値の保存
    - データベース操作の抽象化
    """

    def __init__(self, db_path: str = "cph_history.db", json_provider=None, sqlite_provider=None):
        """初期化

        Args:
            db_path: SQLiteデータベースのパス
            json_provider: JSON操作プロバイダー
            sqlite_provider: SQLite操作プロバイダー
        """
        self.db_path = db_path
        self._json_provider = json_provider or self._get_default_json_provider()
        self._sqlite_provider = sqlite_provider or self._get_default_sqlite_provider()

    def _get_default_json_provider(self):
        """Get default JSON provider if none provided."""
        from src.infrastructure.providers.json_provider import SystemJsonProvider
        return SystemJsonProvider()

    def _get_default_sqlite_provider(self):
        """Get default SQLite provider if none provided."""
        from src.infrastructure.providers.sqlite_provider import SystemSQLiteProvider
        return SystemSQLiteProvider()

    def load_previous_values(self) -> Dict[str, str]:
        """前回値の読み込み

        Returns:
            Dict[str, str]: 前回値の辞書（contest_name, problem_name）
        """
        result = {
            "old_contest_name": "",
            "old_problem_name": ""
        }

        if not Path(self.db_path).exists():
            return result

        try:
            conn = self._sqlite_provider.connect(self.db_path)
            try:
                # old_contest_nameを取得
                old_contest_name = self._get_config_value(conn, "old_contest_name")
                if old_contest_name:
                    result["old_contest_name"] = old_contest_name

                # old_problem_nameを取得
                old_problem_name = self._get_config_value(conn, "old_problem_name")
                if old_problem_name:
                    result["old_problem_name"] = old_problem_name
            finally:
                self._sqlite_provider.close(conn)

        except Exception:
            # エラー時は空文字列を返す
            pass

        return result

    def save_current_values(self, contest_name: str, problem_name: str) -> None:
        """現在値の保存

        Args:
            contest_name: コンテスト名
            problem_name: 問題名
        """
        if not Path(self.db_path).exists():
            return

        try:
            conn = self._sqlite_provider.connect(self.db_path)
            try:
                # 値を保存
                self._save_config_value(conn, "old_contest_name", contest_name)
                self._save_config_value(conn, "old_problem_name", problem_name)
                self._sqlite_provider.commit(conn)
            finally:
                self._sqlite_provider.close(conn)

        except Exception:
            # エラー時は無視
            pass

    def _get_config_value(self, conn, key: str) -> Optional[str]:
        """設定値を取得

        Args:
            conn: SQLite接続
            key: 設定キー

        Returns:
            Optional[str]: 設定値（存在しない場合はNone）
        """
        cursor = self._sqlite_provider.execute(
            conn,
            "SELECT config_value FROM system_config WHERE config_key = ?",
            (key,)
        )
        row = self._sqlite_provider.fetchone(cursor)

        if row and row[0]:
            try:
                return self._json_provider.loads(row[0])
            except Exception:
                return None

        return None

    def _save_config_value(self, conn, key: str, value: str) -> None:
        """設定値を保存

        Args:
            conn: SQLite接続
            key: 設定キー
            value: 設定値
        """
        json_value = self._json_provider.dumps(value)

        self._sqlite_provider.execute(conn, """
            INSERT OR REPLACE INTO system_config (config_key, config_value)
            VALUES (?, ?)
        """, (key, json_value))

    def get_available_config_keys(self) -> list[str]:
        """利用可能な設定キーの一覧を取得

        Returns:
            list[str]: 設定キーのリスト
        """
        if not Path(self.db_path).exists():
            return []

        try:
            conn = self._sqlite_provider.connect(self.db_path)
            try:
                cursor = self._sqlite_provider.execute(conn, "SELECT config_key FROM system_config", ())
                rows = self._sqlite_provider.fetchall(cursor)
                return [row[0] for row in rows]
            finally:
                self._sqlite_provider.close(conn)

        except Exception:
            return []
