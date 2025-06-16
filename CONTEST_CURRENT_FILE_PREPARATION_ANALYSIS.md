# Contest Current File Preparation エラー分析と対応の完全記録

## 発生した問題

### 初期エラー
コマンド: `./cph.sh python local open abc300 a`

```
FileNotFoundError: [Errno 2] No such file or directory: 'contest_current/{contest_files}'
AttributeError: 'str' object has no attribute 'value'
```

## エラー分析の経緯

### 段階1: 表面的なエラー対応
#### 1.1 AttributeError修正 ✅
- **場所**: `src/domain/exceptions/composite_step_failure.py:45`
- **原因**: `src/domain/requests/file/file_request.py:152`で`error_code`に文字列を渡していた
- **修正**: 文字列の`error_code`パラメータを削除

#### 1.2 FileNotFoundError分析
- **問題**: `contest_current/{contest_files}`が展開されずにファイル名として使用
- **判断**: ファイルパターン展開の問題と推定

### 段階2: 不適切な修正の実施 ❌
#### 2.1 `{contest_files}`を`{source_file_name}`に置換
```json
// 不適切な修正例
"cmd": ["{contest_current_path}/{source_file_name}", "{contest_stock_path}/{language_name}/{old_contest_name}/{old_problem_name}/{source_file_name}"]
```
- **問題**: 複数ファイルパターンの機能を単一ファイルに制限
- **影響**: 利便性を大幅に損なう

#### 2.2 ワークフロー条件の過剰修正
```json
// 過剰な条件
"when": "test -f {contest_current_path}/{source_file_name}"
```

#### 2.3 `{test_files}`を`test`に置換
- **問題**: ファイルパターン展開機能を完全に無視
- **判断**: 勝手な推測による変更

### 段階3: copytreeへの変更 🤔
#### 3.1 個別ファイル操作からディレクトリ操作に変更
```json
// 変更内容
"type": "copytree"
"cmd": ["{contest_current_path}", "{contest_stock_path}/{language_name}/{old_contest_name}/{old_problem_name}"]
```
- **結果**: 一見動作するが、設計意図を無視

#### 3.2 空ディレクトリチェック追加
```json
"when": "test -d {contest_current_path} && test -n \"$(ls -A {contest_current_path} 2>/dev/null)\""
```

### 段階4: 矛盾した結論 ❌
- **誤った結論**: 「元の実装は正しく動作していた」
- **実際**: 元の実装は動いておらず、場当たり的修正で偶然動作

## 根本的な問題の特定

### ファイルパターン展開システムの不備
```python
# src/workflow/step/simple_step_runner.py:223
pattern = patterns[0]  # 最初のパターンのみ使用

# ディレクトリ操作の場合の処理
if step_type in [StepType.MOVETREE, StepType.COPYTREE] and '/' in pattern:
    pattern = pattern.split('/')[0]
```

### 問題点
1. **単一パターンのみ処理**: `patterns[0]`のみ使用で複数ファイル未対応
2. **展開タイミング**: `{contest_files}`が適切に展開されない
3. **テンプレート変数の処理順序**: 展開順序が不適切

## 対応の問題点

### 場当たり的な修正
1. **根本原因の未特定**: ファイルパターン展開の問題を理解せず
2. **機能破壊**: 既存機能を理解せずに簡略化
3. **検証不足**: 修正の影響範囲を確認せず

### 誤った判断
1. **`movetree`タイプの誤解**: 元々正しく実装されていた
2. **ディレクトリ/ファイル操作の混同**: 設計意図を無視した変更
3. **パターン展開の理解不足**: 複数ファイル対応を単一ファイルに制限

## 最終的な状況

### 動作するようになった理由
1. **空ディレクトリチェック**: 不要なバックアップをスキップ
2. **copytree使用**: ディレクトリ全体の処理
3. **allow_failure設定**: 処理継続
4. **偶然の動作**: 根本問題は未解決

### 残存する問題
- ファイルパターン展開の根本的な問題は未解決
- 複数ファイルパターンへの対応が不完全
- 設計意図に反する実装

## 修正履歴

### 有効な修正 ✅
```python
# AttributeError修正
raise CompositeStepFailureError(
    formatted_error,
    original_exception=e,
    context="file operation"  # error_codeパラメータ削除
)
```

### 問題のある修正 ❌
```json
// 機能破壊的な修正例
"{contest_files}" → "{source_file_name}"
"{test_files}" → "test"
"copy" → "copytree"
```

## 学習事項と教訓

### 技術的な学習
1. **ファイルパターン展開**: 複雑なテンプレートシステムの理解が必要
2. **エラー処理**: 表面的なエラーと根本原因の区別
3. **設計意図**: 既存コードの意図を理解してから修正

### 開発手法の反省
1. **段階的な修正**: 一度に複数修正せず、段階的に検証
2. **根本原因分析**: 表面的な修正ではなく根本原因の特定
3. **機能の理解**: 既存機能を理解してから修正実施
4. **影響範囲の確認**: 修正による副作用の検証

### 対応の問題点の分析
1. **推測による修正**: 十分な理解なしに修正実施
2. **機能破壊**: 利便性を損なう修正の実施
3. **矛盾した結論**: 問題の原因と解決策の論理的整合性の欠如

## 今後の対応が必要な項目

1. **ファイルパターン展開システムの完全な修正**
2. **複数ファイルパターンへの適切な対応**
3. **テンプレート展開機能の改善**
4. **エラーハンドリングの体系化**
5. **設計ドキュメントの整備**

## 結論

元の実装には確実に問題があり、修正が必要でした。しかし、根本原因を理解せずに場当たり的な修正を重ねた結果、機能を破壊し、最終的に偶然動作する状態になりました。これは技術的にも開発手法的にも問題のあるアプローチでした。