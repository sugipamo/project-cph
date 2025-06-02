"""
システム情報純粋関数のテスト
モック不要で実際の動作をテスト
"""
import pytest
import json
from src.pure_functions.system_info_pure import (
    SystemInfo,
    FileContent,
    SystemInfoResult,
    create_default_system_info_pure,
    parse_system_info_from_json_pure,
    load_system_info_from_content_pure,
    serialize_system_info_to_json_pure,
    update_system_info_pure,
    merge_system_info_pure,
    validate_system_info_pure,
    extract_contest_info_pure,
    extract_execution_info_pure,
    filter_system_info_fields_pure,
    calculate_system_info_metrics_pure,
    create_system_info_from_params_pure
)


class TestSystemInfo:
    """SystemInfoのテスト"""
    
    def test_create_system_info(self):
        """システム情報作成のテスト"""
        info = SystemInfo(
            command="build",
            language="python",
            env_type="local",
            contest_name="abc123",
            problem_name="a",
            env_json={"python": {"version": "3.9"}}
        )
        
        assert info.command == "build"
        assert info.language == "python"
        assert info.env_type == "local"
        assert info.contest_name == "abc123"
        assert info.problem_name == "a"
        assert info.env_json == {"python": {"version": "3.9"}}
    
    def test_system_info_immutability(self):
        """システム情報の不変性テスト"""
        info = SystemInfo(command="test")
        
        with pytest.raises(AttributeError):
            info.command = "build"
    
    def test_system_info_defaults(self):
        """システム情報のデフォルト値テスト"""
        info = SystemInfo()
        
        assert info.command is None
        assert info.language is None
        assert info.env_type is None
        assert info.contest_name is None
        assert info.problem_name is None
        assert info.env_json is None
    
    def test_to_dict(self):
        """辞書変換のテスト"""
        info = SystemInfo(
            command="build",
            language="python",
            contest_name="abc123"
        )
        
        result = info.to_dict()
        
        assert result["command"] == "build"
        assert result["language"] == "python"
        assert result["contest_name"] == "abc123"
        assert result["env_type"] is None
    
    def test_from_dict(self):
        """辞書からの作成テスト"""
        data = {
            "command": "test",
            "language": "rust",
            "env_type": "docker",
            "contest_name": "abc123",
            "problem_name": "b"
        }
        
        info = SystemInfo.from_dict(data)
        
        assert info.command == "test"
        assert info.language == "rust"
        assert info.env_type == "docker"
        assert info.contest_name == "abc123"
        assert info.problem_name == "b"


class TestFileContent:
    """FileContentのテスト"""
    
    def test_create_file_content(self):
        """ファイル内容作成のテスト"""
        content = FileContent(
            content='{"test": "value"}',
            exists=True,
            path="/path/to/file.json"
        )
        
        assert content.content == '{"test": "value"}'
        assert content.exists is True
        assert content.path == "/path/to/file.json"
        assert content.encoding == "utf-8"
    
    def test_file_content_immutability(self):
        """ファイル内容の不変性テスト"""
        content = FileContent(content="test", exists=True, path="/test")
        
        with pytest.raises(AttributeError):
            content.content = "new_content"


class TestCreateDefaultSystemInfo:
    """デフォルトシステム情報作成のテスト"""
    
    def test_create_default(self):
        """デフォルト作成のテスト"""
        info = create_default_system_info_pure()
        
        assert isinstance(info, SystemInfo)
        assert info.command is None
        assert info.language is None
        assert info.env_type is None
        assert info.contest_name is None
        assert info.problem_name is None
        assert info.env_json is None


class TestParseSystemInfoFromJson:
    """JSON解析のテスト"""
    
    def test_parse_valid_json(self):
        """有効なJSON解析のテスト"""
        json_data = {
            "command": "build",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "a"
        }
        json_str = json.dumps(json_data)
        
        result = parse_system_info_from_json_pure(json_str)
        
        assert result.success is True
        assert result.info is not None
        assert result.info.command == "build"
        assert result.info.language == "python"
        assert len(result.errors) == 0
    
    def test_parse_invalid_json(self):
        """無効なJSON解析のテスト"""
        invalid_json = '{"command": "build", "language":}'
        
        result = parse_system_info_from_json_pure(invalid_json)
        
        assert result.success is False
        assert result.info is None
        assert len(result.errors) == 1
        assert "Invalid JSON format" in result.errors[0]
    
    def test_parse_empty_json(self):
        """空JSON解析のテスト"""
        result = parse_system_info_from_json_pure('{}')
        
        assert result.success is True
        assert result.info is not None
        assert result.info.command is None


class TestLoadSystemInfoFromContent:
    """ファイル内容からの読み込みテスト"""
    
    def test_load_from_existing_file(self):
        """存在するファイルからの読み込みテスト"""
        json_data = {"command": "build", "language": "python"}
        content = FileContent(
            content=json.dumps(json_data),
            exists=True,
            path="/test/system_info.json"
        )
        
        result = load_system_info_from_content_pure(content)
        
        assert result.success is True
        assert result.info.command == "build"
        assert result.info.language == "python"
    
    def test_load_from_nonexistent_file(self):
        """存在しないファイルからの読み込みテスト"""
        result = load_system_info_from_content_pure(None)
        
        assert result.success is True
        assert result.info is not None
        assert result.info.command is None  # デフォルト値
        assert len(result.warnings) == 1
        assert "file not found" in result.warnings[0]
    
    def test_load_from_empty_file(self):
        """空ファイルからの読み込みテスト"""
        content = FileContent(
            content="   ",  # 空白のみ
            exists=True,
            path="/test/empty.json"
        )
        
        result = load_system_info_from_content_pure(content)
        
        assert result.success is True
        assert result.info is not None
        assert result.info.command is None  # デフォルト値
        assert len(result.warnings) == 1
        assert "file is empty" in result.warnings[0]
    
    def test_load_from_invalid_content(self):
        """無効な内容からの読み込みテスト"""
        content = FileContent(
            content="invalid json content",
            exists=True,
            path="/test/invalid.json"
        )
        
        result = load_system_info_from_content_pure(content)
        
        assert result.success is False
        assert result.info is None
        assert len(result.errors) == 1


class TestSerializeSystemInfo:
    """システム情報シリアライズのテスト"""
    
    def test_serialize_complete_info(self):
        """完全な情報のシリアライズテスト"""
        info = SystemInfo(
            command="build",
            language="python",
            env_type="local",
            contest_name="abc123",
            problem_name="a",
            env_json={"python": {"version": "3.9"}}
        )
        
        json_str = serialize_system_info_to_json_pure(info)
        
        # 再解析して確認
        parsed_data = json.loads(json_str)
        assert parsed_data["command"] == "build"
        assert parsed_data["language"] == "python"
        assert parsed_data["env_json"]["python"]["version"] == "3.9"
    
    def test_serialize_partial_info(self):
        """部分的な情報のシリアライズテスト"""
        info = SystemInfo(command="test", language="rust")
        
        json_str = serialize_system_info_to_json_pure(info)
        
        parsed_data = json.loads(json_str)
        assert parsed_data["command"] == "test"
        assert parsed_data["language"] == "rust"
        assert parsed_data["env_type"] is None
    
    def test_serialize_with_custom_indent(self):
        """カスタムインデントでのシリアライズテスト"""
        info = SystemInfo(command="build")
        
        json_str = serialize_system_info_to_json_pure(info, indent=4)
        
        # インデントが適用されていることを確認
        assert "    " in json_str  # 4スペースのインデント


class TestUpdateSystemInfo:
    """システム情報更新のテスト"""
    
    def test_update_single_field(self):
        """単一フィールド更新のテスト"""
        original = SystemInfo(command="build", language="python")
        
        updated = update_system_info_pure(original, {"command": "test"})
        
        assert updated.command == "test"
        assert updated.language == "python"  # 変更されない
        assert original.command == "build"   # 元は変更されない
    
    def test_update_multiple_fields(self):
        """複数フィールド更新のテスト"""
        original = SystemInfo(command="build", language="python")
        
        updated = update_system_info_pure(original, {
            "command": "test",
            "env_type": "docker",
            "contest_name": "abc123"
        })
        
        assert updated.command == "test"
        assert updated.env_type == "docker"
        assert updated.contest_name == "abc123"
        assert updated.language == "python"  # 元の値が保持
    
    def test_update_invalid_field(self):
        """無効なフィールド更新のテスト"""
        original = SystemInfo(command="build")
        
        # 無効なフィールドは無視される
        updated = update_system_info_pure(original, {
            "command": "test",
            "invalid_field": "value"
        })
        
        assert updated.command == "test"
        # invalid_fieldは無視される


class TestMergeSystemInfo:
    """システム情報マージのテスト"""
    
    def test_merge_basic_fields(self):
        """基本フィールドマージのテスト"""
        base = SystemInfo(command="build", language="python")
        override = SystemInfo(command="test", env_type="docker")
        
        merged = merge_system_info_pure(base, override)
        
        assert merged.command == "test"      # 上書きされる
        assert merged.language == "python"  # ベースが保持
        assert merged.env_type == "docker"  # 新しい値が追加
    
    def test_merge_with_none_values(self):
        """None値でのマージテスト"""
        base = SystemInfo(command="build", language="python")
        override = SystemInfo(command=None, env_type="docker")
        
        merged = merge_system_info_pure(base, override)
        
        assert merged.command == "build"    # Noneは上書きしない
        assert merged.language == "python"
        assert merged.env_type == "docker"
    
    def test_merge_env_json(self):
        """env_jsonマージのテスト"""
        base = SystemInfo(
            env_json={"python": {"version": "3.9"}, "rust": {"version": "1.50"}}
        )
        override = SystemInfo(
            env_json={"python": {"version": "3.10"}, "java": {"version": "11"}}
        )
        
        merged = merge_system_info_pure(base, override, merge_env_json=True)
        
        # env_jsonが深くマージされる
        assert merged.env_json["python"]["version"] == "3.10"  # 上書き
        assert merged.env_json["rust"]["version"] == "1.50"    # 保持
        assert merged.env_json["java"]["version"] == "11"      # 追加
    
    def test_merge_env_json_no_merge(self):
        """env_jsonの非マージテスト"""
        base = SystemInfo(env_json={"python": {"version": "3.9"}})
        override = SystemInfo(env_json={"rust": {"version": "1.50"}})
        
        merged = merge_system_info_pure(base, override, merge_env_json=False)
        
        # env_jsonが完全に置き換えられる
        assert "python" not in merged.env_json
        assert merged.env_json["rust"]["version"] == "1.50"


class TestValidateSystemInfo:
    """システム情報検証のテスト"""
    
    def test_validate_valid_info(self):
        """有効な情報の検証テスト"""
        info = SystemInfo(
            command="build",
            language="python",
            env_type="local",
            contest_name="abc123",
            problem_name="a"
        )
        
        errors = validate_system_info_pure(info)
        
        assert errors == []
    
    def test_validate_invalid_env_type(self):
        """無効な環境タイプの検証テスト"""
        info = SystemInfo(env_type="invalid_env")
        
        errors = validate_system_info_pure(info)
        
        assert len(errors) >= 1
        assert "Invalid env_type" in errors[0]
    
    def test_validate_unsupported_language(self):
        """サポート外言語の検証テスト"""
        info = SystemInfo(language="cobol")
        
        errors = validate_system_info_pure(info)
        
        assert len(errors) >= 1
        assert "unsupported language" in errors[0]
    
    def test_validate_invalid_types(self):
        """無効な型の検証テスト"""
        info = SystemInfo(
            contest_name=123,  # 文字列でない
            env_json="not_dict"  # 辞書でない
        )
        
        errors = validate_system_info_pure(info)
        
        assert len(errors) >= 2
        assert any("contest_name must be a string" in error for error in errors)
        assert any("env_json must be a dictionary" in error for error in errors)


class TestExtractFunctions:
    """抽出関数のテスト"""
    
    def test_extract_contest_info(self):
        """コンテスト情報抽出のテスト"""
        info = SystemInfo(
            command="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local"
        )
        
        contest_info = extract_contest_info_pure(info)
        
        assert contest_info["contest_name"] == "abc123"
        assert contest_info["problem_name"] == "a"
        assert contest_info["language"] == "python"
        assert contest_info["env_type"] == "local"
    
    def test_extract_execution_info(self):
        """実行情報抽出のテスト"""
        info = SystemInfo(
            command="build",
            language="python",
            env_type="docker",
            env_json={
                "python": {
                    "commands": {
                        "build": "python setup.py build",
                        "test": "python -m pytest"
                    }
                }
            }
        )
        
        exec_info = extract_execution_info_pure(info)
        
        assert exec_info["command"] == "build"
        assert exec_info["language"] == "python"
        assert exec_info["env_type"] == "docker"
        assert "available_commands" in exec_info
        assert "build" in exec_info["available_commands"]
        assert "test" in exec_info["available_commands"]
    
    def test_extract_execution_info_no_env_json(self):
        """env_jsonなしの実行情報抽出テスト"""
        info = SystemInfo(command="test", language="rust")
        
        exec_info = extract_execution_info_pure(info)
        
        assert exec_info["command"] == "test"
        assert exec_info["language"] == "rust"
        assert "available_commands" not in exec_info


class TestFilterSystemInfoFields:
    """フィールドフィルタリングのテスト"""
    
    def test_filter_include_fields(self):
        """包含フィールドフィルタリングのテスト"""
        info = SystemInfo(
            command="build",
            language="python",
            env_type="local",
            contest_name="abc123"
        )
        
        filtered = filter_system_info_fields_pure(
            info, 
            include_fields=["command", "language"]
        )
        
        assert "command" in filtered
        assert "language" in filtered
        assert "env_type" not in filtered
        assert "contest_name" not in filtered
    
    def test_filter_exclude_fields(self):
        """除外フィールドフィルタリングのテスト"""
        info = SystemInfo(
            command="build",
            language="python",
            env_type="local"
        )
        
        filtered = filter_system_info_fields_pure(
            info,
            exclude_fields=["env_type", "env_json"]
        )
        
        assert "command" in filtered
        assert "language" in filtered
        assert "env_type" not in filtered
        assert "env_json" not in filtered
    
    def test_filter_include_and_exclude(self):
        """包含と除外の組み合わせテスト"""
        info = SystemInfo(
            command="build",
            language="python",
            env_type="local",
            contest_name="abc123"
        )
        
        filtered = filter_system_info_fields_pure(
            info,
            include_fields=["command", "language", "env_type"],
            exclude_fields=["env_type"]
        )
        
        assert "command" in filtered
        assert "language" in filtered
        assert "env_type" not in filtered  # exclude が優先


class TestCalculateSystemInfoMetrics:
    """システム情報メトリクス計算のテスト"""
    
    def test_calculate_metrics_complete_info(self):
        """完全な情報のメトリクス計算テスト"""
        info = SystemInfo(
            command="build",
            language="python",
            env_type="local",
            contest_name="abc123",
            problem_name="a",
            env_json={
                "python": {"commands": {"build": "cmd1", "test": "cmd2"}},
                "rust": {"commands": {"build": "cmd3"}}
            }
        )
        
        metrics = calculate_system_info_metrics_pure(info)
        
        assert metrics["fields_populated"] == 6
        assert metrics["total_fields"] == 6
        assert metrics["completion_rate"] == 1.0
        assert metrics["has_contest_info"] is True
        assert metrics["has_execution_info"] is True
        assert metrics["env_json_languages"] == 2
        assert metrics["env_json_commands"] == 3
    
    def test_calculate_metrics_partial_info(self):
        """部分的な情報のメトリクス計算テスト"""
        info = SystemInfo(command="build", language="python")
        
        metrics = calculate_system_info_metrics_pure(info)
        
        assert metrics["fields_populated"] == 2
        assert metrics["completion_rate"] == 2/6
        assert metrics["has_contest_info"] is False
        assert metrics["has_execution_info"] is True  # command + language
        assert metrics["env_json_languages"] == 0
    
    def test_calculate_metrics_empty_info(self):
        """空の情報のメトリクス計算テスト"""
        info = SystemInfo()
        
        metrics = calculate_system_info_metrics_pure(info)
        
        assert metrics["fields_populated"] == 0
        assert metrics["completion_rate"] == 0.0
        assert metrics["has_contest_info"] is False
        assert metrics["has_execution_info"] is False


class TestCreateSystemInfoFromParams:
    """パラメータからのシステム情報作成テスト"""
    
    def test_create_from_all_params(self):
        """全パラメータからの作成テスト"""
        info = create_system_info_from_params_pure(
            command="build",
            language="python",
            env_type="local",
            contest_name="abc123",
            problem_name="a",
            env_json={"python": {"version": "3.9"}}
        )
        
        assert info.command == "build"
        assert info.language == "python"
        assert info.env_type == "local"
        assert info.contest_name == "abc123"
        assert info.problem_name == "a"
        assert info.env_json == {"python": {"version": "3.9"}}
    
    def test_create_from_partial_params(self):
        """部分パラメータからの作成テスト"""
        info = create_system_info_from_params_pure(
            command="test",
            language="rust"
        )
        
        assert info.command == "test"
        assert info.language == "rust"
        assert info.env_type is None
        assert info.contest_name is None
    
    def test_create_from_no_params(self):
        """パラメータなしの作成テスト"""
        info = create_system_info_from_params_pure()
        
        assert info.command is None
        assert info.language is None
        assert info.env_type is None


class TestComplexScenarios:
    """複雑なシナリオのテスト"""
    
    def test_complete_workflow_scenario(self):
        """完全なワークフローシナリオのテスト"""
        # 1. JSONからの読み込み
        json_data = {
            "command": "build",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "env_json": {"python": {"version": "3.9"}}
        }
        
        content = FileContent(
            content=json.dumps(json_data),
            exists=True,
            path="/test/system_info.json"
        )
        
        load_result = load_system_info_from_content_pure(content)
        assert load_result.success
        
        # 2. 情報の更新
        updated_info = update_system_info_pure(
            load_result.info,
            {"problem_name": "a", "env_type": "docker"}
        )
        
        # 3. 検証
        errors = validate_system_info_pure(updated_info)
        assert errors == []
        
        # 4. メトリクス計算
        metrics = calculate_system_info_metrics_pure(updated_info)
        assert metrics["completion_rate"] > 0.8
        
        # 5. シリアライズ
        json_output = serialize_system_info_to_json_pure(updated_info)
        
        # 6. 再解析して一貫性確認
        reparse_result = parse_system_info_from_json_pure(json_output)
        assert reparse_result.success
        assert reparse_result.info.problem_name == "a"
        assert reparse_result.info.env_type == "docker"