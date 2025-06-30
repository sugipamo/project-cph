import ast
import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from models.check_result import CheckResult, FailureLocation


@dataclass
class FileMove:
    source: Path
    destination: Path
    reason: str
    element_type: str  # 'function', 'class', 'module'
    element_name: str


@dataclass
class ImportUpdate:
    file_path: Path
    old_import: str
    new_import: str
    line_number: int


@dataclass
class RollbackInfo:
    timestamp: str
    moves: List[FileMove]
    import_updates: List[ImportUpdate]
    backup_dir: Path


class LogicalFileOrganizer:
    """論理的な構造に基づいてファイルを自動整理するツール"""
    
    # Clean Architecture準拠のカテゴリと対応するフォルダ名
    CLEAN_ARCHITECTURE_CATEGORIES = {
        # Domain Layer - ピュアなビジネスロジック、エンティティ、ドメインサービス
        'domain': {
            'patterns': ['config_node', 'base_request', 'base_composite_request', 'workflow', 'step', 'dependency'],
            'keywords': ['entity', 'domain', 'value_object', 'aggregate', 'specification'],
            'interfaces': ['interface', 'protocol'],
            'description': 'Pure business logic entities and domain services'
        },
        
        # Application Layer - アプリケーションサービス、ユースケース、オーケストレーション
        'application': {
            'patterns': ['workflow_execution_svc', 'step_generation_svc', 'config_loader_svc', 'contest_mgmt', 'debug_svc'],
            'keywords': ['service', 'execution', 'orchestrat', 'usecase', 'application', 'coordinator'],
            'suffixes': ['_svc', '_service', '_manager', '_coordinator'],
            'description': 'Application services and use case orchestration'
        },
        
        # Infrastructure Layer - 外部システム連携、永続化、デバイスドライバ
        'infrastructure': {
            'patterns': ['docker_driver', 'file_driver', 'shell_driver', 'sqlite_mgmt', 'persistence_driver',
                        'local_file_driver', 'local_shell_driver', 'unified_driver', 'python_driver',
                        'mock_docker_driver', 'mock_file_driver', 'mock_python_driver', 'mock_shell_driver',
                        'docker_driver_with_tracking', 'fast_sqlite_mgmt'],
            'keywords': ['driver', 'repository', 'adapter', 'connector', 'persistence', 'database', 'external'],
            'suffixes': ['_driver', '_repository', '_adapter', '_connector', '_provider'],
            'description': 'External system integration and data persistence'
        },
        
        # Operations Layer - 横断的関心事、インターフェース、型定義
        'operations': {
            'patterns': ['docker_request', 'file_request', 'shell_request', 'python_request', 'composite_request',
                        'docker_result', 'file_result', 'shell_result', 'workflow_result',
                        'docker_interface', 'execution_interface', 'output_manager_interface',
                        'composite_step_failure', 'error_converter', 'result_factory', 'request_factory'],
            'keywords': ['request', 'result', 'interface', 'factory', 'converter', 'exception', 'error'],
            'suffixes': ['_request', '_result', '_interface', '_factory', '_converter', '_exception'],
            'description': 'Cross-cutting concerns and interface definitions'
        },
        
        # Presentation Layer - CLI、エントリーポイント、ユーザーインターフェース
        'presentation': {
            'patterns': ['cli_app', 'main', 'context_formatter', 'context_validator', 'user_input_parser'],
            'keywords': ['cli', 'main', 'formatter', 'validator', 'parser', 'ui', 'presentation'],
            'suffixes': ['_formatter', '_validator', '_parser', '_cli'],
            'description': 'User interface and presentation logic'
        },
        
        # Utilities - ユーティリティ、ヘルパー、共通ロジック
        'utils': {
            'patterns': ['python_utils', 'path_operations', 'retry_decorator', 'time_adapter', 'sys_provider',
                        'regex_provider', 'mock_regex_provider', 'format_info'],
            'keywords': ['util', 'helper', 'common', 'shared', 'decorator', 'adapter', 'operations'],
            'suffixes': ['_utils', '_helper', '_decorator', '_adapter', '_operations', '_provider'],
            'description': 'Common utilities and helper functions'
        },
        
        # Logging - ログ関連
        'logging': {
            'patterns': ['unified_logger', 'application_logger_adapter', 'workflow_logger_adapter', 'output_mgmt', 'mock_output_mgmt'],
            'keywords': ['logger', 'logging', 'log', 'output'],
            'suffixes': ['_logger', '_adapter', '_mgmt'],
            'description': 'Logging and output management'
        },
        
        # Configuration - 設定管理（ドメイン層とは分離）
        'configuration': {
            'patterns': ['configuration', 'di_config', 'build_infrastructure', 'environment_mgmt', 'system_config_loader', 'system_config_repository'],
            'keywords': ['config', 'configuration', 'settings', 'environment', 'setup'],
            'suffixes': ['_config', '_configuration', '_settings', '_loader'],
            'description': 'Configuration management and system setup'
        },
        
        # Data Access - データアクセス層
        'data': {
            'patterns': ['docker_container_repository', 'docker_image_repository', 'operation_repository',
                        'session_repository', 'sqlite_state_repository', 'state_repository', 'base_repository'],
            'keywords': ['repository', 'dao', 'data', 'persistence', 'storage'],
            'suffixes': ['_repository', '_dao'],
            'description': 'Data access and repository patterns'
        }
    }
    
    def __init__(self, src_dir: str, dry_run: bool = True):
        self.src_dir = Path(src_dir)
        self.dry_run = dry_run
        self.file_moves: List[FileMove] = []
        self.import_updates: List[ImportUpdate] = []
        self.rollback_info: Optional[RollbackInfo] = None
        
    def organize(self) -> Tuple[List[FileMove], List[ImportUpdate]]:
        """ファイルを論理的に整理"""
        print(f"🔍 ファイル整理を{'シミュレーション' if self.dry_run else '実行'}します: {self.src_dir}")
        
        # 1. 現在の構造を分析
        self._analyze_current_structure()
        
        # 2. 論理的な移動計画を作成
        self._create_move_plan()
        
        # 3. インポート更新計画を作成
        self._create_import_update_plan()
        
        # 4. 実行またはシミュレーション
        if not self.dry_run:
            self._execute_organization()
        else:
            self._show_simulation()
            
        return self.file_moves, self.import_updates
        
    def _analyze_current_structure(self) -> None:
        """現在のファイル構造を分析"""
        print("\n📊 現在の構造を分析中...")
        
        for py_file in self.src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or "_test.py" in str(py_file):
                continue
                
            logical_category = self._determine_logical_category(py_file)
            if logical_category:
                ideal_path = self._get_ideal_path(py_file, logical_category)
                
                if ideal_path != py_file:
                    move = FileMove(
                        source=py_file,
                        destination=ideal_path,
                        reason=f"{logical_category}カテゴリに属するため",
                        element_type=self._get_element_type(py_file),
                        element_name=py_file.stem
                    )
                    self.file_moves.append(move)
                    
    def _determine_logical_category(self, file_path: Path) -> Optional[str]:
        """ファイルの論理的カテゴリをClean Architecture準拠で判定"""
        file_name = file_path.stem.lower()
        parent_dir = file_path.parent.name.lower()
        
        # 1. パターンマッチングによる判定（最優先）
        for category, config in self.CLEAN_ARCHITECTURE_CATEGORIES.items():
            if 'patterns' in config:
                for pattern in config['patterns']:
                    if pattern in file_name or pattern in parent_dir:
                        return category
        
        # 2. ファイル名のサフィックスによる判定
        for category, config in self.CLEAN_ARCHITECTURE_CATEGORIES.items():
            if 'suffixes' in config:
                for suffix in config['suffixes']:
                    if file_name.endswith(suffix):
                        return category
        
        # 3. キーワードによる判定
        for category, config in self.CLEAN_ARCHITECTURE_CATEGORIES.items():
            if 'keywords' in config:
                for keyword in config['keywords']:
                    if keyword in file_name:
                        return category
        
        # 4. ファイル内容（クラス名、インポート）による判定
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # インポート文から依存関係を分析
            category_from_imports = self._analyze_imports_for_category(content)
            if category_from_imports:
                return category_from_imports
                
            # クラス名から判定
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name.lower()
                    for category, config in self.CLEAN_ARCHITECTURE_CATEGORIES.items():
                        if 'keywords' in config:
                            for keyword in config['keywords']:
                                if keyword in class_name:
                                    return category
                                    
        except Exception:
            pass
            
        return None
    
    def _analyze_imports_for_category(self, content: str) -> Optional[str]:
        """インポート文から適切なカテゴリを推定（依存関係分析強化版）"""
        lines = content.split('\n')
        import_score = defaultdict(int)
        
        # 各カテゴリの特徴的なインポートパターンとスコア
        category_patterns = {
            'infrastructure': {
                'patterns': ['docker', 'container', 'image', 'shell', 'subprocess', 'pathlib', 'shutil', 'os.path'],
                'score': 3
            },
            'data': {
                'patterns': ['sqlite', 'database', 'db', 'repository', 'persistence', 'storage'],
                'score': 3
            },
            'logging': {
                'patterns': ['logging', 'logger', 'log', 'output', 'debug'],
                'score': 2
            },
            'presentation': {
                'patterns': ['argparse', 'click', 'cli', 'command', 'sys.argv', 'main'],
                'score': 3
            },
            'application': {
                'patterns': ['workflow', 'execution', 'service', 'orchestrat', 'coordinator'],
                'score': 2
            },
            'domain': {
                'patterns': ['entity', 'value', 'specification', 'aggregate', 'domain'],
                'score': 2
            },
            'operations': {
                'patterns': ['request', 'result', 'interface', 'protocol', 'factory', 'abc'],
                'score': 2
            },
            'utils': {
                'patterns': ['util', 'helper', 'common', 'decorator', 'typing', 'datetime'],
                'score': 1
            }
        }
        
        # インポート文を解析してスコアを計算
        for line in lines:
            line = line.strip()
            if line.startswith(('import ', 'from ')):
                line_lower = line.lower()
                
                # 各カテゴリのパターンをチェック
                for category, config in category_patterns.items():
                    for pattern in config['patterns']:
                        if pattern in line_lower:
                            import_score[category] += config['score']
                
                # 特別なパターン分析
                if 'src.infrastructure' in line:
                    import_score['application'] += 2  # infrastructureを使う→application層
                elif 'src.operations' in line:
                    import_score['application'] += 1  # operationsを使う→application層
                elif 'abc.ABC' in line or 'Protocol' in line:
                    import_score['operations'] += 2  # インターフェース定義
                elif 'from typing import' in line:
                    import_score['operations'] += 1  # 型定義
        
        # 最もスコアが高いカテゴリを返す
        if import_score:
            best_category = max(import_score.items(), key=lambda x: x[1])
            if best_category[1] >= 2:  # 閾値以上のスコアがある場合のみ
                return best_category[0]
        
        return None
    
    def _analyze_dependency_relationships(self, file_path: Path, content: str) -> dict:
        """ファイルの依存関係を分析してより詳細な分類情報を取得"""
        dependencies = {
            'imports_infrastructure': False,
            'imports_domain': False,
            'imports_application': False,
            'imports_operations': False,
            'defines_interfaces': False,
            'contains_business_logic': False,
            'contains_external_calls': False
        }
        
        lines = content.split('\n')
        
        # インポート分析
        for line in lines:
            line = line.strip()
            if line.startswith(('import ', 'from ')):
                if 'src.infrastructure' in line:
                    dependencies['imports_infrastructure'] = True
                elif 'src.domain' in line or 'src.core' in line:
                    dependencies['imports_domain'] = True
                elif 'src.application' in line:
                    dependencies['imports_application'] = True
                elif 'src.operations' in line:
                    dependencies['imports_operations'] = True
        
        # コード内容分析
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                # インターフェース定義チェック
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id in ['ABC', 'Protocol']:
                            dependencies['defines_interfaces'] = True
                        elif isinstance(base, ast.Attribute) and base.attr in ['ABC', 'Protocol']:
                            dependencies['defines_interfaces'] = True
                
                # 外部呼び出しチェック
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        # subprocess, docker, shutil等の外部システム呼び出し
                        if hasattr(node.func, 'value') and isinstance(node.func.value, ast.Name):
                            if node.func.value.id in ['subprocess', 'docker', 'shutil', 'os']:
                                dependencies['contains_external_calls'] = True
        
        except Exception:
            pass
        
        return dependencies
        
    def _get_ideal_path(self, current_path: Path, category: str) -> Path:
        """Clean Architecture準拠の理想的なファイルパスを生成"""
        # Clean Architecture層別のディレクトリ構造
        category_dir = self.src_dir / category
        
        # サブカテゴリを判定（例: docker_driver.py → infrastructure/drivers/docker/）
        file_stem = current_path.stem
        
        # Clean Architecture固有のサブディレクトリ分類
        if category == 'infrastructure':
            if 'driver' in file_stem:
                driver_type = self._extract_driver_type(file_stem)
                return category_dir / 'drivers' / driver_type / current_path.name
            elif 'repository' in file_stem:
                return category_dir / 'repositories' / current_path.name
            elif 'adapter' in file_stem:
                return category_dir / 'adapters' / current_path.name
            else:
                return category_dir / current_path.name
                
        elif category == 'domain':
            if 'entity' in file_stem or 'model' in file_stem:
                return category_dir / 'entities' / current_path.name
            elif 'service' in file_stem:
                return category_dir / 'services' / current_path.name
            elif 'value' in file_stem:
                return category_dir / 'values' / current_path.name
            else:
                return category_dir / current_path.name
                
        elif category == 'application':
            if 'service' in file_stem or 'svc' in file_stem:
                return category_dir / 'services' / current_path.name
            elif 'usecase' in file_stem:
                return category_dir / 'usecases' / current_path.name
            else:
                return category_dir / current_path.name
                
        elif category == 'operations':
            if 'request' in file_stem:
                return category_dir / 'requests' / current_path.name
            elif 'result' in file_stem:
                return category_dir / 'results' / current_path.name
            elif 'interface' in file_stem:
                return category_dir / 'interfaces' / current_path.name
            elif 'factory' in file_stem:
                return category_dir / 'factories' / current_path.name
            else:
                return category_dir / current_path.name
                
        elif category == 'data':
            entity_name = self._extract_entity_name(file_stem)
            if entity_name:
                return category_dir / entity_name / current_path.name
            else:
                return category_dir / current_path.name
                
        # その他のカテゴリはフラット構造
        return category_dir / current_path.name
    
    def _extract_driver_type(self, file_stem: str) -> str:
        """ドライバータイプを抽出（例: docker_driver → docker）"""
        if 'docker' in file_stem:
            return 'docker'
        elif 'file' in file_stem:
            return 'file'
        elif 'shell' in file_stem:
            return 'shell'
        elif 'python' in file_stem:
            return 'python'
        else:
            return 'generic'
    
    def _extract_entity_name(self, file_stem: str) -> str:
        """エンティティ名を抽出（例: user_repository → user）"""
        # よくあるサフィックスを削除してエンティティ名を抽出
        suffixes_to_remove = ['_repository', '_service', '_controller', '_model', '_entity']
        entity_name = file_stem
        
        for suffix in suffixes_to_remove:
            if entity_name.endswith(suffix):
                entity_name = entity_name[:-len(suffix)]
                break
                
        return entity_name if entity_name != file_stem else ""
        
    def _get_element_type(self, file_path: Path) -> str:
        """ファイルの要素タイプを判定"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            has_classes = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
            has_functions = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
            
            if has_classes:
                return 'class'
            elif has_functions:
                return 'function'
            else:
                return 'module'
                
        except Exception:
            return 'module'
            
    def _create_move_plan(self) -> None:
        """Clean Architecture依存関係を考慮して移動計画を最適化"""
        
        # Clean Architecture層の移動優先度
        # 依存関係の少ない層から移動（Domain → Application → Infrastructure → Presentation）
        layer_priority = {
            'domain': 0,      # 最優先：ピュアなビジネスロジック、依存関係なし
            'utils': 1,       # ユーティリティ：多くの層から依存される
            'operations': 2,  # 横断的関心事：インターフェース定義
            'data': 3,        # データアクセス：ドメインに依存
            'application': 4, # アプリケーション層：ドメインに依存
            'logging': 5,     # ログ：多くの層から使用される
            'configuration': 6, # 設定：アプリケーション層から使用
            'infrastructure': 7, # インフラ層：外部システム連携
            'presentation': 8  # プレゼンテーション層：最上位、他全てに依存
        }
        
        def get_move_priority(move: FileMove) -> tuple:
            # 移動先のカテゴリを特定
            try:
                # パスから層を抽出（例: src/domain/entities/config_node.py → domain）
                path_parts = move.destination.parts
                src_index = None
                for i, part in enumerate(path_parts):
                    if part == 'src':
                        src_index = i
                        break
                
                if src_index is not None and src_index + 1 < len(path_parts):
                    layer = path_parts[src_index + 1]
                    priority = layer_priority.get(layer, 99)
                else:
                    priority = 99
                    
            except Exception:
                priority = 99
            
            return (priority, str(move.source))
        
        # 依存関係を考慮してソート
        self.file_moves.sort(key=get_move_priority)
        
        # 移動計画の詳細ログ
        print(f"📋 移動計画を依存関係順に整理しました:")
        for i, move in enumerate(self.file_moves[:5]):  # 最初の5件のみ表示
            layer = move.destination.parts[-2] if len(move.destination.parts) > 1 else 'unknown'
            print(f"  {i+1}. {layer}: {move.source.name}")
        if len(self.file_moves) > 5:
            print(f"  ... 他 {len(self.file_moves) - 5} 件")
        
    def _create_import_update_plan(self) -> None:
        """インポート更新計画を作成"""
        # 移動されるファイルのマッピングを作成
        move_mapping = {}
        for move in self.file_moves:
            old_module = self._path_to_module(move.source)
            new_module = self._path_to_module(move.destination)
            move_mapping[old_module] = new_module
            
        # 全ファイルのインポートをチェック
        for py_file in self.src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # ファイル全体で文字列置換（文字列リテラル内も含む）
                content = ''.join(lines)
                updated_content = content
                has_updates = False
                
                for old_module, new_module in move_mapping.items():
                    # インポート文の置換パターン
                    patterns = [
                        f"from {old_module} import",
                        f"from {old_module}.",  # from src.configuration.config_manager import
                        f"import {old_module}",
                        f"'{old_module}'",      # 文字列リテラル内も対象
                        f'"{old_module}"',      # ダブルクォート文字列も対象
                    ]
                    
                    for pattern in patterns:
                        if pattern in updated_content:
                            replacement = pattern.replace(old_module, new_module)
                            updated_content = updated_content.replace(pattern, replacement)
                            has_updates = True
                
                if has_updates:
                    update = ImportUpdate(
                        file_path=py_file,
                        old_import=content,
                        new_import=updated_content,
                        line_number=0
                    )
                    self.import_updates.append(update)
                            
            except Exception as e:
                print(f"⚠️  {py_file}の解析中にエラー: {e}")
                
    def _path_to_module(self, path: Path) -> str:
        """パスをモジュール名に変換"""
        try:
            relative = path.relative_to(self.src_dir)
            parts = list(relative.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            return '.'.join(parts)
        except ValueError:
            return str(path)
            
    def _execute_organization(self) -> None:
        """実際にファイルを移動"""
        print("\n🚀 ファイル整理を実行中...")
        
        # ログディレクトリを作成（バックアップは無効化）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("src_check/auto_correct_log")
        log_dir.mkdir(exist_ok=True)
        
        # ロールバック情報を初期化（ログのみ）
        self.rollback_info = RollbackInfo(
            timestamp=timestamp,
            moves=[],
            import_updates=[],
            backup_dir=log_dir  # ログディレクトリとして使用
        )
        
        # ファイルを移動
        for move in self.file_moves:
            try:
                # バックアップは無効化（Gitで管理）
                
                # 移動先ディレクトリを作成
                move.destination.parent.mkdir(parents=True, exist_ok=True)
                
                # ファイルを移動
                shutil.move(str(move.source), str(move.destination))
                self.rollback_info.moves.append(move)
                
                print(f"✅ 移動: {move.source} → {move.destination}")
                
                # 必要に応じて__init__.pyを作成
                self._ensure_init_files(move.destination.parent)
                
            except Exception as e:
                print(f"❌ 移動失敗: {move.source} - {e}")
                
        # インポートを更新
        self._update_imports()
        
        # ロールバック情報を保存
        self._save_rollback_info()
        
        # 空のディレクトリを削除
        self._cleanup_empty_dirs()
        
    def _ensure_init_files(self, directory: Path) -> None:
        """__init__.pyファイルを確保"""
        current = directory
        while current != self.src_dir and current != current.parent:
            init_file = current / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"📄 作成: {init_file}")
            current = current.parent
            
    def _update_imports(self) -> None:
        """インポート文を更新"""
        files_to_update = defaultdict(list)
        
        for update in self.import_updates:
            files_to_update[update.file_path].append(update)
            
        for file_path, updates in files_to_update.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # バックアップは無効化（Gitで管理）
                    
                # インポートを更新
                for update in updates:
                    if update.line_number == 0:  # ファイル全体の置換
                        content = update.new_import
                    else:  # 行単位の置換
                        content = content.replace(update.old_import, update.new_import)
                    
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print(f"📝 インポート更新: {file_path} ({len(updates)}箇所)")
                
                if self.rollback_info:
                    self.rollback_info.import_updates.extend(updates)
                    
            except Exception as e:
                print(f"❌ インポート更新失敗: {file_path} - {e}")
                
    def _cleanup_empty_dirs(self) -> None:
        """空のディレクトリを削除"""
        for root, dirs, files in os.walk(self.src_dir, topdown=False):
            if not files and not dirs and root != str(self.src_dir):
                try:
                    Path(root).rmdir()
                    print(f"🗑️  空ディレクトリ削除: {root}")
                except Exception:
                    pass
                    
    def _save_rollback_info(self) -> None:
        """ロールバック情報を保存"""
        if self.rollback_info:
            rollback_file = self.rollback_info.backup_dir / f"operation_log_{self.rollback_info.timestamp}.json"
            
            data = {
                'timestamp': self.rollback_info.timestamp,
                'log_dir': str(self.rollback_info.backup_dir),
                'note': 'バックアップは無効化されています。変更はGitで管理してください。',
                'moves': [
                    {
                        'source': str(m.source),
                        'destination': str(m.destination),
                        'reason': m.reason
                    }
                    for m in self.rollback_info.moves
                ],
                'import_updates': [
                    {
                        'file_path': str(u.file_path),
                        'old_import': u.old_import,
                        'new_import': u.new_import,
                        'line_number': u.line_number
                    }
                    for u in self.rollback_info.import_updates
                ]
            }
            
            with open(rollback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"\n💾 ロールバック情報を保存: {rollback_file}")
            
    def _show_simulation(self) -> None:
        """シミュレーション結果を表示"""
        print("\n📋 実行計画（Dry Run）:")
        
        if self.file_moves:
            print("\n🚚 ファイル移動:")
            
            # カテゴリ別にグループ化
            moves_by_category = defaultdict(list)
            for move in self.file_moves:
                category = move.destination.parts[-2] if len(move.destination.parts) > 1 else 'root'
                moves_by_category[category].append(move)
                
            for category, moves in sorted(moves_by_category.items()):
                print(f"\n  📁 {category}/")
                for move in moves:
                    print(f"    ├─ {move.source.name} ← {move.source.parent}")
                    print(f"    │  理由: {move.reason}")
                    
        if self.import_updates:
            print(f"\n📝 インポート更新: {len(self.import_updates)}箇所")
            
            # ファイル別にグループ化
            updates_by_file = defaultdict(int)
            for update in self.import_updates:
                updates_by_file[update.file_path] += 1
                
            for file_path, count in sorted(updates_by_file.items()):
                print(f"  - {file_path}: {count}箇所")
                
    def rollback(self, rollback_file: Path) -> bool:
        """整理をロールバック（無効化済み）"""
        print(f"\n❌ ロールバック機能は無効化されています。")
        print(f"    変更はGitで管理してください。")
        print(f"    git reset --hard HEAD または git checkout でファイルを復元してください。")
        print(f"    ログファイル: {rollback_file}")
        return False


def main() -> CheckResult:
    project_root = Path(__file__).parent.parent.parent.parent
    src_dir = project_root / 'src'
    
    print(f"🔍 論理的ファイル整理解析を開始: {src_dir}")
    
    # DRY_RUNモードをチェック
    import os
    dry_run = bool(os.environ.get('SRC_CHECK_DRY_RUN', False))
    organizer = LogicalFileOrganizer(str(src_dir), dry_run=dry_run)
    file_moves, import_updates = organizer.organize()
    
    failure_locations = []
    
    # 移動が必要なファイルをfailure_locationsに追加
    for move in file_moves:
        failure_locations.append(FailureLocation(
            file_path=str(move.source),
            line_number=0
        ))
        
    if failure_locations:
        fix_policy = (
            f"{len(file_moves)}個のファイルを論理的なフォルダ構造に再配置します。\n"
            f"フォルダ名から機能が一目でわかる構造になります。\n"
            f"影響を受けるインポート: {len(import_updates)}箇所"
        )
        
        # カテゴリ別の移動数を集計
        category_counts = defaultdict(int)
        for move in file_moves:
            category = move.destination.parts[-2] if len(move.destination.parts) > 1 else 'root'
            category_counts[category] += 1
            
        fix_example = "# 整理後のフォルダ構造:\nsrc/\n"
        for category, count in sorted(category_counts.items()):
            fix_example += f"  {category}/  # {count}ファイル\n"
            
    else:
        fix_policy = "現在のファイル構造は既に論理的に整理されています。"
        fix_example = None
        
    return CheckResult(
        failure_locations=failure_locations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    # テスト実行
    result = main()
    print(f"\nCheckResult: {len(result.failure_locations)} files need reorganization")