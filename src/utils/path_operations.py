"""Core path operations for file and directory manipulation.
Main PathOperations class extracted from the original large file.
"""
import os
from pathlib import Path
from typing import Union

# 互換性維持: configuration層への逆方向依存を削除、依存性注入で解決
from src.core.types.path_types import PathOperationResult


class PathOperations:
    """統合されたパス操作クラス

    シンプルなAPI（例外ベース）と詳細なAPI（結果型ベース）の両方を提供
    """

    def __init__(self, config_provider):
        """Initialize PathOperations with configuration provider."""
        self.config_provider = config_provider

    def _get_default_workspace_path(self) -> str:
        """設定からデフォルトワークスペースパスを取得"""
        if self.config_provider is None:
            raise ValueError("Configuration provider is not injected")

        try:
            return self.config_provider.resolve_config(
                ['filesystem_config', 'default_paths', 'workspace'],
                str
            )
        except KeyError as e:
            raise ValueError("No default workspace path configured") from e

    def resolve_path(self, base_dir: Union[str, Path],
                    target_path: Union[str, Path],
                    strict: bool) -> Union[str, PathOperationResult]:
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
                    # Build metadata without conditional expressions
                    base_dir_str = "None"
                    if base_dir is not None:
                        base_dir_str = str(base_dir)
                    target_path_str = "None"
                    if target_path is not None:
                        target_path_str = str(target_path)

                    return PathOperationResult(
                        success=False,
                        result=None,
                        errors=errors,
                        warnings=warnings,
                        metadata={
                            "base_dir": base_dir_str,
                            "target_path": target_path_str
                        }
                    )
                raise ValueError(errors[0])

            base_path = Path(base_dir).resolve()
            target = Path(target_path)

            if target.is_absolute():
                resolved_path = target.resolve()
                resolution_method = "absolute"
            else:
                resolved_path = (base_path / target).resolve()
                resolution_method = "relative"

            result = str(resolved_path)

            if strict:
                return PathOperationResult(
                    success=True,
                    result=result,
                    errors=errors,
                    warnings=warnings,
                    metadata={"base_dir": str(base_path), "target_path": str(target), "resolution_method": resolution_method}
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

    def normalize_path(self, path: Union[str, Path], strict: bool) -> Union[str, PathOperationResult]:
        """パスを正規化する"""
        try:
            if path is None:
                raise ValueError("Path parameter cannot be None")

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

    def safe_path_join(self, *paths: Union[str, Path], strict: bool) -> Union[str, PathOperationResult]:
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

            # Check for potentially unsafe paths
            warnings = []
            for path in str_paths:
                if ".." in path:
                    warnings.append(f"Potentially unsafe path component: {path}")

            if strict:
                return PathOperationResult(
                    success=True,
                    result=result,
                    errors=[],
                    warnings=warnings,
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

    def get_relative_path(self, target: Union[str, Path],
                         base: Union[str, Path],
                         strict: bool) -> Union[str, PathOperationResult]:
        """baseからtargetへの相対パスを取得"""
        try:
            target_path = Path(target).resolve()
            base_path = Path(base).resolve()

            # Check if target is actually relative to base
            try:
                target_path.relative_to(base_path)
            except ValueError as err:
                error_msg = f"Cannot compute relative path: {target} is not relative to {base}"
                if strict:
                    return PathOperationResult(
                        success=False,
                        result=None,
                        errors=[error_msg],
                        warnings=[],
                        metadata={"target": str(target_path), "base": str(base_path)}
                    )
                raise ValueError(error_msg) from err

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

    def is_subdirectory(self, child: Union[str, Path],
                       parent: Union[str, Path],
                       strict: bool) -> Union[bool, tuple]:
        """childがparentのサブディレクトリかどうかチェック"""
        try:
            child_path = Path(child).resolve()
            parent_path = Path(parent).resolve()

            try:
                child_path.relative_to(parent_path)
                result = True
            except ValueError:
                # Not a subdirectory - this is expected behavior when paths are not related
                # The ValueError is not being hidden - it's used as control flow for this specific check
                # 互換性維持: Path.relative_to()のValueErrorは仕様上の正常な動作
                result = False

            if strict:
                operation_result = PathOperationResult(
                    success=True,
                    result=result,
                    errors=[],
                    warnings=[],
                    metadata={"child": str(child_path), "parent": str(parent_path), "is_subdirectory": result}
                )
                return result, operation_result
            return result

        except Exception as e:
            if strict:
                operation_result = PathOperationResult(
                    success=False,
                    result=None,
                    errors=[str(e)],
                    warnings=[],
                    metadata={"error_type": type(e).__name__}
                )
                return False, operation_result
            raise

    def ensure_parent_dir(self, file_path: Union[str, Path],
                         strict: bool) -> Union[str, PathOperationResult]:
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

    def get_file_extension(self, file_path: Union[str, Path],
                          strict: bool) -> Union[str, PathOperationResult]:
        """ファイルの拡張子を取得"""
        try:
            path_obj = Path(file_path)
            extension = path_obj.suffix

            if strict:
                return PathOperationResult(
                    success=True,
                    result=extension,
                    errors=[],
                    warnings=[],
                    metadata={"stem": path_obj.stem, "name": path_obj.name}
                )
            return extension

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

    def change_extension(self, file_path: Union[str, Path],
                        new_extension: str,
                        strict: bool) -> Union[str, PathOperationResult]:
        """ファイルの拡張子を変更"""
        try:
            path_obj = Path(file_path)
            original_extension = path_obj.suffix

            # Ensure new_extension starts with . if it's not empty
            if new_extension and not new_extension.startswith('.'):
                new_extension = '.' + new_extension

            # Create new path by replacing the suffix
            if not original_extension:
                raise ValueError(f"File '{file_path}' has no extension to replace")
            new_path = str(path_obj).replace(original_extension, new_extension)

            if strict:
                return PathOperationResult(
                    success=True,
                    result=new_path,
                    errors=[],
                    warnings=[],
                    metadata={
                        "original_extension": original_extension,
                        "new_extension": new_extension,
                        "original_path": str(path_obj)
                    }
                )
            return new_path

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
