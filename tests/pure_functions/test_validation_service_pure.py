"""
バリデーションサービス純粋関数のテスト
モック不要で実際の動作をテスト
"""
import pytest
from src.pure_functions.validation_service_pure import (
    ValidationResult,
    DebugConfig,
    LanguageConfig,
    EnvJsonConfig,
    ExecutionContextData,
    validate_env_json_pure,
    validate_language_config_pure,
    validate_commands_pure,
    validate_env_types_pure,
    validate_debug_config_pure,
    validate_debug_format_pure,
    validate_execution_context_pure,
    validate_step_data_pure,
    validate_complete_config_pure,
    get_validation_summary_pure,
    combine_validation_results_pure,
    create_validation_filter_pure,
    _calculate_severity_level_pure
)


class TestValidationResult:
    """ValidationResultのテスト"""
    
    def test_create_validation_result(self):
        """バリデーション結果作成のテスト"""
        result = ValidationResult(
            is_valid=True,
            errors=["error1", "error2"],
            warnings=["warning1"]
        )
        
        assert result.is_valid is True
        assert result.errors == ["error1", "error2"]
        assert result.warnings == ["warning1"]
    
    def test_validation_result_immutability(self):
        """バリデーション結果の不変性テスト"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        with pytest.raises(AttributeError):
            result.is_valid = False
    
    def test_validation_result_defaults(self):
        """バリデーション結果のデフォルト値テスト"""
        result = ValidationResult(is_valid=True, errors=None, warnings=None)
        
        assert result.errors == []
        assert result.warnings == []


class TestDebugConfig:
    """DebugConfigのテスト"""
    
    def test_create_debug_config(self):
        """デバッグ設定作成のテスト"""
        config = DebugConfig(
            enabled=True,
            level="detailed",
            format_config={"icons": {"info": "ℹ"}}
        )
        
        assert config.enabled is True
        assert config.level == "detailed"
        assert config.format_config == {"icons": {"info": "ℹ"}}
    
    def test_debug_config_from_dict(self):
        """辞書からのデバッグ設定作成テスト"""
        data = {
            "enabled": True,
            "level": "minimal",
            "format": {"timestamp": True}
        }
        
        config = DebugConfig.from_dict(data)
        
        assert config.enabled is True
        assert config.level == "minimal"
        assert config.format_config == {"timestamp": True}
    
    def test_debug_config_defaults(self):
        """デバッグ設定のデフォルト値テスト"""
        config = DebugConfig()
        
        assert config.enabled is None
        assert config.level is None
        assert config.format_config is None


class TestLanguageConfig:
    """LanguageConfigのテスト"""
    
    def test_create_language_config(self):
        """言語設定作成のテスト"""
        config = LanguageConfig(
            commands={"build": {"steps": []}},
            env_types={"local": {}},
            aliases=["py", "python3"],
            debug=DebugConfig(enabled=True)
        )
        
        assert config.commands == {"build": {"steps": []}}
        assert config.env_types == {"local": {}}
        assert config.aliases == ["py", "python3"]
        assert config.debug.enabled is True
    
    def test_language_config_from_dict(self):
        """辞書からの言語設定作成テスト"""
        data = {
            "commands": {"build": {"steps": []}, "test": {"steps": []}},
            "env_types": {"local": {}, "docker": {}},
            "aliases": ["py"],
            "debug": {"enabled": False, "level": "none"}
        }
        
        config = LanguageConfig.from_dict(data)
        
        assert len(config.commands) == 2
        assert len(config.env_types) == 2
        assert config.aliases == ["py"]
        assert config.debug.enabled is False


class TestValidateEnvJsonPure:
    """env.jsonバリデーションのテスト"""
    
    def test_validate_valid_env_json(self):
        """有効なenv.jsonのバリデーションテスト"""
        data = {
            "python": {
                "commands": {
                    "build": {"steps": []},
                    "test": {"steps": []}
                },
                "env_types": {
                    "local": {},
                    "docker": {}
                }
            }
        }
        
        result = validate_env_json_pure(data)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_invalid_top_level(self):
        """無効なトップレベルのバリデーションテスト"""
        result = validate_env_json_pure("not_a_dict")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "dictである必要があります" in result.errors[0]
    
    def test_validate_empty_env_json(self):
        """空のenv.jsonのバリデーションテスト"""
        result = validate_env_json_pure({})
        
        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert "空です" in result.warnings[0]
    
    def test_validate_env_json_with_errors(self):
        """エラーのあるenv.jsonのバリデーションテスト"""
        data = {
            "python": {
                "commands": "not_a_dict",  # エラー
                "env_types": {}
            },
            "rust": "not_a_dict"  # エラー
        }
        
        result = validate_env_json_pure(data)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2


class TestValidateLanguageConfigPure:
    """言語設定バリデーションのテスト"""
    
    def test_validate_valid_language_config(self):
        """有効な言語設定のバリデーションテスト"""
        config = {
            "commands": {
                "build": {"steps": []},
                "test": {"steps": []}
            },
            "env_types": {
                "local": {},
                "docker": {}
            },
            "aliases": ["py"],
            "debug": {"enabled": True, "level": "detailed"}
        }
        
        errors = validate_language_config_pure(config, "test.json", "python")
        
        assert errors == []
    
    def test_validate_invalid_language_config_type(self):
        """無効な言語設定型のバリデーションテスト"""
        errors = validate_language_config_pure("not_a_dict", "test.json", "python")
        
        assert len(errors) == 1
        assert "dictである必要があります" in errors[0]
    
    def test_validate_missing_required_fields(self):
        """必須フィールド欠如のバリデーションテスト"""
        config = {}  # commands, env_types がない
        
        errors = validate_language_config_pure(config, "test.json", "python")
        
        assert len(errors) >= 2
        assert any("commands" in error for error in errors)
        assert any("env_types" in error for error in errors)
    
    def test_validate_invalid_aliases(self):
        """無効なエイリアスのバリデーションテスト"""
        config = {
            "commands": {"build": {"steps": []}},
            "env_types": {"local": {}},
            "aliases": "not_a_list"  # エラー
        }
        
        errors = validate_language_config_pure(config, "test.json", "python")
        
        assert any("aliasesはlistである必要があります" in error for error in errors)


class TestValidateCommandsPure:
    """コマンドバリデーションのテスト"""
    
    def test_validate_valid_commands(self):
        """有効なコマンドのバリデーションテスト"""
        commands = {
            "build": {"steps": []},
            "test": {"steps": []},
            "run": {"steps": []}
        }
        
        errors = validate_commands_pure(commands, "test.json", "python")
        
        assert errors == []
    
    def test_validate_empty_commands(self):
        """空のコマンドのバリデーションテスト"""
        errors = validate_commands_pure({}, "test.json", "python")
        
        assert len(errors) >= 1
        assert "空です" in errors[0]
    
    def test_validate_missing_required_commands(self):
        """必須コマンド欠如のバリデーションテスト"""
        commands = {"run": {"steps": []}}  # build, test がない
        
        errors = validate_commands_pure(commands, "test.json", "python")
        
        assert len(errors) >= 1
        assert "必要なコマンドがありません" in errors[0]
    
    def test_validate_invalid_command_structure(self):
        """無効なコマンド構造のバリデーションテスト"""
        commands = {
            "build": "not_a_dict",  # エラー
            "test": {"no_steps": []}  # stepsがない
        }
        
        errors = validate_commands_pure(commands, "test.json", "python")
        
        assert len(errors) >= 2
        assert any("dictである必要があります" in error for error in errors)
        assert any("stepsがありません" in error for error in errors)


class TestValidateEnvTypesPure:
    """環境タイプバリデーションのテスト"""
    
    def test_validate_valid_env_types(self):
        """有効な環境タイプのバリデーションテスト"""
        env_types = {
            "local": {"driver": "local"},
            "docker": {"image": "python:3.9"},
            "wsl": {"distribution": "ubuntu"}
        }
        
        errors = validate_env_types_pure(env_types, "test.json", "python")
        
        assert errors == []
    
    def test_validate_empty_env_types(self):
        """空の環境タイプのバリデーションテスト"""
        errors = validate_env_types_pure({}, "test.json", "python")
        
        assert len(errors) >= 1
        assert "空です" in errors[0]
    
    def test_validate_missing_required_env_types(self):
        """必須環境タイプ欠如のバリデーションテスト"""
        env_types = {"wsl": {}}  # local, docker がない
        
        errors = validate_env_types_pure(env_types, "test.json", "python")
        
        assert len(errors) >= 1
        assert "必要な環境タイプがありません" in errors[0]
    
    def test_validate_invalid_env_type_structure(self):
        """無効な環境タイプ構造のバリデーションテスト"""
        env_types = {
            "local": "not_a_dict",  # エラー
            "docker": {}
        }
        
        errors = validate_env_types_pure(env_types, "test.json", "python")
        
        assert len(errors) >= 1
        assert "dictである必要があります" in errors[0]


class TestValidateDebugConfigPure:
    """デバッグ設定バリデーションのテスト"""
    
    def test_validate_valid_debug_config(self):
        """有効なデバッグ設定のバリデーションテスト"""
        debug_config = {
            "enabled": True,
            "level": "detailed",
            "format": {
                "icons": {"info": "ℹ"},
                "timestamp": True,
                "colors": {"error": "red"}
            }
        }
        
        errors = validate_debug_config_pure(debug_config, "test.json", "python")
        
        assert errors == []
    
    def test_validate_invalid_debug_config_type(self):
        """無効なデバッグ設定型のバリデーションテスト"""
        errors = validate_debug_config_pure("not_a_dict", "test.json", "python")
        
        assert len(errors) == 1
        assert "dictである必要があります" in errors[0]
    
    def test_validate_invalid_enabled_field(self):
        """無効なenabledフィールドのバリデーションテスト"""
        debug_config = {"enabled": "not_a_bool"}
        
        errors = validate_debug_config_pure(debug_config, "test.json", "python")
        
        assert len(errors) >= 1
        assert "boolである必要があります" in errors[0]
    
    def test_validate_invalid_level_field(self):
        """無効なlevelフィールドのバリデーションテスト"""
        debug_config = {"level": "invalid_level"}
        
        errors = validate_debug_config_pure(debug_config, "test.json", "python")
        
        assert len(errors) >= 1
        assert "のいずれかである必要があります" in errors[0]


class TestValidateDebugFormatPure:
    """デバッグフォーマットバリデーションのテスト"""
    
    def test_validate_valid_debug_format(self):
        """有効なデバッグフォーマットのバリデーションテスト"""
        format_config = {
            "icons": {"info": "ℹ", "error": "❌"},
            "timestamp": True,
            "colors": {"info": "blue", "error": "red"}
        }
        
        errors = validate_debug_format_pure(format_config, "test.json", "python")
        
        assert errors == []
    
    def test_validate_invalid_format_type(self):
        """無効なフォーマット型のバリデーションテスト"""
        errors = validate_debug_format_pure("not_a_dict", "test.json", "python")
        
        assert len(errors) == 1
        assert "dictである必要があります" in errors[0]
    
    def test_validate_invalid_icons_field(self):
        """無効なiconsフィールドのバリデーションテスト"""
        format_config = {"icons": "not_a_dict"}
        
        errors = validate_debug_format_pure(format_config, "test.json", "python")
        
        assert len(errors) >= 1
        assert "iconsはdictである必要があります" in errors[0]
    
    def test_validate_invalid_timestamp_field(self):
        """無効なtimestampフィールドのバリデーションテスト"""
        format_config = {"timestamp": "not_a_bool"}
        
        errors = validate_debug_format_pure(format_config, "test.json", "python")
        
        assert len(errors) >= 1
        assert "timestampはboolである必要があります" in errors[0]


class TestValidateExecutionContextPure:
    """実行コンテキストバリデーションのテスト"""
    
    def test_validate_valid_execution_context(self):
        """有効な実行コンテキストのバリデーションテスト"""
        context = ExecutionContextData(
            language="python",
            env_json={"python": {"commands": {"build": {}}}},
            command_type="build",
            env_type="local"
        )
        
        result = validate_execution_context_pure(context)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_missing_language(self):
        """言語欠如のバリデーションテスト"""
        context = ExecutionContextData(
            env_json={"python": {}}
        )
        
        result = validate_execution_context_pure(context)
        
        assert result.is_valid is False
        assert any("言語が指定されていません" in error for error in result.errors)
    
    def test_validate_missing_env_json(self):
        """env_json欠如のバリデーションテスト"""
        context = ExecutionContextData(language="python")
        
        result = validate_execution_context_pure(context)
        
        assert result.is_valid is False
        assert any("環境設定が見つかりません" in error for error in result.errors)
    
    def test_validate_language_not_in_env_json(self):
        """env_jsonに言語が存在しないバリデーションテスト"""
        context = ExecutionContextData(
            language="rust",
            env_json={"python": {}}
        )
        
        result = validate_execution_context_pure(context)
        
        assert result.is_valid is False
        assert any("設定が見つかりません" in error for error in result.errors)
    
    def test_validate_invalid_env_type(self):
        """無効な環境タイプのバリデーションテスト"""
        context = ExecutionContextData(
            language="python",
            env_json={"python": {}},
            env_type="invalid_env"
        )
        
        result = validate_execution_context_pure(context)
        
        assert len(result.warnings) >= 1
        assert any("推奨されていません" in warning for warning in result.warnings)


class TestValidateStepDataPure:
    """ステップデータバリデーションのテスト"""
    
    def test_validate_valid_step_data(self):
        """有効なステップデータのバリデーションテスト"""
        step_data = {
            "type": "shell",
            "cmd": ["echo", "hello"]
        }
        
        result = validate_step_data_pure(step_data)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_invalid_step_data_type(self):
        """無効なステップデータ型のバリデーションテスト"""
        result = validate_step_data_pure("not_a_dict")
        
        assert result.is_valid is False
        assert any("辞書である必要があります" in error for error in result.errors)
    
    def test_validate_missing_type(self):
        """type欠如のバリデーションテスト"""
        step_data = {"cmd": ["echo", "hello"]}
        
        result = validate_step_data_pure(step_data)
        
        assert result.is_valid is False
        assert any("typeが指定されていません" in error for error in result.errors)
    
    def test_validate_invalid_cmd(self):
        """無効なcmdのバリデーションテスト"""
        step_data = {
            "type": "shell",
            "cmd": "not_a_list"
        }
        
        result = validate_step_data_pure(step_data)
        
        assert result.is_valid is False
        assert any("cmdはlistである必要があります" in error for error in result.errors)
    
    def test_validate_empty_cmd(self):
        """空のcmdのバリデーションテスト"""
        step_data = {
            "type": "shell",
            "cmd": []
        }
        
        result = validate_step_data_pure(step_data)
        
        assert result.is_valid is False
        assert any("cmdが空です" in error for error in result.errors)
    
    def test_validate_unknown_step_type(self):
        """未知のステップタイプのバリデーションテスト"""
        step_data = {
            "type": "unknown_type",
            "cmd": ["some", "command"]
        }
        
        result = validate_step_data_pure(step_data)
        
        assert result.is_valid is True  # 警告のみ
        assert len(result.warnings) >= 1
        assert any("認識されていません" in warning for warning in result.warnings)


class TestValidateCompleteConfigPure:
    """完全設定バリデーションのテスト"""
    
    def test_validate_complete_valid_config(self):
        """有効な完全設定のバリデーションテスト"""
        config_data = {
            "language": "python",
            "env_json": {
                "python": {
                    "commands": {"build": {"steps": []}, "test": {"steps": []}},
                    "env_types": {"local": {}, "docker": {}}
                }
            },
            "command_type": "build",
            "env_type": "local"
        }
        
        result = validate_complete_config_pure(config_data)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_complete_invalid_config(self):
        """無効な完全設定のバリデーションテスト"""
        config_data = {
            "language": None,  # エラー
            "env_json": "not_a_dict",  # エラー
            "command_type": "build"
        }
        
        result = validate_complete_config_pure(config_data)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2


class TestUtilityFunctions:
    """ユーティリティ関数のテスト"""
    
    def test_get_validation_summary(self):
        """バリデーションサマリー取得のテスト"""
        result = ValidationResult(
            is_valid=False,
            errors=["error1", "error2"],
            warnings=["warning1"]
        )
        
        summary = get_validation_summary_pure(result)
        
        assert summary["is_valid"] is False
        assert summary["error_count"] == 2
        assert summary["warning_count"] == 1
        assert summary["total_issues"] == 3
        assert summary["severity_level"] == "error"
    
    def test_calculate_severity_level_error(self):
        """エラーレベルの深刻度計算テスト"""
        result = ValidationResult(is_valid=False, errors=["error"], warnings=[])
        
        level = _calculate_severity_level_pure(result)
        
        assert level == "error"
    
    def test_calculate_severity_level_warning(self):
        """警告レベルの深刻度計算テスト"""
        result = ValidationResult(is_valid=True, errors=[], warnings=["warning"])
        
        level = _calculate_severity_level_pure(result)
        
        assert level == "warning"
    
    def test_calculate_severity_level_success(self):
        """成功レベルの深刻度計算テスト"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        level = _calculate_severity_level_pure(result)
        
        assert level == "success"
    
    def test_combine_validation_results_empty(self):
        """空のバリデーション結果結合テスト"""
        result = combine_validation_results_pure([])
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
    
    def test_combine_validation_results_multiple(self):
        """複数のバリデーション結果結合テスト"""
        result1 = ValidationResult(is_valid=False, errors=["error1"], warnings=["warning1"])
        result2 = ValidationResult(is_valid=True, errors=[], warnings=["warning2"])
        result3 = ValidationResult(is_valid=False, errors=["error2"], warnings=[])
        
        combined = combine_validation_results_pure([result1, result2, result3])
        
        assert combined.is_valid is False
        assert len(combined.errors) == 2
        assert len(combined.warnings) == 2
        assert "error1" in combined.errors
        assert "error2" in combined.errors
        assert "warning1" in combined.warnings
        assert "warning2" in combined.warnings


class TestValidationFilter:
    """バリデーションフィルターのテスト"""
    
    def test_create_validation_filter_all(self):
        """全てを含むフィルター作成テスト"""
        filter_func = create_validation_filter_pure()
        
        original = ValidationResult(
            is_valid=False,
            errors=["error1", "error2"],
            warnings=["warning1", "warning2"]
        )
        
        filtered = filter_func(original)
        
        assert len(filtered.errors) == 2
        assert len(filtered.warnings) == 2
    
    def test_create_validation_filter_errors_only(self):
        """エラーのみのフィルター作成テスト"""
        filter_func = create_validation_filter_pure(
            include_errors=True,
            include_warnings=False
        )
        
        original = ValidationResult(
            is_valid=False,
            errors=["error1"],
            warnings=["warning1"]
        )
        
        filtered = filter_func(original)
        
        assert len(filtered.errors) == 1
        assert len(filtered.warnings) == 0
    
    def test_create_validation_filter_with_keywords(self):
        """キーワードフィルター作成テスト"""
        filter_func = create_validation_filter_pure(
            error_keywords={"command"},
            warning_keywords={"type"}
        )
        
        original = ValidationResult(
            is_valid=False,
            errors=["command error", "format error"],
            warnings=["type warning", "config warning"]
        )
        
        filtered = filter_func(original)
        
        assert len(filtered.errors) == 1
        assert "command error" in filtered.errors
        assert len(filtered.warnings) == 1
        assert "type warning" in filtered.warnings


class TestComplexScenarios:
    """複雑なシナリオのテスト"""
    
    def test_complete_validation_workflow(self):
        """完全なバリデーションワークフローのテスト"""
        # 1. env.jsonの構造バリデーション
        env_json_data = {
            "python": {
                "commands": {"build": {"steps": []}, "test": {"steps": []}},
                "env_types": {"local": {}, "docker": {}},
                "debug": {"enabled": True, "level": "detailed"}
            },
            "rust": {
                "commands": {"build": {"steps": []}},  # test が不足
                "env_types": {"local": {}}  # docker が不足
            }
        }
        
        env_result = validate_env_json_pure(env_json_data)
        
        # 2. 実行コンテキストのバリデーション
        context = ExecutionContextData(
            language="python",
            env_json=env_json_data,
            command_type="build",
            env_type="local"
        )
        
        context_result = validate_execution_context_pure(context)
        
        # 3. ステップデータのバリデーション
        step_data = {
            "type": "shell",
            "cmd": ["echo", "Building..."]
        }
        
        step_result = validate_step_data_pure(step_data)
        
        # 4. 結果の結合
        combined_result = combine_validation_results_pure([
            env_result, context_result, step_result
        ])
        
        # 検証
        assert env_result.is_valid is False  # rust設定に問題
        assert context_result.is_valid is True  # python設定は正常
        assert step_result.is_valid is True  # ステップは正常
        assert combined_result.is_valid is False  # 全体では無効
        
        # 5. サマリーの取得
        summary = get_validation_summary_pure(combined_result)
        assert summary["severity_level"] == "error"
        assert summary["error_count"] > 0
    
    def test_nested_configuration_validation(self):
        """ネストした設定のバリデーションテスト"""
        config_data = {
            "language": "python",
            "env_json": {
                "python": {
                    "commands": {
                        "build": {"steps": [{"type": "shell", "cmd": ["python", "setup.py", "build"]}]},
                        "test": {"steps": [{"type": "python", "cmd": ["import pytest; pytest.main()"]}]}
                    },
                    "env_types": {
                        "local": {"driver": "local_shell"},
                        "docker": {"image": "python:3.9", "volumes": []}
                    },
                    "aliases": ["py", "python3"],
                    "debug": {
                        "enabled": True,
                        "level": "detailed",
                        "format": {
                            "icons": {"info": "ℹ", "error": "❌", "warning": "⚠"},
                            "timestamp": True,
                            "colors": {"info": "blue", "error": "red", "warning": "yellow"}
                        }
                    }
                }
            },
            "command_type": "build",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "a"
        }
        
        # 完全な設定バリデーション
        result = validate_complete_config_pure(config_data)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # 個別のステップバリデーション
        for step_data in config_data["env_json"]["python"]["commands"]["build"]["steps"]:
            step_result = validate_step_data_pure(step_data)
            assert step_result.is_valid is True
    
    def test_error_accumulation_scenario(self):
        """エラー蓄積シナリオのテスト"""
        # 複数のバリデーション結果を作成
        results = []
        
        # env.jsonエラー
        env_result = validate_env_json_pure({"python": "invalid"})
        results.append(env_result)
        
        # 実行コンテキストエラー
        context_result = validate_execution_context_pure(ExecutionContextData())
        results.append(context_result)
        
        # ステップエラー
        step_result = validate_step_data_pure({"type": "shell"})  # cmd が欠如
        results.append(step_result)
        
        # 結合
        combined = combine_validation_results_pure(results)
        
        # フィルタリング
        error_filter = create_validation_filter_pure(include_warnings=False)
        errors_only = error_filter(combined)
        
        # 検証
        assert combined.is_valid is False
        assert len(combined.errors) >= 3
        assert len(errors_only.warnings) == 0
        assert len(errors_only.errors) >= 3