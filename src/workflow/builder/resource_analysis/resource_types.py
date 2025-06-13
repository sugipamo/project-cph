"""リソース分析の型定義

リソース情報を表現する不変データ構造
"""
from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class ResourceInfo:
    """ステップのリソース情報を表現する不変データ構造
    
    Attributes:
        creates_files: 作成するファイルのセット
        creates_dirs: 作成するディレクトリのセット
        reads_files: 読み取るファイルのセット
        requires_dirs: 必要とするディレクトリのセット
    """
    creates_files: Set[str]
    creates_dirs: Set[str]
    reads_files: Set[str]
    requires_dirs: Set[str]
    
    @classmethod
    def empty(cls) -> 'ResourceInfo':
        """空のリソース情報を作成"""
        return cls(
            creates_files=set(),
            creates_dirs=set(),
            reads_files=set(),
            requires_dirs=set()
        )
    
    def merge(self, other: 'ResourceInfo') -> 'ResourceInfo':
        """他のリソース情報とマージして新しいインスタンスを作成"""
        return ResourceInfo(
            creates_files=self.creates_files | other.creates_files,
            creates_dirs=self.creates_dirs | other.creates_dirs,
            reads_files=self.reads_files | other.reads_files,
            requires_dirs=self.requires_dirs | other.requires_dirs
        )