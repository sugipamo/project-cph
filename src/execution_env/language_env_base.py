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

    @abstractmethod
    def run(self):
        """テスト実行処理を実装してください（必須）"""
        pass
    @abstractmethod
    def build(self):
        """ビルド処理を実装してください（必須）"""
        pass

@dataclass
class LocalTestHandler(BaseTestHandler):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def build(self):
        pass

@dataclass
class DockerTestHandler(BaseTestHandler):
    container_workspace: str = "/workspace"
    memory_limit: Optional[int] = None

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def build(self):
        pass