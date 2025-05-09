import pytest
from unittest.mock import patch, MagicMock
import sys

import src.execution_client.container.oj_build as oj_build

def test_build_ojtools_image_dockerfile_not_found(capsys):
    with patch("os.path.exists", return_value=False):
        with pytest.raises(SystemExit):
            oj_build.build_ojtools_image()
        captured = capsys.readouterr()
        assert "Dockerfile not found" in captured.out

def test_build_ojtools_image_success(capsys):
    with patch("os.path.exists", return_value=True):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            oj_build.build_ojtools_image()
            captured = capsys.readouterr()
            assert "[OK] Built" in captured.out

def test_build_ojtools_image_failure(capsys):
    with patch("os.path.exists", return_value=True):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            oj_build.build_ojtools_image()
            captured = capsys.readouterr()
            assert "[ERROR] Build failed" in captured.out 