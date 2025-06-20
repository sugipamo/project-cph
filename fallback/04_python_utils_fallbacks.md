# Python Utils関連フォールバック処理修正タスク

## 概要
Python実行環境関連のユーティリティで検出された2つのフォールバック処理を適切なエラーハンドリングまたは設定ベースの実装に置き換える。

## 対象ファイルと修正箇所

### 1. infrastructure/drivers/python/utils/python_utils.py:37
- **パターン**: or演算子でのフォールバック
- **優先度**: 高
- **推定修正方法**: Pythonインタープリター設定の明示的取得

### 2. infrastructure/drivers/python/utils/python_utils.py:60
- **パターン**: try-except でのフォールバック代入
- **優先度**: 高
- **推定修正方法**: Python環境検出の明示的エラーハンドリング

## コンテキスト分析

このファイルは競技プログラミング環境でのPython実行に関わる重要な部分であり、以下の機能を担っている可能性：
- Pythonインタープリターの検出
- Pythonバージョンの確認
- 実行環境の設定
- パッケージの存在確認

## 関連設定ファイル

### 既存設定（参考）
- `contest_env/python/env.json` - Python固有の環境設定

### 追加が必要な設定（想定）
```json
{
  "python_config": {
    "interpreters": {
      "default": "python3",
      "alternatives": ["python3.11", "python3.10", "python", "/usr/bin/python3"],
      "minimum_version": "3.8.0"
    },
    "execution": {
      "default_timeout": 30,
      "memory_limit": "256MB",
      "working_directory": ".",
      "encoding": "utf-8"
    },
    "packages": {
      "required": ["sys", "os", "subprocess"],
      "optional": ["numpy", "scipy"],
      "check_availability": true
    },
    "error_handling": {
      "interpreter_not_found": "error",
      "version_mismatch": "warning",
      "package_missing": "warning"
    }
  }
}
```

## 修正アプローチ

1. **インタープリター検出の改善**
   - 設定ファイルからのインタープリター候補リスト取得
   - 順次試行による最適なインタープリター選択
   - 明示的なエラーメッセージ

2. **環境検証の強化**
   - Pythonバージョンチェック
   - 必要パッケージの存在確認
   - 実行権限の確認

3. **エラーハンドリングの明確化**
   - 具体的な例外型の使用
   - ユーザーフレンドリーなエラーメッセージ
   - デバッグ情報の提供

## 典型的な修正パターン

### Before (フォールバック)
```python
# or演算子でのフォールバック
python_cmd = config.get('python_command') or 'python3'

# try-except でのフォールバック代入
try:
    version = get_python_version()
except Exception:
    version = '3.8.0'  # フォールバック値
```

### After (設定ベース + 明示的処理)
```python
# 設定からの明示的取得
try:
    python_cmd = self.config_manager.resolve_config(['python_config', 'interpreters', 'default'], str)
except KeyError:
    raise PythonConfigError("No default Python interpreter configured")

# 明示的な例外処理
try:
    version = get_python_version()
except PythonVersionError as e:
    minimum_version = self.config_manager.resolve_config(['python_config', 'interpreters', 'minimum_version'], str)
    raise PythonEnvironmentError(f"Python version check failed. Minimum required: {minimum_version}") from e
```

## Python環境の特殊性

1. **マルチバージョン対応**
   - Python 2.x/3.x の共存環境
   - 複数のPython 3.xバージョン

2. **仮想環境対応**
   - venv, virtualenv, conda環境
   - パッケージ分離

3. **プラットフォーム差異**
   - Windows: `python.exe`
   - Unix系: `python3`, `python`
   - パス区切り文字の違い

## テスト戦略

1. **環境テスト**
   - 異なるPythonバージョンでのテスト
   - 仮想環境でのテスト
   - パッケージ不在環境でのテスト

2. **設定テスト**
   - 有効な設定での動作確認
   - 無効な設定でのエラーハンドリング
   - 設定不在時の動作

3. **統合テスト**
   - 実際のPythonコード実行
   - タイムアウト処理
   - エラー出力の確認

## 完了条件

- [ ] 2つのフォールバック処理をすべて修正
- [ ] Python実行環境の検出が正常に動作
- [ ] 様々なPython環境でのテストが通過
- [ ] エラーメッセージが分かりやすい
- [ ] 設定ファイル`python_config.json`が追加されている
- [ ] 仮想環境でも正常に動作することを確認