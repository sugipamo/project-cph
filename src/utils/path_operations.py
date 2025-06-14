"""Core path operations for file and directory manipulation.
Main PathOperations class extracted from the original large file.
"""
import os
from pathlib import Path
from typing import Union

from src.utils.path_types import PathOperationResult


class PathOperations:
    """統合されたパス操作クラス

    シンプルなAPI（例外ベース）と詳細なAPI（結果型ベース）の両方を提供
    """

    @staticmethod
    def resolve_path(base_dir: Union[str, Path],
                    target_path: Union[str, Path],
                    strict: bool = False) -> Union[str, PathOperationResult]:
        """パスを解決する"""
        try:
            errors = []
            warnings = []

            if base_dir is None:
                errors.append("Base directory cannot be None")
            if target_path is None:
                errors.append("Path cannot be None")
            if target_path is not None and not str(target_path).strip():
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
                                "target_path": str(target_path) if target_path is not None else "None"}
                    )
                raise ValueError(errors[0])

            base_path = Path(base_dir).resolve()
            target = Path(target_path)

            if target.is_absolute():
                resolved_path = target.resolve()
            else:
                resolved_path = (base_path / target).resolve()

            result = str(resolved_path)

            if strict:
                return PathOperationResult(
                    success=True,
                    result=result,
                    errors=errors,
                    warnings=warnings,
                    metadata={"base_dir": str(base_path), "target_path": str(target)}
                )
            return result

        except Exception as e:
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[str(e)],
                    warnings=[],
                    metadata={"error_type": type(e).__name__}
                )
            raise

    @staticmethod
    def normalize_path(path: Union[str, Path], strict: bool = False) -> Union[str, PathOperationResult]:
        """パスを正規化する"""
        try:
            if path is None:
                error_msg = "Path cannot be None"
                if strict:
                    return PathOperationResult(
                        success=False,
                        result=None,
                        errors=[error_msg],
                        warnings=[],
                        metadata={}
                    )
                raise ValueError(error_msg)

            normalized = os.path.normpath(str(path))

            if strict:
                return PathOperationResult(
                    success=True,
                    result=normalized,
                    errors=[],
                    warnings=[],
                    metadata={"original": str(path)}
                )
            return normalized

        except Exception as e:
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[str(e)],
                    warnings=[],
                    metadata={"error_type": type(e).__name__}
                )
            raise

    @staticmethod
    def safe_path_join(*paths: Union[str, Path], strict: bool = False) -> Union[str, PathOperationResult]:
        """安全にパスを結合する"""
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

            # None チェック
            none_paths = [i for i, p in enumerate(paths) if p is None]
            if none_paths:
                error_msg = f"Path at index {none_paths[0]} is None"
                if strict:
                    return PathOperationResult(
                        success=False,
                        result=None,
                        errors=[error_msg],
                        warnings=[],
                        metadata={"none_indices": none_paths}
                    )
                raise ValueError(error_msg)

            str_paths = [str(p) for p in paths]
            result = os.path.join(*str_paths)
            result = os.path.normpath(result)

            if strict:
                return PathOperationResult(
                    success=True,
                    result=result,
                    errors=[],
                    warnings=[],
                    metadata={"input_paths": str_paths}
                )
            return result

        except Exception as e:
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[str(e)],
                    warnings=[],
                    metadata={"error_type": type(e).__name__}
                )
            raise

    @staticmethod
    def get_relative_path(target: Union[str, Path],
                         base: Union[str, Path],
                         strict: bool = False) -> Union[str, PathOperationResult]:
        """baseからtargetへの相対パスを取得"""
        try:
            target_path = Path(target).resolve()
            base_path = Path(base).resolve()

            relative_path = os.path.relpath(str(target_path), str(base_path))

            if strict:
                return PathOperationResult(
                    success=True,
                    result=relative_path,
                    errors=[],
                    warnings=[],
                    metadata={"target": str(target_path), "base": str(base_path)}
                )
            return relative_path

        except Exception as e:
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[str(e)],
                    warnings=[],
                    metadata={"error_type": type(e).__name__}
                )
            raise

    @staticmethod
    def is_subdirectory(child: Union[str, Path],
                       parent: Union[str, Path],
                       strict: bool = False) -> Union[bool, PathOperationResult]:
        """childがparentのサブディレクトリかどうかチェック"""
        try:
            child_path = Path(child).resolve()
            parent_path = Path(parent).resolve()

            try:
                child_path.relative_to(parent_path)
                result = True
            except ValueError:
                result = False

            if strict:
                return PathOperationResult(
                    success=True,
                    result=result,
                    errors=[],
                    warnings=[],
                    metadata={"child": str(child_path), "parent": str(parent_path)}
                )
            return result

        except Exception as e:
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[str(e)],
                    warnings=[],
                    metadata={"error_type": type(e).__name__}
                )
            raise

    @staticmethod
    def ensure_parent_dir(file_path: Union[str, Path],
                         strict: bool = False) -> Union[str, PathOperationResult]:
        """ファイルの親ディレクトリを作成"""
        try:
            path_obj = Path(file_path)
            parent_dir = path_obj.parent

            if not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)

            result = str(parent_dir)

            if strict:
                return PathOperationResult(
                    success=True,
                    result=result,
                    errors=[],
                    warnings=[],
                    metadata={"file_path": str(path_obj), "created": not parent_dir.exists()}
                )
            return result

        except Exception as e:
            if strict:
                return PathOperationResult(
                    success=False,
                    result=None,
                    errors=[str(e)],
                    warnings=[],
                    metadata={"error_type": type(e).__name__}
                )
            raise
