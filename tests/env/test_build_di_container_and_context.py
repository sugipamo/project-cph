from src.env.build_di_container_and_context import build_di_container_and_context
class DummyEnvContext:
    pass
def test_build_di_container_and_context():
    env, di = build_di_container_and_context(DummyEnvContext())
    # 主要な依存性が登録されているか
    for key in [
        'shell_driver', 'docker_driver', 'file_driver',
        'ShellCommandRequestFactory', 'DockerCommandRequestFactory',
        'CopyCommandRequestFactory', 'OjCommandRequestFactory',
        'RemoveCommandRequestFactory', 'BuildCommandRequestFactory',
        'PythonCommandRequestFactory', 'DockerRequest', 'DockerOpType']:
        assert key in di._providers 