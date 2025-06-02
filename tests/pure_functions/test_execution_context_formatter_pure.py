"""
ExecutionContext フォーマッタ純粋関数のテスト
"""
import pytest
from src.pure_functions.execution_context_formatter_pure import (
    ExecutionFormatData, create_format_dict, format_template_string,
    validate_execution_data, get_docker_naming_from_data
)


class TestExecutionFormatData:
    """ExecutionFormatDataのテスト"""
    
    def test_immutable(self):
        """イミュータブル性のテスト"""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={}
        )
        
        # 変更を試みるとエラーになることを確認
        with pytest.raises(AttributeError):
            data.command_type = "new_test"


class TestCreateFormatDict:
    """create_format_dict関数のテスト"""
    
    def test_basic_format_dict(self):
        """基本的なフォーマット辞書の生成"""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={}
        )
        
        result = create_format_dict(data)
        
        assert result["command_type"] == "test"
        assert result["language"] == "python"
        assert result["contest_name"] == "abc001"
        assert result["problem_name"] == "a"
        assert result["problem_id"] == "a"  # 互換性
        assert result["env_type"] == "test"
    
    def test_with_env_json(self):
        """env_json付きのフォーマット辞書の生成"""
        env_json = {
            "python": {
                "contest_current_path": "/custom/current",
                "contest_stock_path": "/custom/stock",
                "contest_template_path": "/custom/template/{language_name}",
                "contest_temp_path": "/custom/temp",
                "workspace_path": "/custom/workspace",
                "language_id": "py3",
                "source_file_name": "solution.py"
            }
        }
        
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json=env_json
        )
        
        result = create_format_dict(data)
        
        assert result["contest_current_path"] == "/custom/current"
        assert result["contest_stock_path"] == "/custom/stock"
        assert result["contest_template_path"] == "/custom/template/{language_name}"
        assert result["contest_temp_path"] == "/custom/temp"
        assert result["workspace_path"] == "/custom/workspace"
        assert result["language_id"] == "py3"
        assert result["source_file_name"] == "solution.py"
        assert result["language_name"] == "python"
    
    def test_missing_language_in_env_json(self):
        """env_jsonに言語が存在しない場合"""
        env_json = {
            "rust": {
                "language_id": "rust"
            }
        }
        
        data = ExecutionFormatData(
            command_type="test",
            language="python",  # env_jsonにない言語
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json=env_json
        )
        
        result = create_format_dict(data)
        
        # 基本的な値のみが含まれることを確認
        assert "language_id" not in result
        assert "source_file_name" not in result


class TestFormatTemplateString:
    """format_template_string関数のテスト"""
    
    def test_simple_format(self):
        """シンプルなテンプレートのフォーマット"""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={}
        )
        
        template = "{contest_name}/{problem_name}"
        result, missing_keys = format_template_string(template, data)
        
        assert result == "abc001/a"
        assert len(missing_keys) == 0
    
    def test_with_missing_keys(self):
        """存在しないキーを含むテンプレート"""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={}
        )
        
        template = "{contest_name}/{problem_name}/{unknown_key}"
        result, missing_keys = format_template_string(template, data)
        
        assert result == "abc001/a/{unknown_key}"
        assert "unknown_key" in missing_keys
    
    def test_complex_template(self):
        """複雑なテンプレートのフォーマット"""
        env_json = {
            "python": {
                "contest_current_path": "./contest_current",
                "source_file_name": "main.py"
            }
        }
        
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json=env_json
        )
        
        template = "{contest_current_path}/{contest_name}/{problem_name}/{source_file_name}"
        result, missing_keys = format_template_string(template, data)
        
        assert result == "./contest_current/abc001/a/main.py"
        assert len(missing_keys) == 0


class TestValidateExecutionData:
    """validate_execution_data関数のテスト"""
    
    def test_valid_data(self):
        """有効なデータの検証"""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={"python": {}}
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is True
        assert error is None
    
    def test_missing_command_type(self):
        """command_typeが欠けている場合"""
        data = ExecutionFormatData(
            command_type="",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={}
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is False
        assert error == "command_type is required"
    
    def test_missing_language(self):
        """languageが欠けている場合"""
        data = ExecutionFormatData(
            command_type="test",
            language="",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={}
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is False
        assert error == "language is required"
    
    def test_language_not_in_env_json(self):
        """言語がenv_jsonに存在しない場合"""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={"rust": {}}  # pythonがない
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is False
        assert error == "Language 'python' not found in env_json"


class TestGetDockerNamingFromData:
    """get_docker_naming_from_data関数のテスト"""
    
    def test_without_dockerfile_content(self):
        """Dockerfileコンテンツなしの場合"""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={}
        )
        
        result = get_docker_naming_from_data(data)
        
        assert "image_name" in result
        assert "container_name" in result
        assert "oj_image_name" in result
        assert "oj_container_name" in result
        assert "python" in result["container_name"]
    
    def test_with_dockerfile_content(self):
        """Dockerfileコンテンツありの場合"""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={}
        )
        
        dockerfile_content = "FROM python:3.9\nRUN pip install numpy"
        oj_dockerfile_content = "FROM python:3.9\nRUN pip install online-judge-tools"
        
        result = get_docker_naming_from_data(
            data,
            dockerfile_content=dockerfile_content,
            oj_dockerfile_content=oj_dockerfile_content
        )
        
        assert "image_name" in result
        assert "container_name" in result
        assert "oj_image_name" in result
        assert "oj_container_name" in result
        # Dockerfileコンテンツがある場合はハッシュが含まれる
        assert len(result["image_name"]) > len("cph-python-")


class TestPureFunctionProperties:
    """純粋関数の性質をテスト"""
    
    def test_deterministic(self):
        """同じ入力に対して同じ出力を返すこと"""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json={"python": {"language_id": "py3"}}
        )
        
        # 複数回実行して同じ結果が返ることを確認
        result1 = create_format_dict(data)
        result2 = create_format_dict(data)
        result3 = create_format_dict(data)
        
        assert result1 == result2 == result3
    
    def test_no_side_effects(self):
        """副作用がないことを確認"""
        original_env_json = {"python": {"language_id": "py3"}}
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="test",
            env_json=original_env_json
        )
        
        # 関数実行
        create_format_dict(data)
        
        # 元のデータが変更されていないことを確認
        assert original_env_json == {"python": {"language_id": "py3"}}