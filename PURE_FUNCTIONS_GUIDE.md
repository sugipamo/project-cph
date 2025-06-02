# 純粋関数アプローチによるテスト容易性の向上

## 概要

このプロジェクトでは、テストの容易性を向上させるために純粋関数アプローチを導入しました。従来のオブジェクト指向アプローチに加えて、副作用のない純粋関数を提供することで、モックに頼らないテストが可能になりました。

## アーキテクチャ

### 従来のアプローチ（課題）
```python
# モックが大量に必要
@patch('module.dependency1')
@patch('module.dependency2') 
@patch('module.dependency3')
def test_complex_logic(mock1, mock2, mock3):
    # 複雑なモック設定
    mock1.return_value = ...
    # 実装の詳細に依存したテスト
```

### 新しい純粋関数アプローチ
```python
# モック不要、実際の動作をテスト
def test_workflow_building():
    # 実際のデータ
    input_data = WorkflowBuildInput(
        json_steps=[{"type": "shell", "cmd": ["echo", "test"]}],
        context=create_test_context()
    )
    
    # 純粋関数呼び出し
    output = build_workflow_pure(input_data)
    
    # 実際の結果を検証
    assert len(output.nodes) == 1
    assert output.errors == []
```

## 主要コンポーネント

### 1. 純粋関数モジュール (`src/pure_functions/`)

#### `workflow_builder_pure.py`
- ワークフロー構築ロジックの純粋関数実装
- 依存関係解決、最適化などの機能
- 完全に副作用なし

#### `execution_context_pure.py`
- 実行コンテキストの不変データ構造
- バリデーション、フォーマット機能
- フリーズされたデータクラス

#### `workflow_execution_pure.py`
- ワークフロー実行計画の純粋関数
- 準備タスク分析、循環依存検出など

#### `workflow_facade.py`
- 既存APIと純粋関数の橋渡し
- 段階的移行を可能にする

### 2. テスト構造

#### モック不要のテスト
```python
class TestBuildWorkflowPure:
    def test_simple_workflow(self):
        # 実際のデータ作成
        input_data = WorkflowBuildInput(...)
        
        # 純粋関数実行
        output = build_workflow_pure(input_data)
        
        # 実際の結果検証
        assert output.nodes[0].metadata['step_type'] == 'mkdir'
```

#### 不変データ構造のテスト
```python
def test_immutable_data_structures(self):
    data = ExecutionData(...)
    
    # 不変性の検証
    with pytest.raises(AttributeError):
        data.command_type = "new_value"
```

## 利点

### 1. テストの簡素化
- **モック不要**: 実際のロジックをテスト
- **セットアップ簡単**: 最小限のデータ準備
- **高速実行**: I/Oなし、純粋計算のみ

### 2. 保守性の向上
- **実装変更に強い**: 内部実装が変わってもテストが壊れない
- **明確な境界**: 入力と出力が明確
- **デバッグ容易**: 同じ入力で常に同じ出力

### 3. 並行性
- **スレッドセーフ**: 状態変更なし
- **並列テスト**: 副作用がないため安全

## 使用方法

### 新しいコードでの使用
```python
from src.pure_functions.workflow_builder_pure import build_workflow_pure
from src.pure_functions.execution_context_pure import ExecutionData

# データ作成
execution_data = ExecutionData(
    command_type="build",
    language="python",
    contest_name="abc123",
    problem_name="a",
    env_type="local"
)

# ワークフロー構築
input_data = WorkflowBuildInput(
    json_steps=steps,
    context=step_context
)
output = build_workflow_pure(input_data)
```

### 既存コードとの互換性
```python
from src.pure_functions.workflow_facade import PureWorkflowFacade

# 既存のExecutionContextを使用
graph, errors, warnings = PureWorkflowFacade.build_workflow_from_context(
    execution_context,
    json_steps
)
```

## テストデータ作成のヘルパー

### 簡単なテストデータ作成
```python
from src.pure_functions.workflow_facade import (
    create_test_execution_data,
    create_test_step_context_data
)

# デフォルト値で作成
data = create_test_execution_data()

# カスタム値で作成
data = create_test_execution_data(
    language="rust",
    env_type="docker"
)
```

## 段階的移行戦略

### フェーズ1: 純粋関数の並行実装 ✅
- 既存機能を純粋関数で再実装
- 不変データ構造の導入
- ファサードによる互換性確保

### フェーズ2: テストの移行
- 既存テストの純粋関数版作成
- モックの段階的削除
- 統合テストの追加

### フェーズ3: 本体の移行
- 既存クラスの純粋関数使用への移行
- レガシーコードの段階的削除

## 例：従来 vs 純粋関数

### 従来のテスト
```python
@patch('src.module.dependency1')
@patch('src.module.dependency2')
def test_workflow_builder(mock_dep1, mock_dep2):
    # 複雑なモック設定
    mock_dep1.generate_steps.return_value = Mock(...)
    mock_dep2.resolve_dependencies.return_value = [...]
    
    # テスト実行
    builder = GraphBasedWorkflowBuilder(context)
    result = builder.build_graph_from_json_steps(steps)
    
    # モックの呼び出し検証
    mock_dep1.generate_steps.assert_called_once_with(...)
```

### 純粋関数のテスト
```python
def test_workflow_builder_pure():
    # 実際のデータ
    input_data = WorkflowBuildInput(
        json_steps=[
            {"type": "mkdir", "cmd": ["./output"]},
            {"type": "shell", "cmd": ["echo", "Hello"]}
        ],
        context=StepContext(...)
    )
    
    # 純粋関数実行
    output = build_workflow_pure(input_data)
    
    # 実際の結果検証
    assert len(output.nodes) == 2
    assert output.nodes[0].metadata['step_type'] == 'mkdir'
    assert output.errors == []
```

## まとめ

純粋関数アプローチにより：

1. **テストが簡単に**: モック不要、実際の動作テスト
2. **保守が楽に**: 実装変更にテストが依存しない
3. **デバッグが容易に**: 決定論的な動作
4. **並行処理が安全に**: 副作用なし

既存のコードとの互換性を保ちながら、段階的に移行できる設計になっています。