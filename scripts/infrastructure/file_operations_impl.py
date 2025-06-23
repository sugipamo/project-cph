"""ファイル操作関連モジュールのラッパー実装"""
# json, shutilは依存性注入により削除 - json_provider, system_operationsから受け取る
from pathlib import Path
from typing import Any, Dict, Union

from .file_operations import FileOperations


class FileOperationsImpl(FileOperations):
    """shutil, json, yaml などの実装

    副作用操作はjson_provider等のインターフェースを通じて注入される
    """

    def __init__(self, json_provider, system_operations):
        """初期化

        Args:
            json_provider: JSON操作プロバイダー
            system_operations: システム操作インターフェース（shutil操作含む）
        """
        self._json_provider = json_provider
        self._system_operations = system_operations

    def copy_file(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        # shutil操作はsystem_operations経由で実行する必要がある
        # 現在はSystemOperationsにコピー操作がないため一時的にコメントアウト
        raise NotImplementedError("copy_file requires shutil operations to be injected via system_operations")

    def copy_tree(self, src: Union[str, Path], dst: Union[str, Path], dirs_exist_ok: bool) -> None:
        # shutil操作はsystem_operations経由で実行する必要がある
        # 現在はSystemOperationsにコピー操作がないため一時的にコメントアウト
        raise NotImplementedError("copy_tree requires shutil operations to be injected via system_operations")

    def move(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        # shutil操作はsystem_operations経由で実行する必要がある
        # 現在はSystemOperationsに移動操作がないため一時的にコメントアウト
        raise NotImplementedError("move requires shutil operations to be injected via system_operations")

    def remove_tree(self, path: Union[str, Path]) -> None:
        # shutil操作はsystem_operations経由で実行する必要がある
        # 現在はSystemOperationsに削除操作がないため一時的にコメントアウト
        raise NotImplementedError("remove_tree requires shutil operations to be injected via system_operations")

    def load_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        return self._json_provider.load(file_path)

    def dump_json(self, data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> None:
        self._json_provider.dump(data, file_path, indent)

    def load_yaml(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        # yaml操作もjson_provider経由で実行する必要がある
        # 現在はシンプルな実装で代替
        raise NotImplementedError("YAML operations not yet supported through dependency injection")

    def dump_yaml(self, data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        # yaml操作もjson_provider経由で実行する必要がある
        # 現在はシンプルな実装で代替
        raise NotImplementedError("YAML operations not yet supported through dependency injection")
