# インポート自動修正レポート

## 📊 サマリー
- 検査ファイル数: 138
- 修正ファイル数: 0
- 修正箇所数: 0
- 警告数: 38
- エラー数: 0


## ⚠️ 警告 (手動確認が必要)

### 移動された可能性があるモジュールへの参照 (33件)
- `dependency.py:5`
  - 行: `from src.domain.services.step_generation_service import execution_context_to_simple_context`
  - 提案: src.core内を確認してください
- `workflow.py:8`
  - 行: `from src.domain.services.step_generation_service import (`
  - 提案: src.core内を確認してください
- `main.py:8`
  - 行: `from src.application.pure_config_manager import PureConfigManager`
  - 提案: src.core内を確認してください
  ... 他 30件

### 相対インポートが使用されています (5件)
- `__init__.py:3`
  - 行: `from .results.base_result import InfrastructureOperationResult, InfrastructureResult`
  - 提案: 絶対インポートへの変更を検討してください
- `__init__.py:4`
  - 行: `from .results.check_result import CheckResult, CircularImport`
  - 提案: 絶対インポートへの変更を検討してください
- `__init__.py:21`
  - 行: `from .results.file_result import FileResult`
  - 提案: 絶対インポートへの変更を検討してください
  ... 他 2件

## 📋 推奨アクション
1. 警告が出ているインポートを手動で確認してください
2. 特にinfrastructure層への依存は設計を見直す必要があります