"""
環境準備の実行機能
"""
from typing import List, Dict, Any, Optional
from src.operations.di_container import DIContainer
from src.operations.result.result import OperationResult


class PreparationExecutor:
    """
    環境準備を実際に実行するクラス
    
    operations経由で実環境の状態確認と準備作業を行う
    """
    
    def __init__(self, operations: DIContainer):
        """
        Args:
            operations: DI container for accessing drivers
        """
        self.operations = operations
    
    def check_environment_state(self, base_path: str = ".") -> Dict[str, Any]:
        """
        operations経由で実環境の状態を確認
        
        Args:
            base_path: 確認対象のベースパス
            
        Returns:
            Dict[str, Any]: 環境状態情報
        """
        file_driver = self.operations.resolve('file_driver')
        
        state = {
            'existing_files': set(),
            'existing_directories': set(),
            'base_path': base_path
        }
        
        try:
            # ベースディレクトリの存在確認
            if file_driver.exists(base_path):
                # ディレクトリ内容の列挙（可能な場合）
                state['base_exists'] = True
                # 注: file_driverの具体的なAPIに依存
            else:
                state['base_exists'] = False
                
        except Exception as e:
            state['error'] = str(e)
            state['base_exists'] = False
        
        return state
    
    def verify_requirements_against_environment(
        self, 
        workflow_requests,
        base_path: str = "."
    ) -> Dict[str, Any]:
        """
        ワークフローの要求と実環境の差異を確認
        
        Args:
            workflow_requests: ワークフローのrequests
            base_path: ベースパス
            
        Returns:
            Dict[str, Any]: 差異分析結果
        """
        file_driver = self.operations.resolve('file_driver')
        
        # ワークフローから必要なリソースを抽出
        required_resources = self._extract_required_resources(workflow_requests)
        
        missing_items = {
            'directories': [],
            'files': [],
            'preparation_needed': False
        }
        
        # 必要なディレクトリの確認
        for dir_path in required_resources.get('directories', []):
            try:
                if not file_driver.exists(dir_path):
                    missing_items['directories'].append(dir_path)
                    missing_items['preparation_needed'] = True
            except Exception:
                missing_items['directories'].append(dir_path)
                missing_items['preparation_needed'] = True
        
        # 必要なファイルの確認
        for file_path in required_resources.get('files', []):
            try:
                if not file_driver.exists(file_path):
                    missing_items['files'].append(file_path)
                    missing_items['preparation_needed'] = True
            except Exception:
                missing_items['files'].append(file_path)
                missing_items['preparation_needed'] = True
        
        return missing_items
    
    def create_preparation_requests(
        self, 
        missing_items: Dict[str, Any]
    ) -> List[Any]:
        """
        不足している項目に対する準備requestを生成
        
        Args:
            missing_items: verify_requirements_against_environmentの結果
            
        Returns:
            List[Any]: 準備用のrequestリスト
        """
        preparation_requests = []
        
        # DIコンテナから必要なファクトリを取得
        try:
            from src.operations.file.file_request import FileRequest
            from src.operations.file.file_op_type import FileOpType
        except ImportError:
            # フォールバック: 基本的なrequest生成
            return preparation_requests
        
        # 不足ディレクトリの作成request
        for dir_path in missing_items.get('directories', []):
            try:
                mkdir_request = FileRequest(
                    path=dir_path,
                    op=FileOpType.MKDIR,
                    allow_failure=True  # 事前準備なので失敗を許容
                )
                preparation_requests.append(mkdir_request)
            except Exception:
                # Request作成に失敗した場合はスキップ
                continue
        
        # 不足ファイルの作成request（必要に応じて）
        for file_path in missing_items.get('files', []):
            # ファイルはテンプレートコピーまたは空ファイル作成
            try:
                touch_request = FileRequest(
                    path=file_path,
                    op=FileOpType.TOUCH,
                    allow_failure=True
                )
                preparation_requests.append(touch_request)
            except Exception:
                continue
        
        return preparation_requests
    
    def execute_preparation(
        self, 
        preparation_requests: List[Any]
    ) -> List[OperationResult]:
        """
        準備requestを実行
        
        Args:
            preparation_requests: 準備用requestリスト
            
        Returns:
            List[OperationResult]: 実行結果リスト
        """
        results = []
        file_driver = self.operations.resolve('file_driver')
        
        for request in preparation_requests:
            try:
                result = request.execute(driver=file_driver)
                results.append(result)
            except Exception as e:
                # 準備段階のエラーは記録するが継続
                error_result = OperationResult(
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
        
        return results
    
    def fit_workflow_to_environment(
        self, 
        workflow_requests,
        base_path: str = "."
    ) -> Dict[str, Any]:
        """
        ワークフローを実環境に適合させるメイン機能
        
        Args:
            workflow_requests: ワークフローのrequests
            base_path: ベースパス
            
        Returns:
            Dict[str, Any]: 適合処理の結果
        """
        # 1. 環境状態確認
        env_state = self.check_environment_state(base_path)
        
        # 2. 差異確認
        missing_items = self.verify_requirements_against_environment(
            workflow_requests, base_path
        )
        
        # 3. 準備が必要かチェック
        if not missing_items['preparation_needed']:
            return {
                'preparation_needed': False,
                'message': 'Environment is ready for workflow execution',
                'environment_state': env_state
            }
        
        # 4. 準備requestの生成
        preparation_requests = self.create_preparation_requests(missing_items)
        
        # 5. 準備の実行
        preparation_results = self.execute_preparation(preparation_requests)
        
        # 6. 結果の集約
        successful_preparations = sum(1 for r in preparation_results if r.success)
        
        return {
            'preparation_needed': True,
            'preparation_executed': True,
            'total_preparations': len(preparation_requests),
            'successful_preparations': successful_preparations,
            'preparation_results': preparation_results,
            'missing_items': missing_items,
            'environment_state': env_state
        }
    
    def _extract_required_resources(self, workflow_requests) -> Dict[str, List[str]]:
        """
        ワークフローから必要なリソースを抽出
        
        Args:
            workflow_requests: ワークフローのrequests
            
        Returns:
            Dict[str, List[str]]: 必要なリソース情報
        """
        resources = {
            'files': [],
            'directories': []
        }
        
        # CompositeRequestまたはRequestExecutionGraphから抽出
        if hasattr(workflow_requests, 'nodes'):
            # RequestExecutionGraphの場合
            for node in workflow_requests.nodes.values():
                if hasattr(node, 'requires_dirs') and node.requires_dirs:
                    resources['directories'].extend(node.requires_dirs)
                if hasattr(node, 'reads_files') and node.reads_files:
                    resources['files'].extend(node.reads_files)
        elif hasattr(workflow_requests, 'requests'):
            # CompositeRequestの場合
            for request in workflow_requests.requests:
                # FileRequestの場合の特別処理
                if hasattr(request, 'path'):
                    from pathlib import Path
                    parent_dir = str(Path(request.path).parent)
                    if parent_dir != '.':
                        resources['directories'].append(parent_dir)
        
        return resources