# テスト失敗分析結果

## 失敗テスト一覧と要因

### 1. CompositeRequest関連
**失敗テスト**: `tests/composite/test_composite_request.py::TestCompositeRequest::test_make_composite_request_multiple_requests`

**エラー**: `AttributeError: 'CompositeRequest' object has no attribute 'debug_tag'`

**要因**: CompositeRequestクラスに`debug_tag`属性が存在しない
- `tests/composite/test_composite_request.py:286`でテストが`result.debug_tag == "test"`をアサート
- CompositeRequestの`make_composite_request`メソッドで`debug_tag`パラメータが処理されていない

### 2. CompositeStructure関連
**失敗テスト**: `tests/composite/test_composite_structure.py`の複数テスト

**エラー**: `AttributeError: 'DummyRequest' object has no attribute 'count_leaf_requests'`

**要因**: DummyRequestクラスの実装に問題
- `src/operations/requests/composite/composite_structure.py:24`で`req.count_leaf_requests()`を呼び出し
- テストのDummyRequestクラスで`has_count_method`がFalseの場合にAttributeErrorを意図的に発生
- CompositeStructureが期待するインターフェースとテストのモックが不一致

### 3. EnvironmentManager関連
**失敗テスト**: `tests/infrastructure/environment/test_environment_manager.py::TestEnvironmentManager::test_init_loads_config_when_no_env_type`

**エラー**: モックのアサーション失敗
```
Expected: load_from_files(system_dir='config/system')
Actual: load_from_files(system_dir='./config/system', env_dir='./contest_env', language='python')
```

**要因**: EnvironmentManagerの実装が変更されテストが古い期待値を使用
- テストは`system_dir`のみを期待
- 実装は`system_dir`, `env_dir`, `language`の3つのパラメータを渡している

### 4. OperationRepository関連
**失敗テスト**: `tests/persistence/test_operation_repository.py::TestOperationRepository::test_create_entity_record_with_dict`

**エラー**: `TypeError: Operation.__init__() missing 2 required positional arguments: 'id' and 'created_at'`

**要因**: Operationクラスのコンストラクタに必須引数が追加された
- `src/infrastructure/persistence/sqlite/repositories/operation_repository.py:65`で`Operation(**entity)`を実行
- テストの辞書に`id`と`created_at`が含まれていない
- Operationクラスの引数にデフォルト値が禁止されているため必須引数となっている

## 修正方針

1. **CompositeRequest**: `debug_tag`属性の追加または`make_composite_request`メソッドの修正
2. **CompositeStructure**: DummyRequestクラスの`count_leaf_requests`メソッドの適切な実装
3. **EnvironmentManager**: テストの期待値を実際の実装に合わせて更新
4. **OperationRepository**: テスト辞書に`id`と`created_at`を追加、またはOperationクラスの生成方法を修正

# 以前のレポート（CPH Application 失敗原因分析レポート）

## 概要

`./cph.sh abc300 open a local python` コマンドの実行において、基本的なインフラストラクチャ問題は解決されたものの、高度なファイル操作機能で複数の設計上の問題が発覚した。

## ✅ 解決済みの問題

### ✅ ファイルパターンテンプレート変数の解決機能実装完了

**解決内容（2025-06-22）:**
- `{contest_files}`, `{test_files}`, `{build_files}` テンプレート変数の解決機能を実装
- ファイルパターン配列を個別ファイル操作に展開する機能を追加
- `step_runner.py` にファイルパターン専用の展開ロジックを実装

**実装された機能:**
1. **`expand_step_with_file_patterns()`**: ファイルパターンを含むステップを個別ステップに分割
2. **`get_file_patterns_from_context()`**: コンテキストからファイルパターン配列を取得
3. **`expand_file_patterns_to_files()`**: グロブパターンによる実際のファイルリスト生成
4. **テンプレート変数拡張**: `common_attrs`に`contest_files`, `test_files`, `build_files`を追加

**動作例:**
```json
// 設定: contest_files = ["main.py", "*.py"]
{"cmd": ["{contest_current_path}/{contest_files}", "{contest_stock_path}/{contest_files}"]}

// 実行時展開（main.py、util.pyが存在）
[
  {"cmd": ["./contest_current/main.py", "./contest_stock/.../main.py"]},
  {"cmd": ["./contest_current/util.py", "./contest_stock/.../util.py"]}
]
```

### ✅ インフラストラクチャ層の修正

1. **依存性注入の修正**
   - `MinimalCLIApp.__init__()` の logger パラメータ不足
   - `SQLiteManager.__init__()` の db_path パラメータ不足
   - DIKey 定義不足 (`CONFIG_MANAGER`, `LOGGER`)
   - DI コンテナ登録不足

2. **設定システムの修正**
   - `TypedExecutionConfiguration` への必須パス属性追加
   - `env_json` 属性の設定
   - テンプレート解決機能の基本実装

3. **ドライバー統合の修正**
   - `UnifiedDriver` へのファイル操作メソッド委譲機能追加
   - `CompositeRequest` コンストラクタ引数修正

## ✅ 解決済みの主要問題

### 1. ファイルパターン解決の実装完了

**解決内容（2025-06-22）:**
- `{contest_files}` テンプレート変数の解決機能を実装
- ファイルパターン配列を個別ファイル操作に展開する機能を追加
- `step_runner.py` にファイルパターン専用の展開ロジックを実装

**実装された機能:**
1. **`expand_step_with_file_patterns()`**: ファイルパターンを含むステップを個別ステップに分割
2. **`get_file_patterns_from_context()`**: コンテキストからファイルパターン配列を取得
3. **`expand_file_patterns_to_files()`**: グロブパターンによる実際のファイルリスト生成
4. **テンプレート変数拡張**: `common_attrs`に`contest_files`, `test_files`, `build_files`を追加

**動作例:**
```json
// 設定: contest_files = ["main.py", "*.py"]
{"cmd": ["{contest_current_path}/{contest_files}", "{contest_stock_path}/{contest_files}"]}

// 実行時展開（main.py、util.pyが存在）
[
  {"cmd": ["./contest_current/main.py", "./contest_stock/.../main.py"]},
  {"cmd": ["./contest_current/util.py", "./contest_stock/.../util.py"]}
]
```

## 🟡 残存する問題

### 1. パス重複問題

**症状:**
- 期待値: `./contest_stock/python/abc300/a/`
- 実際値: `contest_stock/python/abc300/a/python/abc300/a/`

**推定原因:**
- 設定マネージャーでのテンプレート解決
- ステップ実行時の再解決
- 複数段階でのテンプレート処理による重複

### 2. 設計上のミスマッチ（部分的解決済み）

**解決済み:**
- ファイルパターン配列を個別ファイル操作に展開する機能を実装
- 設定での配列定義を保持しつつ、実行時に適切な個別ファイル操作に変換

**残存課題:**
- 一部のエッジケースでのパターンマッチング精度向上が必要

## 🟡 設計レベルの課題

### 1. テンプレート変数システムの不完全性

**一貫性の欠如:**
```python
# step_runner.py:228-230 - 解決される変数
common_attrs = ['contest_name', 'problem_name', 'language', 'env_type', 
               'local_workspace_path', 'contest_current_path', 'contest_stock_path']
# 解決されない変数: contest_files, test_files, build_files
```

**ファイルパターン変数の特殊性:**
- `contest_files`: 配列形式のファイルパターン
- 一般変数: 単一文字列値
- 必要: 配列→個別パス展開機能

### 2. ワークフロー抽象化の不備

**現在の設定例:**
```json
{
  "name": "contest_currentをバックアップ",
  "type": "copy",
  "cmd": ["{contest_current_path}/{contest_files}", "{contest_stock_path}/.../{contest_files}"]
}
```

**問題点:**
- `{contest_files}` は `["main.py", "*.py"]` だが単一パスとして使用
- `copy` コマンドは個別ファイル操作を期待
- パターンマッチング→複数ファイル操作への展開機能不在

### 3. エラーハンドリングの不備

**現在の問題:**
- 未解決テンプレート変数の検出不足
- ファイル非存在時の適切なフォールバック不在
- エラーメッセージが原因特定を困難にする

## 📊 問題の構造分析

### データフロー問題

```
設定ファイル → 設定ロード → テンプレート解決 → ステップ実行
     ↓             ↓           ↓              ↓
contest_files  TypedExecution  expand_template  ファイル操作
   配列          Configuration     文字列置換      単一パス期待
                    ↓               ↓              ↓
                テンプレート      未解決変数      FileNotFoundError
                 部分解決       リテラル残存
```

### レイヤー別責任の混乱

1. **設定層**: ファイルパターン定義（配列）
2. **解決層**: 部分的テンプレート解決（一部変数のみ）
3. **実行層**: 文字列ベースファイル操作（単一パス期待）
4. **結果**: レイヤー間でのデータ形式不一致

## 💡 推奨修正戦略

### 短期的修正 (緊急)

1. **ファイルパターン解決機能追加**
```python
# step_runner.py の修正
def expand_template(template: str, context) -> str:
    # contest_files 等のファイルパターン変数を処理
    if '{contest_files}' in template:
        # ファイルパターンを実際のファイルリストに展開
        pass
```

2. **重複パス問題の修正**
- テンプレート解決の一本化
- キャッシュによる重複処理防止

### 中期的修正 (アーキテクチャ)

1. **ワークフロー設計の見直し**
- ファイルパターンステップを複数の個別ステップに分解
- パターンマッチング対応ファイル操作の実装

2. **テンプレートシステムの統一**
- 変数タイプ別処理ロジック
- ファイルパターン専用解決機能

### 長期的改善 (設計)

1. **型安全性の向上**
- ファイルパターン専用型定義
- テンプレート変数の型チェック

2. **エラーハンドリング強化**
- 早期バリデーション
- 詳細なエラーメッセージ

## 🎯 次のアクション

### 優先度1: 即座対応が必要
- [ ] `{contest_files}` テンプレート変数解決機能追加
- [ ] パス重複問題の修正
- [ ] ファイル存在チェック強化

### 優先度2: 安定性向上
- [ ] ワークフロー設定の見直し
- [ ] エラーハンドリング改善
- [ ] テストケース追加

### 優先度3: 長期的品質向上
- [ ] アーキテクチャ設計見直し
- [ ] 型安全性向上
- [ ] パフォーマンス最適化

## 📝 結論

現在のシステムは基本的なインフラストラクチャレベルでは動作可能な状態に達しているが、高度なファイル操作機能において設計上の根本的問題が複数存在する。これらの問題は相互に関連しており、部分的修正ではなく、ファイルパターン処理システム全体の見直しが必要である。

**最優先対応**: ファイルパターンテンプレート変数の解決機能実装により、基本的なワークフロー実行を可能にする。