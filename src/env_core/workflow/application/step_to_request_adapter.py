"""
Step to Request adapter - application layer
"""
from typing import List, Any
from src.env_core.step.step import Step
from src.env_core.workflow.pure_request_factory import PureRequestFactory


class StepToRequestAdapter:
    """ステップをリクエストに変換するアダプター"""
    
    def __init__(self):
        self.request_factory = PureRequestFactory()
    
    def convert_steps_to_requests(self, steps: List[Step]) -> List[Any]:
        """
        ステップのリストをリクエストのリストに変換
        
        Args:
            steps: 変換するステップのリスト
            
        Returns:
            変換されたリクエストのリスト
        """
        requests = []
        for step in steps:
            request = self._convert_single_step(step)
            if request:
                requests.append(request)
        return requests
    
    def _convert_single_step(self, step: Step) -> Any:
        """
        単一のステップをリクエストに変換
        
        Args:
            step: 変換するステップ
            
        Returns:
            変換されたリクエスト
        """
        try:
            return self.request_factory.create_request_from_step(step)
        except Exception as e:
            print(f"Warning: Failed to convert step {step}: {e}")
            return None
    
    def validate_conversion(self, steps: List[Step], requests: List[Any]) -> bool:
        """
        変換結果のバリデーション
        
        Args:
            steps: 元のステップのリスト
            requests: 変換されたリクエストのリスト
            
        Returns:
            変換が正常に行われたかどうか
        """
        # 有効なリクエストの数をチェック
        valid_requests = [r for r in requests if r is not None]
        
        # 変換失敗が多すぎる場合は警告
        failure_rate = (len(steps) - len(valid_requests)) / len(steps)
        if failure_rate > 0.5:  # 50%以上失敗
            print(f"Warning: High conversion failure rate: {failure_rate:.2%}")
            return False
        
        return True