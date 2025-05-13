import os
from src.execution_env.execution_env_config import ExecutionEnvConfig

def test_default_values():
    config = ExecutionEnvConfig(type='docker')
    assert config.type == 'docker'
    assert config.image is None
    assert config.mounts == []
    assert config.env_vars == {}
    assert config.temp_dir == '.temp'
    assert config.workspace_dir == './workspace'
    assert os.path.isabs(config.host_project_root)

def test_custom_values():
    config = ExecutionEnvConfig(
        type='local',
        image='img',
        mounts=['/a:/b'],
        env_vars={'A': 'B'},
        temp_dir='/tmp',
        workspace_dir='/ws',
        host_project_root='/root/project'
    )
    assert config.type == 'local'
    assert config.image == 'img'
    assert config.mounts == ['/a:/b']
    assert config.env_vars == {'A': 'B'}
    assert config.temp_dir == '/tmp'
    assert config.workspace_dir == '/ws'
    assert config.host_project_root == '/root/project' 