"""
環境準備のためのプランニング機能
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .environment_inspector import EnvironmentState, RequiredState


@dataclass
class PreparationStep:
    """準備ステップ"""
    type: str  # mkdir, touch, copy, etc.
    target_path: str
    source_path: Optional[str] = None
    priority: int = 0  # 0が最高優先度
    description: str = ""
    allow_failure: bool = True


@dataclass
class PreparationPlan:
    """準備プラン"""
    steps: List[PreparationStep]
    warnings: List[str]
    critical_errors: List[str]
    estimated_duration: float = 0.0


class PreparationPlanner:
    """環境準備のプランを作成する純粋関数的クラス"""
    
    @staticmethod
    def create_preparation_plan(
        current_state: EnvironmentState,
        required_state: RequiredState,
        base_path: str = "."
    ) -> PreparationPlan:
        """
        現在状態と必要状態から準備プランを作成
        
        Args:
            current_state: 現在の環境状態
            required_state: 必要な環境状態
            base_path: ベースパス
            
        Returns:
            PreparationPlan: 実行すべき準備プラン
        """
        steps = []
        warnings = []
        critical_errors = []
        
        # 1. 必要なディレクトリの作成
        for dir_path in sorted(current_state.missing_directories):
            steps.append(PreparationStep(
                type="mkdir",
                target_path=dir_path,
                priority=0,  # 最高優先度（他の操作の前提）
                description=f"Create required directory: {dir_path}",
                allow_failure=False
            ))
        
        # 2. 不足しているファイルの処理
        for file_path in sorted(current_state.missing_files):
            # テンプレートから推測できる場合
            template_suggestions = PreparationPlanner._suggest_file_templates(file_path)
            
            if template_suggestions:
                # テンプレートからのコピーを提案
                for template_path in template_suggestions:
                    steps.append(PreparationStep(
                        type="copy_template",
                        target_path=file_path,
                        source_path=template_path,
                        priority=1,
                        description=f"Copy template {template_path} to {file_path}",
                        allow_failure=True
                    ))
                    break  # 最初の候補のみ
            else:
                # 空ファイルの作成
                steps.append(PreparationStep(
                    type="touch",
                    target_path=file_path,
                    priority=2,
                    description=f"Create empty file: {file_path}",
                    allow_failure=True
                ))
                
                warnings.append(f"File {file_path} will be created as empty. Consider providing content.")
        
        # 3. 権限問題のチェック
        for readonly_path in current_state.readonly_paths:
            if (readonly_path in required_state.files_to_write or 
                readonly_path in required_state.directories_to_create):
                critical_errors.append(
                    f"Permission denied: Cannot write to {readonly_path}"
                )
        
        # 4. 依存関係の解決（ソート）
        sorted_steps = PreparationPlanner._sort_steps_by_dependencies(steps)
        
        # 5. 実行時間の推定
        estimated_duration = len(sorted_steps) * 0.1  # 1ステップあたり0.1秒と仮定
        
        return PreparationPlan(
            steps=sorted_steps,
            warnings=warnings,
            critical_errors=critical_errors,
            estimated_duration=estimated_duration
        )
    
    @staticmethod
    def _suggest_file_templates(file_path: str) -> List[str]:
        """
        ファイルパスからテンプレートファイルを推測
        
        Args:
            file_path: 対象ファイルパス
            
        Returns:
            List[str]: テンプレートファイルパスの候補
        """
        from pathlib import Path
        
        suggestions = []
        path = Path(file_path)
        
        # 拡張子に基づくテンプレート推測
        if path.suffix == '.py':
            suggestions.extend([
                f"contest_template/python/{path.name}",
                f"contest_template/pypy/{path.name}",
                "contest_template/python/main.py"
            ])
        elif path.suffix == '.rs':
            suggestions.extend([
                f"contest_template/rust/src/{path.name}",
                "contest_template/rust/src/main.rs"
            ])
        
        # 特定のファイル名パターン
        if path.name == "main.py":
            suggestions.extend([
                "contest_template/python/main.py",
                "contest_template/pypy/main.py"
            ])
        elif path.name == "main.rs":
            suggestions.append("contest_template/rust/src/main.rs")
        
        return suggestions
    
    @staticmethod
    def _sort_steps_by_dependencies(steps: List[PreparationStep]) -> List[PreparationStep]:
        """
        依存関係に基づいてステップをソート
        
        Args:
            steps: 準備ステップリスト
            
        Returns:
            List[PreparationStep]: ソート済みステップリスト
        """
        # 優先度でまずソート
        steps.sort(key=lambda s: (s.priority, s.target_path))
        
        # ディレクトリ作成を最初に、ファイル作成をその後に配置
        mkdir_steps = [s for s in steps if s.type == "mkdir"]
        file_steps = [s for s in steps if s.type != "mkdir"]
        
        return mkdir_steps + file_steps
    
    @staticmethod
    def create_minimal_plan_for_workflow(workflow_requests) -> PreparationPlan:
        """
        ワークフローに最低限必要な準備プランを作成
        
        Args:
            workflow_requests: ワークフローのrequests
            
        Returns:
            PreparationPlan: 最小限の準備プラン
        """
        from .environment_inspector import EnvironmentInspector
        
        # 現在の環境を検査
        current_state = EnvironmentInspector.inspect_current_environment()
        
        # ワークフローから必要状態を抽出
        required_state = EnvironmentInspector.extract_required_state_from_workflow(workflow_requests)
        
        # 状態比較
        compared_state = EnvironmentInspector.compare_states(current_state, required_state)
        
        # プラン作成
        return PreparationPlanner.create_preparation_plan(compared_state, required_state)
    
    @staticmethod
    def validate_plan_feasibility(plan: PreparationPlan) -> Dict[str, Any]:
        """
        プランの実行可能性を検証
        
        Args:
            plan: 準備プラン
            
        Returns:
            Dict[str, Any]: 検証結果
        """
        validation_result = {
            'is_feasible': True,
            'blocking_issues': [],
            'warnings': plan.warnings.copy(),
            'estimated_time': plan.estimated_duration,
            'step_count': len(plan.steps)
        }
        
        # 致命的エラーのチェック
        if plan.critical_errors:
            validation_result['is_feasible'] = False
            validation_result['blocking_issues'].extend(plan.critical_errors)
        
        # 複雑すぎるプランの警告
        if len(plan.steps) > 50:
            validation_result['warnings'].append(
                f"Plan has {len(plan.steps)} steps, which may take significant time"
            )
        
        # 実行時間の警告
        if plan.estimated_duration > 10.0:
            validation_result['warnings'].append(
                f"Estimated execution time: {plan.estimated_duration:.1f} seconds"
            )
        
        return validation_result