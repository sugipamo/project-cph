# 型エラー関連のテスト失敗

## 概要
OperationRequestFoundationクラスの初期化引数に関連するテスト失敗です。現在のクラス設計とテストの不整合が原因です。

## 失敗したテスト

### BaseRequest関連 (tests/operations/test_base_request.py)
- `test_init` - OperationRequestFoundation.__init__()に必須引数が不足
- `test_set_name` - 同上
- `test_debug_info_enabled` - 同上
- `test_debug_info_disabled` - 同上
- `test_execute_success` - 同上
- `test_execute_without_driver_when_not_required` - 同上
- `test_operation_type_property` - 同上
- `test_debug_info_stack_frame` - 同上

## 検出された問題

### 引数シグネチャの不整合
- `src/operations/requests/base/base_request.py:16` - OperationRequestFoundation.__init__()は以下の必須引数を持つ：
  - `name: Optional[str]`
  - `debug_tag: Optional[str]`
  - `_executed: bool`
  - `_result: Any`
  - `_debug_info: Optional[dict]`

- `tests/operations/test_base_request.py:15-16` - ConcreteRequestクラスは`name`と`debug_tag`のみを受け取り、他の必須引数を提供していない

### CLAUDE.mdルール評価結果
- `src/operations/results/shell_result.py:15` - `op: Optional[str] = None`でデフォルト値使用しているが、これは最後の引数のオプション引数として適切
- `src/infrastructure/providers/sqlite_provider.py:154` - `execute`メソッド名は`MockSQLiteConnection`の標準SQLite互換インターフェースとして適切

## 修正計画

### 1. OperationRequestFoundationクラスの引数設計見直し
- 現在の必須引数`_executed`、`_result`、`_debug_info`は初期化時にデフォルト値を持たせるか、コンストラクタ内で初期化するように変更
- テストが期待する`name`と`debug_tag`のみの初期化パターンに対応

### 2. テストクラスの修正
- ConcreteRequestクラスを現在のOperationRequestFoundationシグネチャに合わせて修正
- または、OperationRequestFoundationの設計を変更してテストの期待動作に合わせる

### 3. 推奨アプローチ
OperationRequestFoundationのコンストラクタを以下のように変更：
```python
def __init__(self, name: Optional[str], debug_tag: Optional[str]):
    self.name = name
    self._executed = False  # 初期化時にデフォルト値設定
    self._result = None     # 初期化時にデフォルト値設定
    self.debug_info = self._create_debug_info(debug_tag)
```

## 影響範囲
- src/operations/requests/base/base_request.py (OperationRequestFoundation.__init__メソッド)
- tests/operations/test_base_request.py (ConcreteRequestクラス)
- OperationRequestFoundationを継承する全てのクラス