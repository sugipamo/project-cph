"""
設定データバリデーションの純粋関数実装
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union, Set


@dataclass(frozen=True)
class ValidationResult:
    """バリデーション結果の不変データクラス"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])


@dataclass(frozen=True)
class DebugConfig:
    """デバッグ設定の不変データクラス"""
    enabled: Optional[bool] = None
    level: Optional[str] = None
    format_config: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DebugConfig':
        """辞書からDebugConfigを作成"""
        return cls(
            enabled=data.get("enabled"),
            level=data.get("level"),
            format_config=data.get("format")
        )


@dataclass(frozen=True)
class LanguageConfig:
    """言語設定の不変データクラス"""
    commands: Dict[str, Any]
    env_types: Dict[str, Any]
    aliases: Optional[List[str]] = None
    debug: Optional[DebugConfig] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LanguageConfig':
        """辞書からLanguageConfigを作成"""
        debug_data = data.get("debug")
        debug_config = DebugConfig.from_dict(debug_data) if debug_data else None
        
        return cls(
            commands=data.get("commands", {}),
            env_types=data.get("env_types", {}),
            aliases=data.get("aliases"),
            debug=debug_config
        )


@dataclass(frozen=True)
class EnvJsonConfig:
    """env.json設定の不変データクラス"""
    languages: Dict[str, LanguageConfig]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvJsonConfig':
        """辞書からEnvJsonConfigを作成"""
        languages = {}
        for lang, config in data.items():
            if isinstance(config, dict):
                languages[lang] = LanguageConfig.from_dict(config)
        
        return cls(languages=languages)


@dataclass(frozen=True)
class ExecutionContextData:
    """実行コンテキストデータの不変データクラス"""
    language: Optional[str] = None
    env_json: Optional[Dict[str, Any]] = None
    command_type: Optional[str] = None
    contest_name: Optional[str] = None
    problem_name: Optional[str] = None
    env_type: Optional[str] = None


def validate_env_json_pure(data: Dict[str, Any], path: str = "env.json") -> ValidationResult:
    """
    env.jsonの構造をバリデートする純粋関数
    
    Args:
        data: バリデートするデータ
        path: ファイルパス（エラーメッセージ用）
        
    Returns:
        ValidationResult: バリデーション結果
    """
    errors = []
    warnings = []
    
    if not isinstance(data, dict):
        errors.append(f"{path}: env.jsonのトップレベルはdictである必要があります")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    
    if not data:
        warnings.append(f"{path}: env.jsonが空です")
        return ValidationResult(is_valid=True, errors=errors, warnings=warnings)
    
    for lang, conf in data.items():
        lang_errors = validate_language_config_pure(conf, path, lang)
        errors.extend(lang_errors)
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_language_config_pure(
    config: Any, 
    path: str, 
    lang: str
) -> List[str]:
    """
    言語設定をバリデートする純粋関数
    
    Args:
        config: 言語設定
        path: ファイルパス（エラーメッセージ用）
        lang: 言語名
        
    Returns:
        エラーメッセージのリスト
    """
    errors = []
    
    if not isinstance(config, dict):
        errors.append(f"{path}: {lang}の値はdictである必要があります")
        return errors
    
    # commands の検証
    if "commands" not in config:
        errors.append(f"{path}: {lang}にcommands(dict)がありません")
    elif not isinstance(config["commands"], dict):
        errors.append(f"{path}: {lang}のcommandsはdictである必要があります")
    else:
        # コマンドの内容検証
        commands_errors = validate_commands_pure(config["commands"], path, lang)
        errors.extend(commands_errors)
    
    # env_types の検証
    if "env_types" not in config:
        errors.append(f"{path}: {lang}にenv_types(dict)がありません")
    elif not isinstance(config["env_types"], dict):
        errors.append(f"{path}: {lang}のenv_typesはdictである必要があります")
    else:
        # env_typesの内容検証
        env_types_errors = validate_env_types_pure(config["env_types"], path, lang)
        errors.extend(env_types_errors)
    
    # aliases の検証（オプション）
    if "aliases" in config and not isinstance(config["aliases"], list):
        errors.append(f"{path}: {lang}のaliasesはlistである必要があります")
    
    # debug の検証（オプション）
    if "debug" in config:
        debug_errors = validate_debug_config_pure(config["debug"], path, lang)
        errors.extend(debug_errors)
    
    return errors


def validate_commands_pure(
    commands: Dict[str, Any], 
    path: str, 
    lang: str
) -> List[str]:
    """
    コマンド設定をバリデートする純粋関数
    
    Args:
        commands: コマンド設定
        path: ファイルパス
        lang: 言語名
        
    Returns:
        エラーメッセージのリスト
    """
    errors = []
    
    if not commands:
        errors.append(f"{path}: {lang}.commandsが空です")
        return errors
    
    required_commands = {"build", "test"}
    missing_commands = required_commands - set(commands.keys())
    
    if missing_commands:
        errors.append(f"{path}: {lang}.commandsに必要なコマンドがありません: {missing_commands}")
    
    # 各コマンドの内容検証
    for cmd_name, cmd_config in commands.items():
        if not isinstance(cmd_config, dict):
            errors.append(f"{path}: {lang}.commands.{cmd_name}はdictである必要があります")
            continue
        
        if "steps" not in cmd_config:
            errors.append(f"{path}: {lang}.commands.{cmd_name}にstepsがありません")
        elif not isinstance(cmd_config["steps"], list):
            errors.append(f"{path}: {lang}.commands.{cmd_name}.stepsはlistである必要があります")
    
    return errors


def validate_env_types_pure(
    env_types: Dict[str, Any], 
    path: str, 
    lang: str
) -> List[str]:
    """
    環境タイプ設定をバリデートする純粋関数
    
    Args:
        env_types: 環境タイプ設定
        path: ファイルパス
        lang: 言語名
        
    Returns:
        エラーメッセージのリスト
    """
    errors = []
    
    if not env_types:
        errors.append(f"{path}: {lang}.env_typesが空です")
        return errors
    
    required_env_types = {"local", "docker"}
    missing_env_types = required_env_types - set(env_types.keys())
    
    if missing_env_types:
        errors.append(f"{path}: {lang}.env_typesに必要な環境タイプがありません: {missing_env_types}")
    
    # 各環境タイプの内容検証
    for env_type, env_config in env_types.items():
        if not isinstance(env_config, dict):
            errors.append(f"{path}: {lang}.env_types.{env_type}はdictである必要があります")
    
    return errors


def validate_debug_config_pure(
    debug_config: Any, 
    path: str, 
    lang: str
) -> List[str]:
    """
    デバッグ設定をバリデートする純粋関数
    
    Args:
        debug_config: デバッグ設定
        path: ファイルパス
        lang: 言語名
        
    Returns:
        エラーメッセージのリスト
    """
    errors = []
    
    if not isinstance(debug_config, dict):
        errors.append(f"{path}: {lang}のdebugはdictである必要があります")
        return errors
    
    # enabled field validation
    if "enabled" in debug_config and not isinstance(debug_config["enabled"], bool):
        errors.append(f"{path}: {lang}.debug.enabledはboolである必要があります")
    
    # level field validation
    if "level" in debug_config:
        valid_levels = {"none", "minimal", "detailed"}
        if debug_config["level"] not in valid_levels:
            errors.append(f"{path}: {lang}.debug.levelは{valid_levels}のいずれかである必要があります")
    
    # format field validation
    if "format" in debug_config:
        format_errors = validate_debug_format_pure(debug_config["format"], path, lang)
        errors.extend(format_errors)
    
    return errors


def validate_debug_format_pure(
    format_config: Any, 
    path: str, 
    lang: str
) -> List[str]:
    """
    デバッグフォーマット設定をバリデートする純粋関数
    
    Args:
        format_config: フォーマット設定
        path: ファイルパス
        lang: 言語名
        
    Returns:
        エラーメッセージのリスト
    """
    errors = []
    
    if not isinstance(format_config, dict):
        errors.append(f"{path}: {lang}.debug.formatはdictである必要があります")
        return errors
    
    # icons field validation
    if "icons" in format_config and not isinstance(format_config["icons"], dict):
        errors.append(f"{path}: {lang}.debug.format.iconsはdictである必要があります")
    
    # timestamp field validation
    if "timestamp" in format_config and not isinstance(format_config["timestamp"], bool):
        errors.append(f"{path}: {lang}.debug.format.timestampはboolである必要があります")
    
    # colors field validation
    if "colors" in format_config and not isinstance(format_config["colors"], dict):
        errors.append(f"{path}: {lang}.debug.format.colorsはdictである必要があります")
    
    return errors


def validate_execution_context_pure(context: ExecutionContextData) -> ValidationResult:
    """
    実行コンテキストをバリデートする純粋関数
    
    Args:
        context: バリデートする実行コンテキスト
        
    Returns:
        ValidationResult: バリデーション結果
    """
    errors = []
    warnings = []
    
    # 言語の検証
    if not context.language:
        errors.append("言語が指定されていません")
    elif not isinstance(context.language, str):
        errors.append("言語は文字列である必要があります")
    
    # env_jsonの検証
    if not context.env_json:
        errors.append("環境設定が見つかりません")
    elif not isinstance(context.env_json, dict):
        errors.append("環境設定は辞書である必要があります")
    elif context.language and context.language not in context.env_json:
        errors.append(f"言語 '{context.language}' の設定が見つかりません")
    
    # 環境タイプの検証
    if context.env_type:
        valid_env_types = {"local", "docker", "wsl"}
        if context.env_type not in valid_env_types:
            warnings.append(f"環境タイプ '{context.env_type}' は推奨されていません。推奨: {valid_env_types}")
    
    # コマンドタイプの検証
    if context.command_type and context.env_json and context.language:
        lang_config = context.env_json.get(context.language, {})
        commands = lang_config.get("commands", {})
        if context.command_type not in commands:
            warnings.append(f"コマンドタイプ '{context.command_type}' が言語設定に見つかりません")
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_step_data_pure(step_data: Any) -> ValidationResult:
    """
    ステップデータをバリデートする純粋関数
    
    Args:
        step_data: ステップデータ
        
    Returns:
        ValidationResult: バリデーション結果
    """
    errors = []
    warnings = []
    
    if not isinstance(step_data, dict):
        errors.append("ステップデータは辞書である必要があります")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    
    # type の検証
    if "type" not in step_data:
        errors.append("ステップにtypeが指定されていません")
    else:
        valid_types = {
            "shell", "python", "copy", "move", "mkdir", "touch", 
            "remove", "rmtree", "movetree", "build", "test", 
            "docker_run", "docker_exec", "docker_cp", "oj"
        }
        if step_data["type"] not in valid_types:
            warnings.append(f"ステップタイプ '{step_data['type']}' は認識されていません")
    
    # cmd の検証
    if "cmd" not in step_data:
        errors.append("ステップにcmdが指定されていません")
    elif not isinstance(step_data["cmd"], list):
        errors.append("ステップのcmdはlistである必要があります")
    elif not step_data["cmd"]:
        errors.append("ステップのcmdが空です")
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_complete_config_pure(config_data: Dict[str, Any]) -> ValidationResult:
    """
    完全な設定をバリデートする純粋関数
    
    Args:
        config_data: 設定データ
        
    Returns:
        ValidationResult: バリデーション結果
    """
    all_errors = []
    all_warnings = []
    
    # env.json部分のバリデーション
    if "env_json" in config_data:
        env_result = validate_env_json_pure(config_data["env_json"])
        all_errors.extend(env_result.errors)
        all_warnings.extend(env_result.warnings)
    
    # 実行コンテキスト部分のバリデーション
    context_data = ExecutionContextData(
        language=config_data.get("language"),
        env_json=config_data.get("env_json"),
        command_type=config_data.get("command_type"),
        contest_name=config_data.get("contest_name"),
        problem_name=config_data.get("problem_name"),
        env_type=config_data.get("env_type")
    )
    
    context_result = validate_execution_context_pure(context_data)
    all_errors.extend(context_result.errors)
    all_warnings.extend(context_result.warnings)
    
    return ValidationResult(
        is_valid=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings
    )


def get_validation_summary_pure(result: ValidationResult) -> Dict[str, Any]:
    """
    バリデーション結果のサマリーを取得する純粋関数
    
    Args:
        result: バリデーション結果
        
    Returns:
        サマリー辞書
    """
    return {
        "is_valid": result.is_valid,
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "total_issues": len(result.errors) + len(result.warnings),
        "severity_level": _calculate_severity_level_pure(result)
    }


def _calculate_severity_level_pure(result: ValidationResult) -> str:
    """
    バリデーション結果の深刻度レベルを計算する純粋関数
    
    Args:
        result: バリデーション結果
        
    Returns:
        深刻度レベル
    """
    if result.errors:
        return "error"
    elif result.warnings:
        return "warning"
    else:
        return "success"


def combine_validation_results_pure(results: List[ValidationResult]) -> ValidationResult:
    """
    複数のバリデーション結果を結合する純粋関数
    
    Args:
        results: バリデーション結果のリスト
        
    Returns:
        結合されたバリデーション結果
    """
    if not results:
        return ValidationResult(is_valid=True, errors=[], warnings=[])
    
    all_errors = []
    all_warnings = []
    
    for result in results:
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)
    
    return ValidationResult(
        is_valid=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings
    )


def create_validation_filter_pure(
    include_errors: bool = True,
    include_warnings: bool = True,
    error_keywords: Optional[Set[str]] = None,
    warning_keywords: Optional[Set[str]] = None
) -> callable:
    """
    バリデーション結果をフィルタリングする関数を作成する純粋関数
    
    Args:
        include_errors: エラーを含めるかどうか
        include_warnings: 警告を含めるかどうか
        error_keywords: エラーメッセージのキーワードフィルタ
        warning_keywords: 警告メッセージのキーワードフィルタ
        
    Returns:
        フィルタ関数
    """
    def filter_func(result: ValidationResult) -> ValidationResult:
        filtered_errors = []
        filtered_warnings = []
        
        if include_errors:
            if error_keywords:
                filtered_errors = [
                    error for error in result.errors
                    if any(keyword in error.lower() for keyword in error_keywords)
                ]
            else:
                filtered_errors = list(result.errors)
        
        if include_warnings:
            if warning_keywords:
                filtered_warnings = [
                    warning for warning in result.warnings
                    if any(keyword in warning.lower() for keyword in warning_keywords)
                ]
            else:
                filtered_warnings = list(result.warnings)
        
        return ValidationResult(
            is_valid=len(filtered_errors) == 0,
            errors=filtered_errors,
            warnings=filtered_warnings
        )
    
    return filter_func