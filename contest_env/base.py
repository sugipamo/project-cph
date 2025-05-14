"""
このファイルは言語環境拡張用の基底クラスです。
独自の言語環境やバージョンを追加したい場合は、このクラスを継承して実装してください。
例: class MyLangHandler(BaseTestHandler): ...

【拡張時の注意】
- run, buildメソッドは必ず継承先で実装してください。
- DockerTestHandlerを使う場合、language_nameプロパティを必ず設定してください。
- run_cmdや各種パスはプロパティで上書き可能です。
- 必要に応じてプロパティやメソッドを追加・オーバーライドしてください。
- ABC（抽象基底クラス）を使うことで、未実装メソッドの検出が容易になります。
"""
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from abc import ABC, abstractmethod

@dataclass
class BaseTestHandler(ABC):
    contest_current_path: Path = Path("./contest_current")
    contest_env_path: Path = Path("./contest_env")
    contest_template_path: Path = Path("./contest_template")
    contest_temp_path: Path = Path("./.temp")
    source_file: Optional[str] = None
    time_limit: Optional[int] = None
    run_cmd: Optional[str] = None

@dataclass
class LocalTestHandler(BaseTestHandler):
    @property
    def run_cmd(self):
        return self.__dict__["run_cmd"]
    
    @property
    def contest_current_path(self):
        return self.__dict__["contest_current_path"]
    
    @property
    def contest_env_path(self):
        return self.__dict__["contest_env_path"]
    
    @property
    def contest_template_path(self):
        return self.__dict__["contest_template_path"]
    
    @property
    def contest_temp_path(self):
        return self.__dict__["contest_temp_path"]
    
    @property
    def source_file_path(self):
        return self.contest_current_path / self.source_file
    
    @property
    def test_case_path(self):
        return self.contest_current_path / "test"
    
    @property
    def test_case_in_path(self):
        return self.test_case_path / "in"
    
    @property
    def test_case_out_path(self):
        return self.test_case_path / "out"

    @abstractmethod
    def run(self):
        """テスト実行処理を実装してください（必須）"""
        pass

    @abstractmethod
    def build(self):
        """ビルド処理を実装してください（必須）"""
        pass
    
    @abstractmethod
    def get_language_name(self):
        """言語名を返すメソッドを実装してください（必須）"""
        pass

@dataclass
class DockerTestHandler(BaseTestHandler):
    container_workspace: str = "/workspace"
    memory_limit: Optional[int] = None
    
    def _to_container_path(self, path):
        """
        ホスト側のパスをコンテナ内のパス（/workspace からの相対パス）に変換します。
        例: ./contest_current/foo.txt → /workspace/contest_current/foo.txt
        """
        path = Path(path).resolve()
        root = Path(".").resolve()
        rel_path = path.relative_to(root)
        return Path(self.container_workspace) / rel_path

    @property
    def run_cmd(self):
        return self.__dict__["run_cmd"]
    
    @property
    def contest_current_path(self):
        return self._to_container_path(self.__dict__["contest_current_path"])
    
    @property
    def contest_env_path(self):
        return self._to_container_path(self.__dict__["contest_env_path"])
    
    @property
    def contest_template_path(self):
        return self._to_container_path(self.__dict__["contest_template_path"])
    
    @property
    def contest_temp_path(self):
        return self._to_container_path(self.__dict__["contest_temp_path"])
    
    @property
    def source_file_path(self):
        return self.contest_current_path / self.source_file
    
    @property
    def test_case_path(self):
        return self.contest_current_path / "test"
    
    @property
    def test_case_in_path(self):
        return self.test_case_path / "in"
    
    @property
    def test_case_out_path(self):
        return self.test_case_path / "out"

    @property
    def mount_point(self):
        return self.__dict__["contest_current_path"].resolve()

    @property
    def dockerfile_path(self):
        # language_nameが未設定の場合はエラーになるので注意
        return self.__dict__["contest_env_path"] / self.__dict__["language_name"] / "Dockerfile"
    
    @abstractmethod
    def run(self):
        """テスト実行処理を実装してください（必須）"""
        pass

    @abstractmethod
    def build(self):
        """ビルド処理を実装してください（必須）"""
        pass

    @abstractmethod
    def get_language_name(self):
        """言語名を返すメソッドを実装してください（必須）"""
        pass