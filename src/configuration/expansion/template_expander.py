"""変数展開の一元化 - 32個の関数を統合"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.execution_configuration import ExecutionConfiguration


class TemplateExpander:
    """変数展開の一元化 - 32個の関数を統合"""
    
    def __init__(self, config: ExecutionConfiguration):
        self.config = config
        self._template_dict = config.to_template_dict()
    
    def expand_basic_variables(self, template: str) -> str:
        """基本変数（{contest_name}, {language}等）の展開
        
        Args:
            template: 変数を含むテンプレート文字列
            
        Returns:
            基本変数が展開された文字列
        """
        result = template
        for key, value in self._template_dict.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
    
    def expand_file_patterns(self, template: str, operation_type: Optional[str] = None) -> str:
        """ファイルパターン（{test_files}, {contest_files}等）の展開
        
        Args:
            template: 変数を含むテンプレート文字列
            operation_type: 操作タイプ（movetree, copytree等）
            
        Returns:
            ファイルパターンが展開された文字列
        """
        result = template
        for pattern_name, patterns in self.config.file_patterns.items():
            placeholder = f"{{{pattern_name}}}"
            if placeholder in result:
                expanded = self._expand_single_pattern(patterns, operation_type)
                result = result.replace(placeholder, expanded)
        return result
    
    def expand_all(self, template: str, operation_type: Optional[str] = None) -> str:
        """統一的な変数展開エントリーポイント
        
        Args:
            template: 変数を含むテンプレート文字列
            operation_type: 操作タイプ（ファイルパターン展開時に使用）
            
        Returns:
            すべての変数が展開された文字列
        """
        # 1. 基本変数を展開
        result = self.expand_basic_variables(template)
        # 2. ファイルパターンを展開
        result = self.expand_file_patterns(result, operation_type)
        return result
    
    def expand_command(self, cmd: List[str], operation_type: Optional[str] = None) -> List[str]:
        """コマンドリストの変数展開
        
        Args:
            cmd: コマンド引数のリスト
            operation_type: 操作タイプ
            
        Returns:
            変数が展開されたコマンドリスト
        """
        return [self.expand_all(arg, operation_type) for arg in cmd]
    
    def _expand_single_pattern(self, patterns: List[str], operation_type: Optional[str]) -> str:
        """単一ファイルパターンの展開ロジック
        
        Args:
            patterns: パターンのリスト
            operation_type: 操作タイプ
            
        Returns:
            展開されたパターン文字列
        """
        if not patterns:
            return ""
        
        # MOVETREEやCOPYTREEの場合はディレクトリ部分のみ
        if operation_type in ["movetree", "copytree"]:
            first_pattern = patterns[0]
            return str(Path(first_pattern).parent) if "/" in first_pattern else first_pattern
        
        # その他の場合は最初のパターンをそのまま使用
        return patterns[0]
    
    def extract_template_keys(self, template: str) -> List[str]:
        """テンプレート内のキーを抽出
        
        Args:
            template: テンプレート文字列
            
        Returns:
            抽出されたキーのリスト
        """
        # {key}パターンを検索
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, template)
        return list(set(matches))  # 重複を除去
    
    def validate_template(self, template: str) -> tuple[bool, List[str]]:
        """テンプレート内の未解決キーを検出
        
        Args:
            template: テンプレート文字列
            
        Returns:
            (is_valid, unresolved_keys): 検証結果とエラーキーのリスト
        """
        keys = self.extract_template_keys(template)
        unresolved_keys = []
        
        for key in keys:
            # 基本変数辞書をチェック
            if key not in self._template_dict:
                # ファイルパターンをチェック
                if key not in self.config.file_patterns:
                    unresolved_keys.append(key)
        
        return len(unresolved_keys) == 0, unresolved_keys


class TemplateValidator:
    """テンプレート検証の統一化"""
    
    @staticmethod
    def validate_template(template: str, config: ExecutionConfiguration) -> tuple[bool, List[str]]:
        """テンプレート内の未解決キーを検出
        
        Args:
            template: テンプレート文字列
            config: 実行設定
            
        Returns:
            (is_valid, unresolved_keys): 検証結果とエラーキーのリスト
        """
        expander = TemplateExpander(config)
        return expander.validate_template(template)
    
    @staticmethod
    def extract_template_keys(template: str) -> List[str]:
        """テンプレート内のキーを抽出
        
        Args:
            template: テンプレート文字列
            
        Returns:
            抽出されたキーのリスト
        """
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, template)
        return list(set(matches))