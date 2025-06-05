"""
Validation service for configuration data
"""
from typing import Dict, Any


class ValidationService:
    """設定データのバリデーションを担当"""
    
    @staticmethod
    def validate_env_json(data: Dict[str, Any], path: str, shared_config=None):
        """
        env.jsonの構造をバリデートする
        
        Args:
            data: バリデートするデータ
            path: ファイルパス（エラーメッセージ用）
            shared_config: 共有設定（sharedフォルダの設定）
            
        Raises:
            ValueError: バリデーション失敗時
        """
        if not isinstance(data, dict):
            raise ValueError(f"{path}: env.jsonのトップレベルはdictである必要があります")
        
        for lang, conf in data.items():
            if not isinstance(conf, dict):
                raise ValueError(f"{path}: {lang}の値はdictである必要があります")
            
            # commandsのバリデーション（sharedに存在するかもチェック）
            has_commands = "commands" in conf and isinstance(conf["commands"], dict)
            has_shared_commands = (shared_config and 
                                  "shared" in shared_config and 
                                  "commands" in shared_config["shared"])
            
            if not has_commands and not has_shared_commands:
                raise ValueError(f"{path}: {lang}にcommands(dict)がありません")
            
            # env_typesのバリデーション（sharedに存在するかもチェック）
            has_env_types = "env_types" in conf and isinstance(conf["env_types"], dict)
            has_shared_env_types = (shared_config and 
                                   "shared" in shared_config and 
                                   ("env_types" in shared_config["shared"] or 
                                    "local" in shared_config["shared"]))
            
            if not has_env_types and not has_shared_env_types:
                raise ValueError(f"{path}: {lang}にenv_types(dict)がありません")
            
            if "aliases" in conf and not isinstance(conf["aliases"], list):
                raise ValueError(f"{path}: {lang}のaliasesはlistである必要があります")
            
            # Debug configuration validation
            if "debug" in conf:
                ValidationService._validate_debug_config(conf["debug"], path, lang)
    
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
    
    @staticmethod
    def _validate_debug_config(debug_config: Dict[str, Any], path: str, lang: str):
        """
        デバッグ設定のバリデーション
        
        Args:
            debug_config: デバッグ設定
            path: ファイルパス（エラーメッセージ用）
            lang: 言語名（エラーメッセージ用）
            
        Raises:
            ValueError: バリデーション失敗時
        """
        if not isinstance(debug_config, dict):
            raise ValueError(f"{path}: {lang}のdebugはdictである必要があります")
        
        # enabled field validation
        if "enabled" in debug_config and not isinstance(debug_config["enabled"], bool):
            raise ValueError(f"{path}: {lang}.debug.enabledはboolである必要があります")
        
        # level field validation
        if "level" in debug_config:
            valid_levels = ["none", "minimal", "detailed"]
            if debug_config["level"] not in valid_levels:
                raise ValueError(f"{path}: {lang}.debug.levelは{valid_levels}のいずれかである必要があります")
        
        # format field validation
        if "format" in debug_config:
            format_config = debug_config["format"]
            if not isinstance(format_config, dict):
                raise ValueError(f"{path}: {lang}.debug.formatはdictである必要があります")
            
            # icons field validation
            if "icons" in format_config and not isinstance(format_config["icons"], dict):
                raise ValueError(f"{path}: {lang}.debug.format.iconsはdictである必要があります")