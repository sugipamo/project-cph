"""統一設定ソース - すべての設定情報の集約"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class ConfigurationSource:
    """統一設定ソース - すべての設定情報の集約"""
    system: Dict[str, Any]      # config/system/*.json
    shared: Dict[str, Any]      # contest_env/shared/env.json  
    language: Dict[str, Any]    # contest_env/{lang}/env.json
    runtime: Dict[str, Any]     # コマンドライン + SQLite
    
    def get_merged_config(self) -> Dict[str, Any]:
        """優先順位に従って設定をマージ
        
        優先順位: runtime > language > shared > system
        
        Returns:
            マージされた設定辞書
        """
        result = {}
        
        # 最低優先度から順にマージ
        for config in [self.system, self.shared, self.language, self.runtime]:
            result = self._deep_merge(result, config)
        
        return result
    
    def _deep_merge(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """深いマージを実行"""
        result = base_dict.copy()
        
        for key, value in update_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result