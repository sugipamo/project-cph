"""
設定管理
JSON設定ファイルによる動作制御
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

@dataclass
class ReorganizerConfig:
    """依存関係整理ツールの設定"""
    
    # 基本設定
    max_file_count: int = 250
    max_depth: int = 5
    execute_mode: bool = False
    dry_run: bool = True
    
    # 解析設定
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__",
        "*.pyc",
        ".git",
        ".pytest_cache",
        "*.egg-info"
    ])
    include_test_files: bool = False
    exclude_type_checking: bool = True
    
    # 移動設定
    create_init_files: bool = True
    cleanup_empty_dirs: bool = True
    preserve_structure_for: List[str] = field(default_factory=lambda: [
        "__init__.py",
        "conftest.py"
    ])
    
    # フォルダ名マッピング
    depth_folder_mapping: Dict[int, str] = field(default_factory=lambda: {
        0: "",  # ルートに残す
        1: "core",
        2: "services", 
        3: "handlers",
        4: "controllers",
        5: "app"
    })
    
    # カスタムフォルダ名規則
    folder_name_patterns: Dict[str, str] = field(default_factory=lambda: {
        "*_manager": "{name}_mgmt",
        "*_service": "{name}_svc",
        "*_handler": "{name}_hdlr",
        "*_controller": "{name}_ctrl",
        "*_processor": "{name}_proc",
        "config*": "configuration",
        "util*": "utilities"
    })
    
    # バックアップ設定
    use_git_backup: bool = True
    backup_dir_name: str = "backup_reorganize_{timestamp}"
    
    # ログ設定
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_name: str = "reorganizer_{timestamp}.log"
    verbose: bool = False
    
    # 検証設定
    validate_syntax: bool = True
    validate_imports: bool = True
    run_tests_after: bool = False
    test_command: str = "pytest"
    
    # エラーハンドリング
    stop_on_first_error: bool = False
    ignore_circular_deps: bool = False
    max_errors_to_show: int = 10
    
    # グラフ生成
    generate_graph: bool = False
    graph_formats: List[str] = field(default_factory=lambda: [
        "dot", "mermaid", "json", "ascii", "html"
    ])
    
    @classmethod
    def from_file(cls, config_path: Path) -> "ReorganizerConfig":
        """JSONファイルから設定を読み込み"""
        if not config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # データクラスのフィールドに合わせて変換
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)
    
    def to_file(self, config_path: Path) -> None:
        """設定をJSONファイルに保存"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
    
    def validate(self) -> List[str]:
        """設定の妥当性を検証"""
        errors = []
        
        if self.max_file_count < 1:
            errors.append("max_file_count は1以上である必要があります")
        
        if self.max_depth < 1:
            errors.append("max_depth は1以上である必要があります")
        
        if self.execute_mode and self.dry_run:
            errors.append("execute_mode と dry_run は同時にTrueにできません")
        
        if not self.depth_folder_mapping:
            errors.append("depth_folder_mapping が空です")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level は {valid_log_levels} のいずれかである必要があります")
        
        return errors
    
    def get_folder_for_depth(self, depth: int) -> str:
        """深度に対応するフォルダ名を取得"""
        # 直接マッピングがある場合
        if depth in self.depth_folder_mapping:
            return self.depth_folder_mapping[depth]
        
        # 最大深度を超えた場合
        max_mapped_depth = max(self.depth_folder_mapping.keys())
        if depth > max_mapped_depth:
            base_folder = self.depth_folder_mapping.get(max_mapped_depth, "deep")
            return f"{base_folder}/level_{depth - max_mapped_depth}"
        
        return ""
    
    def get_custom_folder_name(self, file_name: str) -> Optional[str]:
        """ファイル名からカスタムフォルダ名を生成"""
        import fnmatch
        
        for pattern, template in self.folder_name_patterns.items():
            if fnmatch.fnmatch(file_name, pattern):
                # テンプレート内の{name}を置換
                name = file_name
                for suffix in ["_manager", "_service", "_handler", "_controller", "_processor"]:
                    if name.endswith(suffix):
                        name = name[:-len(suffix)]
                        break
                
                return template.format(name=name)
        
        return None
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """ファイルを除外すべきか判定"""
        import fnmatch
        
        # ファイル名チェック
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        
        # パスの一部に除外パターンが含まれるかチェック
        for part in file_path.parts:
            for pattern in self.exclude_patterns:
                if fnmatch.fnmatch(part, pattern):
                    return True
        
        # テストファイルの除外
        if not self.include_test_files:
            if "test" in file_path.name.lower() or "test" in str(file_path).lower():
                return True
        
        return False


def create_default_config() -> ReorganizerConfig:
    """デフォルト設定を作成"""
    return ReorganizerConfig()


def save_example_config(output_path: Path) -> None:
    """サンプル設定ファイルを生成"""
    config = create_default_config()
    
    # コメント付きのサンプル設定
    example_data = {
        "_comment": "依存関係ベースフォルダ構造整理ツールの設定ファイル",
        "max_file_count": config.max_file_count,
        "max_depth": config.max_depth,
        "execute_mode": config.execute_mode,
        "dry_run": config.dry_run,
        
        "_comment_analysis": "解析設定",
        "exclude_patterns": config.exclude_patterns,
        "include_test_files": config.include_test_files,
        "exclude_type_checking": config.exclude_type_checking,
        
        "_comment_move": "移動設定",
        "create_init_files": config.create_init_files,
        "cleanup_empty_dirs": config.cleanup_empty_dirs,
        "preserve_structure_for": config.preserve_structure_for,
        
        "_comment_folders": "深度別フォルダマッピング",
        "depth_folder_mapping": config.depth_folder_mapping,
        
        "_comment_custom": "カスタムフォルダ名規則 (*はワイルドカード)",
        "folder_name_patterns": config.folder_name_patterns,
        
        "_comment_backup": "バックアップ設定",
        "use_git_backup": config.use_git_backup,
        "backup_dir_name": config.backup_dir_name,
        
        "_comment_log": "ログ設定",
        "log_level": config.log_level,
        "log_to_file": config.log_to_file,
        "log_file_name": config.log_file_name,
        "verbose": config.verbose,
        
        "_comment_validation": "検証設定",
        "validate_syntax": config.validate_syntax,
        "validate_imports": config.validate_imports,
        "run_tests_after": config.run_tests_after,
        "test_command": config.test_command,
        
        "_comment_error": "エラーハンドリング設定",
        "stop_on_first_error": config.stop_on_first_error,
        "ignore_circular_deps": config.ignore_circular_deps,
        "max_errors_to_show": config.max_errors_to_show
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(example_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # サンプル設定ファイルを生成
    save_example_config(Path("reorganizer_config_example.json"))
    print("サンプル設定ファイルを生成しました: reorganizer_config_example.json")