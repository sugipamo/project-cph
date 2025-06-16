"""設定データアクセス層"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional


class ConfigurationRepository:
    """設定データの永続化とアクセスを担当

    責任:
    - SQLiteデータベースからの設定読み込み
    - 設定値の保存
    - データベース操作の抽象化
    """

    def __init__(self, db_path: str = "cph_history.db"):
        """初期化

        Args:
            db_path: SQLiteデータベースのパス
        """
        self.db_path = db_path

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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # old_contest_nameを取得
                old_contest_name = self._get_config_value(cursor, "old_contest_name")
                if old_contest_name:
                    result["old_contest_name"] = old_contest_name

                # old_problem_nameを取得
                old_problem_name = self._get_config_value(cursor, "old_problem_name")
                if old_problem_name:
                    result["old_problem_name"] = old_problem_name

        except (sqlite3.Error, json.JSONDecodeError):
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 値を保存
                self._save_config_value(cursor, "old_contest_name", contest_name)
                self._save_config_value(cursor, "old_problem_name", problem_name)

                conn.commit()

        except sqlite3.Error:
            # エラー時は無視
            pass

    def _get_config_value(self, cursor: sqlite3.Cursor, key: str) -> Optional[str]:
        """設定値を取得

        Args:
            cursor: SQLiteカーソル
            key: 設定キー

        Returns:
            Optional[str]: 設定値（存在しない場合はNone）
        """
        cursor.execute(
            "SELECT config_value FROM system_config WHERE config_key = ?",
            (key,)
        )
        row = cursor.fetchone()

        if row and row[0]:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return None

        return None

    def _save_config_value(self, cursor: sqlite3.Cursor, key: str, value: str) -> None:
        """設定値を保存

        Args:
            cursor: SQLiteカーソル
            key: 設定キー
            value: 設定値
        """
        json_value = json.dumps(value)

        cursor.execute("""
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config_key FROM system_config")
                rows = cursor.fetchall()
                return [row[0] for row in rows]

        except sqlite3.Error:
            return []
