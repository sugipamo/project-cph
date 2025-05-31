"""
Validation service for configuration data
"""
from typing import Dict, Any


class ValidationService:
    """設定データのバリデーションを担当"""
    
    @staticmethod
    def validate_env_json(data: Dict[str, Any], path: str):
        """
        env.jsonの構造をバリデートする
        
        Args:
            data: バリデートするデータ
            path: ファイルパス（エラーメッセージ用）
            
        Raises:
            ValueError: バリデーション失敗時
        """
        if not isinstance(data, dict):
            raise ValueError(f"{path}: env.jsonのトップレベルはdictである必要があります")
        
        for lang, conf in data.items():
            if not isinstance(conf, dict):
                raise ValueError(f"{path}: {lang}の値はdictである必要があります")
            
            if "commands" not in conf or not isinstance(conf["commands"], dict):
                raise ValueError(f"{path}: {lang}にcommands(dict)がありません")
            
            if "env_types" not in conf or not isinstance(conf["env_types"], dict):
                raise ValueError(f"{path}: {lang}にenv_types(dict)がありません")
            
            if "aliases" in conf and not isinstance(conf["aliases"], list):
                raise ValueError(f"{path}: {lang}のaliasesはlistである必要があります")
    
    @staticmethod
    def validate_execution_context(context):
        """
        実行コンテキストのバリデーション
        
        Args:
            context: バリデートする実行コンテキスト
            
        Raises:
            ValueError: バリデーション失敗時
        """
        if not context.language:
            raise ValueError("言語が指定されていません")
        
        if not context.env_json:
            raise ValueError("環境設定が見つかりません")
        
        if context.language not in context.env_json:
            raise ValueError(f"言語 '{context.language}' の設定が見つかりません")