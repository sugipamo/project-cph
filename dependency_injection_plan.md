# 依存性注入対応計画書

## 概要
`result.txt`で特定された副作用配置違反を解決するための依存性注入対応計画

## 検出された問題

### 1. configuration/config_manager.py
- **Line 112**: `hasattr(self, '_command_type')` - 直接的な属性チェック
- **Line 565**: `command_type: str = "open"` - デフォルト値の使用（CLAUDE.mdルール違反）

### 2. operations層での副作用配置違反
- **context/user_input_parser/user_input_parser.py**: operations層への直接インポート
- **operations/factories/request_factory.py**: operations間の循環参照
- **operations/requests/**: 各種リクエストクラスの直接インポート
- **workflow/step/workflow.py**: operations層への直接依存

## 対応方針

### Phase 1: Configuration層の修正
1. **config_manager.py**
   - デフォルト値の削除
   - 設定取得の依存性注入化
   - `create_execution_config`メソッドの引数からデフォルト値を削除

### Phase 2: Operations層の依存性解決
1. **RequestFactory**
   - 依存性注入により外部から必要なオブジェクトを受け取る構造に変更済み
   - 設定管理、エラーコンバータ、結果ファクトリなどを注入
   
2. **Request Objects**
   - 各リクエストクラスは純粋なデータ構造として保持
   - 実行時に必要な依存関係はファクトリから注入

### Phase 3: Context層の修正
1. **user_input_parser.py**
   - operations層への直接依存を削除
   - 必要な型やインターフェースを抽象化層に移動

### Phase 4: Workflow層の修正
1. **workflow.py**
   - operationsオブジェクトの依存性注入を強化
   - 直接的なリクエスト生成を避け、ファクトリパターンを活用

## 具体的な修正項目

### 1. 設定取得方法の統一
```python
# 修正前
def create_execution_config(self, contest_name: str,
                          problem_name: str,
                          language: str,
                          env_type: str = "local",
                          command_type: str = "open") -> TypedExecutionConfiguration:

# 修正後
def create_execution_config(self, contest_name: str,
                          problem_name: str,
                          language: str,
                          env_type: str,
                          command_type: str) -> TypedExecutionConfiguration:
```

### 2. Infrastructure層での副作用の集約
- すべての副作用処理をInfrastructure層に集約
- main.pyから適切な依存性注入を実施

### 3. 抽象化レイヤーの強化
- operations層とcontext層の間に適切な抽象化を導入
- インターフェースベースの設計に移行

## 実装順序

1. **Step 1**: `config_manager.py`のデフォルト値削除
2. **Step 2**: 呼び出し元でのデフォルト値明示化
3. **Step 3**: `user_input_parser.py`の依存関係修正
4. **Step 4**: `workflow.py`の依存性注入強化
5. **Step 5**: main.pyでの依存性注入設定確認

## 期待される効果

- CLAUDE.mdルールへの完全準拠
- 副作用の適切な配置
- テスタビリティの向上
- 循環依存の解消
- 保守性の向上

## リスク管理

- 各修正後に段階的テスト実行
- 互換性維持のための漸進的移行
- 既存機能への影響最小化

## 完了条件

- 依存性注入チェックの合格
- 全テストの通過
- 副作用配置違反の解消