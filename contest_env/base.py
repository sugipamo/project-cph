"""
このファイルは言語環境拡張用の基底クラスです。
独自の言語環境やバージョンを追加したい場合は、このクラスを継承して実装してください。
例: class MyLangHandler(BaseTestHandler): ...
"""
# 以下、元のbase.pyの内容をそのまま移動
import os
from src.execution_env.profiles import get_profile
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.language_env.constants import CONTAINER_WORKSPACE
from src.language_env.execution_command_builder import ExecutionCommandBuilder
from src.input_data_loader import InputDataLoader
from src.test_result_parser import TestResultParser

class BaseTestHandler:
    def __init__(self, language, env_type):
        self.profile = get_profile(language, env_type)
        self.config = self.profile.language_config
        self.env_config = self.profile.env_config
        self.command_builder = ExecutionCommandBuilder(self.config)

    def prepare_environment(self, *args, **kwargs):
        pass

    def build_command(self, temp_source_path):
        return self.command_builder.build_command(temp_source_path)

    def get_bin_path(self, temp_source_path):
        return temp_source_path

    def run_command(self, temp_source_path):
        bin_path = self.get_bin_path(temp_source_path)
        return self.command_builder.run_command(temp_source_path, bin_path=bin_path)

    def get_build_cwd(self, source_path):
        return os.path.dirname(source_path)

    def get_run_cwd(self, source_path):
        return os.path.dirname(source_path)

    def to_container_path(self, host_path):
        return host_path

    def to_host_path(self, container_path):
        return container_path

    def run(self, exec_client, container, in_file, source_path, artifact_path=None, host_in_file=None, file_operator=None):
        cont_in_file = self.to_container_path(in_file)
        cont_source_path = self.to_container_path(source_path)
        run_cmd = self.run_command(cont_source_path)
        if not run_cmd or run_cmd == ["None"]:
            return False, "", "実行ファイルが見つかりません (run_cmdがNone)"
        host_in_file_path = self.to_host_path(cont_in_file)
        input_data = InputDataLoader.load(file_operator, host_in_file, host_in_file_path)
        run_cwd = self.get_run_cwd(cont_source_path)
        result = exec_client.run_and_measure(container, run_cmd, cwd=run_cwd, input=input_data, image=self.profile.language)
        return TestResultParser.parse(result)

    def build(self, exec_client, container, source_path):
        cmd = self.build_command(self.to_container_path(source_path))
        if cmd is None:
            return True, '', ''
        build_cwd = self.get_build_cwd(self.to_container_path(source_path))
        image = self.profile.language
        result = exec_client.run_and_measure(container, cmd, cwd=build_cwd, image=image)
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr

class LocalTestHandler(BaseTestHandler):
    pass

class ContainerTestHandler(BaseTestHandler):
    def __init__(self, language, env_type):
        super().__init__(language, env_type)
        project_root = getattr(self.env_config, 'host_project_root', None)
        container_root = getattr(self.env_config, 'workspace_dir', CONTAINER_WORKSPACE)
        mounts = getattr(self.env_config, 'mounts', None)
        self.upm = UnifiedPathManager(project_root, container_root, mounts=mounts)

    def run(self, exec_client, container, in_file, source_path, artifact_path=None, host_in_file=None, file_operator=None):
        cont_in_file = self.upm.to_container_path(os.path.abspath(str(in_file)))
        cont_source_path = self.upm.to_container_path(os.path.abspath(str(source_path)))
        run_cmd = self.run_command(cont_source_path)
        if not run_cmd or run_cmd == ["None"]:
            return False, "", "実行ファイルが見つかりません (run_cmdがNone)"
        host_in_file_path = self.upm.to_host_path(cont_in_file)
        input_data = InputDataLoader.load(file_operator, host_in_file, host_in_file_path)
        run_cwd = self.get_run_cwd(cont_source_path)
        result = exec_client.run_and_measure(container, run_cmd, cwd=run_cwd, input=input_data, image=self.profile.language)
        return TestResultParser.parse(result)

    def build(self, exec_client, container, source_path):
        cont_source_path = self.upm.to_container_path(os.path.abspath(str(source_path)))
        cmd = self.build_command(cont_source_path)
        if cmd is None:
            return True, '', ''
        build_cwd = self.get_build_cwd(cont_source_path)
        image = self.profile.language
        result = exec_client.run_and_measure(container, cmd, cwd=build_cwd, image=image)
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr 