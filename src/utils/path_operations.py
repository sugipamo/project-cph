"""統合パス操作ライブラリ
既存の3つのパス操作実装を統合し、統一されたAPIを提供

このモジュールは以下の既存実装を統合します：
- src/operations/utils/path_utils.py (従来のOOP実装)
- src/pure_functions/path_utils_pure.py (関数型実装)
- src/pure_functions/docker_path_utils_pure.py (Docker特化実装)
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from src.context.resolver.config_resolver import ConfigNode, resolve_best


@dataclass(frozen=True)
class PathOperationResult:
    """パス操作結果の統一データクラス"""
    success: bool
    result: Optional[str]
    errors: list[str]
    warnings: list[str]
    metadata: dict[str, Any]

    def __post_init__(self):
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


@dataclass(frozen=True)
class PathInfo:
    """パス情報の不変データクラス"""
    path: str
    is_absolute: bool
    is_directory: bool
    is_file: bool
    parent: str
    name: str
    stem: str
    suffix: str
    parts: tuple[str, ...]

    @classmethod
    def from_path(cls, file_path: Union[str, Path]) -> 'PathInfo':
        """パスからPathInfoを作成"""
        p = Path(file_path)
        return cls(
            path=str(p),
            is_absolute=p.is_absolute(),
            is_directory=p.is_dir() if p.exists() else False,
            is_file=p.is_file() if p.exists() else False,
            parent=str(p.parent),
            name=p.name,
            stem=p.stem,
            suffix=p.suffix,
            parts=p.parts
        )


class PathOperations:
    """統合されたパス操作クラス

    シンプルなAPI（例外ベース）と詳細なAPI（結果型ベース）の両方を提供
    """

    @staticmethod
    def resolve_path(base_dir: Union[str, Path],
                    path: Union[str, Path],
                    strict: bool = False) -> Union[str, PathOperationResult]:
        """パスを解決する

        Args:
            base_dir: ベースディレクトリ
            path: 対象パス
            strict: Trueの場合、詳細な結果型を返す

        Returns:
            strict=Falseの場合: 解決されたパス文字列
            strict=Trueの場合: PathOperationResult

        Raises:
            ValueError: strict=Falseで解決に失敗した場合
        """
        try:
            # 入力値の事前チェック
            errors = []
            warnings = []

            if base_dir is None:
                errors.append("Base directory cannot be None")
            if path is None:
                errors.append("Path cannot be None")
            if path is not None and not str(path).strip():
                errors.append("Path cannot be empty")
            if base_dir is not None and not str(base_dir).strip():
                errors.append("Base directory cannot be empty")

            if errors:
                if strict:
                    return PathOperationResult(
                        success=False,
                        result=None,
                        errors=errors,
                        warnings=warnings,
                        metadata={"base_dir": str(base_dir) if base_dir is not None else "None",
                                "path": str(path) if path is not None else "None"}
                    )
                raise ValueError(errors[0])

            base = Path(base_dir)
            target = Path(path)

            if not base.exists() and not base.is_absolute():
                warnings.append(f"Base directory may not exist: {base}")

            if errors:
                if strict:
                    return PathOperationResult(
                        success=False,
                        result=None,
                        errors=errors,
                        warnings=warnings,
                        metadata={"base_dir": str(base_dir), "path": str(path)}
                    )
                raise ValueError(errors[0])

            # パス解決
            if target.is_absolute():
                resolved = target
            else:
                resolved = base / target

            resolved_str = str(resolved.resolve())

            if strict:
                return PathOperationResult(
                    success=True,
                    result=resolved_str,
                    errors=[],
                    warnings=warnings,
                    metadata={
                        "base_dir": str(base_dir),
                        "path": str(path),
                        "is_absolute": target.is_absolute(),
                        "resolution_method": "absolute" if target.is_absolute() else "relative"
                    }
                )
            return resolved_str

        except Exception as e:
            error_msg = f"Failed to resolve path: {e}"
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[error_msg],
                    warnings=[],
                    metadata={"base_dir": str(base_dir), "path": str(path)}
                )
            raise ValueError(error_msg) from e

    @staticmethod
    def normalize_path(path: Union[str, Path],
                      strict: bool = False) -> Union[str, PathOperationResult]:
        """パスを正規化する

        Args:
            path: 対象パス
            strict: Trueの場合、詳細な結果型を返す

        Returns:
            strict=Falseの場合: 正規化されたパス文字列
            strict=Trueの場合: PathOperationResult
        """
        try:
            p = Path(path)
            normalized = str(p.resolve())

            if strict:
                return PathOperationResult(
                    success=True,
                    result=normalized,
                    errors=[],
                    warnings=[],
                    metadata={"original": str(path), "normalized": normalized}
                )
            return normalized

        except Exception as e:
            error_msg = f"Failed to normalize path: {e}"
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[error_msg],
                    warnings=[],
                    metadata={"original": str(path)}
                )
            raise ValueError(error_msg) from e

    @staticmethod
    def safe_path_join(*paths: Union[str, Path],
                      strict: bool = False) -> Union[str, PathOperationResult]:
        """安全にパスを結合する（パストラバーサル対策）

        Args:
            *paths: 結合するパス要素
            strict: Trueの場合、詳細な結果型を返す

        Returns:
            strict=Falseの場合: 結合されたパス文字列
            strict=Trueの場合: PathOperationResult
        """
        try:
            if not paths:
                error_msg = "At least one path must be provided"
                if strict:
                    return PathOperationResult(
                        success=False,
                        result=None,
                        errors=[error_msg],
                        warnings=[],
                        metadata={}
                    )
                raise ValueError(error_msg)

            # セキュリティチェック
            warnings = []
            for path in paths:
                path_str = str(path)
                if ".." in path_str or path_str.startswith("/"):
                    warnings.append(f"Potentially unsafe path component: {path_str}")

            # パス結合
            result = Path(paths[0])
            for path in paths[1:]:
                result = result / path

            result_str = str(result)

            if strict:
                return PathOperationResult(
                    success=True,
                    result=result_str,
                    errors=[],
                    warnings=warnings,
                    metadata={"paths": [str(p) for p in paths]}
                )
            return result_str

        except Exception as e:
            error_msg = f"Failed to join paths: {e}"
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[error_msg],
                    warnings=[],
                    metadata={"paths": [str(p) for p in paths]}
                )
            raise ValueError(error_msg) from e

    @staticmethod
    def get_relative_path(path: Union[str, Path],
                         base: Union[str, Path],
                         strict: bool = False) -> Union[str, PathOperationResult]:
        """ベースパスからの相対パスを取得する

        Args:
            path: 対象パス
            base: ベースパス
            strict: Trueの場合、詳細な結果型を返す

        Returns:
            strict=Falseの場合: 相対パス文字列
            strict=Trueの場合: PathOperationResult
        """
        try:
            path_obj = Path(path)
            base_obj = Path(base)

            relative = path_obj.relative_to(base_obj)
            result_str = str(relative)

            if strict:
                return PathOperationResult(
                    success=True,
                    result=result_str,
                    errors=[],
                    warnings=[],
                    metadata={"path": str(path), "base": str(base)}
                )
            return result_str

        except ValueError as e:
            error_msg = f"Cannot compute relative path: {e}"
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[error_msg],
                    warnings=[],
                    metadata={"path": str(path), "base": str(base)}
                )
            raise ValueError(error_msg) from e

    @staticmethod
    def is_subdirectory(path: Union[str, Path],
                       parent: Union[str, Path],
                       strict: bool = False) -> Union[bool, tuple[bool, PathOperationResult]]:
        """パスが指定された親ディレクトリのサブディレクトリかチェック

        Args:
            path: チェック対象パス
            parent: 親ディレクトリパス
            strict: Trueの場合、詳細な結果も返す

        Returns:
            strict=Falseの場合: bool
            strict=Trueの場合: (bool, PathOperationResult)
        """
        try:
            path_obj = Path(path).resolve()
            parent_obj = Path(parent).resolve()

            is_sub = str(path_obj).startswith(str(parent_obj))

            if strict:
                result = PathOperationResult(
                    success=True,
                    result=str(is_sub),
                    errors=[],
                    warnings=[],
                    metadata={
                        "path": str(path_obj),
                        "parent": str(parent_obj),
                        "is_subdirectory": is_sub
                    }
                )
                return is_sub, result
            return is_sub

        except Exception as e:
            if strict:
                result = PathOperationResult(
                    success=False,
                    result=None,
                    errors=[f"Failed to check subdirectory: {e}"],
                    warnings=[],
                    metadata={"path": str(path), "parent": str(parent)}
                )
                return False, result
            return False

    @staticmethod
    def ensure_parent_dir(path: Union[str, Path]) -> None:
        """指定されたパスの親ディレクトリを作成する

        Args:
            path: 対象パス

        Raises:
            OSError: ディレクトリ作成に失敗した場合
        """
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_file_extension(path: Union[str, Path],
                          strict: bool = False) -> Union[str, PathOperationResult]:
        """ファイルの拡張子を取得する

        Args:
            path: 対象パス
            strict: Trueの場合、詳細な結果型を返す

        Returns:
            strict=Falseの場合: 拡張子文字列（ドット付き）
            strict=Trueの場合: PathOperationResult
        """
        try:
            p = Path(path)
            extension = p.suffix

            if strict:
                return PathOperationResult(
                    success=True,
                    result=extension,
                    errors=[],
                    warnings=[],
                    metadata={"path": str(path), "name": p.name, "stem": p.stem}
                )
            return extension

        except Exception as e:
            error_msg = f"Failed to get file extension: {e}"
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[error_msg],
                    warnings=[],
                    metadata={"path": str(path)}
                )
            raise ValueError(error_msg) from e

    @staticmethod
    def change_extension(path: Union[str, Path],
                        new_extension: str,
                        strict: bool = False) -> Union[str, PathOperationResult]:
        """ファイルの拡張子を変更する

        Args:
            path: 対象パス
            new_extension: 新しい拡張子（ドットありなし両対応）
            strict: Trueの場合、詳細な結果型を返す

        Returns:
            strict=Falseの場合: 新しいパス文字列
            strict=Trueの場合: PathOperationResult
        """
        try:
            p = Path(path)

            # 拡張子にドットを追加（必要に応じて）
            if new_extension and not new_extension.startswith('.'):
                new_extension = '.' + new_extension

            new_path = p.with_suffix(new_extension)
            result_str = str(new_path)

            if strict:
                return PathOperationResult(
                    success=True,
                    result=result_str,
                    errors=[],
                    warnings=[],
                    metadata={
                        "original": str(path),
                        "original_extension": p.suffix,
                        "new_extension": new_extension
                    }
                )
            return result_str

        except Exception as e:
            error_msg = f"Failed to change extension: {e}"
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[error_msg],
                    warnings=[],
                    metadata={"path": str(path), "new_extension": new_extension}
                )
            raise ValueError(error_msg) from e


class DockerPathOperations:
    """Docker特化のパス操作クラス"""

    @staticmethod
    def should_build_custom_docker_image(image_name: str) -> bool:
        """Determine if a Docker image should be built locally or pulled from registry

        Args:
            image_name: Name of the Docker image

        Returns:
            True if image should be built locally, False if it should be pulled
        """
        # Custom CPH images that need to be built
        custom_image_prefixes = ['ojtools', 'cph_']

        for prefix in custom_image_prefixes:
            if image_name.startswith(prefix):
                return True

        # Check if it's a registry image (e.g., docker.io/library/python)
        # Registry images typically have format: registry/namespace/image:tag
        if '/' in image_name:
            parts = image_name.split('/')
            # Common registries
            registries = ['docker.io', 'gcr.io', 'registry.hub.docker.com', 'quay.io', 'ghcr.io']
            if parts[0] in registries or '.' in parts[0]:
                # Looks like a registry URL
                return False

        # Standard images without registry prefix (e.g., python:3.9, ubuntu)
        # These can be pulled from Docker Hub
        if ':' in image_name and '/' not in image_name:
            return False

        # Simple image names without tag (e.g., python, ubuntu, alpine)
        return '/' in image_name or '@' in image_name

    @staticmethod
    def convert_path_to_docker_mount(path: str,
                                   workspace_path: str,
                                   mount_path: str) -> str:
        """ホストパスをDockerコンテナマウントパスに変換

        Args:
            path: 元のパス（workspace参照を含む可能性）
            workspace_path: ホストのワークスペースパス
            mount_path: Dockerマウントパス

        Returns:
            Dockerコンテナ内で使用するパス
        """
        # パスがワークスペースパスそのものか./workspaceの場合、マウントパスを返す
        if path == "./workspace" or path == workspace_path:
            return mount_path

        # パスにワークスペースパスが含まれている場合、置換する
        if workspace_path in path:
            return path.replace(workspace_path, mount_path)

        return path

    @staticmethod
    def get_docker_mount_path_from_config(env_json: dict,
                                        language: str,
                                        default_mount_path: str = "/workspace") -> str:
        """設定からDockerマウントパスを取得

        Args:
            env_json: 環境設定JSON
            language: プログラミング言語
            default_mount_path: デフォルトマウントパス

        Returns:
            マウントパス
        """
        if not env_json:
            return default_mount_path

        # 言語固有の設定を確認
        if language in env_json:
            lang_config = env_json[language]
            if isinstance(lang_config, dict) and "mount_path" in lang_config:
                return lang_config["mount_path"]

        # グローバル設定を確認
        if "mount_path" in env_json:
            return env_json["mount_path"]

        return default_mount_path


# Configuration-based path resolution functions
# Migrated from src/operations/utils/path_utils.py

def get_workspace_path(resolver: ConfigNode, language: str) -> Path:
    """Get workspace path from configuration."""
    node = resolve_best(resolver, [language, "workspace_path"])
    if node is None or node.value is None or node.key != "workspace_path":
        raise TypeError("workspace_pathが設定されていません")
    return Path(node.value)


def get_contest_current_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest current path from configuration."""
    node = resolve_best(resolver, [language, "contest_current_path"])
    if node is None or node.value is None or node.key != "contest_current_path":
        raise TypeError("contest_current_pathが設定されていません")
    return Path(node.value)


def get_contest_env_path() -> Path:
    """Get contest_env path by searching up directory tree."""
    cur = os.path.abspath(os.getcwd())
    while True:
        candidate = os.path.join(cur, "contest_env")
        if os.path.isdir(candidate):
            return Path(candidate)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    raise ValueError("contest_env_pathが自動検出できませんでした。contest_envディレクトリが見つかりません。")


def get_contest_template_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest template path from configuration."""
    node = resolve_best(resolver, [language, "contest_template_path"])
    if node is None or node.key != "contest_template_path" or node.value is None:
        raise TypeError("contest_template_pathが設定されていません")
    return Path(node.value)


def get_contest_temp_path(resolver: ConfigNode, language: str) -> Path:
    """Get contest temp path from configuration."""
    node = resolve_best(resolver, [language, "contest_temp_path"])
    if node is None or node.key != "contest_temp_path" or node.value is None:
        raise TypeError("contest_temp_pathが設定されていません")
    return Path(node.value)


def get_test_case_path(contest_current_path: Path) -> Path:
    """Get test case directory path."""
    return contest_current_path / "test"


def get_test_case_in_path(contest_current_path: Path) -> Path:
    """Get test case input directory path."""
    return get_test_case_path(contest_current_path) / "in"


def get_test_case_out_path(contest_current_path: Path) -> Path:
    """Get test case output directory path."""
    return get_test_case_path(contest_current_path) / "out"


def get_source_file_name(resolver: ConfigNode, language: str) -> str:
    """Get source file name from configuration using resolve."""
    node = resolve_best(resolver, [language, "source_file_name"])
    if node is None or node.key != "source_file_name" or node.value is None:
        raise ValueError("source_file_nameが設定されていません")
    return str(node.value)
