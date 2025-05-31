"""
実環境の状態を確認するインスペクター
"""
from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from pathlib import Path


@dataclass
class EnvironmentState:
    """環境の現在状態"""
    existing_files: Set[str]
    existing_directories: Set[str]
    missing_files: Set[str]
    missing_directories: Set[str]
    writable_paths: Set[str]
    readonly_paths: Set[str]


@dataclass
class RequiredState:
    """ワークフロー実行に必要な状態"""
    required_files: Set[str]
    required_directories: Set[str]
    files_to_create: Set[str]
    directories_to_create: Set[str]
    files_to_read: Set[str]
    files_to_write: Set[str]


class EnvironmentInspector:
    """実環境の状態を検査する純粋関数的クラス"""
    
    @staticmethod
    def inspect_current_environment(base_path: str = ".") -> EnvironmentState:
        """
        現在の環境状態を検査
        
        Args:
            base_path: 検査対象のベースパス
            
        Returns:
            EnvironmentState: 現在の環境状態
        """
        base = Path(base_path).resolve()
        existing_files = set()
        existing_directories = set()
        writable_paths = set()
        readonly_paths = set()
        
        # 再帰的にファイルとディレクトリを検査
        if base.exists():
            for item in base.rglob("*"):
                relative_path = str(item.relative_to(base))
                
                if item.is_file():
                    existing_files.add(relative_path)
                elif item.is_dir():
                    existing_directories.add(relative_path)
                
                # 書き込み権限の確認
                try:
                    if item.exists():
                        # ファイル/ディレクトリの書き込み権限確認
                        if item.is_file():
                            test_write = item.parent / f".write_test_{item.name}"
                        else:
                            test_write = item / ".write_test"
                        
                        test_write.touch()
                        test_write.unlink()
                        writable_paths.add(relative_path)
                except (PermissionError, OSError):
                    readonly_paths.add(relative_path)
        
        return EnvironmentState(
            existing_files=existing_files,
            existing_directories=existing_directories,
            missing_files=set(),  # 後でrequired_stateと比較して設定
            missing_directories=set(),  # 後でrequired_stateと比較して設定
            writable_paths=writable_paths,
            readonly_paths=readonly_paths
        )
    
    @staticmethod
    def extract_required_state_from_workflow(workflow_requests) -> RequiredState:
        """
        ワークフローから必要な環境状態を抽出
        
        Args:
            workflow_requests: ワークフローのrequestリスト
            
        Returns:
            RequiredState: 必要な環境状態
        """
        from src.env.workflow.graph_to_composite_adapter import GraphToCompositeAdapter
        
        required_files = set()
        required_directories = set()
        files_to_create = set()
        directories_to_create = set()
        files_to_read = set()
        files_to_write = set()
        
        # CompositeRequestまたはRequestExecutionGraphから情報抽出
        if hasattr(workflow_requests, 'nodes'):
            # RequestExecutionGraphの場合
            for node in workflow_requests.nodes.values():
                if node.creates_files:
                    files_to_create.update(node.creates_files)
                if node.creates_dirs:
                    directories_to_create.update(node.creates_dirs)
                if node.reads_files:
                    files_to_read.update(node.reads_files)
                if node.requires_dirs:
                    required_directories.update(node.requires_dirs)
        else:
            # CompositeRequestの場合
            for request in workflow_requests.requests:
                creates_files, creates_dirs, reads_files, requires_dirs = \
                    GraphToCompositeAdapter._extract_resource_info(request)
                
                files_to_create.update(creates_files)
                directories_to_create.update(creates_dirs)
                files_to_read.update(reads_files)
                required_directories.update(requires_dirs)
        
        required_files.update(files_to_read)
        required_directories.update(directories_to_create)
        files_to_write.update(files_to_create)
        
        return RequiredState(
            required_files=required_files,
            required_directories=required_directories,
            files_to_create=files_to_create,
            directories_to_create=directories_to_create,
            files_to_read=files_to_read,
            files_to_write=files_to_write
        )
    
    @staticmethod
    def compare_states(
        current: EnvironmentState, 
        required: RequiredState
    ) -> EnvironmentState:
        """
        現在状態と必要状態を比較し、差異を含む状態を返す
        
        Args:
            current: 現在の環境状態
            required: 必要な環境状態
            
        Returns:
            EnvironmentState: 差異情報を含む環境状態
        """
        missing_files = required.required_files - current.existing_files
        missing_directories = required.required_directories - current.existing_directories
        
        return EnvironmentState(
            existing_files=current.existing_files,
            existing_directories=current.existing_directories,
            missing_files=missing_files,
            missing_directories=missing_directories,
            writable_paths=current.writable_paths,
            readonly_paths=current.readonly_paths
        )
    
    @staticmethod
    def validate_permissions(
        state: EnvironmentState, 
        required: RequiredState
    ) -> Dict[str, List[str]]:
        """
        必要な操作に対する権限を検証
        
        Args:
            state: 環境状態
            required: 必要な操作
            
        Returns:
            Dict[str, List[str]]: 権限エラーのカテゴリ別リスト
        """
        permission_errors = {
            'unwritable_create_files': [],
            'unwritable_create_dirs': [],
            'unreadable_files': [],
            'permission_denied_paths': []
        }
        
        # ファイル作成権限確認
        for file_path in required.files_to_create:
            parent_dir = str(Path(file_path).parent)
            if parent_dir in state.readonly_paths:
                permission_errors['unwritable_create_files'].append(file_path)
        
        # ディレクトリ作成権限確認
        for dir_path in required.directories_to_create:
            parent_dir = str(Path(dir_path).parent)
            if parent_dir in state.readonly_paths:
                permission_errors['unwritable_create_dirs'].append(dir_path)
        
        # 読み込み対象ファイルの権限確認
        for file_path in required.files_to_read:
            if file_path in state.readonly_paths:
                permission_errors['unreadable_files'].append(file_path)
        
        return permission_errors