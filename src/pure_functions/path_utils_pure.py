"""
パス操作の純粋関数実装
副作用なしでテスト容易性を向上
"""
from dataclasses import dataclass
from pathlib import Path
import os
from typing import Optional, List, Union, Tuple, Dict, Any


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
    parts: Tuple[str, ...]
    
    @classmethod
    def from_path(cls, path: Union[str, Path]) -> 'PathInfo':
        """パスからPathInfoを作成"""
        p = Path(path)
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


@dataclass(frozen=True)
class PathResolutionResult:
    """パス解決結果の不変データクラス"""
    resolved_path: str
    is_relative: bool
    resolution_method: str
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])


@dataclass(frozen=True)
class SafePathResult:
    """安全なパス操作結果の不変データクラス"""
    path: Optional[str]
    is_safe: bool
    security_issues: List[str]
    
    def __post_init__(self):
        if self.security_issues is None:
            object.__setattr__(self, 'security_issues', [])


def resolve_path_pure(base_dir: Union[str, Path], path: Union[str, Path]) -> PathResolutionResult:
    """
    ベースディレクトリを基準にパスを解決する純粋関数
    
    Args:
        base_dir: ベースディレクトリ
        path: 対象パス
        
    Returns:
        PathResolutionResult: 解決結果
    """
    try:
        base = Path(base_dir)
        target = Path(path)
        
        if target.is_absolute():
            return PathResolutionResult(
                resolved_path=str(target),
                is_relative=False,
                resolution_method="absolute_path",
                errors=[],
                warnings=[]
            )
        
        resolved = base / target
        return PathResolutionResult(
            resolved_path=str(resolved),
            is_relative=True,
            resolution_method="relative_to_base",
            errors=[],
            warnings=[]
        )
    
    except Exception as e:
        return PathResolutionResult(
            resolved_path=str(path),
            is_relative=True,
            resolution_method="fallback",
            errors=[f"Path resolution failed: {str(e)}"],
            warnings=[]
        )


def normalize_path_pure(path: Union[str, Path]) -> PathResolutionResult:
    """
    パスを正規化する純粋関数
    
    Args:
        path: 対象パス
        
    Returns:
        PathResolutionResult: 正規化結果
    """
    try:
        normalized = Path(path).resolve()
        return PathResolutionResult(
            resolved_path=str(normalized),
            is_relative=not normalized.is_absolute(),
            resolution_method="normalize",
            errors=[],
            warnings=[]
        )
    except Exception as e:
        return PathResolutionResult(
            resolved_path=str(path),
            is_relative=True,
            resolution_method="fallback",
            errors=[f"Path normalization failed: {str(e)}"],
            warnings=[]
        )


def get_relative_path_pure(
    base_dir: Union[str, Path], 
    target_path: Union[str, Path]
) -> PathResolutionResult:
    """
    ベースディレクトリからの相対パスを取得する純粋関数
    
    Args:
        base_dir: ベースディレクトリ
        target_path: 対象パス
        
    Returns:
        PathResolutionResult: 相対パス結果
    """
    try:
        base = Path(base_dir).resolve()
        target = Path(target_path).resolve()
        
        try:
            relative = target.relative_to(base)
            return PathResolutionResult(
                resolved_path=str(relative),
                is_relative=True,
                resolution_method="relative_to",
                errors=[],
                warnings=[]
            )
        except ValueError:
            # relative_toで計算できない場合は絶対パスを返す
            return PathResolutionResult(
                resolved_path=str(target),
                is_relative=False,
                resolution_method="absolute_fallback",
                errors=[],
                warnings=["Could not calculate relative path, returning absolute path"]
            )
    
    except Exception as e:
        return PathResolutionResult(
            resolved_path=str(target_path),
            is_relative=False,
            resolution_method="error_fallback",
            errors=[f"Relative path calculation failed: {str(e)}"],
            warnings=[]
        )


def is_subdirectory_pure(
    parent_dir: Union[str, Path], 
    child_path: Union[str, Path]
) -> Tuple[bool, List[str]]:
    """
    指定されたパスが親ディレクトリのサブディレクトリかどうかを判定する純粋関数
    
    Args:
        parent_dir: 親ディレクトリ
        child_path: 子パス
        
    Returns:
        Tuple[bool, List[str]]: (判定結果, エラーメッセージ)
    """
    try:
        parent = Path(parent_dir).resolve()
        child = Path(child_path).resolve()
        child.relative_to(parent)
        return True, []
    except ValueError:
        return False, []
    except Exception as e:
        return False, [f"Subdirectory check failed: {str(e)}"]


def safe_path_join_pure(*paths: Union[str, Path]) -> SafePathResult:
    """
    安全にパスを結合する純粋関数（パストラバーサル攻撃を防ぐ）
    
    Args:
        *paths: 結合するパス
        
    Returns:
        SafePathResult: 安全性チェック結果
    """
    if not paths:
        return SafePathResult(
            path=None,
            is_safe=False,
            security_issues=["No paths provided"]
        )
    
    security_issues = []
    
    try:
        result = Path(paths[0])
        
        for i, path in enumerate(paths[1:], 1):
            path_part = Path(path)
            
            # セキュリティチェック
            if path_part.is_absolute():
                security_issues.append(f"Path {i} is absolute: {path}")
            
            if '..' in path_part.parts:
                security_issues.append(f"Path {i} contains parent directory reference: {path}")
            
            # 隠ファイルのチェック（オプション）
            if any(part.startswith('.') and part != '.' for part in path_part.parts):
                # 警告レベル（エラーではない）
                pass
            
            result = result / path_part
        
        return SafePathResult(
            path=str(result) if not security_issues else None,
            is_safe=len(security_issues) == 0,
            security_issues=security_issues
        )
    
    except Exception as e:
        return SafePathResult(
            path=None,
            is_safe=False,
            security_issues=[f"Path join failed: {str(e)}"]
        )


def get_file_extension_pure(path: Union[str, Path]) -> str:
    """
    ファイルの拡張子を取得する純粋関数
    
    Args:
        path: ファイルパス
        
    Returns:
        拡張子（ドット付き）
    """
    return Path(path).suffix


def change_extension_pure(
    path: Union[str, Path], 
    new_extension: str
) -> PathResolutionResult:
    """
    ファイルの拡張子を変更する純粋関数
    
    Args:
        path: 元のファイルパス
        new_extension: 新しい拡張子（ドット付きまたはなし）
        
    Returns:
        PathResolutionResult: 拡張子変更結果
    """
    try:
        path_obj = Path(path)
        
        # 拡張子の正規化
        if new_extension and not new_extension.startswith('.'):
            new_extension = '.' + new_extension
        
        result = path_obj.with_suffix(new_extension)
        
        return PathResolutionResult(
            resolved_path=str(result),
            is_relative=not result.is_absolute(),
            resolution_method="extension_change",
            errors=[],
            warnings=[]
        )
    
    except Exception as e:
        return PathResolutionResult(
            resolved_path=str(path),
            is_relative=True,
            resolution_method="fallback",
            errors=[f"Extension change failed: {str(e)}"],
            warnings=[]
        )


def analyze_path_structure_pure(path: Union[str, Path]) -> Dict[str, Any]:
    """
    パス構造を分析する純粋関数
    
    Args:
        path: 分析対象のパス
        
    Returns:
        パス構造の分析結果
    """
    try:
        p = Path(path)
        
        return {
            "original_path": str(path),
            "normalized_path": str(p),
            "is_absolute": p.is_absolute(),
            "parent": str(p.parent),
            "name": p.name,
            "stem": p.stem,
            "suffix": p.suffix,
            "suffixes": p.suffixes,
            "parts": p.parts,
            "part_count": len(p.parts),
            "has_extension": bool(p.suffix),
            "is_hidden": p.name.startswith('.') if p.name else False,
            "depth": len(p.parts) - 1 if p.is_absolute() else len(p.parts)
        }
    
    except Exception as e:
        return {
            "original_path": str(path),
            "error": f"Path analysis failed: {str(e)}",
            "is_absolute": False,
            "parts": (),
            "part_count": 0,
            "has_extension": False,
            "is_hidden": False,
            "depth": 0
        }


def find_common_parent_pure(paths: List[Union[str, Path]]) -> Optional[str]:
    """
    複数のパスの共通の親ディレクトリを見つける純粋関数
    
    Args:
        paths: パスのリスト
        
    Returns:
        共通の親ディレクトリ、または見つからない場合はNone
    """
    if not paths:
        return None
    
    if len(paths) == 1:
        return str(Path(paths[0]).parent)
    
    try:
        resolved_paths = [Path(p).resolve() for p in paths]
        
        # 最初のパスの親ディレクトリから開始
        common_parts = resolved_paths[0].parts
        
        # 他のパスと共通部分を見つける
        for path in resolved_paths[1:]:
            path_parts = path.parts
            
            # 共通の先頭部分を見つける
            common_length = 0
            for i, (part1, part2) in enumerate(zip(common_parts, path_parts)):
                if part1 == part2:
                    common_length = i + 1
                else:
                    break
            
            common_parts = common_parts[:common_length]
            
            if not common_parts:
                return None
        
        if common_parts:
            return str(Path(*common_parts))
        else:
            return None
    
    except Exception:
        return None


def validate_path_security_pure(path: Union[str, Path]) -> Dict[str, Any]:
    """
    パスのセキュリティを検証する純粋関数
    
    Args:
        path: 検証対象のパス
        
    Returns:
        セキュリティ検証結果
    """
    p = Path(path)
    issues = []
    warnings = []
    
    # パストラバーサルチェック
    if '..' in p.parts:
        issues.append("Contains parent directory traversal (..)") 
    
    # 絶対パスチェック（コンテキストによる）
    if p.is_absolute():
        warnings.append("Uses absolute path")
    
    # 隠しファイル/ディレクトリチェック
    hidden_parts = [part for part in p.parts if part.startswith('.') and part not in ('.', '..')]
    if hidden_parts:
        warnings.append(f"Contains hidden components: {hidden_parts}")
    
    # 長すぎるパス名チェック
    if len(str(p)) > 255:
        warnings.append("Path length exceeds typical filesystem limits")
    
    # 特殊文字チェック
    suspicious_chars = ['<', '>', ':', '"', '|', '?', '*']
    found_chars = [char for char in suspicious_chars if char in str(p)]
    if found_chars:
        issues.append(f"Contains suspicious characters: {found_chars}")
    
    return {
        "path": str(path),
        "is_secure": len(issues) == 0,
        "security_issues": issues,
        "warnings": warnings,
        "risk_level": "high" if issues else "low" if warnings else "none"
    }


def generate_path_variations_pure(
    base_path: Union[str, Path], 
    variations: List[str]
) -> Dict[str, str]:
    """
    ベースパスから複数のバリエーションを生成する純粋関数
    
    Args:
        base_path: ベースパス
        variations: バリエーション名のリスト
        
    Returns:
        バリエーション名 -> パスのマッピング
    """
    base = Path(base_path)
    result = {}
    
    for variation in variations:
        try:
            if variation == "parent":
                result[variation] = str(base.parent)
            elif variation == "with_timestamp":
                # タイムスタンプの代わりに固定サフィックスを使用（純粋関数のため）
                result[variation] = str(base.with_suffix(f"{base.suffix}.bak"))
            elif variation == "without_extension":
                result[variation] = str(base.with_suffix(""))
            elif variation == "absolute":
                result[variation] = str(base.resolve())
            elif variation == "name_only":
                result[variation] = base.name
            elif variation == "stem_only":
                result[variation] = base.stem
            else:
                # カスタムサフィックスとして扱う
                result[variation] = str(base.with_suffix(f".{variation}"))
        except Exception:
            result[variation] = str(base_path)  # フォールバック
    
    return result


def calculate_path_metrics_pure(paths: List[Union[str, Path]]) -> Dict[str, Any]:
    """
    パスリストのメトリクスを計算する純粋関数
    
    Args:
        paths: パスのリスト
        
    Returns:
        メトリクス辞書
    """
    if not paths:
        return {
            "total_paths": 0,
            "absolute_paths": 0,
            "relative_paths": 0,
            "avg_depth": 0,
            "max_depth": 0,
            "min_depth": 0,
            "extensions": {},
            "common_parent": None
        }
    
    absolute_count = 0
    relative_count = 0
    depths = []
    extensions = {}
    
    for path in paths:
        try:
            p = Path(path)
            
            if p.is_absolute():
                absolute_count += 1
            else:
                relative_count += 1
            
            depth = len(p.parts) - (1 if p.is_absolute() else 0)
            depths.append(depth)
            
            if p.suffix:
                extensions[p.suffix] = extensions.get(p.suffix, 0) + 1
        
        except Exception:
            relative_count += 1
            depths.append(0)
    
    common_parent = find_common_parent_pure(paths)
    
    return {
        "total_paths": len(paths),
        "absolute_paths": absolute_count,
        "relative_paths": relative_count,
        "avg_depth": sum(depths) / len(depths) if depths else 0,
        "max_depth": max(depths) if depths else 0,
        "min_depth": min(depths) if depths else 0,
        "extensions": extensions,
        "common_parent": common_parent
    }