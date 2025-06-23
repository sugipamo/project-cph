"""ファイル操作関連モジュールのラッパー実装"""
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Union

from .file_operations import FileOperations


class FileOperationsImpl(FileOperations):
    """shutil, json, yaml などの実装"""

    def copy_file(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        shutil.copy2(src, dst)

    def copy_tree(self, src: Union[str, Path], dst: Union[str, Path], dirs_exist_ok: bool) -> None:
        shutil.copytree(src, dst, dirs_exist_ok=dirs_exist_ok)

    def move(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        shutil.move(str(src), str(dst))

    def remove_tree(self, path: Union[str, Path]) -> None:
        shutil.rmtree(path)

    def load_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        with open(file_path, encoding='utf-8') as f:
            return json.load(f)

    def dump_json(self, data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> None:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    def load_yaml(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        # yaml モジュールは必要に応じて動的インポート
        try:
            import yaml
        except ImportError as e:
            raise ImportError("PyYAML is required for YAML operations") from e

        with open(file_path, encoding='utf-8') as f:
            return yaml.safe_load(f)

    def dump_yaml(self, data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        # yaml モジュールは必要に応じて動的インポート
        try:
            import yaml
        except ImportError as e:
            raise ImportError("PyYAML is required for YAML operations") from e

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
