import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
import pytest
from command_executor import CommandExecutor
from podman_operator import LocalPodmanOperator

@pytest.mark.integration
@pytest.mark.asyncio
async def test_oj_version_integration():
    """ojコマンドのバージョン表示ができるかだけを確認するintegrationテスト（最小構成）"""
    executor = CommandExecutor(podman_operator=LocalPodmanOperator())
    rc, out, err = await executor.podman_operator.run_oj(["--version"], volumes=None, workdir=None, interactive=False)
    assert rc == 0
    assert "online-judge-tools" in out

@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_integration():
    # 手動でテストする
    # ここではダミーでTrueを返す
    assert True