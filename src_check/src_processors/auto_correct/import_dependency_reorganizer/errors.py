"""
カスタムエラークラスとエラーハンドリング
依存関係整理ツール用の詳細なエラー報告機能
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

class ReorganizerError(Exception):
    """依存関係整理ツールの基底エラークラス"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """エラー情報を辞書形式で返す"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }

class CircularDependencyError(ReorganizerError):
    """循環依存が検出された場合のエラー"""
    
    def __init__(self, cycles: List[List[str]]):
        self.cycles = cycles
        cycle_strs = []
        for cycle in cycles[:3]:  # 最初の3つだけ表示
            cycle_strs.append(" → ".join(cycle))
        
        message = f"循環依存が検出されました ({len(cycles)}個):\n" + "\n".join(cycle_strs)
        details = {
            "cycle_count": len(cycles),
            "cycles": cycles,
            "first_cycle": cycles[0] if cycles else []
        }
        super().__init__(message, details)

class ImportAnalysisError(ReorganizerError):
    """インポート解析中のエラー"""
    
    def __init__(self, file_path: Path, original_error: Exception):
        self.file_path = file_path
        self.original_error = original_error
        
        message = f"インポート解析エラー: {file_path}\n原因: {str(original_error)}"
        details = {
            "file_path": str(file_path),
            "error_type": type(original_error).__name__,
            "error_message": str(original_error)
        }
        super().__init__(message, details)

class ImportUpdateError(ReorganizerError):
    """インポート更新中のエラー"""
    
    def __init__(self, file_path: Path, reason: str, line_number: Optional[int] = None):
        self.file_path = file_path
        self.reason = reason
        self.line_number = line_number
        
        message = f"インポート更新エラー: {file_path}"
        if line_number:
            message += f" (行{line_number})"
        message += f"\n理由: {reason}"
        
        details = {
            "file_path": str(file_path),
            "reason": reason,
            "line_number": line_number
        }
        super().__init__(message, details)

class FileMoveError(ReorganizerError):
    """ファイル移動中のエラー"""
    
    def __init__(self, source: Path, destination: Path, reason: str):
        self.source = source
        self.destination = destination
        self.reason = reason
        
        message = f"ファイル移動エラー:\n  {source} → {destination}\n  理由: {reason}"
        details = {
            "source": str(source),
            "destination": str(destination),
            "reason": reason
        }
        super().__init__(message, details)

class ValidationError(ReorganizerError):
    """検証エラー"""
    
    def __init__(self, validation_type: str, failures: List[Dict[str, Any]]):
        self.validation_type = validation_type
        self.failures = failures
        
        message = f"{validation_type}検証エラー: {len(failures)}件の問題"
        details = {
            "validation_type": validation_type,
            "failure_count": len(failures),
            "failures": failures[:10]  # 最初の10件のみ
        }
        super().__init__(message, details)

class ConfigurationError(ReorganizerError):
    """設定エラー"""
    
    def __init__(self, config_key: str, reason: str):
        self.config_key = config_key
        self.reason = reason
        
        message = f"設定エラー: {config_key}\n理由: {reason}"
        details = {
            "config_key": config_key,
            "reason": reason
        }
        super().__init__(message, details)

class ErrorCollector:
    """エラー収集とレポート生成"""
    
    def __init__(self):
        self.errors: List[ReorganizerError] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def add_error(self, error: ReorganizerError) -> None:
        """エラーを追加"""
        self.errors.append(error)
    
    def add_warning(self, category: str, message: str, details: Optional[Dict] = None) -> None:
        """警告を追加"""
        self.warnings.append({
            "category": category,
            "message": message,
            "details": details or {}
        })
    
    def has_errors(self) -> bool:
        """エラーが存在するか"""
        return len(self.errors) > 0
    
    def has_critical_errors(self) -> bool:
        """クリティカルなエラーが存在するか"""
        critical_types = [CircularDependencyError, ConfigurationError]
        return any(isinstance(error, tuple(critical_types)) for error in self.errors)
    
    def get_summary(self) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        error_types = {}
        for error in self.errors:
            error_type = type(error).__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "error_types": error_types,
            "has_critical_errors": self.has_critical_errors(),
            "errors": [error.to_dict() for error in self.errors[:10]],  # 最初の10件
            "warnings": self.warnings[:10]  # 最初の10件
        }
    
    def format_report(self) -> str:
        """人間が読めるレポートを生成"""
        lines = ["=== エラーレポート ==="]
        
        if not self.errors and not self.warnings:
            lines.append("エラーや警告はありません。")
            return "\n".join(lines)
        
        # エラーセクション
        if self.errors:
            lines.append(f"\n## エラー ({len(self.errors)}件)")
            
            # タイプ別にグループ化
            error_groups = {}
            for error in self.errors:
                error_type = type(error).__name__
                if error_type not in error_groups:
                    error_groups[error_type] = []
                error_groups[error_type].append(error)
            
            for error_type, errors in error_groups.items():
                lines.append(f"\n### {error_type} ({len(errors)}件)")
                for i, error in enumerate(errors[:5], 1):  # 各タイプ最大5件
                    lines.append(f"{i}. {error.message}")
                    if len(errors) > 5:
                        lines.append(f"   ... 他 {len(errors) - 5}件")
        
        # 警告セクション
        if self.warnings:
            lines.append(f"\n## 警告 ({len(self.warnings)}件)")
            
            # カテゴリ別にグループ化
            warning_groups = {}
            for warning in self.warnings:
                category = warning["category"]
                if category not in warning_groups:
                    warning_groups[category] = []
                warning_groups[category].append(warning)
            
            for category, warnings in warning_groups.items():
                lines.append(f"\n### {category} ({len(warnings)}件)")
                for i, warning in enumerate(warnings[:5], 1):
                    lines.append(f"{i}. {warning['message']}")
                if len(warnings) > 5:
                    lines.append(f"   ... 他 {len(warnings) - 5}件")
        
        return "\n".join(lines)