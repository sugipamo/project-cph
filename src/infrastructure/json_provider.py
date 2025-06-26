"""JSONプロバイダー - 副作用を集約"""
from abc import ABC, abstractmethod
from typing import Any, Dict


import json
import os
class JsonProvider(ABC):
    """JSON操作の抽象インターフェース"""

    @abstractmethod
    def dumps(self, data: Any, **kwargs) -> str:
        """オブジェクトをJSON文字列に変換"""
        pass

    @abstractmethod
    def loads(self, s: str, **kwargs) -> Any:
        """JSON文字列をオブジェクトに変換"""
        pass

    @abstractmethod
    def dump(self, data: Any, fp, **kwargs) -> None:
        """オブジェクトをファイルにJSON形式で書き込み"""
        pass

    @abstractmethod
    def load(self, fp, **kwargs) -> Any:
        """ファイルからJSONを読み込み"""
        pass


class SystemJsonProvider(JsonProvider):
    """システムJSON操作の実装 - 副作用はここに集約"""

    def dumps(self, data: Any, **kwargs) -> str:
        """オブジェクトをJSON文字列に変換（副作用なし）"""
        return json.dumps(data, **kwargs)

    def loads(self, s: str, **kwargs) -> Any:
        """JSON文字列をオブジェクトに変換（副作用なし）"""
        return json.loads(s, **kwargs)

    def dump(self, data: Any, fp, **kwargs) -> None:
        """オブジェクトをファイルにJSON形式で書き込み（副作用）"""
        json.dump(data, fp, **kwargs)

    def load(self, fp, **kwargs) -> Any:
        """ファイルからJSONを読み込み（副作用）"""
        return json.load(fp, **kwargs)


class MockJsonProvider(JsonProvider):
    """テスト用モックJSONプロバイダー - 副作用なし"""

    def __init__(self):
        self._mock_data: Dict[str, Any] = {}

    def dumps(self, data: Any, **kwargs) -> str:
        """モックJSON文字列変換（副作用なし）"""
        # 実際のJSON変換を使用してテストの正確性を保つ
        return json.dumps(data, **kwargs)

    def loads(self, s: str, **kwargs) -> Any:
        """モックJSON読み込み（副作用なし）"""
        # 簡単なモック実装
        return json.loads(s)  # Let JSON exceptions propagate

    def dump(self, data: Any, fp, **kwargs) -> None:
        """モックファイル書き込み（副作用なし）"""
        # ファイルパスをキーとして内部辞書に保存
        if hasattr(fp, 'name'):
            self._mock_data[fp.name] = data

    def load(self, fp, **kwargs) -> Any:
        """モックファイル読み込み（副作用なし）"""
        # ファイルパスをキーとして内部辞書から取得
        if hasattr(fp, 'name') and fp.name in self._mock_data:
            return self._mock_data[fp.name]

        # パスの正規化バリアント確認
        if hasattr(fp, 'name'):
            normalized_path = os.path.normpath(fp.name)
            for mock_path in self._mock_data:
                if os.path.normpath(mock_path) == normalized_path:
                    return self._mock_data[mock_path]

        # テスト環境では実際のファイルも読み込めるように
        return json.load(fp, **kwargs)  # エラーは呼び出し元に委譲

    def add_mock_data(self, key: str, data: Any) -> None:
        """テスト用データ追加"""
        self._mock_data[key] = data
