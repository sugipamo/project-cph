# contest_currentファイル準備機能のバグ調査結果

## 調査概要
contest_currentのファイル準備機能が正常に動作しない問題について調査を実施。

## ファイル準備処理の実装構造

### 1. メイン処理（env.json openコマンド）
**場所**: `/home/cphelper/project-cph/contest_env/shared/env.json` 14-81行

**ステップ構成**:
1. **contest_currentをバックアップ** (16-23行)
   - 条件: なし（常に実行）
   - 処理: `{contest_current_path}/{contest_files}` → `{contest_stock_path}/{language_name}/{old_contest_name}/{old_problem_name}/{contest_files}`

2. **contest_stockから復元** (24-32行)
   - 条件: `test -f {contest_stock_path}/{language_name}/{contest_name}/{problem_name}/{contest_files}`
   - 処理: `{contest_stock_path}/{language_name}/{contest_name}/{problem_name}/{contest_files}` → `{contest_current_path}/{contest_files}`

3. **テンプレートから初期化** (33-41行)
   - 条件: `test ! -f {contest_stock_path}/{language_name}/{contest_name}/{problem_name}/{contest_files}`
   - 処理: `{contest_template_path}/{language_name}/{contest_files}` → `{contest_current_path}/{contest_files}`

### 2. 依存関係解決処理
**場所**: `/home/cphelper/project-cph/src/workflow/step/dependency.py` 8-59行

**機能**:
- ステップ実行前の準備ステップ自動生成
- 無効パス検出による準備ステップスキップ機能（34行）
- ディレクトリ・ファイル存在確認

### 3. when条件評価処理
**場所**: `/home/cphelper/project-cph/src/workflow/step/simple_step_runner.py` 156-169行

**機能**:
- `test`コマンド形式の条件評価
- 複合条件（`&&`）サポート
- ファイル存在確認（`-f`, `-d`等）

## 特定された問題

### 1. 否定条件処理のバグ（修正済み）
**場所**: `src/workflow/step/simple_step_runner.py:276`

**問題**: 
```python
if args[0] == '!':  # \! のエスケープケースが処理されない
    negate = True
    args = args[1:]
```

**具体的エラー**:
- `test ! -f` 形式の条件で `!` が `\!` にエスケープされる
- `Unsupported test flag: \!` エラーが発生
- when条件の評価が失敗し、テンプレート初期化ステップが実行されない

**修正内容**:
```python
if args[0] == '!' or args[0] == '\\!':  # エスケープケースを追加
    negate = True
    args = args[1:]
```

### 2. 依存関係解決の安全機構
**場所**: `src/workflow/step/dependency.py:34`

**現在の実装**:
```python
if any('//' in str(arg) for arg in expanded_cmd):
    should_generate_prep = False
```

**改善内容**:
```python
invalid_paths = [str(arg) for arg in expanded_cmd if '//' in str(arg) or str(arg).endswith('/.')]
if invalid_paths:
    should_generate_prep = False
```

## 誤った分析と修正

### env.jsonパステンプレート「重複」問題（誤判断）

**誤った推論**:
1. `contest_stock_path`定義: `./contest_stock/{language_name}/{contest_name}/{problem_name}`
2. 使用箇所: `{contest_stock_path}/{language_name}/{contest_name}/{problem_name}/{contest_files}`
3. 展開結果: `./contest_stock/python/abc300/a/python/abc300/a/*.py`（重複）

**実際の動作**:
- `contest_stock_path`は**文字列リテラル**として扱われる
- 中の`{language_name}`等は展開されない
- 正常なパス: `./contest_stock/{language_name}/{contest_name}/{problem_name}/python/abc300/a/*.py`

**テンプレート展開の仕組み**:
```json
"contest_stock_path": "./contest_stock/{language_name}/{contest_name}/{problem_name}"
```
↓ 使用時
```json
"when": "test -f {contest_stock_path}/{language_name}/{contest_name}/{problem_name}/{contest_files}"
```
↓ 展開時（contest_stock_pathは文字列として置換）
```
"test -f ./contest_stock/{language_name}/{contest_name}/{problem_name}/python/abc300/a/*.py"
```

## ファイル準備が機能しない根本原因

### 主要因: when条件評価の失敗
1. **否定条件エラー**: `test ! -f` で `\!` エスケープエラー → 条件評価失敗
2. **ステップスキップ**: when条件が false → テンプレート初期化ステップが実行されない
3. **ファイル未準備**: contest_currentディレクトリにファイルが作成されない

### 副次的要因
1. **依存関係解決の誤動作**: 無効パス検出機能が正常ケースでも発動する可能性
2. **エラーハンドリング**: 条件評価エラー時の適切な処理不足

## 修正による影響

### 有効な修正
1. **simple_step_runner.py**: 否定条件`\!`処理 → when条件が正常評価される
2. **dependency.py**: 無効パス検出改善 → 安全性向上

### 無効な修正（ロールバック済み）
1. **env.json**: パステンプレート構造は正常だった

## 検証すべき項目

1. **否定条件の動作確認**:
   - `test ! -f {non_existent_file}` → true
   - `test ! -f {existing_file}` → false

2. **ファイル準備フローの確認**:
   - contest_stock未存在時 → テンプレート初期化実行
   - contest_stock存在時 → 復元処理実行

3. **エラーハンドリング**:
   - 条件評価エラー時の適切な処理
   - ファイル操作失敗時の復旧処理

## 学習事項

1. **テンプレート変数の理解不足**:
   - 文字列リテラルとテンプレート変数の区別
   - 展開タイミングと仕組みの誤解

2. **推測に基づく修正の危険性**:
   - 十分な検証なしの修正実施
   - 副作用の考慮不足

3. **デバッグ手法の改善**:
   - エラーログの詳細確認
   - 実際の動作フローの追跡

## 修正状況

✅ **simple_step_runner.py** - 否定条件処理修正（有効）  
❌ **env.json** - 不適切な修正のためロールバック  
✅ **dependency.py** - 安全性向上（有効）