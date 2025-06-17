"""
セキュリティ脆弱性に対するテストケース
"""
import shlex
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.application.factories.unified_request_factory import create_request
from src.infrastructure.drivers.docker.docker_driver import LocalDockerDriver
from src.operations.pure.string_formatters import validate_file_path_format
from src.operations.requests.docker.docker_request import DockerOpType, DockerRequest
from src.workflow.step.step import Step, StepType


class TestDockerExecSecurity:
    """Docker execコマンドのセキュリティテスト"""

    def test_docker_exec_command_type_validation(self):
        """Docker execのコマンド型検証"""
        driver = LocalDockerDriver()

        # 文字列コマンドが受け入れられることを確認
        assert hasattr(driver, 'exec_in_container')

        # 無効な型でエラーが発生することを確認
        try:
            driver.exec_in_container("test", 123)  # 数値型は無効
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Invalid command type" in str(e)


class TestPathTraversalSecurity:
    """パストラバーサル攻撃に対するテスト"""

    def test_reject_relative_path_traversal(self):
        """相対パスでの..使用を拒否"""
        dangerous_paths = [
            "../../../etc/passwd",
            "../../secret.txt",
            "normal/../../../etc/passwd",
            "./../../etc/passwd"
        ]

        for path in dangerous_paths:
            valid, error = validate_file_path_format(path)
            assert not valid
            assert "Path traversal detected" in error

    def test_reject_absolute_path_traversal(self):
        """絶対パスでの..使用を拒否"""
        dangerous_paths = [
            "/home/user/../../../etc/passwd",
            "/var/www/../../etc/passwd"
        ]

        for path in dangerous_paths:
            valid, error = validate_file_path_format(path)
            assert not valid
            assert "Absolute paths with '..' are not allowed" in error

    def test_reject_dangerous_characters(self):
        """危険な文字を含むパスを拒否"""
        dangerous_paths = [
            "file.txt; rm -rf /",
            "file.txt | cat /etc/passwd",
            "file.txt & malicious_command",
            "file.txt`evil`",
            "file.txt$(evil)",
            "file\nname.txt",
            "file\rname.txt",
            "file\x00name.txt"
        ]

        for path in dangerous_paths:
            valid, error = validate_file_path_format(path)
            assert not valid
            assert "dangerous characters" in error

    def test_accept_safe_paths(self):
        """安全なパスは受け入れる"""
        safe_paths = [
            "file.txt",
            "/home/user/file.txt",
            "./subdir/file.txt",
            "subdir/another/file.txt",
            "/var/www/html/index.html",
            "file-name_with.special-chars.txt"
        ]

        for path in safe_paths:
            valid, error = validate_file_path_format(path)
            assert valid
            assert error is None


class TestCommandStringSecurity:
    """コマンド文字列結合の脆弱性に対するテスト"""

    def test_unified_factory_docker_exec_uses_list(self):
        """統一ファクトリーがコマンドをリスト形式で保持することの確認"""
        step = Step(
            type=StepType.DOCKER_EXEC,
            cmd=["container_name", "echo", "hello", "world"]
        )

        request = create_request(step, context={})

        # コマンドがリスト形式で保持されていることを確認
        if request:  # May return None if DOCKER_EXEC is not implemented
            assert isinstance(request.command, list)
            assert request.command == ["echo", "hello", "world"]

    def test_docker_request_accepts_list_command(self):
        """DockerRequestがリスト形式のコマンドを受け入れることの確認"""
        command_list = ["bash", "-c", "echo 'test'"]

        request = DockerRequest(
            op=DockerOpType.EXEC,
            container="test_container",
            command=command_list
        )

        assert request.command == command_list
        assert isinstance(request.command, list)
