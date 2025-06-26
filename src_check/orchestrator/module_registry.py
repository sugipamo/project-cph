"""
モジュールレジストリ - チェック可能なモジュールの登録と管理
"""

from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import importlib.util
import sys


@dataclass
class CheckModule:
    """チェックモジュールの情報"""
    name: str
    path: Path
    priority: int = 0  # 実行優先度（低い値が先）
    enabled: bool = True
    
    def __lt__(self, other):
        """優先度と名前でソート"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.name < other.name


class ModuleRegistry:
    """チェックモジュールのレジストリ"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.modules: Dict[str, CheckModule] = {}
        self._discover_modules()
    
    def _discover_modules(self):
        """processorsディレクトリ内のmain.pyを持つモジュールを探索"""
        processors_path = self.base_path / "processors"
        
        # auto_correct配下のモジュール
        auto_correct_path = processors_path / "auto_correct"
        if auto_correct_path.exists():
            for module_dir in auto_correct_path.iterdir():
                if module_dir.is_dir() and (module_dir / "main.py").exists():
                    module_name = module_dir.name
                    self.modules[module_name] = CheckModule(
                        name=module_name,
                        path=module_dir / "main.py",
                        priority=10  # auto_correctは優先度10
                    )
        
        # rules配下のチェッカー
        rules_path = processors_path / "rules"
        if rules_path.exists():
            for checker_file in rules_path.glob("*_checker.py"):
                module_name = checker_file.stem
                self.modules[module_name] = CheckModule(
                    name=module_name,
                    path=checker_file,
                    priority=20  # rulesは優先度20
                )
    
    def get_modules_sorted(self, reverse: bool = False) -> List[CheckModule]:
        """ソート済みのモジュールリストを取得"""
        modules = [m for m in self.modules.values() if m.enabled]
        return sorted(modules, reverse=reverse)
    
    def get_module(self, name: str) -> Optional[CheckModule]:
        """特定のモジュールを取得"""
        return self.modules.get(name)
    
    def disable_module(self, name: str):
        """モジュールを無効化"""
        if name in self.modules:
            self.modules[name].enabled = False
    
    def enable_module(self, name: str):
        """モジュールを有効化"""
        if name in self.modules:
            self.modules[name].enabled = True